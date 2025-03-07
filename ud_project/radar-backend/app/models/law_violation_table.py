"""Law violation asset model for database."""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from app.core.dependencies import Base


class LawViolation(Base):
    """Represents a law violation record in the database."""

    __tablename__ = "law_violation"
    __table_args__ = ({"schema": "radar_backend_v2"},)

    id = Column(Integer, primary_key=True, autoincrement=True)
    file = Column(String(255))
    name = Column(String(255))
    category = Column(String(255))
    effective_date = Column(DateTime)
    upload_date = Column(DateTime, default=func.now())
    publisher = Column(String(255))
    summary = Column(String(255))
    is_publish = Column(Boolean)

    def __repr__(self) -> str:
        """Return a string representation of the LawViolation instance."""
        return f"{self.id}"


metadata = Base.metadata
