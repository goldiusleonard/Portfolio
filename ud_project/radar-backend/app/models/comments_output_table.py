"""Comments Output table model for database."""

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.core.dependencies import Base


class CommentsOutput(Base):
    """CommentsOutput model class representing the comments_output table in database."""

    __tablename__ = "comments_output"
    __table_args__ = ({"schema": "marketplace_dev"},)
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
        nullable=False,
    )
    comment_mongodb_id = Column(String(50), nullable=True)
    video_comment_id = Column(String(50), nullable=True)
    video_id = Column(String(255), nullable=True)
    text = Column(Text, nullable=True)
    comment_posted_timestamp = Column(DateTime, nullable=True)
    comment_like_count = Column(Integer, nullable=True)
    crawling_timestamp = Column(DateTime, nullable=True)
    request_id = Column(String(50), nullable=True)
    user_handle = Column(String(50), nullable=True)
    video_summary = Column(Text, nullable=True)
    category = Column(String(255), nullable=True)
    subcategory = Column(String(255), nullable=True)
    eng_justification = Column(Text, nullable=True)
    malay_justification = Column(Text, nullable=True)
    risk_status = Column(String(50), nullable=True)
    irrelevant_score = Column(String(50), nullable=True)
    timestamp = Column(DateTime, nullable=True)
    process_time = Column(Float, nullable=True)

    def __repr__(self) -> str:
        """Return a string representation of the object.

        The string representation is the object's Id attribute.

        Returns:
            str: The string representation of the object.

        """
        return f"{self.id}"


metadata = Base.metadata
