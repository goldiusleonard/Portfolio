"""CROSS CATEGORY INSIGHT MINDMAP ."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPBearer

from app.api.endpoints.functions.mindmap_function import (
    find_node,
    generate_json_by_category,
    sqltodf,
)
from app.core.dependencies import get_db_mongo_news
from app.core.vm_mongo_db import MongoClient  # noqa: TCH001

# Create an API router
filter_label_module = APIRouter()
api_key_header = HTTPBearer()


@filter_label_module.get("/filter-category")
async def filter_label(
    category: str = Query(..., description="The category to filter by"),
    db: MongoClient = Depends(get_db_mongo_news),
) -> dict[str, Any]:
    """Endpoint to filter a label by category.

    Args:
        category (str): The category to filter by.
        db: MongoClient.

    Returns:
        Dict[str, Any]: The filtered main node or an error message if not found.

    """
    # Get data from the SQL
    data_frame = sqltodf()

    # Reshape the dataframe into JSON format for the mind map
    mind_map_data = await generate_json_by_category(data_frame, db)

    # Find the main label node
    main_node = find_node(mind_map_data, category)

    if not main_node:
        return {"error": "Main category not found"}

    return main_node
