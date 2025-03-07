import time
from typing import Optional, List, Dict
from .base import Crawler
from ..utils import send_api_request, Logger

log = Logger(name="ReplyCrawler")


class ReplyCrawler(Crawler):
    def crawl(self, video_id: str, comment_id: str, count: str) -> Optional[List[Dict]]:
        """Crawl replies for a given comment from TikTok.

        Args:
            video_id (str): TikTok video ID.
            comment_id (str): TikTok comment ID.
            count (str): Number of replies to fetch.

        Returns:
            comment_reply_list (list): List of comment replies or None in case of an error.
        """
        url = "https://tiktok-scraper7.p.rapidapi.com/comment/reply"
        querystring = {
            "video_id": video_id,
            "comment_id": comment_id,
            "count": count,
        }
        comment_reply_list = self._fetch_reply_comments(url=url, params=querystring)
        if comment_reply_list is None:
            log.info("No replies found!")
            return None

        print(f"{len(comment_reply_list)} replies fetched")
        log.info(f"{len(comment_reply_list)} replies fetched")
        return comment_reply_list

    def _fetch_reply_comments(self, url: str, params: Dict) -> List[Dict]:
        time.sleep(3)
        response: dict = send_api_request(url=url, headers=self.headers, params=params)

        if "error" in response:
            print(response["error"])
            log.info(response["error"])
            return []

        if "data" not in response or not isinstance(response["data"], dict):
            return []

        response_data: dict = response["data"]

        if "comments" in response_data and isinstance(response_data["comments"], list):
            return response_data["comments"]

        return []
