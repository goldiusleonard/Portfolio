"""VM MongoDB Core."""

from __future__ import annotations

import os
from typing import Generic, TypeVar
from urllib.parse import quote_plus

from beanie import init_beanie
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from app.models.news import NewsArticle

load_dotenv()

# Define Type Variable for MongoDB Session
Session_Mongo = TypeVar("Session_Mongo")

# Define MongoDB Configuration
MONGO_CONFIGS = {
    "MONGO": {
        "user": "MONGO_USER",
        "password": "MONGO_PASSWORD",
        "host": "MONGO_HOST",
        "port": "MONGO_PORT",
    },
}


class MongoClient(Generic[Session_Mongo]):
    """MongoDB client class using Beanie and Motor."""

    def __init__(self, db_name: str | None) -> None:
        """Initialize the MongoDB client."""
        self.db_name = db_name
        self.client: AsyncIOMotorClient | None

    async def connect(self) -> Session_Mongo:
        """Create an async MongoDB connection using Beanie.

        :return: MongoDB session instance.
        """
        config = MONGO_CONFIGS["MONGO"]
        user = os.getenv(config["user"])
        password = os.getenv(config["password"])
        host = os.getenv(config["host"])
        port = os.getenv(config["port"])

        if not all([user, password, host, port, self.db_name]):
            raise ValueError(  # noqa: TRY003
                "Missing environment variable(s) for MongoDB configuration.",  # noqa: EM101
            )

        encoded_user = quote_plus(user)
        encoded_password = quote_plus(password)
        mongo_uri = f"mongodb://{encoded_user}:{encoded_password}@{host}:{port}"

        self.client = AsyncIOMotorClient(mongo_uri)
        db = self.client[self.db_name]

        await init_beanie(database=db, document_models=[NewsArticle])
        return db

    async def disconnect(self) -> None:
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
