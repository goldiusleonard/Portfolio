"""Function to return database credentials."""

from __future__ import annotations

import os


def get_credentials(
    database: str,
) -> tuple[str | None, str | None, str | None, str | None]:
    """Retrieve database credentials based on the specified database name.

    This function fetches the user, password, host, and port for the given database
    from environment variables. If the database name is unknown, a ValueError is raised.

    Args:
        database (str): The name of the database. Supported values are "ada" and "mcmc".

    Returns:
        Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]: A tuple containing
        the database credentials: user, password, host, and port. If an environment variable
        is not set, its corresponding value in the tuple will be None.

    Raises:
        ValueError: If the specified database is not supported.

    """
    if database.lower() == "ada":
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT")
        return user, password, host, port
    if database.lower() == "mcmc":
        user = os.getenv("MCMC_DB_USER")
        password = os.getenv("MCMC_DB_PASSWORD")
        host = os.getenv("MCMC_DB_HOST")
        port = os.getenv("MCMC_DB_PORT")
        return user, password, host, port
    error_message = f"Unknown store type: {database}"
    raise ValueError(error_message)
