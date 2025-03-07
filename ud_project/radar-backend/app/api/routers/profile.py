"""Profile router."""

from fastapi import APIRouter, Depends, Request, Security
from fastapi.security import HTTPBearer

from app.api.endpoints.profile import profile_module
from app.auth import auth

profile_router = APIRouter()
api_key_header = HTTPBearer()


def token_validation(request: Request) -> bool:
    """For validating the user authorization token."""
    return auth.get_code_after_validation(request)


profile_router.include_router(
    profile_module,
    dependencies=[Depends(token_validation), Security(api_key_header)],
    prefix="/profile",
    tags=["profile"],
    responses={404: {"description": "Not found"}},
)
