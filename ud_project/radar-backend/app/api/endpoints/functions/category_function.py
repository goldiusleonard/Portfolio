"""Category Functions."""

from __future__ import annotations

import os
from calendar import monthrange
from datetime import datetime
from typing import TYPE_CHECKING

import requests
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException

from app.core.dependencies import get_db
from app.enums.category_visualization_type import CategoryVisualizationType
from app.models import topic_category_table, topic_keywords_details_table

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
from app.core.constants import (
    DEFAULT_CATEGORY_CURRENT_DATA_URL,
    DEFAULT_CATEGORY_PREDICTION_DATA_URL,
    SUCCESS_CODE,
)


def get_all_category_data(db: Session = None) -> list[dict]:
    """Get all category data."""
    if db is None:
        with next(get_db()) as session:
            return _query_category(session)
    return _query_category(db)


def _query_category(db: Session) -> list[dict]:
    """Query category data and return in a serializable format."""
    try:
        results_query = (
            db.query(
                topic_keywords_details_table.TopicKeywordsDetails.sub_category,
                topic_keywords_details_table.TopicKeywordsDetails.category,
                topic_category_table.TopicCategory.topic_category_name,
            )
            .join(
                topic_category_table.TopicCategory,
                topic_category_table.TopicCategory.id
                == topic_keywords_details_table.TopicKeywordsDetails.topic_category_id,
            )
            .distinct()
            .all()
        )

        categories = {}
        for row in results_query:
            category_name = row.category
            sub_category_name = row.sub_category
            topic_name = row.topic_category_name

            category = categories.setdefault(
                category_name,
                {
                    "name": category_name,
                    "about": "",
                    "sentiment": "",
                    "risk": {"high": 0, "medium": 0, "low": 0},
                    "subCategories": {},
                    "totalSubCategory": 0,
                    "totalTopics": 0,
                },
            )

            sub_category = category["subCategories"].setdefault(
                sub_category_name,
                {
                    "name": sub_category_name,
                    "topics": [],
                },
            )

            sub_category["topics"].append(topic_name)
            category["totalTopics"] += 1

        for category in categories.values():
            category["subCategories"] = list(category["subCategories"].values())
            category["totalSubCategory"] = len(category["subCategories"])

        return list(categories.values())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get category: {e!s}",
        ) from e


def get_visual_chart_data(
    categories: list[str],
    period: int,
    chart_type: str,
    state: str,
) -> dict:
    """Get visual chart data."""
    if state == "current":
        return __get_current_data(
            categories=categories,
            period=period,
            chart_type=chart_type,
        )
    if state == "prediction":
        return __get_prediction_data(
            categories=categories,
            period=period,
            chart_type=chart_type,
        )

    raise HTTPException(status_code=400, detail="Invalid state")


def __get_current_data(categories: list[str], period: int, chart_type: str) -> dict:  # noqa: C901
    """Get current data."""
    base_url = (
        os.getenv("CATEGORY_CURRENT_DATA_URL") or DEFAULT_CATEGORY_CURRENT_DATA_URL
    )
    url = base_url + f"?analysis_type={chart_type}&time_range={period}"
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, json=categories)  # noqa: S113

    if response.status_code == SUCCESS_CODE:
        current_data = response.json()
        result = {"data": []}
        if period == 1:
            current_date = datetime.now()  # noqa: DTZ005
            days_in_month = monthrange(current_date.year, current_date.month)[1]
            for category in categories:
                category_data = []
                total = 0
                for day in range(1, days_in_month + 1):
                    date_str = current_date.replace(day=day).strftime("%Y-%m-%d")
                    current_data_dict = {entry["date"]: entry for entry in current_data}
                    if (
                        date_str in current_data_dict
                        and current_data_dict[date_str]["category"] == category
                    ):
                        entry = current_data_dict[date_str]
                        category_data.append(entry["total_count"])
                        total += entry["total_count"]
                    else:
                        category_data.append(0)
                result["data"].append(
                    {
                        "name": category,
                        "data": category_data,
                        "total": total,
                    },
                )
        elif period > 1:
            current_date = datetime.now()  # noqa: DTZ005
            result = {"data": []}
            for category in categories:
                category_data = []
                total = 0
                for month_offset in reversed(range(period)):
                    month_start_date = (
                        current_date - relativedelta(months=month_offset)
                    ).replace(day=1)
                    month_end_date = month_start_date.replace(
                        day=monthrange(month_start_date.year, month_start_date.month)[
                            1
                        ],
                    )
                    month_data = 0
                    for entry in current_data:
                        entry_date = datetime.strptime(entry["date"], "%Y-%m-%d")  # noqa: DTZ007
                        if (
                            month_start_date <= entry_date <= month_end_date
                            and entry["category"] == category
                        ):
                            month_data += entry["total_count"]
                    category_data.append(month_data)
                    total += month_data
                result["data"].append(
                    {
                        "name": category,
                        "data": category_data,
                        "total": total,
                    },
                )
        return result
    raise HTTPException(
        status_code=response.status_code,
        detail=f"Failed to retrieve data: {response.text}",
    )


def __get_prediction_data(categories: list[str], period: int, chart_type: str) -> dict:  # noqa: PLR0912, C901
    """Get prediction data."""
    result = {"data": []}
    for category in categories:
        now = datetime.now()  # noqa: DTZ005
        if period == 1:
            start_date = now.replace(day=1).strftime("%Y-%m-%d")
        else:
            start_date = (
                (now - relativedelta(months=period - 1))
                .replace(day=1)
                .strftime("%Y-%m-%d")
            )
        end_date = (
            datetime.now()  # noqa: DTZ005
            .replace(day=monthrange(datetime.now().year, datetime.now().month)[1])  # noqa: DTZ005
            .strftime("%Y-%m-%d")
        )
        prediction = {}
        try:
            prediction = __call_prediction_api(category, start_date, end_date)
            prediction = prediction["data"]
        except Exception:  # noqa: BLE001
            prediction = []
        data = []
        total = 0
        if period == 1:
            current_date = datetime.now()  # noqa: DTZ005
            days_in_month = monthrange(current_date.year, current_date.month)[1]
            for day in range(1, days_in_month + 1):
                date_str = current_date.replace(day=day).strftime("%Y-%m-%d")

                prediction_dict = {entry["Date"]: entry for entry in prediction}
                if date_str in prediction_dict:
                    entry = prediction_dict[date_str]
                    if chart_type == CategoryVisualizationType.ENGAGEMENT.value:
                        data.append(entry["engagement"])
                    elif chart_type == CategoryVisualizationType.RISK.value:
                        data.append(entry["risk"])
                    else:
                        data.append(0)
                else:
                    data.append(0)
        elif period > 1:
            current_date = datetime.now()  # noqa: DTZ005
            for month_offset in reversed(range(period)):
                month_start_date = (
                    current_date - relativedelta(months=month_offset)
                ).replace(day=1)
                month_end_date = month_start_date.replace(
                    day=monthrange(month_start_date.year, month_start_date.month)[1],
                )
                month_data = 0
                for entry in prediction:
                    entry_date = datetime.strptime(entry["Date"], "%Y-%m-%d")  # noqa: DTZ007
                    if month_start_date <= entry_date <= month_end_date:
                        if chart_type == CategoryVisualizationType.ENGAGEMENT.value:
                            month_data += entry["engagement"]
                        elif chart_type == CategoryVisualizationType.RISK.value:
                            month_data += entry["risk"]
                data.append(month_data)
        total = sum(data)
        result["data"].append(
            {
                "name": category,
                "data": data,
                "total": total,
            },
        )

    return result


def __call_prediction_api(category: str, start_date: str, end_date: str) -> dict:
    url = (
        os.getenv("CATEGORY_PREDICTION_DATA_URL")
        or DEFAULT_CATEGORY_PREDICTION_DATA_URL
    )
    headers = {"accept": "application/json"}
    params = {
        "category": category,
        "start_date": start_date,
        "end_date": end_date,
    }
    response = requests.get(url, headers=headers, params=params)  # noqa: S113
    if response.status_code == SUCCESS_CODE:
        return response.json()
    raise HTTPException(
        status_code=response.status_code,
        detail=f"Failed to retrieve data: {response.text}",
    )
