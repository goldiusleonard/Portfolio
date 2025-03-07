"""Content router module."""

from fastapi import APIRouter, Depends, Request, Security
from fastapi.security import HTTPBearer

from app.api.endpoints.content import content_module
from app.auth import auth

content_router = APIRouter()
api_key_header = HTTPBearer()


def token_validation(request: Request) -> bool:
    """For validating the user authorization token."""
    return auth.get_code_after_validation(request)


content_router.include_router(
    content_module,
    dependencies=[Depends(token_validation), Security(api_key_header)],
    prefix="/content",
    tags=["content"],
    responses={404: {"description": "Not found"}},
)
