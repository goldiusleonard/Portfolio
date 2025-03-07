"""Creator Details router."""

from fastapi import APIRouter, Depends, Request, Security
from fastapi.security import HTTPBearer

from app.api.endpoints.creator_details import creator_details_module
from app.auth import auth

creator_details_router = APIRouter()
api_key_header = HTTPBearer()


def token_validation(request: Request) -> bool:
    """For validating the user authorization token."""
    return auth.get_code_after_validation(request)


creator_details_router.include_router(
    creator_details_module,
    dependencies=[Depends(token_validation), Security(api_key_header)],
    prefix="/creator_details",
    tags=["creator_details"],
    responses={404: {"description": "Not found"}},
)
