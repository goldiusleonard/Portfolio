"""Module contains the NewsArticle model using Beanie."""

from __future__ import annotations

from datetime import datetime  # noqa: TCH003

from beanie import Document


class NewsArticle(Document):
    """NewsArticle model class representing the NewsArticle collection in MongoDB."""

    article_id: str
    category: str
    expanded_query: str | None
    content: str
    published_date: datetime
    source: str
    sub_category: str | None
    title: str
    topic: str | None
    url: str
    image: str | None

    class Settings:
        """Beanie settings for MongoDB collection configuration."""

        collection = "news_articles"
        indexes = ["article_id", "category", "sub_category"]  # noqa: RUF012
