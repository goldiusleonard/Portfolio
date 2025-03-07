import favicon
import os

from datetime import datetime
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from eventregistry import EventRegistry, QueryArticlesIter
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, model_validator
from typing import Optional, Union
from requests.exceptions import Timeout, RequestException

from ..news_filter.base import filter_news
from ..query_expander.base import expand_topic
from ..utils.mongodb import save_mongodb

router = APIRouter()

load_dotenv()

newsapi_api_key: str = os.getenv("NEWS_API_KEY", "")

if newsapi_api_key == "":
    raise ValueError("NewsAPI.ai API key is not valid!")


def fetch_favicon(url: str, timeout: int = 5):
    try:
        # Using requests to get the favicon with a timeout
        favicons = favicon.get(
            url,
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
        )
        if favicons:
            return favicons[0].url
        return ""
    except Timeout:
        print(f"Timeout while fetching favicon for {url}")
        return ""
    except RequestException as e:
        print(f"Error fetching favicon for {url}: {e}")
        return ""


def fetch_articles(topic_dict: dict):
    # Initialize the EventRegistry client
    er = EventRegistry(apiKey=newsapi_api_key)
    articles_list: list = []

    # Filter only the category, sub_category, and topic fields
    relevant_fields = {
        key: value
        for key, value in topic_dict.items()
        if key in ["category", "sub_category", "topic"] and value is not None
    }

    # Concatenate the relevant fields into a single string
    topic_to_expand = "".join(relevant_fields.values())

    # Expands the topic
    news_query = expand_topic(topic_to_expand)

    query_filters: dict = {
        "lang": "eng",
    }

    if "start_date" in topic_dict and topic_dict["start_date"] is not None:
        query_filters["dateStart"] = topic_dict["start_date"]

    if "end_date" in topic_dict and topic_dict["end_date"] is not None:
        query_filters["dateEnd"] = topic_dict["end_date"]

    # Define the complex query with the topic
    query = {
        "$query": {
            "$and": [
                {"keyword": news_query, "keywordSearchMode": "simple"},
                query_filters,
            ]
        },
        "$filter": {
            "isDuplicate": "skipDuplicates",
        },
    }

    # Initialize the query with the complex query structure
    q = QueryArticlesIter.initWithComplexQuery(query)
    max_results = topic_dict["max_news"]

    # Fetch articles and add them to the list
    for article in q.execQuery(er, maxItems=max_results):
        try:
            # Fetch the favicon with a timeout of 5 seconds
            icon_url = fetch_favicon(article.get("url"))
        except Exception as e:
            # In case of any error (e.g., invalid URL, no favicon), set image to an empty string
            icon_url = ""
            print(f"Error fetching favicon for {article.get('url')}: {e}")

        articles_list.append(
            {
                "title": article.get("title"),
                "url": article.get("url"),
                "image": icon_url,
                "published_date": article.get("dateTime"),
                "source": article.get("source", {}).get("title"),
                "content": article.get("body", "Full content not available"),
            }
        )

    # PostProcessing - Filtering Relevant
    filtered_article_list = filter_news(articles_list, news_query)

    # save to MongoDB
    save_mongodb(filtered_article_list, topic_dict, news_query)

    return filtered_article_list


######################### API #########################
# Pydantic model for validation
class NewsParams(BaseModel):
    category: Optional[Union[str, None]] = None
    sub_category: Optional[Union[str, None]] = None
    topic: Optional[Union[str, None]] = None
    max_news: Optional[int] = 100
    start_date: Optional[Union[str, None]] = None
    end_date: Optional[Union[str, None]] = None

    @model_validator(mode="after")
    def validate_combinations(cls, values):
        category = values.category
        sub_category = values.sub_category
        topic = values.topic

        # Validate allowed scenarios:
        # 1. Only category is provided
        # 2. Both category and sub_category are provided
        # 3. All category, sub_category, and topic are provided
        if not category:
            raise ValueError("The 'category' field is required.")

        if sub_category and not category:
            raise ValueError("'sub_category' is not allowed without 'category'.")

        if topic and not (category and sub_category):
            raise ValueError(
                "'topic' is not allowed without both 'category' and 'sub_category'."
            )

        if not values.max_news:
            values.max_news = 100

        if values.max_news <= 0:
            raise ValueError("'max_news' should not be less than or equal to zero.")

        # Validate date formats
        date_format = "%Y-%m-%d"
        if values.start_date:
            try:
                start_date = datetime.strptime(values.start_date, date_format)
            except ValueError:
                raise ValueError("'start_date' must be in YYYY-MM-DD format.")

        if values.end_date:
            try:
                end_date = datetime.strptime(values.end_date, date_format)
            except ValueError:
                raise ValueError("'end_date' must be in YYYY-MM-DD format.")

        if values.start_date and values.end_date:
            # Check if start_date is not later than end_date
            if start_date > end_date:
                raise ValueError("'start_date' cannot be later than 'end_date'.")

        return values


# Parse query parameters into Pydantic model
def parse_query_params(
    category: Optional[Union[str, None]] = Query(
        None, description="Filter by category."
    ),
    sub_category: Optional[Union[str, None]] = Query(
        None, description="Filter by sub-category."
    ),
    topic: Optional[Union[str, None]] = Query(None, description="Filter by AI topic."),
    max_news: Optional[int] = 100,
    start_date: Optional[Union[str, None]] = Query(
        None, description="Start date in 'YYYY-MM-DD'."
    ),
    end_date: Optional[Union[str, None]] = Query(
        None, description="End date in 'YYYY-MM-DD'."
    ),
):
    return NewsParams(
        category=category,
        sub_category=sub_category,
        topic=topic,
        max_news=max_news,
        start_date=start_date,
        end_date=end_date,
    )


# Endpoint to get news
@router.get("")
def get_news(params: NewsParams = Depends(parse_query_params)):
    try:
        # Simulated function to fetch news articles
        news_articles = fetch_articles(params.model_dump())

        if news_articles is None:
            # Return a 404 status if no news is found
            return JSONResponse(
                content={"error": "No news found"},
                status_code=404,
            )
    except Exception as e:
        print(f"News Retrieval Error: {e}")
        # Return a 500 status for unexpected errors
        return JSONResponse(
            content={"error": "An error occurred while retrieving news"},
            status_code=500,
        )
    # Return the news articles if found
    return JSONResponse(
        content=news_articles,
        status_code=200,
    )
