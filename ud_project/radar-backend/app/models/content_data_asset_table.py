"""Ba content data asset model for database."""

from sqlalchemy import TIMESTAMP, Column, Float, Integer, String, Text, UniqueConstraint

from app.core.dependencies import Base


class BAContentDataAsset(Base):
    """BAContentDataAsset model class.

    Representing the ba_content_data_asset table in database.
    """

    __tablename__ = "ba_content_data_asset"
    __table_args__ = (
        UniqueConstraint("video_id", name="video_id_UNIQUE"),
        {"schema": "mcmc_business_agent"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String(255), nullable=False)
    identification_id = Column(String(255), nullable=False)
    profile_api_id = Column(String(255), nullable=False)
    user_handle = Column(String(255), nullable=False)
    category = Column(String(255), nullable=True)
    sub_category = Column(String(255), nullable=True)
    topic_category = Column(String(255), nullable=True)
    relates_to = Column(String(255), nullable=True)
    purpose = Column(String(255), nullable=True)
    execution_method = Column(String(255), nullable=True)
    target_person = Column(String(255), nullable=True)
    video_language = Column(String(255), nullable=False)
    video_description = Column(Text, nullable=False)
    video_hashtags = Column(String(1000), nullable=False)
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
    original_transcription = Column(Text, nullable=False)
    video_summary = Column(Text, nullable=False)
    eng_justification = Column(Text, nullable=False)
    malay_justification = Column(Text, nullable=False)
    risk_status = Column(String(255), nullable=False)
    content_law_regulated = Column(Text, nullable=False)
    video_url = Column(String(2083), nullable=False)
    video_screenshot_url = Column(String(2083), nullable=False)
    video_path = Column(String(2083), nullable=False)
    user_following_count = Column(Integer, nullable=False)
    user_followers_count = Column(Integer, nullable=False)
    user_total_videos = Column(Integer, nullable=False)
    creator_photo_link = Column(Text, nullable=False)
    status = Column(String(255), nullable=False)
    is_flagged = Column(Integer, nullable=False)
    is_reported = Column(Integer, nullable=False)
    is_resolved = Column(Integer, nullable=False)
    process_time = Column(Float, nullable=False)
    social_media_source = Column(String(255), nullable=False)
    video_source = Column(String(255), nullable=False)
    video_posted_timestamp = Column(TIMESTAMP, nullable=False)
    crawling_timestamp = Column(TIMESTAMP, nullable=False)
    ss_process_timestamp = Column(TIMESTAMP, nullable=False)

    def __repr__(self) -> str:
        """Return a string representation of the object.

        Returns:
            str: A string containing the object's Id.

        """
        return f"{self.Id}"


metadata = Base.metadata
