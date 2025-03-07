"""Engagement risk table."""

from sqlalchemy import TIMESTAMP, Column, Integer, String

from app.core.dependencies import Base


class BaContentDataAsset(Base):
    """Database model for storing engagement and risk data assets.

    Represents video and user-related engagement metrics, including likes,
    views, shares, comments, and user metadata.
    """

    __tablename__ = "ba_content_data_asset"

    id = Column(Integer, primary_key=True, index=True)

    user_handle = Column(String(255), nullable=True)
    video_posted_timestamp = Column(TIMESTAMP, nullable=True)

    # Renamed fields
    video_share_count = Column(Integer, default=0)
    video_like_count = Column(Integer, default=0)  # was total_likes
    video_view_count = Column(Integer, default=0)  # was total_views
    comment_count = Column(Integer, default=0)  # was total_comments
    video_save_count = Column(Integer, default=0)  # was total_saved

    user_following_count = Column(Integer, default=0)
    user_total_videos = Column(Integer, default=0)
    video_source = Column(String(255), nullable=True)
    risk_status = Column(String(255), nullable=True)
    category = Column(String(255), nullable=True)
    sub_category = Column(String(255), nullable=True)

    # Renamed from topic -> topic_category
    topic_category = Column(String(255), nullable=True)
