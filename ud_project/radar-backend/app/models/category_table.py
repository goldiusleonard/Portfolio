"""Category table model for database."""

from sqlalchemy import Column, Integer, String

from app.core.dependencies import Base


class Category(Base):
    """Category model class representing the category table in database."""

    __tablename__ = "category"
    __table_args__ = ({"schema": "marketplace_dev"},)
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    category_name = Column(String(50), nullable=False)

    def __repr__(self) -> str:
        """Return a string representation of the object."""
        return f"{self.Id}"


metadata = Base.metadata
