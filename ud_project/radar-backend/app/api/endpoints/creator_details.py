"""Profile endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.endpoints.functions import creator_details_function, taglist_function
from app.core.dependencies import get_db

creator_details_module = APIRouter()


@creator_details_module.get("/taglist")
def get_taglist(
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve taglist."""
    return taglist_function.get_taglist(db)


@creator_details_module.get("/category_post_status")
def get_category_post_status(
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve category post status."""
    return creator_details_function.get_category_post_status(db)
