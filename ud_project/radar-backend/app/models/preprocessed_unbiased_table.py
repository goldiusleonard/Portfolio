"""Preprocessed Unbiased Table model for database."""

from sqlalchemy import Column, DateTime, Integer, String

from app.core.dependencies import Base


class PreprocessedUnbiased(Base):
    """PreprocessedUnbiased model class representing the PreprocessedUnbiased table in database."""

    __tablename__ = "preprocessed_unbiased_dev"
    __table_args__ = ({"schema": "marketplace_dev"},)
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    video_mongodb_id = Column(String(255))
    video_id = Column(String(255))
    region = Column(String(255))
    title = Column(String(255))
    video_screenshot = Column(String(2048))
    video_duration_seconds = Column(Integer)
    video_path = Column(String(2048))
    video_url = Column(String(2048))
    video_view_count = Column(Integer)
    video_like_count = Column(Integer)
    comment_count = Column(Integer)
    video_share_count = Column(Integer)
    video_download_count = Column(Integer)
    video_posted_timestamp = Column(DateTime)
    request_id = Column(String(255))
    crawling_timestamp = Column(DateTime)
    video_source = Column(String(255))
    video_save_count = Column(Integer)
    profile_id = Column(String(255))
    user_handle = Column(String(255))
    creator_photo_link = Column(String)
    video_hashtags = Column(String(1000))
    user_followers_count = Column(Integer)
    user_following_count = Column(Integer)
    user_total_videos = Column(Integer)
    comments = Column(Integer)
    tiktok = Column(Integer)
    news = Column(Integer)
    value = Column(String)
    video_description = Column(String)
    video_language = Column(String(255))
    transcription = Column(String)
    video_summary = Column(String)

    def __repr__(self) -> str:
        """Return string representation of PreprocessedUnbiased object.

        Returns
        -------
        str
            String representation showing preprocessed unbiased ID

        """
        return f"{self.id}"


metadata = Base.metadata
