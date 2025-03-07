"""Category and Subcategory Data Functions.

This module provides functions for retrieving category and subcategory data from an external API.
"""

from __future__ import annotations

import os

import httpx


async def fetch_category_data(category: list[str]) -> list[dict]:
    """Fetch data for the given categories from the external API.

    Args:
        category (list[str]): A list of category names to fetch data for.

    Returns:
        list[dict]: A list of dictionaries containing the fetched data.

    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            os.getenv(
                "CROSS_CATEGORY_INSIGHT_API_URL",
                "http://af3164eb711524ba5afd1b47b63ebdd3-1243418058.ap-southeast-1.elb.amazonaws.com:8080/group_by_category/",
            ),
            headers={
                "accept": "application/json",
                "Content-Type": "application/json",
            },
            json=category,
        )
        response.raise_for_status()
        data = response.json()
        return data if data else []
