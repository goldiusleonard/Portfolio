"""Comment recording endpoints for the API."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.endpoints.functions.comment_recording_function import (
    start_comment_recording,
    stop_comment_recording,
)
from app.core.db_config import get_live_db

comment_router = APIRouter()


@comment_router.post("/start/")
async def start_comments(
    username: str,
    stream_id: str,
    user_id: str,
    live_db: Session = Depends(get_live_db),
) -> dict:
    """Start recording comments for a live stream."""
    return await start_comment_recording(username, stream_id, user_id, live_db)


@comment_router.post("/stop/")
async def stop_comments(
    username: str,
    user_id: str,
    live_db: Session = Depends(get_live_db),
) -> dict:
    """Stop recording comments for a live stream."""
    return await stop_comment_recording(username, user_id, live_db)
