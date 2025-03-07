"""News endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.endpoints.functions import news_function
from app.core.dependencies import get_db_mongo_news
from app.core.vm_mongo_db import MongoClient  # noqa: TCH001

news_module = APIRouter()


@news_module.get("/")
async def get_news_and_categories(
    categories: list[str] = Query(..., alias="categories"),
    db: MongoClient = Depends(get_db_mongo_news),
) -> dict:
    """Retrieve news and categories."""
    return await news_function.get_all_news_with_categories(categories, db)
