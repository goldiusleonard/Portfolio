"""law violation router module."""

from fastapi import APIRouter, Depends, Request, Security
from fastapi.security import HTTPBearer

from app.api.endpoints.law_violation import law_violation_module
from app.auth import auth

law_violation_router = APIRouter()
api_key_header = HTTPBearer()


def token_validation(request: Request) -> bool:
    """For validating the user authorization token."""
    return auth.get_code_after_validation(request)


law_violation_router.include_router(
    law_violation_module,
    dependencies=[Depends(token_validation), Security(api_key_header)],
    prefix="/law_violation",
    tags=["law_violation"],
    responses={404: {"description": "Not found"}},
)
