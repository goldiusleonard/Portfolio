"""Trial BA Wordcloud table model for database."""

from sqlalchemy import Column, DateTime, Integer, String

from app.core.dependencies import Base


class TrialBAWordcloud(Base):
    """TrialBAWordcloud model class representing the trial_ba_wordcloud table in database."""

    __tablename__ = "trial_ba_wordcloud"
    __table_args__ = ({"schema": "mcmc_business_agent"},)
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
        nullable=False,
    )
    keyword = Column(String(255), nullable=True)
    count = Column(Integer, nullable=True)
    category = Column(String(255), nullable=True)
    crawling_timestamp = Column(DateTime, nullable=True)
    processed_timestamp = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        """Return a string representation of the object.

        The string representation is the object's Id attribute.

        Returns:
            str: The string representation of the object.

        """
        return f"{self.id}"


metadata = Base.metadata
