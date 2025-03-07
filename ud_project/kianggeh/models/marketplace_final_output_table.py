"""Model for Marketplace table."""

from sqlalchemy import TIMESTAMP, Column, Float, Integer, String, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class MarketplaceFinalOutput(Base):
    """Model for marketplace table.

    Args:
        Base: Declarativee base.

    Returns:
        Column names and values.

    Raises:
        None.

    """

    __tablename__ = "final_output"
    _id = Column(String, primary_key=True, autoincrement=False, index=True)
    ai_dynamic_cover = Column(String, nullable=True)
    anchors = Column(String, nullable=True)
    anchors_extras = Column(String, nullable=True)
    api_sentiment = Column(String, nullable=True)
    api_sentiment_score = Column(Float, nullable=True)
    author = Column(String, nullable=True)
    aweme_id = Column(String, nullable=True)
    category = Column(String, nullable=True)
    collect_count = Column(Integer, nullable=True)
    comment_count = Column(Integer, nullable=True)
    comments = Column(String, nullable=True)
    commerce_info = Column(String, nullable=True)
    commercial_video_info = Column(String, nullable=True)
    cover = Column(String, nullable=True)
    create_time = Column(Integer, nullable=True)
    created_at = Column(
        TIMESTAMP,
        nullable=True,
        server_default=func.current_timestamp(),
    )
    digg_count = Column(Integer, nullable=True)
    download_count = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)
    eng_justification = Column(String, nullable=True)
    images = Column(String, nullable=True)
    is_ad = Column(Integer, nullable=True)
    is_flagged = Column(Integer, nullable=True)
    is_top = Column(Integer, nullable=True)
    item_comment_settings = Column(Integer, nullable=True)
    law_regulated = Column(String, nullable=True)
    malay_justification = Column(String, nullable=True)
    music = Column(String, nullable=True)
    music_info = Column(String, nullable=True)
    origin_cover = Column(String, nullable=True)
    perspective = Column(String, nullable=True)
    platform = Column(String, nullable=True)
    play = Column(String, nullable=True)
    play_count = Column(Integer, nullable=True)
    process_sec = Column("process_time(sec)", Float, nullable=True)
    region = Column(String, nullable=True)
    request_id = Column(Integer, nullable=True)
    risk_status = Column(String, nullable=True)
    sentiment = Column(String, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    share_count = Column(Integer, nullable=True)
    size = Column(Integer, nullable=True)
    subcategories = Column(String, nullable=True)
    timestamp = Column(String, nullable=True)
    title = Column(String, nullable=True)
    transcription = Column(String, nullable=True)
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        server_default=func.current_timestamp(),
    )
    video_description = Column(String, nullable=True)
    video_id = Column(Integer, nullable=True)
    video_language = Column(String, nullable=True)
    video_source = Column(String, nullable=True)
    video_summary = Column(String, nullable=True)
    wm_size = Column(Integer, nullable=True)
    wmplay = Column(String, nullable=True)

    def __repr__(self) -> str:
        """Dynamically get all column names and their values.

        Args:
            self: self.

        Returns:
            Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]: A tuple containing
            the database credentials: user, password, host, and port. If an environment variable
            is not set, its corresponding value in the tuple will be None.

        Raises:
            None.

        """
        attrs = [
            f"{column.name}={getattr(self, column.name, 'N/A')}"
            for column in self.__table__.columns
        ]
        return f"<{self.__class__.__name__}({', '.join(attrs)})>"


metadata = Base.metadata
