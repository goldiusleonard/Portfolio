"""MapDirectLinkAnalysisPreprocessedUnbiased table model for database."""

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.sql import func

from app.core.dependencies import Base


class MapDirectLinkAnalysisPreprocessedUnbiased(Base):
    """MapDirectLinkAnalysisPreprocessedUnbiased model class.

    Representing the map_agents_preprocessed_unbiased table in database.
    """

    __tablename__ = "MapDirectLinkAnalysisPreprocessedUnbiased"
    __table_args__ = ({"schema": "radar_backend_v2"},)
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    preprocessed_unbiased_id = Column(Integer, nullable=False)
    direct_link_analysis_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
    )
    deleted_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        """Return string representation of MapDirectLinkAnalysisPreprocessedUnbiased object.

        Returns
        -------
        str
            String representation showing map agents preprocessed unbiased ID

        """
        return f"{self.id}"


metadata = Base.metadata
