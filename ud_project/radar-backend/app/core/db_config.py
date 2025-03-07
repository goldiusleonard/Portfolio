"""Database configuration and session management."""

import os
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()
# Load environment variables
DB_CONFIG = {
    "user": os.getenv("VM_USER"),
    "password": os.getenv("VM_PASSWORD"),
    "host": os.getenv("VM_HOST"),
    "port": os.getenv("VM_PORT"),
}

# Encode credentials
encoded_username = quote_plus(DB_CONFIG["user"])
encoded_password = quote_plus(DB_CONFIG["password"])

# SSL configuration
connect_args = {"ssl": {"fake_flag_to_enable_tls": True}}


class DatabaseManager:
    """Manages connections to multiple databases."""

    def __init__(self) -> None:
        """Initialize the database manager."""
        self.engines = {}
        self.async_engines = {}
        self.session_factories = {}
        self.async_session_factories = {}

        # Initialize connections for both databases
        self._init_database("radar_backend_v2")
        self._init_database("mcmc_business_agent")

    def _init_database(self, db_name: str) -> None:
        """Initialize sync and async engines for a database."""
        # Sync engine
        sync_url = f"mysql+pymysql://{encoded_username}:{encoded_password}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{db_name}"
        self.engines[db_name] = create_engine(sync_url, connect_args=connect_args)

        # Async engine
        async_url = f"mysql+aiomysql://{encoded_username}:{encoded_password}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{db_name}"
        self.async_engines[db_name] = create_async_engine(async_url, pool_pre_ping=True)

        # Create session factories
        self.session_factories[db_name] = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engines[db_name],
        )

        self.async_session_factories[db_name] = sessionmaker(
            bind=self.async_engines[db_name],
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    @contextmanager
    def get_db_session(self, db_name: str) -> Generator[Session, None, None]:
        """Get a synchronous database session."""
        session = self.session_factories[db_name]()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def get_async_session(
        self,
        db_name: str,
    ) -> AsyncGenerator[AsyncSession, None]:
        """Get an asynchronous database session as a proper context manager."""
        async_session = self.async_session_factories[db_name]()
        try:
            yield async_session
            await async_session.commit()
        except Exception:
            await async_session.rollback()
            raise
        finally:
            await async_session.close()

    def dispose_all(self) -> None:
        """Dispose all database connections."""
        for engine in self.engines.values():
            engine.dispose()
        for engine in self.async_engines.values():
            engine.dispose()


# Create a singleton instance
db_manager = DatabaseManager()


# Dependency functions for FastAPI
def get_live_db() -> Generator[Session, None, None]:
    """Get a session for radar_backend_v2 database."""
    with db_manager.get_db_session("radar_backend_v2") as session:
        yield session


def get_mcmc_db() -> Generator[Session, None, None]:
    """Get a session for mcmc_business_agent database."""
    with db_manager.get_db_session("mcmc_business_agent") as session:
        yield session


@asynccontextmanager
async def get_live_db_async() -> AsyncGenerator[AsyncSession, None]:
    """Get an async session for radar_backend_v2 database."""
    async with db_manager.get_async_session("radar_backend_v2") as session:
        yield session


async def get_mcmc_db_async() -> AsyncGenerator[AsyncSession, None]:
    """Get an async session for mcmc_business_agent database."""
    async with db_manager.get_async_session("mcmc_business_agent") as session:
        yield session
