"""Cross category insight router."""

from fastapi import APIRouter, Depends, Request, Security
from fastapi.security import HTTPBearer

from app.api.endpoints.cross_category_insight import cross_category_insight_module
from app.auth import auth

cross_category_insight_router = APIRouter()
api_key_header = HTTPBearer()


def token_validation(request: Request) -> bool:
    """For validating the user authorization token."""
    return auth.get_code_after_validation(request)


cross_category_insight_router.include_router(
    cross_category_insight_module,
    dependencies=[Depends(token_validation), Security(api_key_header)],
    prefix="/cross-category-insight",
    tags=["cross-category-insight"],
    responses={404: {"description": "Not found"}},
)
