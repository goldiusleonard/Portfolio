"""Docstring for serving tables endpoint."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.routers.login_authentication import login_authentication_router
from app.api.routers.role import role_router
from app.api.routers.user import user_router
from app.api.routers.user_role import user_role_router

stored_app = FastAPI()


@stored_app.get("/")
async def root() -> dict:
    """Test Stored Procedure API."""
    return {"message": "Welcome to Stored Procedure API."}


stored_app.include_router(login_authentication_router)
stored_app.include_router(role_router)
stored_app.include_router(user_router)
stored_app.include_router(user_role_router)
