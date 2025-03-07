"""Database connection module."""

from typing import Generator

from sqlalchemy.orm import declarative_base

from app.core.azure_db import SessionLocal_master
from app.core.azure_db_replica import SessionLocal_replica
from app.core.business_agent_db import SessionOutput
from app.core.marketplace_db import SessionInput

Base = declarative_base()


def get_db() -> Generator[SessionLocal_replica, None, None]:
    """Yield a database session for replica."""
    db = SessionLocal_replica()
    try:
        yield db
    finally:
        db.close()


def get_db_for_post() -> Generator[SessionLocal_master, None, None]:
    """Yield a database session for master."""
    db = SessionLocal_master()
    try:
        yield db
    finally:
        db.close()


def get_input_db() -> Generator[SessionInput, None, None]:
    """Yield input db."""
    db = SessionInput()
    try:
        yield db
    finally:
        db.close()


def get_output_db() -> Generator[SessionOutput, None, None]:
    """Yield output db."""
    db = SessionOutput()
    try:
        yield db
    finally:
        db.close()
