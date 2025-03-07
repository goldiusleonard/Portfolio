"""Pydantic schema for Agent."""

from __future__ import annotations

from pydantic import BaseModel


class DirectLinkAnalysisRequest(BaseModel):
    """Schema for requesting direct link analysis."""

    urls: list[str]
