import os
import uvicorn
from src.modules.news import router as newsapi_router
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from multiprocessing.pool import Pool

# Metadata for tags
tags_metadata = [
    {
        "name": "NewsAPI",
        "description": "Operations for retrieving relevant news articles using NewsAPI.",
    }
]

# FastAPI application with enhanced description and summary
app = FastAPI(
    debug=False,
    title="Putumayo-Agent",
    version=os.getenv("VERSION"),
    summary="A robust API for accessing and filtering news articles via NewsAPI.",
    description=(
        "The Putumayo-Agent allows users to retrieve news articles based on various "
        "parameters such as keywords, sources, or dates using the powerful NewsAPI service. "
        "With features like flexible query options and cross-origin support, this API serves as "
        "an excellent tool for building news aggregation and analysis applications."
    ),
    openapi_tags=tags_metadata,
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

app.include_router(newsapi_router, prefix="/news", tags=["NewsAPI"])


@app.get("/healthz", response_class=JSONResponse)
def healthz() -> dict:
    """Health check endpoint to verify the application's status.

    Returns a 200 OK status with a message if the app is healthy.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    with Pool() as mp_pool:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            h11_max_incomplete_event_size=5000000000,
            timeout_keep_alive=10,
        )
