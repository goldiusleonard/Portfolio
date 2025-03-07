"""FastAPI router module for managing watchlist functionality."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session  # noqa: TCH002

from app.api.endpoints.functions.watchlist_tracker_function import (
    add_user_to_watchlist,
    fetch_watchlist,
    remove_user_from_watchlist,
    update_user_live_status,
    update_user_stats,
)
from app.core.db_config import get_live_db, get_mcmc_db

router = APIRouter()


@router.post("/watchlist/add")
async def add_to_watchlist(
    user_handle: str,
    live_db: Session = Depends(get_live_db),
) -> dict:
    """Add a user to the watchlist."""
    try:
        await add_user_to_watchlist(user_handle, live_db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add {user_handle}: {e!s}",
        ) from e
    else:
        return {"message": f"User {user_handle} added to watchlist"}


@router.post("/watchlist/update_stats")
async def update_stats(
    user_handle: str,
    mcmc_db: Session = Depends(get_mcmc_db),
    live_db: Session = Depends(get_live_db),
) -> dict:
    """Update user stats from MCMC database."""
    try:
        await update_user_stats(user_handle, mcmc_db, live_db)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update stats for {user_handle}: {e!s}",
        ) from e
    else:
        return {"message": f"User stats updated for {user_handle}"}


@router.delete("/watchlist/remove")
async def remove_from_watchlist(
    user_handle: str,
    live_db: Session = Depends(get_live_db),
) -> dict:
    """Remove a user from the watchlist."""
    try:
        await remove_user_from_watchlist(user_handle, live_db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove {user_handle}: {e!s}",
        ) from e
    else:
        return {"message": f"User {user_handle} removed from watchlist"}


@router.get("/watchlist")
async def get_watchlist(
    live_db: Session = Depends(get_live_db),
) -> dict:
    """Fetch all users in the watchlist."""
    try:
        watchlist = await fetch_watchlist(live_db)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch watchlist: {e!s}",
        ) from e
    else:
        return {"watchlist": watchlist}


@router.post("/watchlist/update_status")
async def update_live_status(
    user_handle: str,
    *,
    is_live: bool,
    live_db: Session = Depends(get_live_db),
) -> dict:
    """Update the live status of a user."""
    try:
        await update_user_live_status(user_handle, is_live, live_db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update status for {user_handle}: {e!s}",
        ) from e
    else:
        return {"message": f"Updated live status for {user_handle}"}
