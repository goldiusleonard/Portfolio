"""Routing for Fetching Keyword Trend."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

app = APIRouter()


@app.get("/healthz", response_class=JSONResponse)
async def healthz() -> dict:
    """Health check endpoint to verify the application's status.

    Returns a 200 OK status with a message if the app is healthy.
    """
    return {"status": "healthy"}
