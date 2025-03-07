"""Agent table model for database."""

from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String

from app.core.dependencies import Base


class Agent(Base):
    """Agent model class representing the Agent table in database."""

    __tablename__ = "Agents"
    __table_args__ = ({"schema": "radar_backend_v2"},)
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    agentName = Column(String(255))  # noqa: N815
    createdBy = Column(String(255))  # noqa: N815
    createdTime = Column(DateTime, default=datetime.now(tz=UTC))  # noqa: N815
    description = Column(String)
    category = Column(String(255))
    subcategory = Column(String(255))
    crawlingStartDate = Column(DateTime)  # noqa: N815
    crawlingEndDate = Column(DateTime)  # noqa: N815
    legalDocuments = Column(JSON)  # noqa: N815
    URLList = Column(JSON)
    SocialMediaList = Column(JSON)
    isPublished = Column(Boolean)  # noqa: N815
    isUsernameCrawler = Column(Boolean)  # noqa: N815
    isKeywordCrawler = Column(Boolean)  # noqa: N815
    usernameList = Column(JSON)  # noqa: N815
    keywordList = Column(JSON)  # noqa: N815
    status = Column(String(255))

    def __repr__(self) -> str:
        """Return string representation of Agent object.

        Returns
        -------
        str
            String representation showing agent ID

        """
        return f"{self.id}"


metadata = Base.metadata
