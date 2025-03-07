"""extraction law pdf router module."""

from fastapi import APIRouter, Depends, Request, Security
from fastapi.security import HTTPBearer

from app.api.endpoints.extraction_law_pdf import extraction_law_pdf
from app.auth import auth

extraction_law_router = APIRouter()
api_key_header = HTTPBearer()


def token_validation(request: Request) -> bool:
    """For validating the user authorization token."""
    return auth.get_code_after_validation(request)


extraction_law_router.include_router(
    extraction_law_pdf,
    dependencies=[Depends(token_validation), Security(api_key_header)],
    prefix="/extraction_law_pdf",
    tags=["/extraction_law_pdf"],
    responses={404: {"description": "Not found"}},
)
