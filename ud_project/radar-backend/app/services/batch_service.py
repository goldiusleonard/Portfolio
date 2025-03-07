"""Batch service for processing multiple requests."""

from __future__ import annotations

import asyncio

from app.core.config import get_risk_weights_map, get_subcat_weights_map, settings
from app.models.batch_models import (
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
    EngagementCalculationRequest,  # noqa: TCH001
    RiskCalculationRequest,  # noqa: TCH001
)
from app.services.engagement_risk import EngagementRiskService


class BatchProcessingError(Exception):
    """Custom exception for batch processing errors."""


class BatchProcessingService:
    """Service for handling batch processing operations."""

    @staticmethod
    def get_weights_for_record(
        risk_status: str,
        sub_category: str,
    ) -> tuple[float, float]:
        """Get risk and subcategory weights from configuration.

        Args:
            risk_status: Risk status of the content
            sub_category: Subcategory of the content

        Returns:
            Tuple containing risk weight and subcategory weight

        """
        risk_weights = get_risk_weights_map()
        subcat_weights = get_subcat_weights_map()

        risk_weight = risk_weights.get(risk_status, settings.RISK_WEIGHT_LOW)
        subcat_weight = subcat_weights.get(sub_category, settings.SUBCAT_WEIGHT_DEFAULT)

        return risk_weight, subcat_weight

    @staticmethod
    async def process_engagement_batch(
        batch_request: BatchEngagementCalculationRequest,
    ) -> BatchEngagementCalculationResponse:
        """Process multiple engagement calculation requests in parallel.

        Args:
            batch_request: Batch of engagement calculation requests

        Returns:
            Response containing processed results and statistics

        """
        results = []
        failed_indices = []

        async def process_single(
            index: int,
            request: EngagementCalculationRequest,
        ) -> tuple[int, dict | None]:
            try:
                total_eng, eng_rate, breakdown = (
                    EngagementRiskService.calculate_engagement(request)
                )
            except BatchProcessingError:
                return index, None
            else:
                return index, {
                    "total_engagement": total_eng,
                    "video_engagement": eng_rate,
                    "engagement_breakdown": breakdown,
                }

        tasks = [
            process_single(idx, request)
            for idx, request in enumerate(batch_request.requests)
        ]

        processed_results = await asyncio.gather(*tasks)

        results = [None] * len(batch_request.requests)
        for index, result in processed_results:
            if result is None:
                failed_indices.append(index)
            else:
                results[index] = result

        # Remove None values
        results = [r for r in results if r is not None]

        return BatchEngagementCalculationResponse(
            results=results,
            failed_indices=failed_indices,
            total_processed=len(batch_request.requests),
            total_success=len(results),
            total_failed=len(failed_indices),
        )

    @staticmethod
    async def process_risk_batch(
        batch_request: BatchRiskCalculationRequest,
    ) -> BatchRiskCalculationResponse:
        """Process multiple risk calculation requests in parallel.

        Args:
            batch_request: Batch of risk calculation requests

        Returns:
            Response containing processed results and statistics

        """
        results = []
        failed_indices = []

        async def process_single(
            index: int,
            request: RiskCalculationRequest,
        ) -> tuple[int, dict | None]:
            try:
                risk_score, recency_score, factors = (
                    EngagementRiskService.calculate_risk(request)
                )
            except BatchProcessingError:
                return index, None
            else:
                return index, {
                    "video_engagement_risk": risk_score,
                    "recency_score": recency_score,
                    "risk_factors": factors,
                }

        tasks = [
            process_single(idx, request)
            for idx, request in enumerate(batch_request.requests)
        ]

        processed_results = await asyncio.gather(*tasks)

        results = [None] * len(batch_request.requests)
        for index, result in processed_results:
            if result is None:
                failed_indices.append(index)
            else:
                results[index] = result

        results = [r for r in results if r is not None]

        return BatchRiskCalculationResponse(
            results=results,
            failed_indices=failed_indices,
            total_processed=len(batch_request.requests),
            total_success=len(results),
            total_failed=len(failed_indices),
        )

    @staticmethod
    async def process_engagement_prediction_batch(
        batch_request: BatchEngagementPredictionRequest,
    ) -> BatchEngagementPredictionResponse:
        """Process multiple engagement prediction requests in parallel.

        Args:
            batch_request: Batch of requests containing predicted metrics

        Returns:
            BatchEngagementPredictionResponse with results and processing statistics

        """
        results = []
        failed_indices = []

        async def process_single(
            index: int,
            request: dict,
        ) -> tuple[int, dict[str, dict] | None]:
            try:
                total_pred, pred_rate, breakdown = (
                    EngagementRiskService.calculate_engagement_prediction(
                        request,
                    )
                )
            except BatchProcessingError:
                return index, None
            else:
                return index, {
                    "predicted_total_engagement": total_pred,
                    "predicted_engagement_rate": pred_rate,
                    "predicted_engagement_breakdown": breakdown,
                }

        tasks = [
            process_single(idx, request)
            for idx, request in enumerate(batch_request.requests)
        ]
        processed_results = await asyncio.gather(*tasks)

        results = [None] * len(batch_request.requests)

        for index, result in processed_results:
            if result is None:
                failed_indices.append(index)
            else:
                results[index] = result

        results = [r for r in results if r is not None]

        return BatchEngagementPredictionResponse(
            results=results,
            failed_indices=failed_indices,
            total_processed=len(batch_request.requests),
            total_success=len(results),
            total_failed=len(failed_indices),
        )

    @staticmethod
    async def process_risk_prediction_batch(
        batch_request: BatchRiskPredictionRequest,
    ) -> BatchRiskPredictionResponse:
        """Process multiple risk prediction requests in parallel.

        Args:
            batch_request: Batch of requests containing predicted metrics

        Returns:
            BatchRiskPredictionResponse with results and processing statistics

        """
        results = []
        failed_indices = []

        async def process_single(
            index: int,
            request: dict,
        ) -> tuple[int, dict[str, dict] | None]:
            try:
                risk_score, recency_score, factors = (
                    EngagementRiskService.calculate_risk_prediction(
                        request,
                    )
                )
            except BatchProcessingError:
                return index, None
            else:
                return index, {
                    "predicted_video_risk_score": risk_score,
                    "recency_score": recency_score,
                    "risk_factors": factors,
                }

        tasks = [
            process_single(idx, request)
            for idx, request in enumerate(batch_request.requests)
        ]
        processed_results = await asyncio.gather(*tasks)

        results = [None] * len(batch_request.requests)

        for index, result in processed_results:
            if result is None:
                failed_indices.append(index)
            else:
                results[index] = result

        results = [r for r in results if r is not None]

        return BatchRiskPredictionResponse(
            results=results,
            failed_indices=failed_indices,
            total_processed=len(batch_request.requests),
            total_success=len(results),
            total_failed=len(failed_indices),
        )
