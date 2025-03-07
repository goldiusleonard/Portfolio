"""Engagement risk routers."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import get_risk_weights_map, get_subcat_weights_map, settings
from app.core.db_manager import db_manager
from app.db.crud import (
    get_content_by_id,
    update_calculated_engagement,
    update_calculated_risk_score,
)
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
from app.services.engagement_risk import EngagementRiskService

engagement_risk_router = APIRouter(tags=["engagement-risk"])


# ---------------------------------------------------------------------
# 1) CALCULATE ENGAGEMENT (CURRENT) - POST
# ---------------------------------------------------------------------
@engagement_risk_router.post(
    "/calculate-engagement",
    response_model=EngagementCalculationResponse,
    summary="Calculate *current* engagement",
)
async def calculate_engagement(
    request: EngagementCalculationRequest,
) -> EngagementCalculationResponse:
    """Calculate *current* engagement metrics based on actual share/save/comment/like counts."""
    try:
        total_eng, eng_rate, breakdown = EngagementRiskService.calculate_engagement(
            request,
        )
        return EngagementCalculationResponse(
            total_engagement=total_eng,
            video_engagement=eng_rate,
            engagement_breakdown=breakdown,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# ---------------------------------------------------------------------
# 2) CALCULATE RISK (CURRENT) - POST
# ---------------------------------------------------------------------
@engagement_risk_router.post(
    "/calculate-risk",
    response_model=RiskCalculationResponse,
    summary="Calculate *current* risk",
)
async def calculate_risk(request: RiskCalculationRequest) -> RiskCalculationResponse:
    """Calculate the *current* risk score using actual engagement rate.

    Includes risk weights, subcat weights, and posted date for recency.
    """
    try:
        risk_score, recency_score, factors = EngagementRiskService.calculate_risk(
            request,
        )
        return RiskCalculationResponse(
            video_engagement_risk=risk_score,
            recency_score=recency_score,
            risk_factors=factors,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# ---------------------------------------------------------------------
# 3) CALCULATE ENGAGEMENT PREDICTION - POST
# ---------------------------------------------------------------------
@engagement_risk_router.post(
    "/calculate-engagement-prediction",
    response_model=EngagementPredictionResponse,
    summary="Calculate *predicted* engagement",
)
async def calculate_engagement_prediction(
    request: EngagementPredictionRequest,
) -> JSONResponse:
    """Calculate engagement using the *same* formula, but with predicted share/save/comment/like counts."""
    try:
        total_pred, pred_rate, breakdown = (
            EngagementRiskService.calculate_engagement_prediction(request)
        )
        result = {
            "predicted_total_engagement": total_pred,
            "predicted_engagement_rate": pred_rate,
            "predicted_engagement_breakdown": breakdown,
        }
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# ---------------------------------------------------------------------
# 4) CALCULATE RISK PREDICTION - POST
# ---------------------------------------------------------------------
@engagement_risk_router.post(
    "/calculate-risk-prediction",
    response_model=RiskPredictionResponse,
    summary="Calculate *predicted* risk",
)
async def calculate_risk_prediction(request: RiskPredictionRequest) -> JSONResponse:
    """Calculate a *predicted* risk score using a future scenario or predicted engagement data."""
    try:
        risk_score, recency_score, factors = (
            EngagementRiskService.calculate_risk_prediction(request)
        )
        result = {
            "predicted_video_risk_score": risk_score,
            "recency_score": recency_score,
            "risk_factors": factors,
        }
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# ---------------------------------------------------------------------
# 5) CALCULATE ENGAGEMENT FROM DB (CURRENT) - GET
# ---------------------------------------------------------------------
@engagement_risk_router.get(
    "/calculate-engagement-from-db/{content_id}",
    response_model=EngagementCalculationResponse,
    summary="Fetch DB data, then calculate *current* engagement",
)
async def calculate_engagement_from_db(
    content_id: int,
    db: Session = Depends(db_manager.get_db),
) -> JSONResponse:
    """Fetch record from DB and calculate engagement metrics.

    1. Fetch record from DB by content_id.
    2. Build EngagementCalculationRequest from actual fields.
    3. Call `calculate_engagement`.
    4. (Optional) Store the engagement rate in DB if you want.
    """
    record = get_content_by_id(db, content_id)
    if not record:
        raise HTTPException(status_code=404, detail="Content not found.")
    try:
        req_model = EngagementCalculationRequest(
            video_share_count=0,  # if DB doesn't store shares
            video_save_count=record.video_save_count,
            comment_count=record.comment_count,
            video_like_count=record.video_like_count,
            video_view_count=record.video_view_count,
        )
        total_eng, eng_rate, breakdown = EngagementRiskService.calculate_engagement(
            req_model,
        )

        update_calculated_engagement(db, content_id, eng_rate)

        result = {
            "total_engagement": total_eng,
            "video_engagement": eng_rate,
            "engagement_breakdown": breakdown,
        }
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# ---------------------------------------------------------------------
# 6) CALCULATE RISK FROM DB (CURRENT) - GET
# ---------------------------------------------------------------------
@engagement_risk_router.get(
    "/calculate-risk-from-db/{content_id}",
    response_model=RiskCalculationResponse,
    summary="Fetch DB data, then calculate *current* risk",
)
async def calculate_risk_from_db(
    content_id: int,
    db: Session = Depends(db_manager.get_db),
) -> JSONResponse:
    """Fetch record from DB and calculate risk metrics.

    1. Fetch record from DB by content_id.
    2. Compute actual engagement if needed.
    3. Use constants for risk weight & subcat weight.
    4. Call `calculate_risk`.
    5. (Optional) Store the risk score in DB.
    """
    record = get_content_by_id(db, content_id)
    if not record:
        raise HTTPException(status_code=404, detail="Content not found.")
    try:
        eng_req = EngagementCalculationRequest(
            video_share_count=record.video_share_count,
            video_save_count=record.video_save_count,
            comment_count=record.comment_count,
            video_like_count=record.video_like_count,
            video_view_count=record.video_view_count,
        )
        _, eng_rate, _ = EngagementRiskService.calculate_engagement(eng_req)

        risk_weights = get_risk_weights_map()
        subcat_weights = get_subcat_weights_map()

        risk_weight = risk_weights.get(record.risk_status, settings.RISK_WEIGHT_LOW)
        subcat_weight = subcat_weights.get(
            record.sub_category,
            settings.SUBCAT_WEIGHT_DEFAULT,
        )

        risk_req = RiskCalculationRequest(
            video_engagement=eng_rate,
            risk_weights_mapping=risk_weight,
            subcat_weights_mapping=subcat_weight,
            video_posted_date=record.video_posted_timestamp,
        )

        risk_score, recency_score, factors = EngagementRiskService.calculate_risk(
            risk_req,
        )

        update_calculated_risk_score(db, content_id, risk_score)
        result = {
            "video_engagement_risk": risk_score,
            "recency_score": recency_score,
            "risk_factors": factors,
        }
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
