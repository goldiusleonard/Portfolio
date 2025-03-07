import logging
import os

from datetime import datetime
from logging.handlers import RotatingFileHandler


# Shared logging configuration for all modules
def setup_logging(logger_name: str):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # Remove existing handlers
    logger.handlers = []

    # Configure rotating file handler
    os.makedirs("logs", exist_ok=True)
    log_file = f'logs/{logger_name}_{datetime.now().strftime("%Y%m%d")}.log'
    file_handler = RotatingFileHandler(
        log_file, maxBytes=1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)

    # Set up formatters
    file_format = logging.Formatter(
        fmt="%(asctime)s,%(msecs)03d | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    return logger


# Shared environment variable validation for all modules
def validate_env_variables(required_vars: list) -> bool:
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print("\n❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   • {var}")
        return False
    return True


def get_service_timeout(service_name: str, default: int = 30) -> int:
    """Get service timeout from environment with default"""
    return int(os.getenv(f"{service_name}_TIMEOUT", default))


# Add to validate_env_variables
def validate_embedding_config() -> bool:
    """Validate embedding service configuration"""
    required_vars = ["EMBEDDING_MODEL_URL", "EMBEDDING_MODEL_NAME", "EMBEDDING_TIMEOUT"]
    return validate_env_variables(required_vars)
