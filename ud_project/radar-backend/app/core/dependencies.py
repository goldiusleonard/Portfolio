"""Database connection module."""

from typing import AsyncGenerator, Generator

from sqlalchemy.orm import declarative_base

from app.core.vm_db import Session_Vm
from app.core.vm_mongo_db import MongoClient, Session_Mongo

Base = declarative_base()


def get_db() -> Generator[Session_Vm, None, None]:
    """Yield a database session for VM."""
    db = Session_Vm()
    try:
        yield db
    finally:
        db.close()


async def get_db_mongo_news() -> AsyncGenerator[Session_Mongo, None]:
    """Yield a database session for MongoDB News using Beanie."""
    db = MongoClient("newsapi")
    session = await db.connect()
    try:
        yield session
    finally:
        await db.disconnect()
