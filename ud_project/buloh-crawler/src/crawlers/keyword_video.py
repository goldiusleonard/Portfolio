from typing import List, Dict
from termcolor import cprint
from .base import VideoCrawler
from .profile import ProfileCrawler
from .comment import CommentCrawler
from ..utils import Logger

log = Logger(name="KeywordVideoCrawler")


class KeywordVideoCrawler(VideoCrawler):
    def crawl(
        self,
        type: str,
        keyword: str,
        region: str,
        count: str,
        cursor: str,
        request_id: int,
    ) -> List[Dict]:
        """Crawl videos for a given keyword from TikTok.

        Args:
            type (str): Type of video to fetch.
            keyword (str): TikTok keyword.
            region (str): Region code.
            count (str): Number of videos to fetch.
            cursor (str): Cursor for pagination.

        Returns:
            List[Dict]: list of videos.
        """
        cprint(f"Fetching videos for [{keyword}]...", "green", attrs=["bold"])
        log.info(f"Fetching videos for [{keyword}]...")
        url = "https://tiktok-scraper7.p.rapidapi.com/feed/search"
        video_list = self.fetch_videos(
            url=url,
            type=type,
            keyword=keyword,
            region=region,
            count=count,
            cursor=cursor,
        )
        if video_list is None:
            print("No videos found!")
            log.info("No videos found!")
            return []

        # Save videos to the database
        self.save_videos_to_db(
            video_list=video_list, video_type="keyword", request_id=request_id
        )

        for video in video_list:
            # Fetch author's profile
            ProfileCrawler().crawl(
                username=video["author"]["unique_id"], userid=video["author"]["id"]
            )

            # Fetch coments and replies
            CommentCrawler().crawl(
                video_id=video["video_id"],
                username=video["author"]["unique_id"],
                request_id=request_id,
                count="5",
            )

        return video_list
