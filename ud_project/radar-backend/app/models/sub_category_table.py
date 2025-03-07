"""SubCategory table model for database."""

from sqlalchemy import Column, Integer, Numeric, String

from app.core.dependencies import Base


class SubCategory(Base):
    """SubCategory model class representing the sub_category table in database."""

    __tablename__ = "sub_category"
    __table_args__ = ({"schema": "marketplace_dev"},)
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    sub_category_name = Column(String(50), nullable=False)
    category_id = Column(Integer, nullable=False)
    sub_category_weight = Column(Numeric(10, 4), nullable=True)

    def __repr__(self) -> str:
        """Return string representation of SubCategory object.

        Returns
        -------
        str
            String representation showing sub category ID

        """
        return f"{self.id}"


metadata = Base.metadata
