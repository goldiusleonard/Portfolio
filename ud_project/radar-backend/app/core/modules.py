"""Core module for the application."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI  # Moved into type-checking block

from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers.api import router


def init_routers(app_: FastAPI) -> None:
    """Initialize the routers for the FastAPI application.

    Args:
        app_: The FastAPI application instance to which the routers will be added.

    """
    app_.include_router(router)


def make_middleware() -> list[Middleware]:
    """Create and return a list of middleware for the FastAPI application.

    Returns:
    - A list of Middleware instances.

    """
    origins = ["*"]
    return [
        Middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
    ]
