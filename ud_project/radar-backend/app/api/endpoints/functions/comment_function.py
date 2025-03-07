"""Content Functions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.models.category_table import Category
from app.models.comments_output_table import CommentsOutput
from app.models.content_data_asset_table import BAContentDataAsset
from app.models.mapped_cat_sub_table import MappedCatSub
from app.models.sub_category_table import SubCategory
from app.models.topic_category_table import TopicCategory
from app.models.topic_keywords_details_table import TopicKeywordsDetails
from app.utils.utils import format_datetime, safe_json_loads

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_all_comment_details(db: Session = None) -> dict:
    """Get all comment details."""
    contents = db.query(BAContentDataAsset).all()
    return {"data": [get_comment_details(content.video_id, db) for content in contents]}


def get_comment_details(video_id: str, db: Session = None) -> dict:
    """Get comment details."""
    content = (
        db.query(BAContentDataAsset)
        .filter(BAContentDataAsset.video_id == video_id)
        .first()
    )
    mapped_cat_sub = (
        db.query(MappedCatSub).filter(MappedCatSub.video_id == video_id).first()
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

    comments = [
        {
            "comment_id": comment.video_comment_id,
            "text": comment.text,
            "author": comment.user_handle,
            "timestamp": format_datetime(comment.comment_posted_timestamp),
            "likes": comment.comment_like_count,
        }
        for comment in comments
    ]
    return {
        "social_media_type": "TikTok",
        "content_id": content.video_id,
        "identification_id": f"TKHSL{content.video_id}",
        "content_date": format_datetime(content.video_posted_timestamp),
        "report_status": content.status,
        "sub_category": sub_categories.sub_category_name if sub_categories else None,
        "ai_topic": [topic.topic_category_name for topic in topic],
        "likes": content.video_like_count,
        "engagement_score": content.video_engagement_rate,
        "comments_no": len(comments),
        "shares": content.video_share_count,
        "risk_level": content.risk_status,
        "content_img": content.video_screenshot_url,
        "user_handle": content.user_handle,
        "content_events": [
            {"time": "09:54:21", "date": "2024-09-09", "text": "Content Scanned"},
            {"time": "", "date": "", "text": ""},
        ],
        "content_tags": [None],
        "content_url": content.video_path,
        "content_description": content.original_transcription,
        "scrappedDate": format_datetime(content.crawling_timestamp),
        "comment_content": comments,
        "content_justifications": [
            {
                "justification": i + 1,
                "justification_text": justification,
            }
            for i, justification in enumerate(
                safe_json_loads(content.eng_justification or "[]"),
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
        "content_law_regulated": safe_json_loads(content.content_law_regulated or "{}"),
        "malay_justification": [
            {
                "justification": i + 1,
                "justification_text": justification,
            }
            for i, justification in enumerate(
                safe_json_loads(content.malay_justification or "[]"),
            )
        ],
        "original_transcription": content.original_transcription,
        "video_summary": content.video_summary,
        "categories": [categories.category_name] if categories else [],
        "subCategories": [sub_categories.sub_category_name] if sub_categories else [],
        "topics": content.topic_category,
        "hashtags": [
            {
                "id": i + 1,
                "name": tag,
                "risk_level": "Low",
            }
            for i, tag in enumerate(safe_json_loads(content.video_hashtags or "[]"))
        ],
        "similar_keywords": [
            "Ethereum",
            "Tether",
            "Binance Coin",
            "USD Coin",
            "XRP",
            "Cardano",
            "Dogecoin",
            "Solana",
            "Polkadot",
        ],
        "other_relevant_categories": [
            "Hate Speech",
            "Scam",
            "Racism",
            "Sexual Harassment",
            "Violence",
        ],
    }
