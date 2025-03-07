"""Test the get_law_violation_file_by_id function."""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.api.endpoints.functions.content_function import get_content_details
from app.models.analysis_output_table import AnalysisOutput
from app.models.category_table import Category
from app.models.comments_output_table import CommentsOutput
from app.models.content_data_asset_table import BAContentDataAsset
from app.models.mapped_cat_sub_table import MappedCatSub
from app.models.profile_data_asset_table import BAProfileDataAsset
from app.models.sub_category_table import SubCategory
from app.models.topic_category_table import TopicCategory
from app.models.trial_ba_wordcloud_table import TrialBAWordcloud

LIKES = 100
ENGAGEMENT_SCORE = 0.5
SHARES = 5
COMMENT_LIKES = 10

USER_FOLLOWING_COUNT = 100
USER_FOLLOWERS_COUNT = 200
USER_TOTAL_VIDEOS = 50


@pytest.fixture
def mock_db_session() -> Session:
    """Fixture to mock a database session."""
    return MagicMock(spec=Session)


def test_content_details(mock_db_session: Session) -> None:  # noqa: PLR0915
    """Test retrieval of content details successfully."""
    # Mocking the BAContentDataAsset object
    mock_content = MagicMock(spec=BAContentDataAsset)
    mock_content.video_id = "video123"
    mock_content.profile_api_id = "profile123"
    mock_content.video_posted_timestamp = "2024-01-01T00:00:00"
    mock_content.status = "active"
    mock_content.video_like_count = LIKES
    mock_content.video_engagement_rate = ENGAGEMENT_SCORE
    mock_content.comment_count = COMMENT_LIKES
    mock_content.video_share_count = SHARES
    mock_content.risk_status = "low"
    mock_content.video_screenshot_url = "http://example.com/image.png"
    mock_content.user_handle = "user123"
    mock_content.video_path = "http://example.com/video.mp4"
    mock_content.original_transcription = "This is a video description"
    mock_content.crawling_timestamp = "2024-01-01T00:00:00"
    mock_content.video_hashtags = '["hashtag1", "hashtag2"]'
    mock_content.eng_justification = '["justification1", "justification2"]'
    mock_content.malay_justification = '["justifikasi1", "justifikasi2"]'
    mock_content.video_summary = "This is a video summary"
    mock_content.topic_category = "Topic A"

    # Mocking the MappedCatSub object
    mock_mapped_cat_sub = MagicMock(spec=MappedCatSub)
    mock_mapped_cat_sub.category_id = 1
    mock_mapped_cat_sub.sub_category_id = 2

    # Mocking the Category and SubCategory objects
    mock_category = MagicMock(spec=Category)
    mock_category.category_name = "Category A"
    mock_sub_category = MagicMock(spec=SubCategory)
    mock_sub_category.sub_category_name = "SubCategory A"

    # Mocking the AnalysisOutput object
    mock_analysis = MagicMock(spec=AnalysisOutput)
    mock_analysis.timestamp = "2024-01-01T00:00:00"

    # Mocking the CommentsOutput object
    mock_comment = MagicMock(spec=CommentsOutput)
    mock_comment.comment_posted_timestamp = "2024-01-01T00:00:00"
    mock_comment.text = "This is a comment"

    # Mocking the BAProfileDataAsset object
    mock_profile = MagicMock(spec=BAProfileDataAsset)
    mock_profile.user_following_count = USER_FOLLOWING_COUNT
    mock_profile.user_followers_count = USER_FOLLOWERS_COUNT
    mock_profile.user_total_videos = USER_TOTAL_VIDEOS
    mock_profile.creator_photo_link = "http://example.com/profile.png"
    mock_profile.profile_engagement_risk = "low"
    mock_profile.profile_threat_level = "low"
    mock_profile.profile_engagement_score = ENGAGEMENT_SCORE
    mock_profile.profile_rank_engagement = 1
    mock_profile.latest_posted_date = "2024-01-01T00:00:00"

    # Mocking the TrialBAWordcloud object
    mock_wordcloud = MagicMock(spec=TrialBAWordcloud)
    mock_wordcloud.keyword = "keyword1"

    # Mocking the TopicCategory and TopicKeywordsDetails objects
    mock_topic_category = MagicMock(spec=TopicCategory)
    mock_topic_category.topic_category_name = "Topic A"

    # Setting up the mock session to return the mocked objects
    mock_db_session.query.return_value.filter.return_value.first.side_effect = [
        mock_content,
        mock_mapped_cat_sub,
        mock_analysis,
        mock_category,
        mock_sub_category,
        mock_profile,
    ]
    mock_db_session.query.return_value.filter.return_value.all.side_effect = [
        [mock_comment],
        [mock_wordcloud],
        [mock_topic_category],
    ]

    # Calling the function under test
    result = get_content_details("video123", mock_db_session)

    # Assertions to verify the expected output
    assert result["social_media_type"] == "TikTok"  # noqa: S101
    assert result["content_id"] == "video123"  # noqa: S101
    assert result["category"] == "Category A"  # noqa: S101
    assert result["sub_category"] == "SubCategory A"  # noqa: S101
    assert result["likes"] == LIKES  # noqa: S101
    assert result["engagement_score"] == ENGAGEMENT_SCORE  # noqa: S101
    assert result["comments_no"] == COMMENT_LIKES  # noqa: S101
    assert result["shares"] == SHARES  # noqa: S101
    assert result["risk_level"] == "low"  # noqa: S101
    assert result["content_img"] == "http://example.com/image.png"  # noqa: S101
    assert result["user_handle"] == "user123"  # noqa: S101
    assert result["content_url"] == "http://example.com/video.mp4"  # noqa: S101
    assert result["content_description"] == "This is a video description"  # noqa: S101
    assert result["scrappedDate"] == "2024-01-01T00:00:00"  # noqa: S101
    assert result["comment_content"] == ["This is a comment"]  # noqa: S101
    assert result["profile"]["user_following_count"] == USER_FOLLOWING_COUNT  # noqa: S101
    assert result["profile"]["user_followers_count"] == USER_FOLLOWERS_COUNT  # noqa: S101
    assert result["profile"]["user_total_videos"] == USER_TOTAL_VIDEOS  # noqa: S101
    assert result["profile"]["creator_photo_link"] == "http://example.com/profile.png"  # noqa: S101
    assert result["profile"]["profile_engagement_risk"] == "low"  # noqa: S101
    assert result["profile"]["profile_threat_level"] == "low"  # noqa: S101
    assert result["profile"]["profile_engagement_score"] == ENGAGEMENT_SCORE  # noqa: S101
    assert result["profile"]["profile_rank_engagement"] == 1  # noqa: S101
    assert result["profile"]["latest_posted_date"] == "2024-01-01T00:00:00"  # noqa: S101
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
    ]
    assert result["other_relevant_categories"] == [  # noqa: S101
        "Hate Speech",
        "Scam",
        "Racism",
        "Sexual Harassment",
        "Violence",
    ]
