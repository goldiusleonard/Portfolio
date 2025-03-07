import pytest
from unittest.mock import patch, MagicMock
from src.crawlers.comment import CommentCrawler


@pytest.fixture
def comment_crawler():
    """Fixture to provide a CommentCrawler instance."""
    return CommentCrawler()


@patch("src.crawlers.comment.send_api_request")
def test_fetch_comments_success(mock_send_api_request, comment_crawler):
    """Test _fetch_comments with successful API response."""
    mock_response = {
        "data": {
            "comments": [
                {"id": "123", "text": "Great video!"},
                {"id": "124", "text": "Nice content!"},
            ]
        }
    }
    mock_send_api_request.return_value = mock_response

    url = "https://example.com/comment/list"
    params = {"url": "video_url", "count": "10"}
    result = comment_crawler._fetch_comments(url, params)

    assert result == mock_response["data"]["comments"]
    mock_send_api_request.assert_called_once_with(
        url=url, headers=comment_crawler.headers, params=params
    )


@patch("src.crawlers.comment.send_api_request")
def test_fetch_comments_failure(mock_send_api_request, comment_crawler):
    """Test _fetch_comments with API failure response."""
    mock_response = {"error": "API rate limit exceeded"}
    mock_send_api_request.return_value = mock_response

    url = "https://example.com/comment/list"
    params = {"url": "video_url", "count": "10"}
    result = comment_crawler._fetch_comments(url, params)

    assert result is None
    mock_send_api_request.assert_called_once_with(
        url=url, headers=comment_crawler.headers, params=params
    )


@patch("src.crawlers.comment.MongoDBClient")
def test_save_comments_to_db(mock_mongo_client, comment_crawler):
    """Test _save_comments_to_db stores comments in the database."""
    mock_db = MagicMock()
    mock_mongo_client.return_value.__enter__.return_value = mock_db

    comments = [
        {"id": "123", "text": "Great video!"},
        {"id": "124", "text": "Nice content!"},
    ]
    request_id = 1
    comment_crawler._save_comments_to_db(comments, request_id)

    assert mock_db["comment"].insert_one.call_count == len(comments)
    for comment in comments:
        assert "updated_at" in comment
        assert "created_at" in comment
        assert comment["request_id"] == request_id


@patch.object(CommentCrawler, "_fetch_comments")
@patch.object(CommentCrawler, "_save_comments_to_db")
def test_crawl(mock_save_comments_to_db, mock_fetch_comments, comment_crawler):
    """Test the crawl method integrates _fetch_comments and _save_comments_to_db."""
    mock_comments = [
        {"id": "123", "text": "Great video!"},
        {"id": "124", "text": "Nice content!"},
    ]
    mock_fetch_comments.return_value = mock_comments

    video_id = "test_video"
    username = "test_user"
    count = "10"
    request_id = 1

    comment_crawler.crawl(video_id, username, count, request_id)

    mock_fetch_comments.assert_called_once()
    mock_save_comments_to_db.assert_called_once_with(
        mock_comments, request_id=request_id
    )
