"""FastAPI router module for handling notification functionality."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.endpoints.functions import notification_function
from app.core.db_config import get_live_db, get_mcmc_db

notification_module = APIRouter()


class NotificationCreate(BaseModel):
    """Data model for creating new notifications."""

    user_id: int
    name: str
    status: str
    live_detail: str
    stream_id: str


@notification_module.get("/get_all_notifications/")
async def get_all_notifications(
    live_db: Session = Depends(get_live_db),
    mcmc_db: Session = Depends(get_mcmc_db),
) -> dict:
    """Get all notifications with user details."""
    return await notification_function.get_all_notifications(live_db, mcmc_db)


@notification_module.post("/create_notification/")
async def create_notification(
    data: NotificationCreate,
    live_db: Session = Depends(get_live_db),
    mcmc_db: Session = Depends(get_mcmc_db),
) -> dict:
    """Create a new notification."""
    return await notification_function.create_notification(
        user_id=data.user_id,
        name=data.name,
        status=data.status,
        live_detail=data.live_detail,
        stream_id=data.stream_id,
        mcmc_db=mcmc_db,
        db=live_db,
    )
