import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.modules.news import router
from src.modules.news import fetch_articles


@pytest.fixture(scope="function")
def mock_env_vars(monkeypatch):
    """Fixture to mock environment variables with proper cleanup"""
    env_vars = {
        "LLAMA70B_MODEL": "mock_model",
        "LLAMA70B_LLM_BASE_URL": "mock_url",
        "LLAMA70B_LLM_API_KEY": "mock_api_key",
        "OPENAI_API_KEY": "mock_openai_key",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def mock_chat_completion():
    """Mock for OpenAI chat completion response"""
    return {
        "id": "chatcmpl-mock123",
        "object": "chat.completion",
        "created": 1677858242,
        "model": "gpt-4",
        "usage": {"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150},
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "This article is relevant because it discusses hate speech targeting the royal family, \
                          specifically addressing discriminatory language and harmful rhetoric. The content aligns \
                          with the specified category and topic of royal heritage-related hate speech.",
                },
                "finish_reason": "stop",
                "index": 0,
            }
        ],
    }


@pytest.fixture
def mock_fetch_articles():
    with patch("src.modules.news.fetch_articles") as mock:
        yield mock


@pytest.fixture
def mock_openai(mock_chat_completion):
    """Comprehensive OpenAI mock fixture with realistic chat completion"""
    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = type(
            "ChatCompletion", (), mock_chat_completion
        )
        mock_openai_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_event_registry():
    with patch("src.modules.news.EventRegistry") as mock:
        mock_er = MagicMock()
        mock_er.QueryArticlesIter.return_value = MagicMock()
        mock.return_value = mock_er
        yield mock


@pytest.fixture
def mock_filter_news():
    with patch("src.modules.news.filter_news") as mock:
        yield mock


@pytest.fixture
def mock_save_mongodb():
    with patch("src.utils.mongodb.save_mongodb") as mock:
        yield mock


def test_fetch_articles_success(
    mock_env_vars,
    mock_event_registry,
    mock_filter_news,
    mock_save_mongodb,
    mock_openai,
    mock_chat_completion,
):
    """Test successful article fetching with all dependencies mocked"""
    topic_dict = {
        "category": "Hate Speech",
        "sub_category": "Royal",
        "topic": "Royal Heritage",
        "max_news": 5,
    }

    mock_article = {
        "title": "Royal Family Hate Speech",
        "url": "http://example.com",
        "dateTime": "2025-01-15",
        "source": {"title": "Example Source"},
        "body": "Example content of the article.",
    }

    mock_er = mock_event_registry.return_value
    mock_er.QueryArticlesIter.return_value = [mock_article] * 3
    mock_filter_news.return_value = [mock_article] * 3

    # Configure OpenAI mock with the chat completion
    mock_openai.chat.completions.create.return_value = type(
        "ChatCompletion", (), mock_chat_completion
    )

    result = fetch_articles(topic_dict)

    assert len(result) == 3
    assert all(article["title"] == "Royal Family Hate Speech" for article in result)


def test_fetch_articles_with_different_completion(
    mock_env_vars, mock_event_registry, mock_filter_news, mock_save_mongodb, mock_openai
):
    """Test with a different chat completion response"""

    # Mock the response from the expand_topic function
    different_completion = {
        "id": "chatcmpl-mock456",
        "object": "chat.completion",
        "created": 1677858242,
        "model": "gpt-4",
        "usage": {"prompt_tokens": 40, "completion_tokens": 80, "total_tokens": 120},
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": '"Royal family controversies hate speech news surrounding royal families worldwide"',
                },
                "finish_reason": "stop",
                "index": 0,
            }
        ],
    }

    mock_openai.chat.completions.create.return_value = MagicMock(
        choices=different_completion["choices"]
    )

    # Input topic dictionary
    topic_dict = {
        "category": "Hate Speech",
        "sub_category": "Royal",
        "topic": "Royal Heritage",
        "max_news": 5,
        "start_date": "2025-01-01",
        "end_date": "2025-01-15",
    }

    # Mock the EventRegistry response
    mock_article = {
        "title": "Unrelated Royal News",
        "url": "http://example.com",
        "dateTime": "2025-01-15",
        "source": {"title": "Example Source"},
        "body": "Unrelated content.",
    }

    mock_er = mock_event_registry.return_value
    mock_er.QueryArticlesIter.return_value = [mock_article]

    # Mock the filter_news function to return an empty list
    mock_filter_news.return_value = []  # Simulate no articles passing the filter

    # Call the function under test
    result = fetch_articles(topic_dict)

    # Assertions
    assert len(result) == 0  # No articles should be returned


app = FastAPI()

app.include_router(router, prefix="/news")

# FastAPI endpoint tests remain the same
client = TestClient(app)


def test_get_news_endpoint_success(mock_fetch_articles, mock_env_vars):
    """Test successful API endpoint call"""
    params = {
        "category": "Hate Speech",
        "sub_category": "Royal",
        "topic": "Royal Heritage",
        "max_news": 5,
    }

    mock_fetch_articles.return_value = [{"title": "Mock Article"}]

    response = client.get("/news", params=params)

    assert response.status_code == 200
    assert response.json() == [{"title": "Mock Article"}]


def test_get_news_endpoint_error(mock_fetch_articles, mock_env_vars):
    """Test API endpoint error handling"""
    params = {
        "category": "Hate Speech",
        "sub_category": "Royal",
        "topic": "Royal Heritage",
        "max_news": 5,
    }

    mock_fetch_articles.side_effect = Exception("Test error")

    response = client.get("/news", params=params)

    assert response.status_code == 500
    assert "error" in response.json()
