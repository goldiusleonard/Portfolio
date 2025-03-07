"""Cross category insight endpoints."""

from __future__ import annotations

import os

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.api.endpoints.functions import engagement_function
from app.core.constants import DEFAULT_ENGAGEMENT_COUNT_URL
from app.models.schemas.engagement import EngagementScore, TotalEngagement  # noqa: TCH001

engagement_module = APIRouter()


@engagement_module.post("/total")
def get_total_engagement(engagement: TotalEngagement) -> dict:
    """Calculate total engagement."""
    total = engagement_function.calculate_total_engagement(
        engagement.share_count,
        engagement.saved_count,
        engagement.comment_count,
        engagement.like_count,
    )
    return {"total_engagement": total}


@engagement_module.post("/score")
def get_engagement_score(engagement: EngagementScore) -> dict:
    """Calculate engagement score."""
    try:
        score = engagement_function.calculate_engagement_score(
            engagement.share_count,
            engagement.saved_count,
            engagement.comment_count,
            engagement.like_count,
            engagement.video_count,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    else:
        return {"engagement_score": score}


@engagement_module.get("/process_user_videos")
async def process_user_videos(
    start_date: str,
    end_date: str,
    user_handles: list[str] = Query(),
) -> dict:
    """Store the latest data in the database."""
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "user_handles": user_handles,
    }
    url = os.getenv("DEFAULT_ENGAGEMENT_COUNT_URL") or DEFAULT_ENGAGEMENT_COUNT_URL
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=f"{url}/process_user_videos",
            params=params,
        )
        response.raise_for_status()
        data = response.json()
        return data if data else []


@engagement_module.get("/fetch_user_videos")
async def fetch_user_videos(
    start_date: str,
    end_date: str,
    user_handles: list[str] = Query(),
) -> list:
    """Calculate engagement score for the selected user_handles and provide it."""
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "user_handles": user_handles,
    }
    url = os.getenv("DEFAULT_ENGAGEMENT_COUNT_URL") or DEFAULT_ENGAGEMENT_COUNT_URL
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=f"{url}/fetch_user_videos",
            params=params,
        )
        response.raise_for_status()
        data = response.json()
        return data if data else []
