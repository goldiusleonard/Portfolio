"""Category endpoint module."""

# fastapi
from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
from sqlalchemy.exc import SQLAlchemyError

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# Other imports
from app.api.endpoints.functions import category_function
from app.core.dependencies import get_db

category_module = APIRouter()
api_key_header = HTTPBearer()


###############CATEGORY#######################


@category_module.get("/")
def get_all_category(db: Session = Depends(get_db)) -> dict:
    """Retrieve all category details."""
    try:
        # Get all users from the database
        category = category_function.get_all_category_data(db=db)
    except SQLAlchemyError as e:
        # Handle SQLAlchemy specific exceptions
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {e!s}",
        ) from e
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(
            status_code=400,
            detail=f"Unexpected error: {e!s}",
        ) from e
    else:
        # Return users as a response
        return {"categories": category}


@category_module.get("/insights/visual-chart-data")
def get_visual_chart_data(
    categories: list[str] = Query([], description="List of categories"),
    period: int = 1,
    chart_type: str = "risk",
    state: str = "current",
) -> dict:
    """Get visual chart data."""
    try:
        max_categories = 4
        if len(categories) > max_categories:
            raise HTTPException(  # noqa: TRY301
                status_code=400,
                detail="Maximum 4 categories are allowed",
            )
        visual_chart_data = category_function.get_visual_chart_data(
            categories=categories,
            period=period,
            chart_type=chart_type,
            state=state,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Unexpected error: {e!s}") from e
    else:
        return visual_chart_data
