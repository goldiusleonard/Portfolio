"""Engagament risk service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.core.constants import TIER_RANGES

if TYPE_CHECKING:
    from app.models.engagement_risk import (
        EngagementCalculationRequest,
        EngagementPredictionRequest,
        RiskCalculationRequest,
        RiskPredictionRequest,
    )


class EngagementRiskService:
    """Service for calculating engagement and risk metrics."""

    @staticmethod
    def calculate_engagement(
        request: EngagementCalculationRequest,
    ) -> tuple[int, float, dict[str, float]]:
        """Calculate engagement metrics from request data.

        Args:
            request: The engagement calculation request

        Returns:
            Tuple containing total engagement, engagement rate, and breakdown

        """
        total_engagement = (
            request.video_share_count
            + request.video_save_count
            + request.comment_count
            + request.video_like_count
        )
        video_engagement = (total_engagement / request.video_view_count) * 100

        if total_engagement > 0:
            breakdown = {
                "shares": round(
                    (request.video_share_count / total_engagement) * 100,
                    2,
                ),
                "saves": round((request.video_save_count / total_engagement) * 100, 2),
                "comments": round((request.comment_count / total_engagement) * 100, 2),
                "likes": round((request.video_like_count / total_engagement) * 100, 2),
            }
        else:
            breakdown = {"shares": 0, "saves": 0, "comments": 0, "likes": 0}
        return total_engagement, round(video_engagement, 2), breakdown

    @staticmethod
    def calculate_recency_score(posted_date: datetime) -> int:
        """Calculate recency score based on posted date.

        Args:
            posted_date: The date when content was posted

        Returns:
            Integer recency score

        """
        if posted_date.tzinfo is not None:
            posted_date = posted_date.astimezone(timezone.utc)
        else:
            posted_date = posted_date.replace(tzinfo=timezone.utc)

        current_time = datetime.now(timezone.utc)
        days_diff = (current_time - posted_date).days

        for min_days, max_days, score in TIER_RANGES:
            if min_days <= days_diff <= max_days:
                return score
        return TIER_RANGES[-1][2]  # fallback

    @classmethod
    def calculate_risk(
        cls,
        request: RiskCalculationRequest,
    ) -> tuple[float, int, dict[str, float]]:
        """Calculate risk score from request data.

        Args:
            request: The risk calculation request

        Returns:
            Tuple containing risk score, recency score, and risk factors

        """
        recency_score = cls.calculate_recency_score(request.video_posted_date)
        risk_score = (
            request.video_engagement
            * request.risk_weights_mapping
            * request.subcat_weights_mapping
            * recency_score
        )

        if risk_score == 0:
            factors = {
                "engagement_contribution": 0,
                "risk_weight_contribution": 0,
                "subcat_weight_contribution": 0,
                "recency_contribution": 0,
            }
        else:
            factors = {
                "engagement_contribution": round(
                    (request.video_engagement / risk_score) * 100,
                    2,
                ),
                "risk_weight_contribution": round(
                    (request.risk_weights_mapping / risk_score) * 100,
                    2,
                ),
                "subcat_weight_contribution": round(
                    (request.subcat_weights_mapping / risk_score) * 100,
                    2,
                ),
                "recency_contribution": round((recency_score / risk_score) * 100, 2),
            }
        return round(risk_score, 2), recency_score, factors

    # ===================== PREDICTION VERSIONS (SAME FORMULA) ===================== #
    @staticmethod
    def calculate_engagement_prediction(
        request: EngagementPredictionRequest,
    ) -> tuple[int, float, dict[str, float]]:
        """EXACT SAME FORMULA as 'calculate_engagement', but using predicted fields."""
        total_engagement = (
            request.predicted_video_share_count
            + request.predicted_video_save_count
            + request.predicted_comment_count
            + request.predicted_video_like_count
        )
        video_engagement = (total_engagement / request.predicted_video_view_count) * 100

        if total_engagement > 0:
            breakdown = {
                "predicted_shares": round(
                    (request.predicted_video_share_count / total_engagement) * 100,
                    2,
                ),
                "predicted_saves": round(
                    (request.predicted_video_save_count / total_engagement) * 100,
                    2,
                ),
                "predicted_comments": round(
                    (request.predicted_comment_count / total_engagement) * 100,
                    2,
                ),
                "predicted_likes": round(
                    (request.predicted_video_like_count / total_engagement) * 100,
                    2,
                ),
            }
        else:
            breakdown = {
                "predicted_shares": 0,
                "predicted_saves": 0,
                "predicted_comments": 0,
                "predicted_likes": 0,
            }

        return total_engagement, round(video_engagement, 2), breakdown

    @classmethod
    def calculate_risk_prediction(
        cls,
        request: RiskPredictionRequest,
    ) -> tuple[float, int, dict[str, float]]:
        """Calculate risk prediction using predicted fields.

        The only difference is we might call the date 'future_posted_date'
        instead of 'video_posted_date'.

        Args:
            request: The risk prediction request containing predicted metrics

        Returns:
            Tuple containing predicted risk score, recency score, and risk factors

        """
        recency_score = cls.calculate_recency_score(request.future_posted_date)

        predicted_total_eng = (
            request.predicted_video_share_count
            + request.predicted_video_save_count
            + request.predicted_comment_count
            + request.predicted_video_like_count
        )

        if request.predicted_video_view_count == 0:
            error_msg = "Predicted video_view_count cannot be zero"
            raise ValueError(error_msg)

        predicted_eng_rate = (
            predicted_total_eng / request.predicted_video_view_count
        ) * 100

        risk_score = (
            predicted_eng_rate
            * request.risk_weights_mapping
            * request.subcat_weights_mapping
            * recency_score
        )
        if risk_score == 0:
            factors = {
                "predicted_engagement_contribution": 0,
                "risk_weight_contribution": 0,
                "subcat_weight_contribution": 0,
                "recency_contribution": 0,
            }
        else:
            factors = {
                "predicted_engagement_contribution": round(
                    (predicted_eng_rate / risk_score) * 100,
                    2,
                ),
                "risk_weight_contribution": round(
                    (request.risk_weights_mapping / risk_score) * 100,
                    2,
                ),
                "subcat_weight_contribution": round(
                    (request.subcat_weights_mapping / risk_score) * 100,
                    2,
                ),
                "recency_contribution": round((recency_score / risk_score) * 100, 2),
            }

        return round(risk_score, 2), recency_score, factors
