"""Module contains tests for the cross_category_insight_function in the app.api.endpoints.functions module."""

import os
from unittest.mock import MagicMock, patch

import pytest

from app.api.endpoints.functions.cross_category_insight_function import (
    get_keyword_trends,
    get_search_categories,
)
from app.core.constants import SUCCESS_CODE


def setup_module() -> None:
    """Set up the environment variable before running the tests."""
    os.environ["KEYWORD_TRENDS_URL"] = "http://localhost:8009"


@pytest.fixture
def mock_requests_get() -> MagicMock:
    """Fixture to mock requests.get."""
    with patch("requests.get") as mock_get:
        yield mock_get


def test_get_keyword_trends_success(mock_requests_get: MagicMock) -> None:
    """Test successful retrieval of keyword trends."""
    # Mock the response for requests.get
    mock_response = MagicMock()
    mock_response.status_code = SUCCESS_CODE
    mock_response.json.return_value = {"message": ["keyword1", "keyword2"]}
    mock_requests_get.return_value = mock_response

    # Call the function
    result = get_keyword_trends(["Scam", "Fraud"], 7)

    # Assert the results
    assert result == {"keywordTrends": ["keyword1", "keyword2"]}  # noqa: S101


def test_get_keyword_trends_empty_response(mock_requests_get: MagicMock) -> None:
    """Test retrieval of keyword trends with an empty response."""
    # Mock the response for requests.get
    mock_response = MagicMock()
    mock_response.status_code = SUCCESS_CODE
    mock_response.json.return_value = {"message": []}
    mock_requests_get.return_value = mock_response

    # Call the function
    result = get_keyword_trends(["Scam", "Fraud"], 7)

    # Assert the results
    assert result == {"keywordTrends": []}  # noqa: S101


def test_get_keyword_trends_error_response(mock_requests_get: MagicMock) -> None:
    """Test retrieval of keyword trends with an error response."""
    # Mock the response for requests.get
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_requests_get.return_value = mock_response

    # Call the function
    result = get_keyword_trends(["Scam", "Fraud"], 7)

    # Assert the results
    assert result == {"keywordTrends": []}  # noqa: S101


def test_get_search_categories() -> None:
    """Test retrieval of search categories."""
    mock_db_session = MagicMock()
    mock_db_session.query.return_value.distinct.return_value.filter.return_value.all.return_value = [
        MagicMock(sub_category="SubCat1", topic_category="Topic1"),
        MagicMock(sub_category="SubCat2", topic_category="Topic2"),
    ]

    with patch(
        "app.api.endpoints.functions.cross_category_insight_function.__get_group_by_category_data",
        return_value=[
            {
                "category": "Category1",
                "sentiment": "Positive",
                "about_category": "about",
                "risk_status_distribution": {
                    "High": 0,
                    "Medium": 0,
                    "Low": 0,
                },
                "total_reported_cases": 10,
                "total_subcategories": 2,
                "total_topics": 3,
            },
        ],
    ):
        result = get_search_categories(["Category1"], mock_db_session)
        expected_result = {
            "categories": [
                {
                    "name": "Category1",
                    "about": "about",
                    "sentiment": "positive",
                    "risk": {
                        "high": 0,
                        "medium": 0,
                        "low": 0,
                    },
                    "subCategories": [
                        {
                            "name": "SubCat1",
                            "topics": ["Topic1"],
                        },
                        {
                            "name": "SubCat2",
                            "topics": ["Topic2"],
                        },
                    ],
                    "totalReportedCases": 10,
                    "totalSubCategory": 2,
                    "totalTopics": 3,
                },
            ],
            "totalReportedCases": 10,
        }

        assert result == expected_result  # noqa: S101
