"""Model for Content Data Asset table."""

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ContentModel(Base):
    """SQLAlchemy Model for Data Asset."""

    __tablename__ = "ba_content_data_asset"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String(255), nullable=False)
    identification_id = Column(String(255), nullable=False)
    profile_api_id = Column(Integer, nullable=False)
    user_handle = Column(String(255), nullable=False)
    category = Column(String(255), nullable=False)
    sub_category = Column(String(255), nullable=False)
    topic_category = Column(String(255), nullable=False)
    relates_to = Column(String(255), nullable=False)
    purpose = Column(String(255), nullable=False)
    execution_method = Column(String(255), nullable=False)
    target_person = Column(String(255), nullable=False)
    video_language = Column(String(255), nullable=False)
    video_description = Column(String(255), nullable=False)
    video_hashtags = Column(String(255), nullable=False)
    video_duration_seconds = Column(Integer, nullable=False)
    video_share_count = Column(Integer, nullable=False)
    video_view_count = Column(Integer, nullable=False)
    video_save_count = Column(Integer, nullable=False)
    video_like_count = Column(Integer, nullable=False)
    comment_count = Column(Integer, nullable=False)
    risk_weight = Column(Float, nullable=False)
    sub_category_weight_score = Column(Float, nullable=False)
    posted_recency_days = Column(Integer, nullable=False)
    recency_score = Column(Float, nullable=False)
    total_video_engagement = Column(Float, nullable=False)
    video_engagement_rate = Column(Float, nullable=False)
    video_engagement_risk = Column(Float, nullable=False)
    original_transcription = Column(String(255), nullable=False)
    video_summary = Column(String(255), nullable=False)
    eng_justification = Column(String(255), nullable=False)
    malay_justification = Column(String(255), nullable=False)
    risk_status = Column(String(255), nullable=False)
    content_law_regulated = Column(String(255), nullable=False)
    video_url = Column(String(255), nullable=False)
    video_screenshot_url = Column(String(255), nullable=False)
    video_path = Column(String(255), nullable=False)
    user_following_count = Column(Integer, nullable=False)
    user_followers_count = Column(Integer, nullable=False)
    user_total_videos = Column(Integer, nullable=False)
    creator_photo_link = Column(String(255), nullable=False)
    status = Column(String(255), nullable=False)
    is_flagged = Column(Integer, nullable=False)
    is_reported = Column(Integer, nullable=False)
    is_resolved = Column(Integer, nullable=False)
    process_time = Column(Float, nullable=False)
    social_media_source = Column(String(255), nullable=False)
    video_source = Column(String(255), nullable=False)
    video_posted_timestamp = Column(DateTime, nullable=False)
    crawling_timestamp = Column(DateTime, nullable=False)
    ss_process_timestamp = Column(DateTime, nullable=False)
