"""Functions for handling system notifications."""

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.endpoints.functions.account_details_function import (
    fetch_account_details_from_db,
)
from app.core.websocket import websocket_manager
from app.models.notification_table import Notification
from utils.logger import Logger

logger = Logger(__name__)
HTTP_SERVER_ERROR = 500


def _raise_http_error(status_code: int, detail: str) -> None:
    """Raise an HTTPException (addresses TRY301)."""
    raise HTTPException(status_code=status_code, detail=detail)


async def get_all_notifications(live_db: Session, mcmc_db: Session) -> dict:
    """Get all notifications with account details."""
    try:
        # Get base notifications from live monitoring system
        notifications = live_db.query(Notification).all()

        enhanced_notifications = []
        for notif in notifications:
            # Get account details from MCMC database
            account_details = fetch_account_details_from_db(notif.Name, mcmc_db)

            enhanced_notifications.append(
                {
                    "id": notif.Id,
                    "isNew": notif.IsNew,
                    "imageUrl": account_details.get(
                        "profilePicUrl",
                    ),  # Get image from account details
                    "name": notif.Name,
                    "status": notif.Status,
                    "dateTime": notif.DateTime,
                    "liveDetail": notif.LiveDetail,
                },
            )

    except SQLAlchemyError as e:
        _raise_http_error(
            HTTP_SERVER_ERROR,
            f"Failed to get notifications (DB error): {e!s}",
        )
    else:
        return {"notifications": enhanced_notifications}


async def create_notification(  # noqa: PLR0913
    user_id: int,
    name: str,
    status: str,
    live_detail: str,
    stream_id: str,
    mcmc_db: Session,
    db: Session,
) -> dict:
    """Create a new notification."""
    try:
        # Get user profile image from MCMC database
        account_details = fetch_account_details_from_db(name, mcmc_db)

        notification = Notification(
            UserId=user_id,
            Name=name,
            Status=status,
            LiveDetail=live_detail,
            StreamId=stream_id,
            ImageUrl=account_details.get("profilePicUrl"),
            IsNew=True,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        message = {
            "type": "notification",
            "data": {
                "name": name,
                "status": status,
                "live_detail": live_detail,
                "stream_id": stream_id,
                "image_url": account_details.get("profilePicUrl"),
            },
        }

        logger.info("Broadcasting notification: %s", message)

        # Broadcast the notification through WebSocket
        await websocket_manager.broadcast_notification(message)

        logger.info("Notification broadcast completed")

    except SQLAlchemyError as e:
        db.rollback()
        _raise_http_error(
            HTTP_SERVER_ERROR,
            f"Failed to create notification (DB error): {e!s}",
        )
    else:
        return {"message": "Notification created successfully"}
