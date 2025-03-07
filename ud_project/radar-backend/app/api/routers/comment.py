"""Content router module."""

from fastapi import APIRouter, Depends, Request, Security
from fastapi.security import HTTPBearer

from app.api.endpoints.comment import comment_module
from app.auth import auth

comment_router = APIRouter()
api_key_header = HTTPBearer()


def token_validation(request: Request) -> bool:
    """For validating the user authorization token."""
    return auth.get_code_after_validation(request)


comment_router.include_router(
    comment_module,
    dependencies=[Depends(token_validation), Security(api_key_header)],
    prefix="/comment",
    tags=["comment"],
    responses={404: {"description": "Not found"}},
)
