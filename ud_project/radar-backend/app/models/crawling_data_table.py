"""Crawling Data table model for database."""

from sqlalchemy import Column, DateTime, Integer, String

from app.core.dependencies import Base


class CrawlingData(Base):
    """CrawlingData model class representing the crawling_data table in database."""

    __tablename__ = "crawling_data"
    __table_args__ = ({"schema": "marketplace"},)
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    request_id = Column(Integer, nullable=False)
    agent_id = Column(Integer, nullable=False)
    category = Column(String(255), nullable=False)
    subcategory = Column(String(255), nullable=False)
    agent_name = Column(String(255), nullable=False)
    request_by = Column(String(255), nullable=False)
    description = Column(String(255), nullable=False)
    created_time = Column(DateTime, nullable=False)

    def __repr__(self) -> str:
        """Return string representation of CrawlingData object.

        Returns
        -------
        str
            String representation showing crawling data ID

        """
        return f"{self.id}"


metadata = Base.metadata
