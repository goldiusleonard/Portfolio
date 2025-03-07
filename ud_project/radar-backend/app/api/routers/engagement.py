"""Engagement router."""

from fastapi import APIRouter

from app.api.endpoints.engagement import engagement_module

engagement_router = APIRouter()

engagement_router.include_router(
    engagement_module,
    prefix="/engagements",
    tags=["engagements"],
    responses={404: {"description": "Not found"}},
)
