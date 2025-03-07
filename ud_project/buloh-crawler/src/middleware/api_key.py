import os

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


# Middleware for API key validation
class APIKeyMiddleware(BaseHTTPMiddleware):
    EXCLUDED_PATHS = {"/status", "/docs", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        # Check if the request path is in the excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            response = await call_next(request)
            return response

        # API key validation
        headers = request.headers
        api_key = os.getenv("API_KEY")

        if headers.get("Authorization") != api_key:
            return Response(content="Invalid API key", status_code=401)

        response = await call_next(request)
        return response
