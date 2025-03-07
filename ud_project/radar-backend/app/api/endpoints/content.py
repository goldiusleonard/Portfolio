"""Content endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.endpoints.functions import content_function
from app.core.dependencies import get_db

content_module = APIRouter()


@content_module.get("/details/{video_id}")
def get_content_details(
    video_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve content details."""
    return content_function.get_content_details(video_id, db)


@content_module.get("/all")
def get_all_content_details(
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve all content details."""
    return content_function.get_all_content_details(db)
