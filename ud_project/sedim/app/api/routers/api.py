"""API router."""

from fastapi import APIRouter

from app.api.routers.healthz_api import healthz_router
from app.api.routers.login_authentication import login_authentication_router
from app.api.routers.role import role_router
from app.api.routers.user import user_router
from app.api.routers.user_role import user_role_router

router = APIRouter()

router.include_router(user_router)
router.include_router(role_router)
router.include_router(user_role_router)
router.include_router(login_authentication_router)
router.include_router(healthz_router)
