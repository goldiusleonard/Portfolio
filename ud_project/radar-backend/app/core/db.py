"""Database get session."""

import os
from typing import Generator

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.vm_db import Session_Vm


class DatabaseSession:
    """Handles the creation and configuration of database sessions."""

    @staticmethod
    def get_session() -> Session:
        """Create and configure a new database session.

        Sets the active database using the value of the `VM_DATABASE_2`
        environment variable, if specified.

        Returns:
            A configured SQLAlchemy session object.

        """
        session = Session_Vm()
        database = os.getenv("VM_DATABASE_2")
        if database:
            # Use SQLAlchemy's text() function for raw SQL
            session.execute(text(f"USE {database}"))
        return session


def get_db_session() -> Generator[Session, None, None]:
    """Provide a database session for use in dependency injection.

    Yields:
        An active SQLAlchemy database session.

    Ensures the session is properly closed after use.

    """
    db = DatabaseSession.get_session()
    try:
        yield db
    finally:
        db.close()
