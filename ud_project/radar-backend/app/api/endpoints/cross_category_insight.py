"""Cross category insight endpoints."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import httpx
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.core.dependencies import get_db

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from app.api.endpoints.functions import (
    cross_category_insight_function,
)
from app.core.constants import (
    DEFAULT_CROSS_CATEGORY_INSIGHT_URL,
    DEFAULT_NUM_OF_DAYS_KEYWORD_SEARCH,
)

cross_category_insight_module = APIRouter()


@cross_category_insight_module.get("/search-categories")
def search_categories(
    categories: list[str] = Query(
        [],
        description="List of categories",
    ),
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve search categories."""
    return cross_category_insight_function.get_search_categories(
        categories,
        db,
    )


@cross_category_insight_module.get("/keyword-trends")
def get_keywords(
    categories: list[str] = Query(..., alias="categories"),
) -> dict:
    """Retrieve heatmap."""
    return cross_category_insight_function.get_keyword_trends(
        categories,
        DEFAULT_NUM_OF_DAYS_KEYWORD_SEARCH,
    )


class InputProcessData(BaseModel):
    """Input for process data."""

    id_list: list[int]


@cross_category_insight_module.post("/process-data")
async def process_data(input_: InputProcessData) -> dict:
    """Process data."""
    url = (
        os.getenv("DEFAULT_CROSS_CATEGORY_INSIGHT_URL")
        or DEFAULT_CROSS_CATEGORY_INSIGHT_URL
    )
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=f"{url}/process-data/",
            headers={
                "accept": "application/json",
                "Content-Type": "application/json",
            },
            json=input_.model_dump(),
        )
        response.raise_for_status()
        data = response.json()
        return data if data else []


class InputFilterCalculateDailyTotals(BaseModel):
    """Input for filter and calculate daily totals."""

    categories: list[str]


@cross_category_insight_module.post(
    "/filter_and_calculate_daily_totals",
)
async def cross_category_insight_filter_and_calculate_daily_totals(
    analysis_type: str,
    time_range: int,
    categories: list[str],
) -> list:
    """Filter and calculate daily totals."""
    params = {
        "analysis_type": analysis_type,
        "time_range": time_range,
    }
    url = (
        os.getenv("DEFAULT_CROSS_CATEGORY_INSIGHT_URL")
        or DEFAULT_CROSS_CATEGORY_INSIGHT_URL
    )
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=f"{url}/filter_and_calculate_daily_totals/",
            headers={
                "accept": "application/json",
                "Content-Type": "application/json",
            },
            json=categories,
            params=params,
        )
        response.raise_for_status()
        data = response.json()
        return data if data else []


@cross_category_insight_module.post("/group_by_category")
async def cross_category_insight_group_by_category(
    categories: list[str],
) -> list:
    """Group by category."""
    url = (
        os.getenv("DEFAULT_CROSS_CATEGORY_INSIGHT_URL")
        or DEFAULT_CROSS_CATEGORY_INSIGHT_URL
    )
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=f"{url}/group_by_category/",
            headers={
                "accept": "application/json",
                "Content-Type": "application/json",
            },
            json=categories,
        )
        response.raise_for_status()
        data = response.json()
        return data if data else []


@cross_category_insight_module.post("/sentiment_justification")
async def cross_category_insight_sentiment_justification(
    categories: list[str],
) -> dict:
    """Sentiment justification."""
    url = (
        os.getenv("DEFAULT_CROSS_CATEGORY_INSIGHT_URL")
        or DEFAULT_CROSS_CATEGORY_INSIGHT_URL
    )
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=f"{url}/sentiment_justification/",
            headers={
                "accept": "application/json",
                "Content-Type": "application/json",
            },
            json=categories,
        )
        response.raise_for_status()
        data = response.json()
        return data if data else []
