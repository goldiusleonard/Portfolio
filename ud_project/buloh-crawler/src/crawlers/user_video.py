from typing import List, Dict
from termcolor import cprint
from .base import VideoCrawler
from .comment import CommentCrawler
from .profile import ProfileCrawler
from ..utils.logger import Logger

log = Logger(name="UserVideoCrawler")


class UserVideoCrawler(VideoCrawler):
    def crawl(
        self,
        type: str,
        username: str,
        count: str,
        cursor: str,
        request_id: int,
    ) -> List[Dict]:
        """Crawl videos for a given username from TikTok.

        Args:
            type (str): Type of video to fetch.
            username (str): TikTok username.
            count (int): Number of videos to fetch.
            cursor (str): Cursor for pagination.

        Returns:
            list[Dict]: list of videos.
        """
        cprint(f"Fetching videos for [{username}]...", "green", attrs=["bold"])
        log.info(f"Fetching videos for [{username}]...")
        url = "https://tiktok-scraper7.p.rapidapi.com/user/posts"
        video_list = self.fetch_videos(
            url=url,
            type=type,
            username=username,
            video_count=count,
            cursor=cursor,
        )
        if video_list is None:
            print("No videos found!")
            log.info("No videos found!")
            return []

        # Save videos to the database
        self.save_videos_to_db(
            video_list=video_list, video_type="user", request_id=request_id
        )

        # Crawl and store comments and replies for each video
        for video in video_list:
            # Fetch author's profile
            ProfileCrawler().crawl(
                username=video["author"]["unique_id"], userid=video["author"]["id"]
            )

            # Fetch coments and replies
            CommentCrawler().crawl(
                video_id=video["video_id"],
                username=video["author"]["unique_id"],
                request_id=video["request_id"],
                count="5",
            )

        return video_list
