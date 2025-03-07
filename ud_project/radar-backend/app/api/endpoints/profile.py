"""Profile endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.endpoints.functions import profile_function
from app.core.dependencies import get_db

profile_module = APIRouter()


@profile_module.get("/heatmap")
def get_heatmap(
    username: str = Query(..., description="The username to retrieve data for"),
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve heatmap."""
    return profile_function.get_heatmap_by_username(username, db)
