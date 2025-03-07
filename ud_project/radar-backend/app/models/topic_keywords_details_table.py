"""Topic Keywords Details table model for database."""

from sqlalchemy import TIMESTAMP, Column, Integer, String

from app.core.dependencies import Base


class TopicKeywordsDetails(Base):
    """TopicKeywordsDetails model class representing the TopicKeywordsDetails table in database."""

    __tablename__ = "topic_keywords_details"
    __table_args__ = ({"schema": "mcmc_business_agent"},)
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
        nullable=False,
    )
    topic_category_id = Column(Integer, nullable=False)
    video_id = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    sub_category = Column(String(100), nullable=True)
    topic_summary = Column(String(255), nullable=True)
    relates_to = Column(String(255), nullable=True)
    purpose = Column(String(255), nullable=True)
    execution_method = Column(String(255), nullable=True)
    target_person = Column(String(255), nullable=True)
    topic_updated_time = Column(TIMESTAMP, nullable=True)
    category_id = Column(Integer, nullable=True)
    sub_category_id = Column(Integer, nullable=True)
    preprocessed_unbiased_id = Column(Integer, nullable=True)

    def __repr__(self) -> str:
        """Return string representation of TopicKeywordsDetails object.

        Returns
        -------
        str
            String representation showing topic keywords details ID

        """
        return f"{self.id}"


metadata = Base.metadata
