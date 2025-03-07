from termcolor import cprint
from .base import VideoCrawler
from .comment import CommentCrawler
from .profile import ProfileCrawler
from ..utils import Logger

log = Logger(name="TrendingVideoCrawler")


class TrendingVideoCrawler(VideoCrawler):
    def crawl(self, type: str, region: str, count: str, request_id: int):
        """Crawl videos for a given keyword from TikTok.

        Args:
            type (str): Type of video to fetch.
            region (str): Region code.
            count (str): Number of videos to fetch.
            request_id (int): Unique request ID for the crawl.

        Returns:
            None
        """
        cprint("Fetching trending videos...", "green", attrs=["bold"])
        log.info("Fetching trending videos...")
        url = "https://tiktok-scraper7.p.rapidapi.com/feed/list"
        video_list = self.fetch_videos(url=url, type=type, region=region, count=count)
        if video_list is None:
            print("No videos found!")
            log.info("No videos found!")
            return []

        # Save videos to the database
        self.save_videos_to_db(
            video_list=video_list, video_type="trending", request_id=request_id
        )

        # Crawl and store comments and replies for each video
        for video in video_list:
            # Fetch author's profile
            ProfileCrawler().crawl(
                username=video["author"]["unique_id"], userid=video["author"]["id"]
            )

            # Fetch comments and replies
            CommentCrawler().crawl(
                video_id=video["video_id"],
                username=video["author"]["unique_id"],
                count="5",
                request_id=request_id,  # Pass the request_id here
            )

        log.info(f"Processed {len(video_list)} trending videos.")
        print(f"Processed {len(video_list)} trending videos.")

        return video_list
