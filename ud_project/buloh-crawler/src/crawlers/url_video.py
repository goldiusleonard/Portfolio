import httpx
from .base import VideoCrawler
from .profile import ProfileCrawler
from .comment import CommentCrawler
from typing import List
from ..utils import Logger

log = Logger(name="VideoURLCrawler")


class URLVideoCrawler(VideoCrawler):
    def __init__(self) -> None:
        super().__init__()

    def crawl(self, urls: List[str], request_id: int) -> list:
        video_list: list = []
        url = "https://tiktok-scraper7.p.rapidapi.com/"
        for video_url in urls:
            querystring = {"url": video_url, "hd": "1"}
            response = httpx.get(url, headers=self.headers, params=querystring).json()

            # Fetch author's profile
            ProfileCrawler().crawl(
                username=response["data"]["author"]["unique_id"],
                userid=response["data"]["author"]["id"],
            )
            log.info(f"Fetched: {response['data']['author']['unique_id']}")

            # Fetch comments and replies
            CommentCrawler().crawl(
                video_id=response["data"]["id"],
                username=response["data"]["author"]["unique_id"],
                count="5",
                request_id=request_id,  # Pass the request_id here
            )
            log.info(
                f"Fetched Comments and Replies for Video: {response['data']['id']}"
            )

            # Append video to the list
            video_list.append(response["data"])

        self.save_videos_to_db(
            video_list=video_list, video_type="agent", request_id=request_id
        )
        log.info(f"Saved {len(video_list)} videos from agent-builder to database")

        return video_list
