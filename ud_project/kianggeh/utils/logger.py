"""Module contains a logger for the application."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Create logs directory if it doesn't exist
Path("logs").mkdir(parents=True, exist_ok=True)

# Set up logging configuration
logger = logging.getLogger("data-asset-context-api")
logger.setLevel(logging.DEBUG)

# Create formatters and handlers
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# File handler with rotation
log_file = Path("logs") / "app.log"
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=1024 * 1024,  # 1MB
    backupCount=4,  # Keep 4 backup files (4 weeks of logs)
    encoding="utf-8",
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
