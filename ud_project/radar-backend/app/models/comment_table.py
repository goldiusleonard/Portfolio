"""Comment table model."""

from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, String, Text, func

from app.core.dependencies import Base


class CommentRecord(Base):
    """Model for comment record."""

    __tablename__ = "CommentRecord"

    Id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    Username = Column(String, nullable=False)  # TikTok username
    StreamId = Column(String, ForeignKey("LiveStream.StreamId"), nullable=False)
    Comment = Column(Text, nullable=False)
    Timestamp = Column(
        TIMESTAMP,
        nullable=False,
        server_default=func.current_timestamp(),
    )
