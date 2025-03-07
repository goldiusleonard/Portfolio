"""Notification update model."""

from datetime import datetime

from pydantic import BaseModel


class NotificationUpdate(BaseModel):
    """Model for updating a notification."""

    notification_id: int
    is_new: bool
    status: str
    datetime: datetime
