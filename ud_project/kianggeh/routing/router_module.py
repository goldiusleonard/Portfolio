"""Routing for Generate Keyword Trend."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI  # Moved into type-checking block

from routing.router import router


def init_routers(app_: FastAPI) -> None:
    """Initialize the routers for the FastAPI application.

    Args:
        app_: The FastAPI application instance to which the routers will be added.

    """
    app_.include_router(router)
