import logging
import os

from fastapi import Query, APIRouter
from fastapi.responses import JSONResponse
from apify_client import ApifyClient

# Initialize FastAPI Router
router = APIRouter()


# Your Apify API token
APIFY_API_TOKEN = os.getenv("TIKTOK_APIFY_API_TOKEN")


### 1. Scrape TikTok by Hashtag
@router.get("/by/hashtag")
async def scrape_tiktok_by_hashtag(
    hashtag: str = Query(..., description="Hashtag to scrape"),
    max_videos: int = Query(100, description="Number of maximum videos to scrape"),
):
    """Scrapes TikTok videos based on a given hashtag."""
    try:
        client = ApifyClient(APIFY_API_TOKEN)
        run_input = {
            "excludePinnedPosts": False,
            "hashtags": [hashtag],
            "resultsPerPage": max_videos,
            "shouldDownloadCovers": False,
            "shouldDownloadSlideshowImages": False,
            "shouldDownloadSubtitles": False,
            "shouldDownloadVideos": False,
        }

        run = client.actor("clockworks/free-tiktok-scraper").call(run_input=run_input)
        results = list(client.dataset(run["defaultDatasetId"]).iterate_items())

        return JSONResponse(content={"videos": results}, status_code=200)

    except Exception as e:
        logging.error(f"Error scraping TikTok data: {str(e)}")
        return JSONResponse(
            content={"error": "Failed to fetch TikTok data", "details": str(e)},
            status_code=500,
        )


### 2. Scrape TikTok by Profile Username
@router.get("/by/profile")
def scrape_tiktok_by_profile(
    username: str = Query(..., description="TikTok username to scrape"),
    max_videos: int = Query(10, description="Number of max videos to scrape"),
):
    """Scrapes TikTok videos based on profile username."""
    try:
        client = ApifyClient(APIFY_API_TOKEN)
        run_input = {
            "excludePinnedPosts": False,
            "profiles": [username],
            "resultsPerPage": max_videos,
            "shouldDownloadCovers": False,
            "shouldDownloadSlideshowImages": False,
            "shouldDownloadSubtitles": False,
            "shouldDownloadVideos": False,
        }

        run = client.actor("clockworks/free-tiktok-scraper").call(run_input=run_input)
        results = list(client.dataset(run["defaultDatasetId"]).iterate_items())

        return JSONResponse(content={"videos": results}, status_code=200)

    except Exception as e:
        return JSONResponse(
            content={"error": "Failed to fetch TikTok data", "details": str(e)},
            status_code=500,
        )


### 3. Scrape TikTok by Keyword
@router.get("/by/keyword")
def scrape_tiktok_by_keyword(
    keyword: str = Query(..., description="Keyword to scrape"),
    max_videos: int = Query(10, description="Number of max videos to scrape"),
):
    """Scrapes TikTok videos based on given keyword."""
    try:
        client = ApifyClient(APIFY_API_TOKEN)
        run_input = {
            "excludePinnedPosts": False,
            "resultsPerPage": max_videos,
            "searchQueries": [keyword],
            "shouldDownloadCovers": False,
            "shouldDownloadSlideshowImages": False,
            "shouldDownloadSubtitles": False,
            "shouldDownloadVideos": False,
        }

        run = client.actor("clockworks/free-tiktok-scraper").call(run_input=run_input)
        results = list(client.dataset(run["defaultDatasetId"]).iterate_items())

        return JSONResponse(content={"videos": results}, status_code=200)

    except Exception as e:
        return JSONResponse(
            content={"error": "Failed to fetch TikTok data", "details": str(e)},
            status_code=500,
        )


### 4. Scrape TikTok by Video URL
@router.get("/by/videourl")
def scrape_tiktok_by_url(
    video_url: str = Query(..., description="TikTok video URL to scrape"),
):
    """Scrapes TikTok video details based on video URL."""
    try:
        client = ApifyClient(APIFY_API_TOKEN)
        run_input = {
            "excludePinnedPosts": False,
            "postURLs": [video_url],
            "shouldDownloadCovers": False,
            "shouldDownloadSlideshowImages": False,
            "shouldDownloadSubtitles": False,
            "shouldDownloadVideos": False,
        }

        run = client.actor("clockworks/free-tiktok-scraper").call(run_input=run_input)
        results = list(client.dataset(run["defaultDatasetId"]).iterate_items())

        return JSONResponse(content={"videos": results}, status_code=200)

    except Exception as e:
        return JSONResponse(
            content={"error": "Failed to fetch TikTok data", "details": str(e)},
            status_code=500,
        )


### 5. Scrape TikTok Trends
@router.get("/by/trend")
async def scrape_tiktok_trends(
    limit: int = Query(10, description="Number of maximum videos to scrape"),
    region: str = Query(None, description="Optional region code (e.g., US, MY, IN)"),
):
    """Scrapes trending TikTok videos with an optional region filter."""
    try:
        # Initialize Apify Client
        client = ApifyClient(APIFY_API_TOKEN)

        # Prepare input for the Apify Actor
        run_input = {
            "limit": limit,
            "region": region
            if region
            else "",  # Use empty string if no region is provided
            "proxyConfiguration": {"useApifyProxy": False},
        }

        # Run the Apify Actor
        run = client.actor("novi/tiktok-trend-api").call(run_input=run_input)
        results = list(client.dataset(run["defaultDatasetId"]).iterate_items())

        return JSONResponse(content={"trending_videos": results}, status_code=200)

    except Exception as e:
        logging.error(f"Error scraping TikTok trends: {str(e)}")
        return JSONResponse(
            content={"error": "Failed to fetch TikTok trends", "details": str(e)},
            status_code=500,
        )
