"""Routing for Generate Keyword Trend."""

from __future__ import annotations

from fastapi import APIRouter

from functions.wordcloud_process import process_wordcloud

keyword_generator = APIRouter()


@keyword_generator.get(
    "/generate_keyword_trend/",
    name="generate_keyword_trend",
)
async def generate_wordcloud() -> dict:
    """Generate keywords."""
    return process_wordcloud()
