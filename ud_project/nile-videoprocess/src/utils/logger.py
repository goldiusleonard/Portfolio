import os
import re
import logging
from logging.handlers import TimedRotatingFileHandler


class Logger:
    def __init__(
        self,
        name: str,
        log_dir: str = "logs/",
        level: int = logging.DEBUG,
        backup_count: int = 7,
    ):
        """
        Initialize the Logger instance.

        :param name: Name of the logger (e.g., 'my_module').
        :param log_dir: Directory where log files will be stored.
        :param level: Logging level (default is logging.DEBUG).
        :param backup_count: Number of backup files to keep. Default is 5.
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Create a formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Create console handler and set level
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        if log_dir:
            # Ensure the log directory exists
            os.makedirs(log_dir, exist_ok=True)

            # Create a timed rotating file handler for daily rotation
            file_handler = TimedRotatingFileHandler(
                filename=os.path.join(log_dir, "app.log"),
                when="midnight",  # Rotate logs at midnight
                interval=1,  # Interval of 1 day
                backupCount=backup_count,  # Number of backup files to keep
                encoding="utf-8",  # Ensure proper encoding
            )
            file_handler.setFormatter(formatter)
            file_handler.suffix = "%Y-%m-%d"  # Add date suffix to filenames
            file_handler.extMatch = re.compile(r"\d{4}-\d{2}-\d{2}")
            self.logger.addHandler(file_handler)

    def debug(self, msg: str, *args, **kwargs):
        """Log a message with level DEBUG."""
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        """Log a message with level INFO."""
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """Log a message with level WARNING."""
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """Log a message with level ERROR."""
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        """Log a message with level CRITICAL."""
        self.logger.critical(msg, *args, **kwargs)


def configure_logging(log_filename="video_descriptionDB.log"):
    # Configure logging to log to both console and file
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Example usage
if __name__ == "__main__":
    # Create a logger instance with a file output
    log = Logger(name="MyLogger")

    log.debug("This is a debug message.")
    log.info("This is an info message.")
    log.warning("This is a warning message.")
    log.error("This is an error message.")
    log.critical("This is a critical message.")
