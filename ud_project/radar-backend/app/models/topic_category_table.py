"""Topic Category table model for database."""

from sqlalchemy import Column, Integer, String

from app.core.dependencies import Base


class TopicCategory(Base):
    """TopicCategory model class representing the TopicCategory table in database."""

    __tablename__ = "topic_category"
    __table_args__ = ({"schema": "mcmc_business_agent"},)
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    topic_category_name = Column(String, nullable=False)

    def __repr__(self) -> str:
        """Return string representation of TopicCategory object.

        Returns
        -------
        str
            String representation showing topic category ID

        """
        return f"{self.id}"


metadata = Base.metadata
