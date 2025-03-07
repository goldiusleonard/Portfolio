"""News function from mongoDB."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId

from app.api.endpoints.functions.news_function import (
    get_all_news_with_categories,
    get_categories_with_subcategories,
)

EXPECTED_NEWS_COUNT = 1
DEFAULT_RELEVANCY_SCORE = 0


@pytest.fixture
def sample_news_data() -> list[dict]:
    """Mock news data from MongoDB."""
    return [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "article_id": "article1",
            "url": "http://example.com/1",
            "source": "source1",
            "content": "Test content 1",
            "title": "Test title 1",
            "published_date": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "category": "tech",
            "sub_category": "AI",
            "image": "http://example.com/image1.jpg",
        },
    ]


@pytest.mark.asyncio
async def test_get_all_news_with_categories(sample_news_data: list[dict]) -> None:
    """Test get all news with categories."""
    mock_db = MagicMock()
    mock_db.news_articles.find.return_value.to_list = AsyncMock(
        return_value=sample_news_data,
    )

    with patch(
        "app.api.endpoints.functions.news_function.get_categories_with_subcategories",
        new=AsyncMock(
            return_value=[{"category": "tech", "subCategories": ["AI"]}],
        ),
    ):
        result = await get_all_news_with_categories(["tech"], mock_db)

        assert "news" in result  # noqa: S101
        assert "categories" in result  # noqa: S101
        assert len(result["news"]) == EXPECTED_NEWS_COUNT  # noqa: S101

        first_news = result["news"][0]
        assert first_news["article"] == "article1"  # noqa: S101
        assert first_news["link"] == "http://example.com/1"  # noqa: S101
        assert first_news["sourceId"] == "source1"  # noqa: S101
        assert first_news["content"] == "Test content 1"  # noqa: S101
        assert first_news["title"] == "Test title 1"  # noqa: S101
        assert first_news["category"] == "tech"  # noqa: S101
        assert first_news["subCategory"] == "AI"  # noqa: S101
        assert first_news["image"] == "http://example.com/image1.jpg"  # noqa: S101


@pytest.mark.asyncio
async def test_get_categories_with_subcategories(sample_news_data: list[dict]) -> None:
    """Test extracting categories and subcategories from formatted news."""
    formatted_news = [
        {
            "category": article["category"],
            "subCategory": article["sub_category"],
        }
        for article in sample_news_data
    ]
    result = await get_categories_with_subcategories(formatted_news)
    expected_result = [{"category": "tech", "subCategories": ["AI"]}]
    assert result == expected_result  # noqa: S101
