"""Module for retrieving and merging keyword trends across multiple categories."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import requests

from app.core.constants import (
    DEFAULT_GROUP_BY_CATEGORY_URL,
    DEFAULT_KEYWORD_TRENDS_URL,
    SUCCESS_CODE,
)
from app.models.content_data_asset_table import BAContentDataAsset

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from utils.logger import Logger

log = Logger("Cross_Category_Insight_Function")


# Constants
KEYWORD_TRENDS_URL_ENV = "KEYWORD_TRENDS_URL"
HTTP_OK = 200
TIMEOUT = 10  # seconds


def get_keyword_trends(categories: list[str], num_of_days: int) -> dict:
    """Retrieve keyword trends for multiple categories and merge results."""
    results = set()
    url = os.getenv(KEYWORD_TRENDS_URL_ENV) or DEFAULT_KEYWORD_TRENDS_URL
    if not url:
        error_msg = f"Environment variable {KEYWORD_TRENDS_URL_ENV} is not set."
        raise ValueError(error_msg)

    for category in categories:
        full_url = f"{url}/retrieve_keyword_trend/?category={category}&num_of_days={num_of_days}"
        response = requests.get(
            full_url,
            headers={"accept": "application/json"},
            timeout=TIMEOUT,
        )
        if response.status_code == SUCCESS_CODE:
            data = response.json()
            results.update(data.get("message", []))

    return {"keywordTrends": sorted(results)}


def get_search_categories(categories: list[str], db: Session) -> dict:
    """Retrieve search categories."""
    group_by_category_data = __get_group_by_category_data(categories)
    search_categories = []
    total_reported_cases = 0
    for item in group_by_category_data:
        sub_categories_data = []
        content_data_assets = (
            db.query(BAContentDataAsset)
            .distinct(
                BAContentDataAsset.sub_category,
                BAContentDataAsset.topic_category,
            )
            .filter(BAContentDataAsset.category == item["category"])
            .all()
        )
        sub_category_map = {}
        for content_data_asset in content_data_assets:
            if content_data_asset.sub_category and content_data_asset.topic_category:
                if content_data_asset.sub_category not in sub_category_map:
                    sub_category_map[content_data_asset.sub_category] = {
                        "name": content_data_asset.sub_category,
                        "topics": {content_data_asset.topic_category},
                    }
                else:
                    sub_category_map[content_data_asset.sub_category]["topics"].add(
                        content_data_asset.topic_category,
                    )
        for data in sub_category_map.values():
            data["topics"] = list(data["topics"])
            sub_categories_data.append(data)
        search_categories.append(
            {
                "name": item["category"],
                "about": item["about_category"],
                "sentiment": item["sentiment"].lower(),
                "risk": {
                    "high": item["risk_status_distribution"]["High"],
                    "medium": item["risk_status_distribution"]["Medium"],
                    "low": item["risk_status_distribution"]["Low"],
                },
                "subCategories": sub_categories_data,
                "totalSubCategory": item["total_subcategories"],
                "totalTopics": item["total_topics"],
                "totalReportedCases": item["total_reported_cases"],
            },
        )
        total_reported_cases += item["total_reported_cases"]
    return {"categories": search_categories, "totalReportedCases": total_reported_cases}


def __get_group_by_category_data(categories: list[str]) -> dict:
    """Retrieve group by category data."""
    url = os.getenv("GROUP_BY_CATEGORY_URL_ENV") or DEFAULT_GROUP_BY_CATEGORY_URL
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
    }
    response = requests.post(
        url,
        headers=headers,
        json=categories,
        timeout=TIMEOUT,
    )
    if response.status_code == SUCCESS_CODE:
        return response.json()

    error_msg = "Failed to retrieve group by category data."
    log.error("Error response for __get_group_by_category_data: %s", response.text)
    raise ValueError(error_msg)
