"""Watchlist tracker router."""

from fastapi import APIRouter

from app.api.endpoints.watchlist_tracker import router as watchlist_tracker_router

router = APIRouter()

# Include watchlist tracker routes
router.include_router(
    watchlist_tracker_router,
    prefix="/watchlist_tracker",
    tags=["watchlist-tracker"],
    responses={404: {"description": "Not found"}},
)
