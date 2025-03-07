"""similarity agent endpoints."""

from __future__ import annotations

import os

import httpx
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.constants import DEFAULT_SIMILARITY_AGENT_URL

similarity_agent = APIRouter()


class InputSaveCollection(BaseModel):
    """Class input for save collection."""

    video_ids: list[int]


@similarity_agent.post("/save_collection")
async def similarity_agent_save_collection(input_: InputSaveCollection) -> dict:
    """Save collection."""
    url = os.getenv("DEFAULT_SIMILARITY_AGENT_URL") or DEFAULT_SIMILARITY_AGENT_URL
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=f"{url}/save_collection",
            headers={"accept": "application/json", "Content-Type": "application/json"},
            json=input_.model_dump(),
        )
        response.raise_for_status()
        data = response.json()
        return data if data else []


class InputQuery(BaseModel):
    """Class input for query."""

    video_id: int
    user_handle: str
    search_type: str = "video"


@similarity_agent.post("/query")
async def similarity_agent_query(input_: InputQuery) -> dict:
    """Perform query."""
    url = os.getenv("DEFAULT_SIMILARITY_AGENT_URL") or DEFAULT_SIMILARITY_AGENT_URL
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=f"{url}/query",
            headers={"accept": "application/json", "Content-Type": "application/json"},
            json={
                "video_id": input_.video_id,
                "user_handle": input_.user_handle,
                "searchType": input_.search_type,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data if data else []
