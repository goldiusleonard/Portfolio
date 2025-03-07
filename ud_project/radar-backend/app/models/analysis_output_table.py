"""Analysis Output table model for database."""

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.core.dependencies import Base


class AnalysisOutput(Base):
    """AnalysisOutput model class representing the analysis_output table in database."""

    __tablename__ = "analysis_output"
    __table_args__ = ({"schema": "marketplace_dev"},)
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
        nullable=False,
    )
    category_id = Column(Integer, nullable=True)
    sub_category_id = Column(Integer, nullable=True)
    video_id = Column(String(255), nullable=True)
    preprocessed_unbiased_id = Column(Integer, nullable=True)
    sentiment = Column(String(255), nullable=True)
    sentiment_score = Column(Float, nullable=True)
    api_sentiment_score = Column(Float, nullable=True)
    eng_justification = Column(Text, nullable=True)
    malay_justification = Column(Text, nullable=True)
    risk_status = Column(String(255), nullable=True)
    irrelevant_score = Column(String(255), nullable=True)
    law_regulated = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=True)
    process_time = Column(Float, nullable=True)

    def __repr__(self) -> str:
        """Return a string representation of the object.

        The string representation is the object's Id attribute.

        Returns:
            str: The string representation of the object.

        """
        return f"{self.Id}"


metadata = Base.metadata
