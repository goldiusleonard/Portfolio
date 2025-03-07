"""Category and Subcategory Data Endpoints.

This module provides endpoints for retrieving category and subcategory data.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.api.endpoints.functions import (
    category_sub_category_data_function as catsubcat_function,
)

catsubcat_module = APIRouter()


@catsubcat_module.get("/")
async def group_by_category(
    category: list[str] | None = Query(
        None,
        description="Filter one or more categories",
    ),
) -> list[dict]:
    """Retrieve categories."""
    if not category:
        raise HTTPException(status_code=400, detail="Category is required")
    return await catsubcat_function.fetch_category_data(category)
