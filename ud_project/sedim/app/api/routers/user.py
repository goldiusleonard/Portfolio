"""User router module."""

from fastapi import APIRouter

from app.api.endpoints.user import user_module

user_router = APIRouter()

user_router.include_router(
    user_module,
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)
