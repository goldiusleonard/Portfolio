#!/usr/bin/env python3
"""Docstring for serving tables endpoint."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from connections.mysql_connection import mysql_engine
from router.routes_content_stored_procedure import router as content_stored_router
from router.routes_profile_stored_procedure import router as profile_stored_router

load_dotenv()

host = os.getenv("DB_HOST")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
database1 = "mcmc_business_agent"

mysqlengine = mysql_engine(database1)

stored_app = FastAPI()


@stored_app.get("/")
async def root() -> dict:
    """Test Stored Procedure API."""
    return {"message": "Welcome to Stored Procedure API."}


@stored_app.get("/healthz", response_class=JSONResponse)
async def healthz() -> dict:
    """Health check endpoint to verify the application's status.

    Returns a 200 OK status with a message if the app is healthy.
    """
    return {"status": "healthy"}


stored_app.include_router(content_stored_router)
stored_app.include_router(profile_stored_router)
