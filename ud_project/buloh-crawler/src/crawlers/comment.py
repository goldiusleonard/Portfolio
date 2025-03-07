import time
from .base import Crawler
from termcolor import cprint
from typing import Optional, List, Dict
from ..utils import send_api_request, Logger
from ..database.connection import MongoDBClient
from datetime import datetime

log = Logger(name="CommentCrawler")


class CommentCrawler(Crawler):
    def crawl(self, video_id: str, username: str, count: str, request_id: int) -> None:
        """Crawl comments and replies for a given video from TikTok.

        Args:
            video_id (str): TikTok video ID.
            username (str): TikTok username.
            count (str): Number of comments to fetch.

        Returns:
            None
        """
        cprint(
            f"Fetching comments and replies for video ID: [{video_id}]...",
            "green",
            attrs=["bold"],
        )
        log.info(f"Fetching comments and replies for video ID: [{video_id}]...")
        # -------------------------
        # Fetch comments
        url = "https://tiktok-scraper7.p.rapidapi.com/comment/list"
        querystring = {
            "url": f"https://www.tiktok.com/@{username}/video/{video_id}",
            "count": 10,
        }
        comment_list = self._fetch_comments(url=url, params=querystring)
        if comment_list is None:
            return None

        print(f"{len(comment_list)} comments fetched")
        log.info(f"{len(comment_list)} comments fetched")

        # -------------------------
        # Fetch reply comments
        # for comment in comment_list:
        #     print(f"Comment ID: {comment['id']}")
        #     log.info(f"Comment ID: {comment['id']}")
        #     # rename comment [id] to [comment_id]
        #     comment["comment_id"] = comment["id"]
        #     replies = ReplyCrawler().crawl(
        #         video_id=video_id, comment_id=comment["id"], count="5"
        #     )
        #     if replies is None:
        #         continue
        #     comment["replies"] = replies

        # -------------------------
        # Save comments to the database
        self._save_comments_to_db(comment_list, request_id=request_id)

    def _fetch_comments(self, url: str, params: Dict) -> Optional[List[Dict]]:
        time.sleep(3)
        response: dict = send_api_request(url=url, headers=self.headers, params=params)
        if "error" in response:
            print(response["error"])
            log.error(response["error"])
            return None

        if "data" in response and isinstance(response["data"], dict):
            if "comments" in response["data"] and isinstance(
                response["data"]["comments"], list
            ):
                return response["data"]["comments"]

        return None

    def _save_comments_to_db(self, comments: List[Dict], request_id: int) -> None:
        with MongoDBClient() as db:
            for comment in comments:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                comment["updated_at"] = now
                comment["created_at"] = now
                comment["is_flagged"] = False
                comment["request_id"] = request_id  # Associate with request_id

                # Insert the comment into the database
                db["comment"].insert_one(comment)

        print(f"{len(comments)} comments stored in the database")
        log.info(f"{len(comments)} comments stored in the database")
