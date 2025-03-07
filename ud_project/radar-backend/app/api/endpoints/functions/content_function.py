"""Content Functions."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.models.analysis_output_table import AnalysisOutput
from app.models.category_table import Category
from app.models.comments_output_table import CommentsOutput
from app.models.content_data_asset_table import BAContentDataAsset
from app.models.mapped_cat_sub_table import MappedCatSub
from app.models.profile_data_asset_table import BAProfileDataAsset
from app.models.sub_category_table import SubCategory
from app.models.topic_category_table import TopicCategory
from app.models.topic_keywords_details_table import TopicKeywordsDetails
from app.models.trial_ba_wordcloud_table import TrialBAWordcloud
from app.utils.utils import format_datetime, safe_json_loads

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_all_content_details(db: Session = None) -> dict:
    """Get all content details."""
    contents = db.query(BAContentDataAsset).all()

    content_data = []

    for content in contents:
        content_details = get_content_details(content.video_id, db)
        if content_details:
            content_data.append(content_details)

    return {"data": content_data}


def get_content_details(video_id: str, db: Session = None) -> dict | None:
    """Get content details."""
    try:
        content = (
            db.query(BAContentDataAsset)
            .filter(BAContentDataAsset.video_id == video_id)
            .first()
        )
        mapped_cat_sub = (
            db.query(MappedCatSub).filter(MappedCatSub.video_id == video_id).first()
        )

        if mapped_cat_sub is None:
            return None

        analysis = (
            db.query(AnalysisOutput).filter(AnalysisOutput.video_id == video_id).first()
        )
        comments = (
            db.query(CommentsOutput).filter(CommentsOutput.video_id == video_id).all()
        )
        categories = (
            db.query(Category).filter(Category.id == mapped_cat_sub.category_id).first()
        )
        sub_categories = (
            db.query(SubCategory)
            .filter(SubCategory.id == mapped_cat_sub.sub_category_id)
            .first()
        )
        wordcloud = db.query(TrialBAWordcloud).all()
        profile = (
            db.query(BAProfileDataAsset)
            .filter(BAProfileDataAsset.profile_api_id == content.profile_api_id)
            .first()
        )
        topic = (
            db.query(
                TopicCategory.topic_category_name,
            )
            .join(
                TopicKeywordsDetails,
                TopicCategory.id == TopicKeywordsDetails.topic_category_id,
            )
            .filter(
                TopicKeywordsDetails.video_id == content.video_id,
            )
            .all()
        )
        content_events = []
        if analysis:
            content_events.append(
                {
                    "time": "",
                    "date": format_datetime(analysis.timestamp),
                    "text": "Analysis Completed",
                },
            )
        if comments:
            content_events.extend(
                [
                    {
                        "time": "",
                        "date": format_datetime(comment.comment_posted_timestamp),
                        "text": "Comments Retrieved",
                    }
                    for comment in comments
                ],
            )
        return {
            "social_media_type": "TikTok",
            "content_id": content.video_id,
            "identification_id": f"{content.identification_id}",
            "content_date": format_datetime(content.video_posted_timestamp),
            "report_status": content.status,
            "category": categories.category_name if categories else None,
            "sub_category": sub_categories.sub_category_name
            if sub_categories
            else None,
            "ai_topic": [topic.topic_category_name for topic in topic],
            "likes": content.video_like_count,
            "engagement_score": content.video_engagement_rate,
            "comments_no": content.comment_count,
            "shares": content.video_share_count,
            "risk_level": content.risk_status,
            "content_img": content.video_screenshot_url,
            "user_handle": content.user_handle,
            "content_events": content_events,
            "content_tags": [
                item.keyword
                for item in wordcloud
                if item.keyword in content.video_description
            ],
            "content_url": content.video_path,
            "content_description": content.original_transcription,
            "scrappedDate": format_datetime(content.crawling_timestamp),
            "comment_content": [comment.text for comment in comments]
            if comments
            else None,
            "wordcloud": [
                item.keyword
                for item in wordcloud
                if item.keyword in content.video_description
            ],
            "profile": {
                "user_following_count": profile.user_following_count
                if profile
                else None,
                "user_followers_count": profile.user_followers_count
                if profile
                else None,
                "user_total_videos": profile.user_total_videos if profile else None,
                "creator_photo_link": profile.creator_photo_link if profile else None,
                "profile_engagement_risk": profile.profile_engagement_risk
                if profile
                else None,
                "profile_threat_level": profile.profile_threat_level
                if profile
                else None,
                "profile_engagement_score": profile.profile_engagement_score
                if profile
                else None,
                "profile_rank_engagement": profile.profile_rank_engagement
                if profile
                else None,
                "latest_posted_date": format_datetime(profile.latest_posted_date)
                if profile
                else None,
            },
            "content_justifications": [
                {"justification": i + 1, "justification_text": justification}
                for i, justification in enumerate(
                    safe_json_loads(content.eng_justification),
                )
            ],
            "video_description_hashtags": content.video_hashtags,
            "content_creator": {
                "creator_img": content.creator_photo_link,
                "creator_name": content.user_handle,
                "creator_id": content.user_handle,
                "creator_followings": content.user_following_count,
                "creator_followers": content.user_followers_count,
                "creator_post": content.user_total_videos,
            },
            "content_law_regulated": safe_json_loads(content.content_law_regulated),
            "malay_justification": [
                {"justification": i + 1, "justification_text": justification}
                for i, justification in enumerate(
                    safe_json_loads(content.malay_justification),
                )
            ],
            "original_transcription": content.original_transcription,
            "video_summary": content.video_summary,
            "categories": [categories.category_name] if categories else [],
            "subCategories": [sub_categories.sub_category_name]
            if sub_categories
            else [],
            "topics": content.topic_category,
            "hashtags": [
                {"id": i + 1, "name": tag, "risk_level": "Low"}
                for i, tag in enumerate(safe_json_loads(content.video_hashtags))
            ],
            "similar_keywords": [
                "Ethereum",
                "Tether",
                "Binance Coin",
                "USD Coin",
                "XRP",
            ],
            "other_relevant_categories": [
                "Hate Speech",
                "Scam",
                "Racism",
                "Sexual Harassment",
                "Violence",
            ],
        }
    except (ValueError, TypeError, RuntimeError):  # Catch specific exceptions
        logger.exception(
            "Error processing Video ID %s",
            content.video_id,
        )  # TRY400
        return None
