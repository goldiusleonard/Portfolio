"""News router."""

from fastapi import APIRouter, Depends, Request, Security
from fastapi.security import HTTPBearer

from app.api.endpoints.news import news_module
from app.auth import auth

news_router = APIRouter()
api_key_header = HTTPBearer()


def token_validation(request: Request) -> bool:
    """For validating the user authorization token."""
    return auth.get_code_after_validation(request)


news_router.include_router(
    news_module,
    dependencies=[Depends(token_validation), Security(api_key_header)],
    prefix="/news",
    tags=["news"],
    responses={404: {"description": "Not found"}},
)
