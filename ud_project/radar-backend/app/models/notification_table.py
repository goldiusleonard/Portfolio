"""Notification table model."""

from sqlalchemy import TIMESTAMP, Boolean, Column, Integer, String, func

from app.core.dependencies import Base


class Notification(Base):
    """Notification table model."""

    __tablename__ = "Notification"

    Id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    UserId = Column(String, nullable=False)
    IsNew = Column(Boolean, default=True)
    ImageUrl = Column(String, nullable=True)
    Name = Column(String, nullable=False)
    Status = Column(String, nullable=False)  # 'live' or 'ended'
    DateTime = Column(TIMESTAMP, server_default=func.current_timestamp())
    LiveDetail = Column(String, nullable=False)
    StreamId = Column(String, nullable=False)
