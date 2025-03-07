"""Tags table model for database."""

from sqlalchemy import Column, Integer, String

from app.core.dependencies import Base


class Tags(Base):
    """Tags model class representing the tags table in database."""

    __tablename__ = "tags"
    __table_args__ = ({"schema": "marketplace"},)
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    request_id = Column(Integer, nullable=False)
    type = Column(String(255), nullable=False)
    value = Column(String(255), nullable=False)

    def __repr__(self) -> str:
        """Return string representation of Tags object.

        Returns
        -------
        str
            String representation showing tags ID

        """
        return f"{self.id}"


metadata = Base.metadata
