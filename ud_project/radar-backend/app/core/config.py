"""Engagement risk config to get weights, etc."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration settings for engagement risk weights."""

    # Database
    VM_USER: str
    VM_PASSWORD: str
    VM_HOST: str
    VM_PORT: str

    # API Endpoints
    TIKTOK_API_BASE_URL: str
    TRANSCRIPTION_API_URL: str
    CAPTION_API_URL: str
    JUSTIFICATION_API_URL: str

    # Polling Interval
    POLLING_INTERVAL: int = 30

    # Others
    FRONTEND_BASE_URL: str

    TIKTOK_API_USER_ID: str = "goldius.leo@userdata.tech"

    # Risk Weights
    RISK_WEIGHT_HIGH: float
    RISK_WEIGHT_MEDIUM: float
    RISK_WEIGHT_LOW: float
    RISK_WEIGHT_IRRELEVANT: float

    # Subcategory Weights with defaults
    SUBCAT_WEIGHT_DEFAULT: float
    SUBCAT_WEIGHT_GOLD: float
    SUBCAT_WEIGHT_CRYPTOCURRENCY: float
    SUBCAT_WEIGHT_FOREX: float
    SUBCAT_WEIGHT_RACE: float
    SUBCAT_WEIGHT_RELIGION: float
    SUBCAT_WEIGHT_ROYALTY: float
    SUBCAT_WEIGHT_HUMAN_TRAFFICKING: float
    SUBCAT_WEIGHT_JOB_SCAM: float
    SUBCAT_WEIGHT_ILLEGAL_IMMIGRANTS: float
    SUBCAT_WEIGHT_SEXUAL_CRIMES: float
    SUBCAT_WEIGHT_VIOLATION_WOMEN: float
    SUBCAT_WEIGHT_VIOLATION_CHILDREN: float

    class Config:
        """Config class."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Create settings instance
settings = get_settings()


# Create risk weights map
def get_risk_weights_map() -> dict[str, float]:
    """Create a mapping of risk levels to their corresponding weights.

    Returns:
        A dictionary mapping risk levels to weights.

    """
    return {
        "High": settings.RISK_WEIGHT_HIGH,
        "Medium": settings.RISK_WEIGHT_MEDIUM,
        "Low": settings.RISK_WEIGHT_LOW,
        "Irrelevant": settings.RISK_WEIGHT_IRRELEVANT,
    }


# Create subcat weights map
def get_subcat_weights_map() -> dict[str, float]:
    """Create a mapping of subcategories to their corresponding weights.

    Returns:
        A dictionary mapping subcategories to weights.

    """
    return {
        "Gold": settings.SUBCAT_WEIGHT_GOLD,
        "Cryptocurrency": settings.SUBCAT_WEIGHT_CRYPTOCURRENCY,
        "Forex": settings.SUBCAT_WEIGHT_FOREX,
        "Race": settings.SUBCAT_WEIGHT_RACE,
        "Religion": settings.SUBCAT_WEIGHT_RELIGION,
        "Royalty": settings.SUBCAT_WEIGHT_ROYALTY,
        "Human Trafficking": settings.SUBCAT_WEIGHT_HUMAN_TRAFFICKING,
        "Job Scam": settings.SUBCAT_WEIGHT_JOB_SCAM,
        "Illegal Immigrants": settings.SUBCAT_WEIGHT_ILLEGAL_IMMIGRANTS,
        "Sexual Crimes (porn)": settings.SUBCAT_WEIGHT_SEXUAL_CRIMES,
        "Violation of women": settings.SUBCAT_WEIGHT_VIOLATION_WOMEN,
        "Violation of Children": settings.SUBCAT_WEIGHT_VIOLATION_CHILDREN,
    }
