"""Main module for ada-knowledge-injector FastAPI application."""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.endpoints.functions.watchlist_function import (
    initialize_monitoring,
    shutdown_monitoring,
)
from app.core.modules import init_routers, make_middleware
from utils.logger import Logger

logger = Logger(__name__)


@asynccontextmanager
async def lifespan(app_: FastAPI):  # noqa: ARG001, ANN201
    """Application lifespan event handler."""
    try:
        logger.info("Starting up: Initializing watchlist monitoring.")
        await initialize_monitoring()
        yield
    finally:
        logger.info("Shutting down: Cleaning up watchlist monitoring.")
        await shutdown_monitoring()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns
    -------
    FastAPI
        The configured FastAPI application instance.

    """
    app_ = FastAPI(
        title="radar_business_agent",
        description="All the modules for radar_business_agent fast API",
        version="1.0.0",
        middleware=make_middleware(),
        lifespan=lifespan,
        docs_url="/",
        redoc_url="/redocs",
    )
    init_routers(app_=app_)
    return app_


app = create_app()


@app.get("/healthz", response_class=JSONResponse)
async def healthz() -> dict:
    """Health check endpoint to verify the application's status.

    Returns a 200 OK status with a message if the app is healthy.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
