"""DirectLinkAnalysis table model for database."""

from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String

from app.core.dependencies import Base


class DirectLinkAnalysis(Base):
    """DirectLinkAnalysis model class representing the DirectLinkAnalysis table in database."""

    __tablename__ = "DirectLinkAnalysis"
    __table_args__ = ({"schema": "radar_backend_v2"},)
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    URLList = Column(JSON)
    agentName = Column(String(255))  # noqa: N815
    createdTime = Column(DateTime, default=datetime.now(tz=UTC))  # noqa: N815
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
