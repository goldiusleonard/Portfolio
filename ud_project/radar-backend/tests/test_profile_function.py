"""Module contains tests for the profile_function in the app.api.endpoints.functions module."""

from datetime import datetime, timezone
from typing import NamedTuple
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.api.endpoints.functions.profile_function import (
    get_categories_by_username,
    get_heatmap_by_username,
    get_profile_details,
)

CHART_DATA_TOTAL = 5


@pytest.fixture
def mock_db_session() -> Session:
    """Fixture to mock a database session."""
    return MagicMock(spec=Session)


def test_get_profile_details_success(mock_db_session: Session) -> None:
    """Test successful retrieval of profile details."""
    mock_profile = MagicMock()
    mock_profile.id = 1
    mock_profile.user_handle = "test_user"
    mock_profile.profile_engagement_score = 85
    mock_profile.user_following_count = 100
    mock_profile.user_followers_count = 500
    mock_profile.user_total_videos = 50
    mock_profile.latest_posted_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    mock_profile.creator_photo_link = "http://example.com/profile.jpg"
    mock_profile.profile_api_id = "api_123"

    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        mock_profile
    )

    result = get_profile_details("test_user", mock_db_session)

    assert result["id"] == "1"  # noqa: S101
    assert result["name"] == "test_user"  # noqa: S101
    assert result["engagement"] == "85"  # noqa: S101
    assert result["following"] == "100"  # noqa: S101
    assert result["followers"] == "500"  # noqa: S101
    assert result["posts"] == "50"  # noqa: S101
    assert result["lastPostDate"] == "2024-01-01"  # noqa: S101
    assert result["profilePicture"] == "http://example.com/profile.jpg"  # noqa: S101
    assert result["creator_id"] == "api_123"  # noqa: S101


def test_get_profile_details_not_found(mock_db_session: Session) -> None:
    """Test retrieval of profile details when no profile is found."""
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    result = get_profile_details("unknown_user", mock_db_session)

    assert result["id"] == 0  # noqa: S101
    assert result["name"] == ""  # noqa: S101
    assert result["engagement"] == "0%"  # noqa: S101
    assert result["following"] == "0"  # noqa: S101
    assert result["followers"] == "0"  # noqa: S101
    assert result["posts"] == "0"  # noqa: S101
    assert result["lastPostDate"] == ""  # noqa: S101
    assert result["profilePicture"] == ""  # noqa: S101
    assert result["creator_id"] == ""  # noqa: S101


def test_get_categories_by_username(mock_db_session: Session) -> None:
    """Test retrieval of categories by username."""

    class MockCategory(NamedTuple):
        category_name: str
        risk_status: str
        category_count: int

    mock_db_session.query.return_value.filter.return_value.all.return_value = [
        MockCategory(category_name="tech", risk_status="high", category_count=10),
        MockCategory(category_name="sports", risk_status="low", category_count=5),
    ]

    result = get_categories_by_username("test_user", mock_db_session)

    assert result == [  # noqa: S101
        {"name": "tech", "risk": "high", "count": 10},
        {"name": "sports", "risk": "low", "count": 5},
    ]


def test_get_heatmap_by_username(mock_db_session: Session) -> None:
    """Test retrieval of heatmap and profile details by username."""
    with patch(
        "app.api.endpoints.functions.profile_function.get_heatmap_calendar_by_username",
    ) as mock_heatmap_calendar, patch(
        "app.api.endpoints.functions.profile_function.get_profile_details",
    ) as mock_profile_details, patch(
        "app.api.endpoints.functions.profile_function.get_categories_by_username",
    ) as mock_categories:
        mock_heatmap_calendar.return_value = {
            "calendar": [{"date": "2024-01-01", "count": 5}],
        }
        mock_profile_details.return_value = {
            "id": "1",
            "name": "test_user",
            "engagement": "85",
            "following": "100",
            "followers": "500",
            "posts": "50",
            "lastPostDate": "2024-01-01",
            "profilePicture": "http://example.com/profile.jpg",
            "creator_id": "api_123",
        }
        mock_categories.return_value = [{"name": "tech", "risk": "high", "count": 10}]

        result = get_heatmap_by_username("test_user", mock_db_session)

        assert result["id"] == "1"  # noqa: S101
        assert result["creator"]["name"] == "test_user"  # noqa: S101
        assert result["creator"]["categories"][0]["name"] == "tech"  # noqa: S101
        assert result["creator"]["chartData"]["total"] == CHART_DATA_TOTAL  # noqa: S101
        assert result["creator"]["chartData"]["calendar"][0]["date"] == "2024-01-01"  # noqa: S101
