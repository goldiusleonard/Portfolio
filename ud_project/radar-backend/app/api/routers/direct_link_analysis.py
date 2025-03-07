"""Direct Link router module."""

from fastapi import APIRouter, Depends, Request, Security
from fastapi.security import HTTPBearer

from app.api.endpoints.direct_link_analysis import direct_link_analysis_module
from app.auth import auth

direct_link_analysis_router = APIRouter()
api_key_header = HTTPBearer()


def token_validation(request: Request) -> bool:
    """For validating the user authorization token."""
    return auth.get_code_after_validation(request)


direct_link_analysis_router.include_router(
    direct_link_analysis_module,
    dependencies=[Depends(token_validation), Security(api_key_header)],
    prefix="/direct_link_analysis",
    tags=["direct_link_analysis"],
    responses={404: {"description": "Not found"}},
)
