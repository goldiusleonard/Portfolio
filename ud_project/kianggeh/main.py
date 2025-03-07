"""Main module for ada-knowledge-injector FastAPI application."""

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from routing.router_module import init_routers

app = FastAPI(
    title="Keyword Trend",
    description="All modules for Keyword Trend",
    version="1.0.0",
    docs_url="/",
    redoc_url="/redocs",
)
init_routers(app_=app)


@app.get("/healthz", response_class=JSONResponse)
async def healthz() -> dict:
    """Health check endpoint to verify the application's status.

    Returns a 200 OK status with a message if the app is healthy.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
