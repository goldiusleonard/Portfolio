"""Comment endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.endpoints.functions import comment_function
from app.core.dependencies import get_db

comment_module = APIRouter()


@comment_module.get("/comment/{video_id}")
def get_comment_details(
    video_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve comment details."""
    return comment_function.get_comment_details(video_id, db)


@comment_module.get("/all")
def get_all_comment_details(
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve all comment details."""
    return comment_function.get_all_comment_details(db)
