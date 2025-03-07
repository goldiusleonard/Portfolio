"""Mapped Category Sub Table model for database."""

from sqlalchemy import Column, Integer, String

from app.core.dependencies import Base


class MappedCatSub(Base):
    """MappedCatSub model class representing the mapped_cat_sub table in database."""

    __tablename__ = "mapped_cat_sub"
    __table_args__ = ({"schema": "marketplace_dev"},)
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    category_id = Column(Integer)
    sub_category_id = Column(Integer)
    video_id = Column(String)
    preprocessed_unbiased_id = Column(Integer)
    analysis_id = Column(Integer)

    def __repr__(self) -> str:
        """Return string representation of MappedCatSub object.

        Returns
        -------
        str
            String representation showing mapped cat sub ID

        """
        return f"{self.id}"


metadata = Base.metadata
