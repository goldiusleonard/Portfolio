"""Category and Subcategory Data router."""

from fastapi import APIRouter, Depends, Request, Security
from fastapi.security import HTTPBearer

from app.api.endpoints.category_sub_category_data import catsubcat_module
from app.auth import auth

catsubcat_router = APIRouter()
api_key_header = HTTPBearer()


def token_validation(request: Request) -> bool:
    """For validating the user authorization token."""
    return auth.get_code_after_validation(request)


catsubcat_router.include_router(
    catsubcat_module,
    dependencies=[Depends(token_validation), Security(api_key_header)],
    prefix="/category-subcategory-data",
    tags=["category-subcategory-data"],
    responses={404: {"description": "Not found"}},
)
