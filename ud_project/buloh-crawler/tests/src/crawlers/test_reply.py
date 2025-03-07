import pytest
from unittest.mock import patch
from src.crawlers.reply import ReplyCrawler


@pytest.fixture
def reply_crawler():
    """Fixture to provide a ReplyCrawler instance."""
    return ReplyCrawler()


@patch("src.crawlers.reply.send_api_request")
def test_fetch_reply_comments_success(mock_send_api_request, reply_crawler):
    """Test _fetch_reply_comments with successful API response."""
    mock_response = {
        "data": {
            "comments": [
                {"id": "reply_1", "text": "Interesting reply!"},
                {"id": "reply_2", "text": "I agree with this!"},
            ]
        }
    }
    mock_send_api_request.return_value = mock_response

    url = "https://tiktok-scraper7.p.rapidapi.com/comment/reply"
    params = {"video_id": "test_video", "comment_id": "test_comment", "count": "10"}
    result = reply_crawler._fetch_reply_comments(url, params)

    assert result == mock_response["data"]["comments"]
    mock_send_api_request.assert_called_once_with(
        url=url, headers=reply_crawler.headers, params=params
    )


@patch("src.crawlers.reply.send_api_request")
def test_fetch_reply_comments_failure(mock_send_api_request, reply_crawler):
    """Test _fetch_reply_comments with an API failure response."""
    mock_response = {"error": "Invalid request"}
    mock_send_api_request.return_value = mock_response

    url = "https://tiktok-scraper7.p.rapidapi.com/comment/reply"
    params = {"video_id": "test_video", "comment_id": "test_comment", "count": "10"}
    result = reply_crawler._fetch_reply_comments(url, params)

    assert result == []
    mock_send_api_request.assert_called_once_with(
        url=url, headers=reply_crawler.headers, params=params
    )


@patch.object(ReplyCrawler, "_fetch_reply_comments")
def test_crawl_with_replies(mock_fetch_reply_comments, reply_crawler):
    """Test crawl method when replies are fetched successfully."""
    mock_replies = [
        {"id": "reply_1", "text": "Interesting reply!"},
        {"id": "reply_2", "text": "I agree with this!"},
    ]
    mock_fetch_reply_comments.return_value = mock_replies

    video_id = "test_video"
    comment_id = "test_comment"
    count = "5"
    result = reply_crawler.crawl(video_id, comment_id, count)

    assert result == mock_replies
    mock_fetch_reply_comments.assert_called_once_with(
        url="https://tiktok-scraper7.p.rapidapi.com/comment/reply",
        params={"video_id": video_id, "comment_id": comment_id, "count": count},
    )


@patch.object(ReplyCrawler, "_fetch_reply_comments")
def test_crawl_no_replies(mock_fetch_reply_comments, reply_crawler):
    """Test crawl method when no replies are found."""
    mock_fetch_reply_comments.return_value = None

    video_id = "test_video"
    comment_id = "test_comment"
    count = "5"
    result = reply_crawler.crawl(video_id, comment_id, count)

    assert result is None
    mock_fetch_reply_comments.assert_called_once_with(
        url="https://tiktok-scraper7.p.rapidapi.com/comment/reply",
        params={"video_id": video_id, "comment_id": comment_id, "count": count},
    )
