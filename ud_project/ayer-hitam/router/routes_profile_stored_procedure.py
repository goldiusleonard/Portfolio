#!/usr/bin/env python3
"""Docstring to access multiple endpoint."""

from __future__ import annotations

from typing import Generator

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from connections.mysql_connection import mysql_engine
from modules.profile_stored_procedure import call_update_profile_data_asset
from utils.logger import logger

router = APIRouter()

database1 = "mcmc_business_agent"


def get_mysql_session() -> Generator[Session, None, None]:
    """Get MySQL Session."""
    logger.info("Opening a new database session.")
    with Session(mysql_engine(database_name=database1).connect()) as session:
        try:
            yield session
        except Exception as e:
            error_message = f"An error occured: {e}"
            logger.exception(error_message)
            session.rollback()
            raise HTTPException(
                status_code=500,
                detail="Database error occurred.",
            ) from e
        finally:
            session.close()
            logger.info("Closing the database session.")


@router.get("/update_profile_data_asset/", name="update_content_data_asset")
async def update_content_data_asset() -> dict:
    """Update Profile Data Asset."""
    return call_update_profile_data_asset()
