"""Live stream table model."""

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.core.dependencies import Base


class LiveStream(Base):
    """Live stream table model."""

    __tablename__ = "LiveStream"

    Id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    Username = Column(
        String,
        ForeignKey("Watchlist.user_handle"),
        nullable=False,
    )  # TikTok username
    StreamId = Column(String, nullable=False, unique=True)
    Status = Column(String, nullable=False)  # 'active', 'ended'
    StartTime = Column(TIMESTAMP, server_default=func.current_timestamp())
    EndTime = Column(TIMESTAMP, nullable=True)
    FullVideoUrl = Column(String, nullable=True)
    last_chunk_number = Column(Integer, nullable=False, default=0)
    notification_sent = Column(Boolean, default=False, nullable=False)

    stream_chunks = relationship("StreamChunk", backref="live_stream", lazy="selectin")


class StreamChunk(Base):
    """Stream chunk table model."""

    __tablename__ = "StreamChunk"

    Id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    StreamId = Column(String, ForeignKey("LiveStream.StreamId"), nullable=False)
    ChunkNumber = Column(Integer, nullable=False)
    Transcription = Column(JSON, nullable=True)
    Caption = Column(JSON, nullable=True)
    Justification = Column(JSON, nullable=True)
    RiskLevel = Column(String, nullable=True)
    CreatedAt = Column(TIMESTAMP, server_default=func.current_timestamp())
