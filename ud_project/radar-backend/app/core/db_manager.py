"""Database manager for engagement risk API."""

import os
from typing import Generator
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    "user": os.getenv("VM_USER"),
    "password": os.getenv("VM_PASSWORD"),
    "host": os.getenv("VM_HOST"),
    "port": os.getenv("VM_PORT"),
    "database": "mcmc_business_agent",  # Default database for risk API
}

# Encode credentials
encoded_username = quote_plus(DB_CONFIG["user"])
encoded_password = quote_plus(DB_CONFIG["password"])


class DatabaseManager:
    """Database manager for risk analysis operations."""

    def __init__(self) -> None:
        """Initialize database connection."""
        # SSL configuration
        self.connect_args = {"ssl": {"fake_flag_to_enable_tls": True}}

        # Create sync engine
        self.engine = create_engine(
            f"mysql+pymysql://{encoded_username}:{encoded_password}"
            f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}",
            connect_args=self.connect_args,
            pool_pre_ping=True,
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )

    def get_db(self) -> Generator[Session, None, None]:
        """Get database session."""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def get_session(self) -> Session:
        """Get a new database session directly."""
        return self.SessionLocal()

    def dispose(self) -> None:
        """Dispose database connection."""
        self.engine.dispose()


# Create singleton instance
db_manager = DatabaseManager()
