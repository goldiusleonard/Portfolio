"""Authentication module."""

from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.auth_handler import decode_jwt


class JWTBearer(HTTPBearer):
    """Custom JWTBearer class for handling JWT authentication."""

    def __init__(self, *, auto_error: bool = True) -> None:
        """Automatically raise an error if the authentication fails.

        Args:
            auto_error (bool): Error if the authentication fails.Defaults to True.

        """
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> str | None:
        """Handle the authentication process for each incoming request.

        Args:
            request (Request): The incoming request.

        Returns:
            Optional[str]: The decoded JWT token,
            if authentication is successful, otherwise None.

        """
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if credentials:
            if credentials.scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=403,
                    detail="Invalid authentication scheme.",
                )
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(
                    status_code=403,
                    detail="Invalid token or expired token.",
                )
            return credentials.credentials
        raise HTTPException(status_code=403, detail="Invalid authorization code.")

    def verify_jwt(self, jwtoken: str) -> bool:
        """Verify the JWT token by decoding it.

        Args:
            jwtoken (str): The JWT token to be verified.

        Returns:
            bool: True if the token is valid, otherwise False.

        """
        try:
            payload = decode_jwt(jwtoken)
            return bool(payload)
        except ValueError:
            return False
