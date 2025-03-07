"""Main module for ada-knowledge-injector FastAPI application."""

import httpx
from fastapi import FastAPI

from app.core.modules import init_routers, make_middleware
from utils.topic_keyword_generator import TopicKeywordGenerator


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns
    -------
    FastAPI
        The configured FastAPI application instance.

    """
    app_ = FastAPI(
        title="Topic Keyword Generator",
        description="All the modules for Topic Keyword Generator fast API",
        version="1.0.0",
        middleware=make_middleware(),
        docs_url="/",
        redoc_url="/redocs",
    )
    init_routers(app_=app_)
    return app_


app = create_app()


@app.put("/tkg/")
async def call_tkg_endpoint() -> str:
    """Endpoint to call the TopicKeywordGenerator function.

    This endpoint will trigger the topic keyword generation process.
    The process will generate the topic and keywords for each video
    in the database and store them in the database.

    Returns
    -------
    str
        The number of new videos and updated videos after the process is finished.

    """
    # Create an instance of the TopicKeywordGenerator class
    tkg = TopicKeywordGenerator()

    # Call the run method of the TopicKeywordGenerator instance
    number_new_videos, number_updated_videos = tkg.run()

    # Trigger the external endpoint before returning the response
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://18.143.205.116:8016/update_content_data_asset",
        )
        status_code = 200
        if response.status_code != status_code:
            return "Error triggering the content data asset endpoint"

    # If there are no new videos to process, return a message
    if number_new_videos == 0 and number_updated_videos == 0:
        return "No new videos to process"

    # If there are new videos to process, return the number of new videos and updated videos
    return (
        f"Number of unprocessed videos detected: {number_new_videos} , "
        f"Number of videos processed and upserted: {number_updated_videos}"
    )


@app.put("/tkg_on_the_fly/")
async def call_tkg_for_on_the_fly(payload: str) -> dict:
    """Endpoint to call the TopicKeywordGenerator function that process on the fly.

    This endpoint will trigger the topic keyword generation process.
    The process will generate the topic and keywords for each video
    in the database and store them in the database.

    """
    # Create an instance of the TopicKeywordGenerator class
    tkg = TopicKeywordGenerator()

    return tkg.process_on_the_fly(payload)
