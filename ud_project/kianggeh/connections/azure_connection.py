"""Module contains functions to connect to the MySQL database."""

from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def get_azure_engine(
    database: str,
    user: str,
    password: str,
    host: str,
    port: int,
) -> Engine:
    """Create MySQL Engine."""
    encoded_username = quote_plus(user)
    encoded_password = quote_plus(password)

    connect_args = {"ssl": {"fake_flag_to_enable_tls": True}}

    return create_engine(
        f"mysql+pymysql://{encoded_username}:{encoded_password}@{host}:{port}/{database}",
        connect_args=connect_args,
    )


def get_azure_session(
    database: str,
    user: str,
    password: str,
    host: str,
    port: int,
) -> Session:
    """Create Session."""
    engine = get_azure_engine(database, user, password, host, port)
    session_factory = sessionmaker(bind=engine)

    return session_factory()
