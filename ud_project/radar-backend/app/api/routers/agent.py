"""Agent router module."""

from fastapi import APIRouter, Depends, Request, Security
from fastapi.security import HTTPBearer

from app.api.endpoints.agent import agent_module
from app.auth import auth

agent_router = APIRouter()
api_key_header = HTTPBearer()


def token_validation(request: Request) -> bool:
    """For validating the user authorization token."""
    return auth.get_code_after_validation(request)


agent_router.include_router(
    agent_module,
    dependencies=[Depends(token_validation), Security(api_key_header)],
    prefix="/agent",
    tags=["agent"],
    responses={404: {"description": "Not found"}},
)
