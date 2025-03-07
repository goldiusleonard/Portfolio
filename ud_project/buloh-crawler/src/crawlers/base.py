import time
import os

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv
from pytz import timezone
from ..database.connection import MongoDBClient
from ..utils import send_api_request, Logger, helpers, get_env_variable

load_dotenv()

AWS_BUCKET_NAME: str = os.getenv("AWS_BUCKET_NAME", "")

if AWS_BUCKET_NAME == "":
    raise ValueError("AWS_BUCKET_NAME is not set in the environment variables")

# Set timezone
MYT = timezone(os.getenv("TIMEZONE"))

log = Logger(name="BaseCrawlers")

# Set how many times to fetch videos
# if API hasMore flag is True
FETCH_NUM = 1

bucket_name: str = get_env_variable(
    "AWS_BUCKET_NAME", "AWS_BUCKET_NAME is not provided!"
)


class Crawler(ABC):
    def __init__(self) -> None:
        self.headers = {
            "x-rapidapi-key": "a6863c9089msh9ca0d472abf6e7dp1309fdjsn27ff658cfa5c",
            "x-rapidapi-host": "tiktok-scraper7.p.rapidapi.com",
        }

    @abstractmethod
    def crawl(self, *args, **kwargs):
        pass


class VideoCrawler(Crawler):
    def __init__(self) -> None:
        super().__init__()
        self.FETCH_NUM = FETCH_NUM

    @abstractmethod
    def crawl(self, *args, **kwargs):
        pass

    def fetch_videos(self, url, **kwargs) -> List[Dict]:
        querystring = self._choose_querystring(**kwargs)
        tmp_video_list: list = []
        time.sleep(3)  # Be respectful of API rate limits
        response: dict = send_api_request(
            url=url, headers=self.headers, params=querystring
        )

        if "error" in response:
            print(response["error"])
            log.info(response["error"])
            return []

        # Trending check here, since it doesn't have pagination
        # and we need to fetch all videos and store them
        if kwargs["type"] == "trending":
            return response["data"]

        print(f"First time fetched: {len(response['data']['videos'])} videos")
        log.info(f"First time fetched: {len(response['data']['videos'])} videos")
        tmp_video_list.extend(response["data"]["videos"])

        video_list = self._fetch_more_videos(
            response=response,
            url=url,
            querystring=querystring,
            tmp_video_list=tmp_video_list,
        )

        if video_list is None:
            return []

        return video_list

    def _choose_querystring(self, **kwargs) -> Dict[str, str]:
        if kwargs["type"] == "username":
            querystring = {
                "unique_id": kwargs["username"],
                "count": kwargs["video_count"],
                "cursor": kwargs["cursor"],
            }
        elif kwargs["type"] == "keyword":
            querystring = {
                "keywords": kwargs["keyword"],
                "region": kwargs["region"],
                "count": kwargs["count"],
                "cursor": kwargs["cursor"],
                "publish_time": "180",  # last 6 months
                "sort_type": "0",
            }
        elif kwargs["type"] == "trending":
            querystring = {"region": kwargs["region"], "count": kwargs["count"]}
        elif kwargs["type"] == "url":
            querystring = {"region": kwargs["region"], "count": kwargs["count"]}
        else:
            return {
                "error": "Please choose a valid type. [username, keyword, trending]"
            }

        return querystring

    def _fetch_more_videos(
        self, response: dict, url: str, querystring: dict, tmp_video_list: list
    ) -> List[Dict]:
        fetch_count = 0

        if "data" not in response or not isinstance(response["data"], dict):
            return []

        response_data: dict = response["data"]

        while response_data.get("hasMore", False) and fetch_count < self.FETCH_NUM:
            print("Fetching more videos...")
            log.info("Fetching more videos...")
            time.sleep(3)  # Be respectful of API rate limits

            querystring["cursor"] = response_data.get("cursor", "")
            response = send_api_request(
                url=url, headers=self.headers, params=querystring
            )

            if "error" in response:
                print(response["error"])
                log.info(str(response["error"]))
                return []

            if response.get("msg") != "success":
                print("Failed to fetch videos")
                log.info("Failed to fetch videos")
                return []

            new_response_data = response.get("data", {})

            if not isinstance(new_response_data, dict):
                return tmp_video_list

            # Update response_data for the next iteration
            response_data = new_response_data

            # Log fetched videos
            videos = response_data.get("videos", [])
            if not isinstance(videos, list):
                return tmp_video_list

            print(f"Newly fetched: {len(videos)} videos")
            log.info(f"Newly fetched: {len(videos)} videos")

            tmp_video_list.extend(videos)
            fetch_count += 1

        return tmp_video_list

    def save_videos_to_db(
        self, video_list: List[Dict], video_type: str, request_id: int
    ) -> None:
        """
        Save videos to MongoDB and update timestamps, including location information.

        Args:
            video_list (List[Dict]): List of video dictionaries to be saved.
            video_type (str): Type of the video source.
            request_id (int): ID associated with the request.
        """
        video_count = 0
        with MongoDBClient() as db:
            for video in video_list:
                if video["region"] != "MY":
                    continue

                if "video_id" not in video:
                    video["video_id"] = video["id"]

                now = datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S")
                video["updated_at"] = now
                video["request_id"] = request_id  # Associate with request_id

                video["created_at"] = now
                video["is_flagged"] = False
                video["video_source"] = video_type

                # Include location if available
                video["location"] = video.get(
                    "location", "Unknown"
                )  # Default to 'Unknown' if no location provided

                # Check for existing video with the same video_id and request_id
                existing_video = db["video"].find_one(
                    {"video_id": video["video_id"], "request_id": request_id}
                )

                if existing_video:
                    log.info(
                        f"Video ID: {video['video_id']} already exists for request ID {request_id}. Skipping..."
                    )
                    continue  # Skip to the next video

                # Split datetime into date, month, year
                year, month, day = video["created_at"].split(" ")[0].split("-")
                video["year"] = int(year)
                video["month"] = int(month)
                video["day"] = int(day)

                # Storing video into Azure Blob and set blob URL
                video_data = helpers.download_file(video["play"])
                if not video_data:
                    raise RuntimeError("Video data download failed!")

                video["play"] = helpers.upload_s3_file(
                    bucket_name=bucket_name,
                    filename=video["video_id"],
                    data=video_data,
                    extension="mp4",
                    folder="videos",
                )

                # Storing video cover into Azure Blob and set blob URL
                video_cover = helpers.download_file(video["cover"])

                if not video_cover:
                    raise RuntimeError("Video cover download failed!")

                video["cover"] = helpers.upload_s3_file(
                    bucket_name=bucket_name,
                    filename=video["video_id"],
                    data=video_cover,
                    extension="jpg",
                    folder="video-covers",
                )

                video_count += 1

                video["updated_at"] = now  # Always update the timestamp
                db["video"].insert_one(video)
                log.info(
                    f"Video ID: {video['video_id']} stored as a new data in the database with location: {video['location']}"
                )

        print(f"{video_count} videos stored in the database")
        log.info(f"Total {video_count} videos stored in the database")
