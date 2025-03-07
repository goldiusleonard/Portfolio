"""Functions for the news functionality, including getting news articles and categories."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from utils.logger import Logger

log = Logger("News_Function")

if TYPE_CHECKING:
    from app.core.vm_mongo_db import MongoClient


async def get_categories_with_subcategories(
    formatted_news: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Extract categories along with their subcategories from formatted news."""
    category_map = {}
    for article in formatted_news:
        category = article.get("category", "")
        sub_category = article.get("subCategory", "")
        if category:
            if category not in category_map:
                category_map[category] = set()
            if sub_category:
                category_map[category].add(sub_category)

    return [
        {"category": cat, "subCategories": list(set(subs))}
        for cat, subs in category_map.items()
    ]


async def get_all_news_with_categories(
    categories: list[str],
    db: MongoClient,
) -> dict[str, list[dict[str, Any]]]:
    """Get all news articles filtered by categories."""
    query = {"category": {"$in": categories}} if categories else {}
    try:
        all_news = await db.news_articles.find(query).to_list()
        formatted_news = [
            {
                "id": str(article.get("_id", "")),
                "article": article.get("article_id", ""),
                "link": article.get("url", ""),
                "sourceId": article.get("source", ""),
                "content": article.get("content", ""),
                "title": article.get("title", ""),
                "publishDate": article.get("published_date", ""),
                "relevancyScore": 0,
                "subCategory": article.get("sub_category", ""),
                "category": article.get("category", ""),
                "timestamp": article.get("published_date", ""),
                "image": article.get("image", ""),
            }
            for article in all_news
        ]

        return {
            "news": formatted_news,
            "categories": await get_categories_with_subcategories(formatted_news),
        }
    except Exception as e:  # noqa: BLE001
        log.error(f"Error fetching news articles: {e}")  # noqa: TRY400, G004
        return {"news": [], "categories": []}
