"""Test comment function."""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.api.endpoints.functions.comment_function import get_comment_details
from app.models.category_table import Category
from app.models.comments_output_table import CommentsOutput
from app.models.content_data_asset_table import BAContentDataAsset
from app.models.mapped_cat_sub_table import MappedCatSub
from app.models.sub_category_table import SubCategory
from app.models.topic_category_table import TopicCategory

LIKES = 100
ENGAGEMENT_SCORE = 0.5
SHARES = 5
COMMENT_LIKES = 10


@pytest.fixture
def mock_db_session() -> Session:
    """Fixture to mock a database session."""
    return MagicMock(spec=Session)


def test_comment_details(mock_db_session: Session) -> None:  # noqa: PLR0915
    """Test retrieval of comment details successfully."""
    # Mocking the BAContentDataAsset object
    mock_content = MagicMock(spec=BAContentDataAsset)
    mock_content.video_id = "video123"
    mock_content.video_posted_timestamp = "2024-01-01T00:00:00"
    mock_content.status = "active"
    mock_content.video_like_count = LIKES
    mock_content.video_engagement_rate = ENGAGEMENT_SCORE
    mock_content.video_share_count = SHARES
    mock_content.risk_status = "low"
    mock_content.video_screenshot_url = "http://example.com/image.png"
    mock_content.user_handle = "user123"
    mock_content.video_path = "http://example.com/video.mp4"
    mock_content.original_transcription = "This is a video description"
    mock_content.crawling_timestamp = "2024-01-01T00:00:00"
    mock_content.eng_justification = '["justification1", "justification2"]'
    mock_content.malay_justification = '["justifikasi1", "justifikasi2"]'
    mock_content.video_summary = "This is a video summary"
    mock_content.topic_category = "Topic A"
    mock_content.video_hashtags = '["hashtag1", "hashtag2"]'
    mock_content.creator_photo_link = "http://example.com/profile.png"
    mock_content.user_following_count = 100
    mock_content.user_followers_count = 200
    mock_content.user_total_videos = 50
    mock_content.content_law_regulated = "{}"

    # Mocking the MappedCatSub object
    mock_mapped_cat_sub = MagicMock(spec=MappedCatSub)
    mock_mapped_cat_sub.category_id = 1
    mock_mapped_cat_sub.sub_category_id = 2

    # Mocking the Category and SubCategory objects
    mock_category = MagicMock(spec=Category)
    mock_category.category_name = "Category A"
    mock_sub_category = MagicMock(spec=SubCategory)
    mock_sub_category.sub_category_name = "SubCategory A"

    # Mocking the CommentsOutput object
    mock_comment = MagicMock(spec=CommentsOutput)
    mock_comment.video_comment_id = "comment123"
    mock_comment.text = "This is a comment"
    mock_comment.user_handle = "user456"
    mock_comment.comment_posted_timestamp = "2024-01-01T00:00:00"
    mock_comment.comment_like_count = COMMENT_LIKES

    # Mocking the TopicCategory and TopicKeywordsDetails objects
    mock_topic_category = MagicMock(spec=TopicCategory)
    mock_topic_category.topic_category_name = "Topic A"

    # Setting up the mock session to return the mocked objects
    mock_db_session.query.return_value.filter.return_value.first.side_effect = [
        mock_content,
        mock_mapped_cat_sub,
        mock_category,
        mock_sub_category,
    ]
    mock_db_session.query.return_value.filter.return_value.all.side_effect = [
        [mock_comment],
        [mock_topic_category],
    ]

    # Calling the function under test
    result = get_comment_details("video123", mock_db_session)

    # Assertions to verify the expected output
    assert result["social_media_type"] == "TikTok"  # noqa: S101
    assert result["content_id"] == "video123"  # noqa: S101
    assert result["identification_id"] == "TKHSLvideo123"  # noqa: S101
    assert result["content_date"] == "2024-01-01T00:00:00"  # noqa: S101
    assert result["report_status"] == "active"  # noqa: S101
    assert result["sub_category"] == "SubCategory A"  # noqa: S101
    assert result["likes"] == LIKES  # noqa: S101
    assert result["engagement_score"] == ENGAGEMENT_SCORE  # noqa: S101
    assert result["comments_no"] == 1  # noqa: S101
    assert result["shares"] == SHARES  # noqa: S101
    assert result["risk_level"] == "low"  # noqa: S101
    assert result["content_img"] == "http://example.com/image.png"  # noqa: S101
    assert result["user_handle"] == "user123"  # noqa: S101
    assert result["content_url"] == "http://example.com/video.mp4"  # noqa: S101
    assert result["content_description"] == "This is a video description"  # noqa: S101
    assert result["scrappedDate"] == "2024-01-01T00:00:00"  # noqa: S101
    assert result["comment_content"] == [  # noqa: S101
        {
            "comment_id": "comment123",
            "text": "This is a comment",
            "author": "user456",
            "timestamp": "2024-01-01T00:00:00",
            "likes": COMMENT_LIKES,
        },
    ]
    assert result["content_justifications"] == [  # noqa: S101
        {"justification": 1, "justification_text": "justification1"},
        {"justification": 2, "justification_text": "justification2"},
    ]
    assert result["malay_justification"] == [  # noqa: S101
        {"justification": 1, "justification_text": "justifikasi1"},
        {"justification": 2, "justification_text": "justifikasi2"},
    ]
    assert result["video_summary"] == "This is a video summary"  # noqa: S101
    assert result["categories"] == ["Category A"]  # noqa: S101
    assert result["subCategories"] == ["SubCategory A"]  # noqa: S101
    assert result["topics"] == "Topic A"  # noqa: S101
    assert result["hashtags"] == [  # noqa: S101
        {"id": 1, "name": "hashtag1", "risk_level": "Low"},
        {"id": 2, "name": "hashtag2", "risk_level": "Low"},
    ]
    assert result["similar_keywords"] == [  # noqa: S101
        "Ethereum",
        "Tether",
        "Binance Coin",
        "USD Coin",
        "XRP",
        "Cardano",
        "Dogecoin",
        "Solana",
        "Polkadot",
    ]
    assert result["other_relevant_categories"] == [  # noqa: S101
        "Hate Speech",
        "Scam",
        "Racism",
        "Sexual Harassment",
        "Violence",
    ]
