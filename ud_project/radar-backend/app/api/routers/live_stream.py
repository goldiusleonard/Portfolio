"""Live stream routers."""

from fastapi import APIRouter

from app.api.endpoints.live_stream import live_stream_module

live_stream_router = APIRouter()

# Include live stream routes
live_stream_router.include_router(
    live_stream_module,
    prefix="/live_stream",
    tags=["live-stream"],
    responses={404: {"description": "Not found"}},
)
