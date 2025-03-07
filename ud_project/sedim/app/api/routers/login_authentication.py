"""Login authentication router."""

from fastapi import APIRouter

from app.api.endpoints.login_authentication import login_authentication_module

login_authentication_router = APIRouter()

login_authentication_router.include_router(
    login_authentication_module,
    prefix="/login_authentication_router",
    tags=["login_authentication_router"],
    responses={404: {"description": "Not found"}},
)
