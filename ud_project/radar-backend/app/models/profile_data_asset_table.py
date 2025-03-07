"""Profile data asset model for database."""

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Column,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)

from app.core.dependencies import Base


class BAProfileDataAsset(Base):
    """BAProfileDataAsset model for storing profile data assets."""

    __tablename__ = "ba_profile_data_asset"
    __table_args__ = (
        UniqueConstraint("user_handle", name="user_handle_UNIQUE"),
        {"schema": "mcmc_business_agent"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_api_id = Column(BigInteger, nullable=True)
    user_handle = Column(String(255), nullable=True)
    user_following_count = Column(Integer, nullable=True)
    user_followers_count = Column(Integer, nullable=True)
    user_total_videos = Column(Integer, nullable=True)
    creator_photo_link = Column(Text, nullable=True)
    profile_engagement_risk = Column(Numeric(54, 5), nullable=True)
    profile_threat_level = Column(Numeric(58, 9), nullable=True)
    profile_engagement_score = Column(Numeric(45, 4), nullable=True)
    profile_rank_engagement = Column(BigInteger, nullable=True, default=0)
    latest_posted_date = Column(TIMESTAMP, nullable=True)
    ba_process_timestamp = Column(DateTime, nullable=False)

    def __repr__(self) -> str:
        """Return a string representation of the ProfileDataAssetTable instance.

        The string representation is the ID of the instance

        Returns:
            str: The ID of the ProfileDataAssetTable instance as a string.

        """
        return f"{self.id}"
