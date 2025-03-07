"""Batch router for Engagement Risk."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from app.core.config import get_risk_weights_map, get_subcat_weights_map, settings
from app.core.db_manager import db_manager
from app.db.crud import (
    get_content_by_id,
    update_calculated_engagement,
    update_calculated_risk_score,
)
from app.models.batch_models import (
    BatchContentIdsRequest,
    BatchContentProcessingResponse,
    BatchEngagementCalculationRequest,
    BatchEngagementCalculationResponse,
    BatchEngagementPredictionRequest,
    BatchEngagementPredictionResponse,
    BatchRiskCalculationRequest,
    BatchRiskCalculationResponse,
    BatchRiskPredictionRequest,
    BatchRiskPredictionResponse,
)
from app.models.engagement_risk import (
    EngagementCalculationRequest,
    RiskCalculationRequest,
)
from app.services.batch_service import BatchProcessingService
from app.services.engagement_risk import EngagementRiskService

batch_router = APIRouter(prefix="/batch", tags=["batch-processing"])


@batch_router.post(
    "/calculate-engagement",
    response_model=BatchEngagementCalculationResponse,
    summary="Batch calculate engagement metrics",
    description="Process multiple engagement calculation requests in parallel",
)
async def batch_calculate_engagement(
    batch_request: BatchEngagementCalculationRequest,
) -> BatchEngagementCalculationResponse:
    """Batch calculate engagement metrics.

    Processes a batch of engagement calculation requests.
    """
    try:
        return await BatchProcessingService.process_engagement_batch(batch_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@batch_router.post(
    "/calculate-risk",
    response_model=BatchRiskCalculationResponse,
    summary="Batch calculate risk scores",
    description="Process multiple risk calculation requests in parallel",
)
async def batch_calculate_risk(
    batch_request: BatchRiskCalculationRequest,
) -> BatchRiskCalculationResponse:
    """Batch calculate risk scores."""
    try:
        return await BatchProcessingService.process_risk_batch(batch_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@batch_router.post(
    "/calculate-engagement-prediction",
    response_model=BatchEngagementPredictionResponse,
    summary="Batch calculate engagement predictions",
    description="Process multiple engagement prediction requests in parallel",
)
async def batch_calculate_engagement_prediction(
    batch_request: BatchEngagementPredictionRequest,
) -> BatchEngagementPredictionResponse:
    """Batch calculate engagement predictions.

    Processes a batch of engagement prediction requests.
    """
    try:
        return await BatchProcessingService.process_engagement_prediction_batch(
            batch_request,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@batch_router.post(
    "/calculate-risk-prediction",
    response_model=BatchRiskPredictionResponse,
    summary="Batch calculate risk predictions",
    description="Process multiple risk prediction requests in parallel",
)
async def batch_calculate_risk_prediction(
    batch_request: BatchRiskPredictionRequest,
) -> BatchRiskPredictionResponse:
    """Batch calculate risk predictions.

    Processes a batch of risk prediction requests.
    """
    try:
        return await BatchProcessingService.process_risk_prediction_batch(batch_request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@batch_router.post(
    "/process-db-content",
    response_model=BatchContentProcessingResponse,
    summary="Batch process content IDs from database",
    description="Process multiple content IDs from database, calculating both engagement and risk metrics",
)
async def batch_process_db_content(
    request: BatchContentIdsRequest,
    db: Session = Depends(db_manager.get_db),
) -> BatchContentProcessingResponse:
    """Process multiple content IDs from the database and calculate engagement and risk metrics.

    Returns:
        BatchContentProcessingResponse: Contains successful results and content IDs that failed.

    """
    try:
        successful_results = {}
        failed_content_ids = []

        async def process_single_content(
            content_id: int,
        ) -> tuple[int, dict[str, Any] | None]:
            """Process a single content ID and return its results.

            Returns a tuple of content_id and either a dict containing processing
            results or None if processing failed.
            """
            try:
                record = get_content_by_id(db, content_id)
                if not record:
                    return content_id, None

                # Calculate engagement
                eng_req = EngagementCalculationRequest(
                    video_share_count=record.video_share_count,
                    video_save_count=record.video_save_count,
                    comment_count=record.comment_count,
                    video_like_count=record.video_like_count,
                    video_view_count=record.video_view_count,
                )
                total_eng, eng_rate, eng_breakdown = (
                    EngagementRiskService.calculate_engagement(eng_req)
                )

                # Update engagement in DB
                update_calculated_engagement(db, content_id, eng_rate)

                # Get risk weights from config
                risk_weights = get_risk_weights_map()
                subcat_weights = get_subcat_weights_map()

                risk_weight = risk_weights.get(
                    record.risk_status,
                    settings.RISK_WEIGHT_LOW,
                )
                subcat_weight = subcat_weights.get(
                    record.sub_category,
                    settings.SUBCAT_WEIGHT_DEFAULT,
                )

                # Calculate risk
                risk_req = RiskCalculationRequest(
                    video_engagement=eng_rate,
                    risk_weights_mapping=risk_weight,
                    subcat_weights_mapping=subcat_weight,
                    video_posted_date=record.video_posted_timestamp,
                )
                risk_score, recency_score, risk_factors = (
                    EngagementRiskService.calculate_risk(risk_req)
                )

                # Update risk score in DB
                update_calculated_risk_score(db, content_id, risk_score)

            except ValueError:
                return content_id, None
            else:
                return content_id, {
                    "engagement_metrics": {
                        "total_engagement": total_eng,
                        "engagement_rate": eng_rate,
                        "engagement_breakdown": eng_breakdown,
                    },
                    "risk_metrics": {
                        "risk_score": risk_score,
                        "recency_score": recency_score,
                        "risk_factors": risk_factors,
                    },
                }

        # Process all content IDs in parallel
        tasks = [
            process_single_content(content_id) for content_id in request.content_ids
        ]
        processed_results = await asyncio.gather(*tasks)

        # Organize results
        for content_id, result in processed_results:
            if result is None:
                failed_content_ids.append(content_id)
            else:
                successful_results[content_id] = result

        return BatchContentProcessingResponse(
            successful_results=successful_results,
            failed_content_ids=failed_content_ids,
            total_processed=len(request.content_ids),
            total_success=len(successful_results),
            total_failed=len(failed_content_ids),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
