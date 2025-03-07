"""Similarity agent router module."""

from fastapi import APIRouter, Depends, Request, Security
from fastapi.security import HTTPBearer

from app.api.endpoints.mega_similarity_agent import similarity_agent
from app.auth import auth

similarity_agent_router = APIRouter()
api_key_header = HTTPBearer()


def token_validation(request: Request) -> bool:
    """For validating the user authorization token."""
    return auth.get_code_after_validation(request)


similarity_agent_router.include_router(
    similarity_agent,
    dependencies=[Depends(token_validation), Security(api_key_header)],
    prefix="/mega_similarity_agent",
    tags=["mega_similarity_agent"],
    responses={404: {"description": "Not found"}},
)
