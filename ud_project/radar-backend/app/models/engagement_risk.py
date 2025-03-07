"""Engagement risk models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from datetime import datetime

# Error messages
VIEW_COUNT_ERROR = "View count cannot be zero"
PREDICTED_VIEW_COUNT_ERROR = "Predicted view count cannot be zero"


class ViewCountError(ValueError):
    """Base error for view count validation."""


class ActualViewCountError(ViewCountError):
    """Error raised when actual view count is invalid."""

    def __init__(self) -> None:
        """Initialize with standard message."""
        super().__init__(VIEW_COUNT_ERROR)


class PredictedViewCountError(ViewCountError):
    """Error raised when predicted view count is invalid."""

    def __init__(self) -> None:
        """Initialize with standard message."""
        super().__init__(PREDICTED_VIEW_COUNT_ERROR)


# ----------------- CURRENT ----------------- #
class EngagementCalculationRequest(BaseModel):
    """Request model for calculating current engagement metrics."""

    video_share_count: int = Field(..., ge=0)
    video_save_count: int = Field(..., ge=0)
    comment_count: int = Field(..., ge=0)
    video_like_count: int = Field(..., ge=0)
    video_view_count: int = Field(..., ge=0)

    @field_validator("video_view_count")
    @classmethod
    def validate_view_count(cls, v: int) -> int:
        """Validate that video view count is not zero.

        Args:
            v: View count to validate

        Returns:
            The validated view count

        Raises:
            ActualViewCountError: If view count is zero

        """
        if v == 0:
            raise ActualViewCountError
        return v


class EngagementCalculationResponse(BaseModel):
    """Response model for current engagement calculation."""

    total_engagement: int
    video_engagement: float
    engagement_breakdown: dict[str, float]


class RiskCalculationRequest(BaseModel):
    """Request model for calculating current risk metrics."""

    video_engagement: float = Field(..., ge=0)
    risk_weights_mapping: float = Field(..., gt=0)
    subcat_weights_mapping: float = Field(..., gt=0)
    video_posted_date: datetime


class RiskCalculationResponse(BaseModel):
    """Response model for current risk calculation."""

    video_engagement_risk: float
    recency_score: int
    risk_factors: dict[str, float]


# ----------------- PREDICTION ----------------- #
class EngagementPredictionRequest(BaseModel):
    """Request model for predicting engagement metrics."""

    predicted_video_share_count: int = Field(..., ge=0)
    predicted_video_save_count: int = Field(..., ge=0)
    predicted_comment_count: int = Field(..., ge=0)
    predicted_video_like_count: int = Field(..., ge=0)
    predicted_video_view_count: int = Field(..., ge=0)

    @field_validator("predicted_video_view_count")
    @classmethod
    def validate_predicted_view_count(cls, v: int) -> int:
        """Validate that predicted video view count is not zero.

        Args:
            v: Predicted view count to validate

        Returns:
            The validated predicted view count

        Raises:
            PredictedViewCountError: If predicted view count is zero

        """
        if v == 0:
            raise PredictedViewCountError
        return v


class EngagementPredictionResponse(BaseModel):
    """Response model for engagement prediction."""

    predicted_total_engagement: int
    predicted_engagement_rate: float
    predicted_engagement_breakdown: dict[str, float]


class RiskPredictionRequest(BaseModel):
    """Request model for predicting risk metrics."""

    predicted_video_share_count: int = Field(..., ge=0)
    predicted_video_save_count: int = Field(..., ge=0)
    predicted_comment_count: int = Field(..., ge=0)
    predicted_video_like_count: int = Field(..., ge=0)
    predicted_video_view_count: int = Field(..., ge=0)
    risk_weights_mapping: float = Field(..., gt=0)
    subcat_weights_mapping: float = Field(..., gt=0)
    future_posted_date: datetime


class RiskPredictionResponse(BaseModel):
    """Response model for risk prediction."""

    predicted_video_risk_score: float
    recency_score: int
    risk_factors: dict[str, float]
