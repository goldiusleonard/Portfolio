"""Routing for Checking Health."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

healthz_app = APIRouter()


@healthz_app.get("/healthz", response_class=JSONResponse)
async def healthz() -> dict:
    """Health check endpoint to verify the application's status.

    Returns a 200 OK status with a message if the app is healthy.
    """
    return {"status": "healthy"}
