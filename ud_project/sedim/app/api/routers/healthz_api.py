"""Health checker router."""

from fastapi import APIRouter

from app.api.endpoints.healthz_api import healthz_app

healthz_router = APIRouter()

healthz_router.include_router(
    healthz_app,
)
