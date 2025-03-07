"""Model for Wordcloud table."""

from sqlalchemy import TIMESTAMP, Column, Integer, String, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class WordCloud(Base):
    """Columns for wordcloud table."""

    __tablename__ = "trial_ba_wordcloud"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    keyword = Column(String, nullable=False)
    count = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    crawling_timestamp = Column(
        TIMESTAMP,
        nullable=False,
        server_default=func.current_timestamp(),
    )
    processed_timestamp = Column(
        TIMESTAMP,
        nullable=False,
        server_default=func.current_timestamp(),
    )

    def __repr__(self) -> str:
        """Return a string representation of the WordCloud object."""
        return f"{self.id}"


metadata = Base.metadata
