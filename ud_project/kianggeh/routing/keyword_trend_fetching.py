"""Routing for Fetching Keyword Trend."""

from __future__ import annotations

from fastapi import APIRouter

from functions.wordcloud_fetching import fetch_wordcloud

keyword_fetching = APIRouter()


@keyword_fetching.get("/retrieve_keyword_trend/", name="retrieve_keyword_trend")
async def get_wordcloud(
    category: str | None = None,
    num_of_days: int | None = None,
) -> dict:
    """Retrieve keywords."""
    keyword_list = fetch_wordcloud(category, num_of_days)
    return {"message": keyword_list}
