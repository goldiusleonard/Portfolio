"""Category router module."""

from fastapi import APIRouter, Depends, Request, Security
from fastapi.security import HTTPBearer

from app.api.endpoints.category import category_module
from app.auth import auth

category_router = APIRouter()
api_key_header = HTTPBearer()


def token_validation(request: Request) -> bool:
    """For validating the user authorization token."""
    return auth.get_code_after_validation(request)


category_router.include_router(
    category_module,
    dependencies=[Depends(token_validation), Security(api_key_header)],
    prefix="/category",
    tags=["category"],
    responses={404: {"description": "Not found"}},
)
