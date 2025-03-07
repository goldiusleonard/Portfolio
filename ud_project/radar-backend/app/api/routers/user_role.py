"""User role router."""

from fastapi import APIRouter

from app.api.endpoints.user_role import user_role_module

user_role_router = APIRouter()

user_role_router.include_router(
    user_role_module,
    prefix="/user_role",
    tags=["user_role"],
    responses={404: {"description": "Not found"}},
)
