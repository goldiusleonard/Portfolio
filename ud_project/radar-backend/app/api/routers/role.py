"""Role router."""

from fastapi import APIRouter

from app.api.endpoints.role import role_module

role_router = APIRouter()

role_router.include_router(
    role_module,
    prefix="/role",
    tags=["role"],
    responses={404: {"description": "Not found"}},
)
