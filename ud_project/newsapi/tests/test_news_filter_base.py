import os
import pytest

from unittest.mock import patch, MagicMock
from src.news_filter.base import filter_news


# Mock environment variables for testing
@pytest.fixture(autouse=True)
def mock_env_vars():
    with patch.dict(
        os.environ,
        {
            "LLAMA70B_MODEL": "mock_model",
            "LLAMA70B_LLM_BASE_URL": "mock_url",
            "LLAMA70B_LLM_API_KEY": "mock_api_key",
        },
    ):
        yield


# Test for filtering function
@patch("src.news_filter.base.llama70b_client.chat.completions.create")
def test_filtering(mock_create):
    # Mock data
    article_list = [
        {
            "title": "Prince Harry met with hate speech",
            "url": "http://example.com/1",
            "published_date": "2024-01-01",
        },
        {
            "title": "Unrelated News Article",
            "url": "http://example.com/2",
            "published_date": "2024-01-02",
        },
    ]
    news_query = "Hate Speech"

    # Mock the response from OpenAI for relevance check
    mock_create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="relevant"))]
    )

    # Call the function
    filtered_articles = filter_news(article_list, news_query)

    # Assertions
    assert len(filtered_articles) == 2
    assert filtered_articles[0]["title"] == "Prince Harry met with hate speech"

    # Making it Irrelevant = 0
    mock_create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="0"))]
    )

    filtered_articles = filter_news(article_list, news_query)

    assert len(filtered_articles) == 0
