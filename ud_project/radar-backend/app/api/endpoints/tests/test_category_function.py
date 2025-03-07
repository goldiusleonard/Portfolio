"""Module contains tests for the category_function in the app.api.endpoints.functions module."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.api.endpoints.functions import category_function

mock_data = [
    MagicMock(
        sub_category="SubCategory1",
        category="Category1",
        topic_category_name="Topic1",
    ),
    MagicMock(
        sub_category="SubCategory2",
        category="Category1",
        topic_category_name="Topic2",
    ),
    MagicMock(
        sub_category="SubCategory1",
        category="Category2",
        topic_category_name="Topic3",
    ),
]


@pytest.fixture
def mock_db_session() -> Session:
    """Mock the database session."""
    session = MagicMock(spec=Session)
    session.query.return_value.join.return_value.distinct.return_value.all.return_value = mock_data
    return session


def test_get_all_category_data(mock_db_session: Session) -> None:
    """Test the get_all_category_data function."""
    result = category_function.get_all_category_data(mock_db_session)

    expected_result = [
        {
            "name": "Category1",
            "about": "",
            "sentiment": "",
            "risk": {"high": 0, "medium": 0, "low": 0},
            "subCategories": [
                {
                    "name": "SubCategory1",
                    "topics": ["Topic1"],
                },
                {
                    "name": "SubCategory2",
                    "topics": ["Topic2"],
                },
            ],
            "totalSubCategory": 2,
            "totalTopics": 2,
        },
        {
            "name": "Category2",
            "about": "",
            "sentiment": "",
            "risk": {"high": 0, "medium": 0, "low": 0},
            "subCategories": [
                {
                    "name": "SubCategory1",
                    "topics": ["Topic3"],
                },
            ],
            "totalSubCategory": 1,
            "totalTopics": 1,
        },
    ]

    assert result == expected_result  # noqa: S101


def test_get_visual_chart_data_current() -> None:
    """Test the get_visual_chart_data function for current state."""
    mock_response = {
        "data": [
            {"name": "Category1", "data": [10, 20, 30], "total": 60},
            {"name": "Category2", "data": [5, 15, 25], "total": 45},
        ],
    }
    with patch(
        "app.api.endpoints.functions.category_function.__get_current_data",
        return_value=mock_response,
    ):
        result = category_function.get_visual_chart_data(
            categories=["Category1", "Category2"],
            period=1,
            chart_type="risk",
            state="current",
        )

    assert result == mock_response  # noqa: S101
