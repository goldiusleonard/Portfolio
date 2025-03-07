"""Functions for managing the watchlist tracking system."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session  # noqa: TCH002

from app.models.watchlist_table import Watchlist


def _raise_http_error(status_code: int, detail: str) -> None:
    """Raise an HTTPException for consistent usage (addresses TRY301)."""
    raise HTTPException(status_code=status_code, detail=detail)


async def add_user_to_watchlist(user_handle: str, live_db: Session) -> None:
    """Add a user to the watchlist."""
    # Check if already in watchlist
    existing_user = (
        live_db.query(Watchlist).filter(Watchlist.user_handle == user_handle).first()
    )
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail=f"User {user_handle} is already in the watchlist",
        )

    # Add to watchlist with just the user_handle
    watchlist_item = Watchlist(
        user_handle=user_handle,
        is_live=False,
        is_comment_recording=False,
        ba_process_timestamp=datetime.now(timezone.utc),
    )
    live_db.add(watchlist_item)
    live_db.commit()


async def update_user_stats(
    user_handle: str,
    mcmc_db: Session,
    live_db: Session,
) -> None:
    """Update user stats from ba_content_data_asset."""
    query = text("""
        SELECT
            creator_photo_link,
            user_following_count,
            user_followers_count,
            user_total_videos
        FROM ba_content_data_asset
        WHERE user_handle = :user_handle
        LIMIT 1
    """)

    try:
        user_data = mcmc_db.execute(query, {"user_handle": user_handle}).first()
        if user_data:
            watchlist_item = (
                live_db.query(Watchlist)
                .filter(Watchlist.user_handle == user_handle)
                .first()
            )
            if watchlist_item:
                watchlist_item.creator_photo_link = user_data.creator_photo_link
                watchlist_item.user_following_count = user_data.user_following_count
                watchlist_item.user_followers_count = user_data.user_followers_count
                watchlist_item.user_total_videos = user_data.user_total_videos
                watchlist_item.last_updated = datetime.now(timezone.utc)
                live_db.commit()
            else:
                _raise_http_error(404, f"User {user_handle} not found in watchlist")
        else:
            _raise_http_error(
                404,
                f"User {user_handle} not found in ba_content_data_asset",
            )
    except Exception as e:
        live_db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update stats for {user_handle}: {e!s}",
        ) from e


async def remove_user_from_watchlist(user_handle: str, live_db: Session) -> None:
    """Remove a user from the watchlist."""
    deleted = (
        live_db.query(Watchlist).filter(Watchlist.user_handle == user_handle).delete()
    )
    if deleted == 0:
        raise HTTPException(
            status_code=404,
            detail=f"User {user_handle} not found in the watchlist",
        )
    live_db.commit()


async def fetch_watchlist(live_db: Session) -> list[dict]:
    """Fetch all users in the watchlist."""
    watchlist_users = live_db.query(Watchlist).all()

    return [
        {
            "user_handle": user.user_handle,
            "creator_photo_link": user.creator_photo_link,
            "user_following_count": user.user_following_count,
            "user_followers_count": user.user_followers_count,
            "user_total_videos": user.user_total_videos,
            "is_live": user.is_live,
            "last_updated": user.last_updated,
            "is_comment_recording": user.is_comment_recording,
        }
        for user in watchlist_users
    ]


async def update_user_live_status(
    user_handle: str,
    *,
    is_live: bool,
    live_db: Session,
) -> None:
    """Update the live status of a user in the watchlist."""
    watchlist_item = (
        live_db.query(Watchlist).filter(Watchlist.user_handle == user_handle).first()
    )
    if not watchlist_item:
        raise HTTPException(
            status_code=404,
            detail=f"User {user_handle} not found in the watchlist",
        )
    watchlist_item.is_live = is_live
    watchlist_item.last_updated = datetime.now(timezone.utc)
    live_db.commit()
