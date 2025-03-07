import os
import httpx
import time
from time import sleep
from dotenv import load_dotenv
from ..utils import Logger
from ..crawlers.user_video import UserVideoCrawler
from ..crawlers.keyword_video import KeywordVideoCrawler
from ..crawlers.trending_video import TrendingVideoCrawler
from ..crawlers.url_video import URLVideoCrawler

load_dotenv()


def trigger_fastapi(url: str):
    """Trigger the FastAPI endpoint to start a process."""
    log = Logger(name="FastAPI Trigger")
    try:
        log.info(f"Triggering FastAPI endpoint: {url}")
        # Ensure POST method is used
        response = httpx.post(url, timeout=30)

        if response.status_code == 200:
            log.info(f"Successfully triggered FastAPI endpoint: {url}")
            log.info(f"Response: {response.json()}")
        else:
            log.warning(
                f"FastAPI endpoint responded with status code: {response.status_code}. Response: {response.text}"
            )
    except Exception as e:
        log.error(f"Failed to trigger FastAPI endpoint: {url}. Error: {str(e)}")


def reconnect_and_trigger_haraz(url: str, retries: int = 3, delay: int = 60):
    """Attempt to reconnect and trigger FastAPI endpoint for 'haraz' with retries and 5-minute intervals."""
    log = Logger(name="Reconnection Handler")
    for attempt in range(retries):
        try:
            trigger_fastapi(url)
            break  # Exit loop if the trigger is successful
        except Exception:
            log.error(
                f"Attempt {attempt + 1} failed to trigger FastAPI. Retrying in {delay} seconds..."
            )
            if attempt < retries - 1:  # Don't sleep after last attempt
                sleep(delay)  # 5-minute delay for retrying
            else:
                log.error("All attempts to trigger FastAPI have failed.")


def start_crawl(type: str, inputs: list, request_id: int, tiktok: bool = True):
    log = Logger(name="CrawlerRun")
    log.info(
        f"Starting crawl of type: {type} with request_id: {request_id} and TikTok: {tiktok}"
    )
    crawled_video_ids = []

    try:
        if type == "username" and tiktok:
            all_usernames = [
                username.strip() for username in inputs if isinstance(username, str)
            ]
            all_usernames = [
                u for usernames in all_usernames for u in usernames.split(",")
            ]

            for username in all_usernames:
                log.info(f"Starting crawl for username: {username}")
                uvc = UserVideoCrawler()
                crawled_video_ids = uvc.crawl(
                    type="username",
                    username=username,
                    count="100",  # Ensure only 10 videos are crawled
                    cursor="0",
                    request_id=request_id,
                )
                log.info(
                    f"Completed crawl for username: {username}, Crawled video IDs: {crawled_video_ids}"
                )
                break  # Stop after crawling 10 videos

        elif type == "keyword":
            for keyword in inputs:
                log.info(f"Starting crawl for keyword: {keyword}")
                kwv = KeywordVideoCrawler()
                crawled_video_ids = kwv.crawl(
                    type="keyword",
                    keyword=keyword,
                    region="MY",
                    count="100",  # Ensure only 100 videos are crawled
                    cursor="0",
                    request_id=request_id,
                )
                log.info(
                    f"Completed crawl for keyword: {keyword}, Crawled video IDs: {crawled_video_ids}"
                )

        elif type == "trending":
            log.info("Starting crawl for trending videos")
            tvc = TrendingVideoCrawler()
            crawled_video_ids = tvc.crawl(
                type="trending", region="MY", count="1000", request_id=request_id
            )
            log.info(
                f"Completed crawl for trending videos, Crawled video IDs: {crawled_video_ids}"
            )

        elif type == "url":
            log.info("Starting crawl for URLs")
            urlvc = URLVideoCrawler()
            crawled_video_ids = urlvc.crawl(urls=inputs, request_id=request_id)
            log.info(
                f"Completed crawl for URLs, Crawled video IDs: {crawled_video_ids}"
            )

        else:
            log.error(f"Invalid crawl type: {type}")
            raise ValueError("Invalid crawl type specified")

        # Crawl completed message for request_id
        log.info(f"Crawl completed for request_id: {request_id}")

        # Remove the len() check and proceed to trigger APIs regardless of crawled_video_ids
        log.info("Crawl completed for the requset")
        log.info("Crawl completed, triggering FastAPI endpoints now...")

        # Trigger Transcription for 10 videos
        log.info("Triggering Transcription videos...")
        trigger_fastapi(f"{os.getenv('TRANSCRIPTION_URL')}/trigger/")  # Transcription
        time.sleep(
            5
        )  # Optional delay to ensure the system doesn't trigger requests too fast

        # Trigger Description for 10 videos
        log.info("Triggering Description videos...")
        trigger_fastapi(f"{os.getenv('DESCRIPTION_URL')}/trigger/")  # Description
        time.sleep(2)  # Optional delay

        # Trigger Haraz for 10 videos (with reconnect mechanism, retry every 5 minutes)
        log.info("Triggering Haraz for videos...")
        reconnect_and_trigger_haraz(f"{os.getenv('HARAZ_URL')}/Haraz")

    except Exception as e:
        log.error(f"Error occurred during crawl: {str(e)}")
        raise
