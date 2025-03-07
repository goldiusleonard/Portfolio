import uvicorn
from vers import version
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.modules.live_tiktok_video_crawler import (
    router as live_tiktok_video_crawler_router,
    start_video_channel,
    close_video_channel,
)
from src.modules.tiktok_video_crawler import router as tiktok_video_crawler_router
from src.modules.live_tiktok_comment_crawler import (
    router as live_tiktok_comment_recorder_router,
    start_comment_channel,
    close_comment_channel,
)
from src.modules.twitter_crawler import router as twitter_crawler_router
from src.modules.instagram_content_crawler import (
    router as instagram_content_crawler_router,
)
from src.modules.facebook_crawler import router as facebook_crawler_router
from contextlib import asynccontextmanager
from src.modules.tiktok_crawler import router as tiktok_router

TAGS_METADATA: List[dict] = [
    {
        "name": "TikTok",
        "description": (
            "Endpoints for managing TikTok live stream recordings, live comment streaming, "
            "and automated crawling of video posts. This includes starting and stopping "
            "recordings, monitoring user live status, and extracting video data for analysis."
        ),
    },
    {
        "name": "Instagram",
        "description": (
            "Endpoints for managing Instagram content crawling. This includes scraping "
            "Instagram posts, stories, and user profiles for data analysis and storage."
        ),
    },
    {
        "name": "Facebook",
        "description": (
            "Endpoints for managing Facebook content crawling. This includes scraping "
            "Facebook posts, comments, user profiles, pages, and groups for data analysis "
            "and storage."
        ),
    },
    {
        "name": "Twitter",
        "description": (
            "Endpoints for fetching recent tweets based on a query and retrieving user details. "
            "This includes searching for tweets, fetching user information, and analyzing tweet data."
        ),
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager to handle startup and shutdown events."""
    start_video_channel()
    start_comment_channel()
    yield
    close_video_channel()
    close_comment_channel()


app = FastAPI(
    debug=False,
    title="Buloh-Crawler",
    summary="A comprehensive API for managing TikTok live streams, comment streaming, and video crawling.",
    description="""
    The **Buloh-Crawler API** is designed to automate and manage TikTok live stream data efficiently. 
    This includes recording live videos, streaming live comments in real-time, and extracting TikTok video post data for storage and analysis.

    ### Key Features:
    - **Live Video Recording**: Start or stop recording TikTok live streams.
    - **Live Comment Streaming**: Stream comments from TikTok live sessions in real-time.
    - **Live Status Monitoring**: Check if a user is currently live.
    - **Video Post Crawling**: Automate the crawling of TikTok video posts for analysis.

    This API supports multiple user IDs and usernames simultaneously, enabling scalable management of TikTok data workflows.
    """,
    version=version,
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=[
        "*",
    ],
)

app.include_router(live_tiktok_video_crawler_router, prefix="/tiktok", tags=["TikTok"])
app.include_router(tiktok_video_crawler_router, prefix="/tiktok", tags=["TikTok"])
app.include_router(
    live_tiktok_comment_recorder_router, prefix="/tiktok", tags=["TikTok"]
)
app.include_router(tiktok_router, prefix="/tiktok", tags=["TikTok"])
app.include_router(twitter_crawler_router, prefix="/twitter", tags=["Twitter"])
app.include_router(
    instagram_content_crawler_router, prefix="/instagram", tags=["Instagram"]
)
app.include_router(facebook_crawler_router, prefix="/facebook", tags=["Facebook"])


@app.get("/healthz", response_class=JSONResponse)
def healthz():
    """
    Health check endpoint to verify the application's status.
    Returns a 200 OK status with a message if the app is healthy.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        h11_max_incomplete_event_size=5000000000,
        timeout_keep_alive=10,
    )
