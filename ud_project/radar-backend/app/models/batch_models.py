"""Batch models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from app.models.engagement_risk import (
    EngagementCalculationRequest,
    EngagementCalculationResponse,
    EngagementPredictionRequest,
    EngagementPredictionResponse,
    RiskCalculationRequest,
    RiskCalculationResponse,
    RiskPredictionRequest,
    RiskPredictionResponse,
)

if TYPE_CHECKING:
    from app.models.engagement_risk import (
        EngagementCalculationRequest,
        EngagementCalculationResponse,
        EngagementPredictionRequest,
        EngagementPredictionResponse,
        RiskCalculationRequest,
        RiskCalculationResponse,
        RiskPredictionRequest,
        RiskPredictionResponse,
    )


class BatchEngagementCalculationRequest(BaseModel):
    """Request model for batch engagement calculations."""

    requests: list[EngagementCalculationRequest] = Field(
        ...,
        min_length=1,
        description="List of engagement calculation requests",
    )


class BatchEngagementCalculationResponse(BaseModel):
    """Response model for batch engagement calculations."""

    results: list[EngagementCalculationResponse]
    failed_indices: list[int] = []
    total_processed: int
    total_success: int
    total_failed: int


class BatchRiskCalculationRequest(BaseModel):
    """Request model for batch risk calculations."""

    requests: list[RiskCalculationRequest] = Field(
        ...,
        min_length=1,
        description="List of risk calculation requests",
    )


class BatchRiskCalculationResponse(BaseModel):
    """Response model for batch risk calculations."""

    results: list[RiskCalculationResponse]
    failed_indices: list[int] = []
    total_processed: int
    total_success: int
    total_failed: int


class BatchEngagementPredictionRequest(BaseModel):
    """Request model for batch engagement predictions."""

    requests: list[EngagementPredictionRequest] = Field(
        ...,
        min_length=1,
        description="List of engagement prediction requests",
    )


class BatchEngagementPredictionResponse(BaseModel):
    """Response model for batch engagement predictions."""

    results: list[EngagementPredictionResponse]
    failed_indices: list[int] = []
    total_processed: int
    total_success: int
    total_failed: int


class BatchRiskPredictionRequest(BaseModel):
    """Request model for batch risk predictions."""

    requests: list[RiskPredictionRequest] = Field(
        ...,
        min_length=1,
        description="List of risk prediction requests",
    )


class BatchRiskPredictionResponse(BaseModel):
    """Response model for batch risk predictions."""

    results: list[RiskPredictionResponse]
    failed_indices: list[int] = []
    total_processed: int
    total_success: int
    total_failed: int


class BatchContentIdsRequest(BaseModel):
    """Request model for batch content ID processing."""

    content_ids: list[int] = Field(
        ...,
        min_length=1,
        description="List of content IDs to process",
    )


class BatchContentProcessingResponse(BaseModel):
    """Response model for batch content processing."""

    successful_results: dict[int, dict[str, dict]]
    failed_content_ids: list[int]
    total_processed: int
    total_success: int
    total_failed: int
