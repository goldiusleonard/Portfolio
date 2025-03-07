"""Notification router."""

from fastapi import APIRouter

from app.api.endpoints.notification import notification_module

notification_router = APIRouter()

# Include notification routes
notification_router.include_router(
    notification_module,
    prefix="/notification",
    tags=["notification"],
    responses={404: {"description": "Not found"}},
)
