import logging
import numpy as np
import pandas as pd
import traceback
from fastapi.responses import JSONResponse
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional
from ..prediction import EngagementAndRiskPrediction
from ..utils import fetch_data_asset_table, load_and_verify_env_var, get_mysql_engine

router = APIRouter()

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

DATA_ASSET_TABLE: str = load_and_verify_env_var(
    "DATA_ASSET_TABLE", var_type=str, required=True
)
NUM_OF_DAYS_TRAIN_DATA: int = int(
    load_and_verify_env_var("NUM_OF_DAYS_TRAIN_DATA", var_type=str, required=True)
)


@router.get("/engagement-risk")
def predict_engagement_and_risk_trend(
    user_handle: Optional[str] = Query(None, description="Optional user handle."),
    category: Optional[str] = Query(None, description="Filter by category."),
    sub_category: Optional[str] = Query(None, description="Filter by sub-category."),
    topic: Optional[str] = Query(None, description="Filter by AI topic."),
    start_date: str = Query(..., description="Start date in 'YYYY-MM-DD'."),
    end_date: str = Query(..., description="End date in 'YYYY-MM-DD'."),
):
    try:
        # Log incoming request
        logging.info(
            f"Received request: user_handle={user_handle}, "
            f"category={category}, sub_category={sub_category}, topic={topic}, "
            f"start_date={start_date}, end_date={end_date}"
        )

        # Ensure one of the valid combinations of category, sub_category, and topic
        if not (
            (category and not sub_category and not topic)
            or (category and sub_category and not topic)
            or (category and sub_category and topic)
        ):
            raise HTTPException(
                status_code=400,
                detail="You must provide 'category' only, or 'category' and 'sub_category', or 'category', 'sub_category', and 'topic'.",
            )

        # Normalize inputs
        category = category.lower() if category else None
        sub_category = sub_category.lower() if sub_category else None
        topic = topic.lower() if topic else None

        # Validate date format
        try:
            start_date_parsed = datetime.strptime(start_date, "%Y-%m-%d")
            end_date_parsed = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format.")

        # Ensure start_date is before or equal to end_date
        if start_date_parsed > end_date_parsed:
            raise HTTPException(
                status_code=400,
                detail="Start date must be before or equal to end date.",
            )

        # Fetch the filtered dataset from the database
        engine = get_mysql_engine()
        filtered_video_df = fetch_data_asset_table(
            engine,
            DATA_ASSET_TABLE,
            NUM_OF_DAYS_TRAIN_DATA,
            category,
            sub_category,
            topic,
            user_handle,
        )

        # Check for essential column existence
        if "video_posted_timestamp" not in filtered_video_df.columns:
            raise HTTPException(
                status_code=400,
                detail="'video_posted_timestamp' column is missing from the dataset.",
            )

        if filtered_video_df.empty:
            raise HTTPException(
                status_code=404,
                detail="No data found.",
            )

        # Generate predictions
        predictor = EngagementAndRiskPrediction(filtered_video_df, start_date, end_date)

        # Get the prediction results
        result = predictor.predict()

        # Handle NaN and infinite values
        for record in result:
            if isinstance(record["Date"], str):
                record["Date"] = pd.to_datetime(record["Date"])
            record["Date"] = record["Date"].strftime("%Y-%m-%d")

            # Handle NaN and Infinite values in the record
            for key, value in record.items():
                if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
                    record[key] = None

    except HTTPException as e:
        print(traceback.format_exc())
        logging.error(f"HTTP error: {e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content={"status": "error", "detail": e.detail},
        )
    except Exception as e:
        print(traceback.format_exc())
        logging.error(f"Unexpected error: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": "Internal server error."},
        )

    headers = {
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Origin": "*",
    }

    return JSONResponse(
        content={"status": "success", "data": result},
        status_code=200,
        headers=headers,
    )
