"""Pydantic schema for Engagement Score."""

from pydantic import BaseModel


class TotalEngagement(BaseModel):
    """Schema for calculating total engagement."""

    share_count: int
    saved_count: int
    comment_count: int
    like_count: int


class EngagementScore(BaseModel):
    """Schema for calculating engagement score."""

    share_count: int
    saved_count: int
    comment_count: int
    like_count: int
    video_count: int
