"""Comment recording routers."""

from fastapi import APIRouter

from app.api.endpoints.comment_recording import comment_router

comment_recording_router = APIRouter()

# Include comment recording routes
comment_recording_router.include_router(
    comment_router,
    prefix="/comments",
    tags=["comments"],
    responses={404: {"description": "Not found"}},
)
