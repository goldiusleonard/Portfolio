"""Pydantic model for live stream update."""

from __future__ import annotations

from datetime import datetime  # noqa: TCH003
from typing import Any

from pydantic import BaseModel


class LiveStreamUpdate(BaseModel):
    """Model for live stream update."""

    stream_id: str
    status: str
    end_time: datetime | None
    blob_urls: dict[str, str] | None
    transcriptions: dict[str, Any] | None
    risk_levels: dict[str, str] | None
