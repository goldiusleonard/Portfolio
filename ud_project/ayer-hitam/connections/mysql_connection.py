#!/usr/bin/env python3
"""Module contains functions to connect to the MySQL database."""

import logging
import os
from typing import NoReturn

import mysql.connector
from mysql.connector import Error, MySQLConnection
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def mysql_connection(database_name: str) -> MySQLConnection:
    """Establish a connection to the MySQL database and return the connection object."""
    # Fetch environment variables for database credentials
    host = os.getenv("MYSQL_DB_HOST")
    user = os.getenv("MYSQL_DB_USER")
    password = os.getenv("MYSQL_DB_PASSWORD")
    database = database_name

    # Initialize logging
    logging.basicConfig(level=logging.INFO)

    try:
        # Establish a connection
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
        )

        if connection.is_connected():
            logging.info("Successfully connected to MySQL!")
            # Fetch and log the list of databases
            cursor = connection.cursor()
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            logging.info("Databases in MySQL:")
            for db in databases:
                logging.info(" - %s", db[0])
            cursor.close()
            return connection

    except Error:
        logging.exception("Error connecting to MySQL")
        return None

    except Exception:
        logging.exception("Unexpected error occurred")
        return None


def _raise_missing_env_vars_error() -> NoReturn:
    """Raise a ValueError for missing database connection environment variables."""
    message = "Missing database connection environment variables"
    raise ValueError(message)


def mysql_engine(database_name: str) -> Engine:
    """Create MySQL Engine."""
    from urllib.parse import quote_plus

    try:
        host = os.getenv("MYSQL_DB_HOST")
        user = os.getenv("MYSQL_DB_USER")
        password = os.getenv("MYSQL_DB_PASSWORD")
        port = os.getenv("MYSQL_DB_PORT")

        # Add validation to prevent None values
        if not all([host, user, password, port]):
            _raise_missing_env_vars_error()

        encoded_username = quote_plus(user)
        encoded_password = quote_plus(password)

        # Return SQLAlchemy engine with additional configuration
        return create_engine(
            f"mysql+pymysql://{encoded_username}:{encoded_password}@{host}:{port}/{database_name}",
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=5,
            max_overflow=10,
        )
    except Exception:
        logging.exception("Error creating database engine")
        raise


def get_azure_session(engine: Engine) -> Session:
    """Create Session."""
    try:
        session_factory = sessionmaker(bind=engine)
        session = session_factory()

        # Check if there's a pending transaction
        if session.is_active:
            try:
                session.rollback()
            except Exception:
                logging.exception("Error during rollback")

        # Close the current session
        session.close()

        # Create and return a new session
        return Session()
    except Exception:
        logging.exception("Error creating session")
        return None


if __name__ == "__main__":
    try:
        connection = mysql_connection()
        if connection is None:
            logging.error("Failed to establish connection to MySQL.")
        else:
            logging.info("Connection successful. Ready to use!")
    except Exception:
        logging.exception("Unexpected error occurred")
