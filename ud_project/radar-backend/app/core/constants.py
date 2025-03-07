"""Engagement risk contants."""

from __future__ import annotations

import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

##################
# Recency Tiers
##################
TIER_RANGES: list[tuple[int, int, int]] = [
    (0, 7, 25),
    (8, 14, 20),
    (15, 28, 15),
    (29, 42, 12),
    (43, 56, 10),
    (57, 70, 8),
    (71, 84, 6),
    (85, float("inf"), 4),
]

##################
# Risk Weights
##################
RISK_WEIGHTS_MAP = {
    "High": float(os.getenv("RISK_WEIGHT_HIGH", "0.5")),
    "Medium": float(os.getenv("RISK_WEIGHT_MEDIUM", "0.3")),
    "Low": float(os.getenv("RISK_WEIGHT_LOW", "0.1")),
    "Irrelevant": float(os.getenv("RISK_WEIGHT_IRRELEVANT", "0.1")),
}

##################
# Subcat Weights
##################
SUBCAT_WEIGHTS_MAP = {
    "Gold": float(os.getenv("SUBCAT_WEIGHT_GOLD", "0.33")),
    "Cryptocurrency": float(
        os.getenv("SUBCAT_WEIGHT_CRYPTOCURRENCY", "0.33"),
    ),
    "Forex": float(os.getenv("SUBCAT_WEIGHT_FOREX", "0.33")),
    "Race": float(os.getenv("SUBCAT_WEIGHT_RACE", "0.33")),
    "Religion": float(os.getenv("SUBCAT_WEIGHT_RELIGION", "0.33")),
    "Royalty": float(os.getenv("SUBCAT_WEIGHT_ROYALTY", "0.33")),
    "Human Trafficking": float(
        os.getenv("SUBCAT_WEIGHT_HUMAN_TRAFFICKING", "0.33"),
    ),
    "Job Scam": float(os.getenv("SUBCAT_WEIGHT_JOB_SCAM", "0.33")),
    "Illegal Immigrants": float(
        os.getenv("SUBCAT_WEIGHT_ILLEGAL_IMMIGRANTS", "0.33"),
    ),
    "Sexual Crimes (porn)": float(
        os.getenv("SUBCAT_WEIGHT_SEXUAL_CRIMES", "0.33"),
    ),
    "Violation of women": float(
        os.getenv("SUBCAT_WEIGHT_VIOLATION_WOMEN", "0.33"),
    ),
    "Violation of Children": float(
        os.getenv("SUBCAT_WEIGHT_VIOLATION_CHILDREN", "0.33"),
    ),
}

# Default subcat weight from env or fallback
DEFAULT_SUBCAT_WEIGHT = float(
    os.getenv("SUBCAT_WEIGHT_DEFAULT", "0.33"),
)

SUCCESS_CODE = 200
UNAUTHORIZED_STATUS_CODE = 401
BAD_REQUEST_STATUS_CODE = 400
DEFAULT_CATEGORY_PREDICTION_DATA_URL = "http://ac06db80b0e1b4114b082eae94199205-845785752.ap-southeast-1.elb.amazonaws.com:8000/predictions/engagement-risk"
DEFAULT_CATEGORY_CURRENT_DATA_URL = "http://af3164eb711524ba5afd1b47b63ebdd3-1243418058.ap-southeast-1.elb.amazonaws.com:8080/filter_and_calculate_daily_totals"
DEFAULT_CRAWLER_URL_FOR_AI_AGENT = "http://89.169.97.52:8099/crawler"
DEFAULT_CRAWLER_URL_FOR_DIRECT_LINK = "http://89.169.97.52:8098/crawler"
DEFAULT_GROUP_BY_CATEGORY_URL = "http://af3164eb711524ba5afd1b47b63ebdd3-1243418058.ap-southeast-1.elb.amazonaws.com:8080/group_by_category"
DEFAULT_KEYWORD_TRENDS_URL = "http://a397e48680fea4f5ca23a0fb2d10a348-336664731.ap-southeast-1.elb.amazonaws.com:8009"
DEFAULT_NUM_OF_DAYS_KEYWORD_SEARCH = -180

DEFAULT_SIMILARITY_AGENT_URL = "http://ad34ed07797334e8ba6314ab2e747ff8-1026112678.ap-southeast-1.elb.amazonaws.com:8001"
DEFAULT_CROSS_CATEGORY_INSIGHT_URL = "http://af3164eb711524ba5afd1b47b63ebdd3-1243418058.ap-southeast-1.elb.amazonaws.com:8080"
DEFAULT_EXTRACTION_LAW_PDF_URL = "http://a155f7502d7f2406087d86f8aefcac97-500080031.ap-southeast-1.elb.amazonaws.com:8077"
DEFAULT_ENGAGEMENT_COUNT_URL = "http://a67e02a6c8e6b4b3898befefb32d4549-107744915.ap-southeast-1.elb.amazonaws.com:8001"
