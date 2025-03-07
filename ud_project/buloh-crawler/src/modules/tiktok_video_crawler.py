import logging
import os

from datetime import datetime
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from dotenv import load_dotenv
from fastapi import HTTPException, APIRouter
from pydantic import BaseModel
from typing import List
from pytz import timezone
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from ..database.connection import MySQLConnection
from ..utils import Logger
from ..scheduler import schedule_crawling

# Get the current time
current_time = datetime.now()

log = Logger(name="API Run")
# Set up logging to log messages to the terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

scheduler = None

# Set timezone
MYT = timezone("Asia/Kuala_Lumpur")


@asynccontextmanager
async def lifespan(router: APIRouter):
    global scheduler
    scheduler = BackgroundScheduler()
    scheduler.start()
    yield


router = APIRouter()


# Middleware for API key validation
class APIKeyMiddleware(BaseHTTPMiddleware):
    EXCLUDED_PATHS = {"/status", "/docs", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        # Check if the request path is in the excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            response = await call_next(request)
            return response

        # API key validation
        headers = request.headers
        api_key = os.getenv("API_KEY")

        if headers.get("Authorization") != api_key:
            return Response(content="Invalid API key", status_code=401)

        response = await call_next(request)
        return response


# Define the Tag and StartCrawlRequest models
class Tag(BaseModel):
    type: str  # Either "keyword" or "username"
    value: str  # the actual keyword or username


class StartCrawlRequest(BaseModel):
    tags: List[Tag]
    category: str
    subcategory: str
    fromDate: str
    toDate: str
    tiktok: bool  # Accept as string ("true" or "false")
    news: bool  # Accept as string ("true" or "false")


@router.post("/start-crawling")
def start_tiktok_post_crawling(request: StartCrawlRequest):
    # Validate input for tag types
    if any(tag.type not in ["keyword", "username", "url"] for tag in request.tags):
        raise HTTPException(status_code=400, detail="Invalid type in tags")

    try:
        # If TikTok is False, skip crawling
        if not request.tiktok:
            logger.info(
                f"Crawl cannot be initiated for TikTok as it is unticked. tiktok: {request.tiktok}"
            )
            return {
                "message": "Crawl cannot be initiated for TikTok as it is unticked.",
                "tiktok": False,
            }

        # Prepend the subcategory to keywords
        for tag in request.tags:
            if tag.type == "keyword":
                # Split the values and prepend the subcategory to each
                tag.value = ", ".join(
                    [
                        f"{request.subcategory} {value.strip()}"
                        for value in tag.value.split(",")
                    ]
                )

        # Save main data to the database
        with MySQLConnection() as db:
            cursor = db.get_cursor()
            # Get current timestamp in Malaysian time
            created_at = datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S")

            # Insert into crawling_data table
            sql_request = """
            INSERT INTO crawling_data (category, subcategory, from_date, to_date, tiktok, news, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                sql_request,
                (
                    request.category,
                    request.subcategory,
                    request.fromDate,
                    request.toDate,
                    request.tiktok,
                    request.news,
                    created_at,
                ),
            )
            request_id = cursor.lastrowid

            # Insert tags into the tags table
            sql_tags = "INSERT INTO tags (request_id, type, value) VALUES (%s, %s, %s)"
            for tag in request.tags:
                # Split values with commas into individual tags
                for value in tag.value.split(","):
                    cursor.execute(sql_tags, (request_id, tag.type, value.strip()))

            db.connection.commit()

            # Group tags by type and split comma-separated values
            usernames = [
                tag.value.split(",") for tag in request.tags if tag.type == "username"
            ]
            keywords = [
                item
                for sublist in [
                    tag.value.split(",")
                    for tag in request.tags
                    if tag.type == "keyword"
                ]
                for item in sublist
            ]
            urls = [tag.value.split(",") for tag in request.tags if tag.type == "url"]

            # Schedule each keyword, username, and URL individually
            schedule_crawling(
                request_id,
                request.fromDate,
                request.toDate,
                {"type": "keyword", "inputs": keywords},
            )

            # Flatten the list of usernames and URLs (if necessary)
            flat_usernames = [
                username.strip() for sublist in usernames for username in sublist
            ]
            flat_urls = [url.strip() for sublist in urls for url in sublist]

            # Schedule the usernames and URLs
            if flat_usernames:
                schedule_crawling(
                    request_id,
                    request.fromDate,
                    request.toDate,
                    {"type": "username", "inputs": flat_usernames},
                )

            if flat_urls:
                schedule_crawling(
                    request_id,
                    request.fromDate,
                    request.toDate,
                    {"type": "url", "inputs": flat_urls},
                )

        db.connection.close()
        return {
            "message": "Crawl request stored and initiated successfully",
            "request_id": request_id,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing crawl request: {str(e)}"
        )
