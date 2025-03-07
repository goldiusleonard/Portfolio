"""CROSS CATEGORY INSIGHT MINDMAP ."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.security import HTTPBearer

from app.api.endpoints.mindmap import filter_label_module

filter_label_router = APIRouter()
api_key_header = HTTPBearer()

filter_label_router.include_router(
    filter_label_module,
    prefix="/cross-category-insight",
    tags=["cross-category-insight"],
    responses={404: {"description": "Not found"}},
)
