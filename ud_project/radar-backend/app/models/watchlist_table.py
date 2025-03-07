"""Watchlist table model."""

from sqlalchemy import TIMESTAMP, Boolean, Column, Integer, String, func

from app.core.dependencies import Base


class Watchlist(Base):
    """Watchlist table model."""

    __tablename__ = "Watchlist"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_handle = Column(String, nullable=False)  # Account being monitored
    is_live = Column(Boolean, default=False)  # Tracks if the user is currently live
    last_updated = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
    is_comment_recording = Column(Boolean, default=False)
    ba_process_timestamp = Column(TIMESTAMP, server_default=func.current_timestamp())
    creator_photo_link = Column(String, nullable=True)
    user_following_count = Column(Integer, nullable=True)
    user_followers_count = Column(Integer, nullable=True)
    user_total_videos = Column(Integer, nullable=True)
