"""module provides utility functions."""

from __future__ import annotations

import json
from datetime import datetime


def safe_json_loads(
    data: str,
    default: dict | list | None = None,
) -> dict | list:
    """Safely load JSON data.

    Args:
        data (str): The JSON data to load.
        default (Union[dict, list], optional): The default value to return if loading fails. Defaults to [].

    Returns:
        Union[dict, list]: The loaded JSON data, or the default value if loading fails.

    """
    try:
        if default is None:
            default = []
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return default


def format_datetime(value: str | datetime) -> str:
    """Format a datetime object to a string in ISO 8601 format.

    Args:
        value (Union[str, datetime]): The value to format, which can be a string or a datetime object.

    Returns:
        str: The formatted datetime string if the input is a datetime object, otherwise the input value.

    """
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%dT%H:%M:%S")
    return value
