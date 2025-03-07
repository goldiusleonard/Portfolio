"""Logger module for handling application logging."""

from __future__ import annotations

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


class Logger:
    """Logger class that handles both console and file logging with rotation."""

    def __init__(
        self,
        name: str,
        log_dir: str = "logs/",
        level: int = logging.INFO,
        backup_count: int = 5,
    ) -> None:
        """Initialize the Logger instance.

        Parameters
        ----------
        name : str
            Name of the logger (e.g., 'my_module')
        log_dir : str, optional
            Directory to store log files, by default "logs/"
        level : int, optional
            Logging level, by default logging.DEBUG
        backup_count : int, optional
            Number of backup files to keep, by default 5

        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Create a formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        # Create console handler and set level
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        if log_dir:
            # Ensure the log directory exists
            Path(log_dir).mkdir(parents=True, exist_ok=True)

            # Create a timed rotating file handler
            file_handler = TimedRotatingFileHandler(
                filename=Path(log_dir) / "app.log",
                when="D",  # Rotate logs every day
                interval=7,  # Interval of 7 days
                backupCount=backup_count,  # Number of backup files to keep
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def debug(self, msg: str, *args: float, **kwargs: float) -> None:
        """Log a message with level DEBUG.

        Parameters
        ----------
        msg : str
            The message to log
        *args : float
            Variable length argument list
        **kwargs : float
            Arbitrary keyword arguments

        """
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args: float, **kwargs: float) -> None:
        """Log a message with level INFO.

        Parameters
        ----------
        msg : str
            The message to log
        *args : float
            Variable length argument list
        **kwargs : float
            Arbitrary keyword arguments

        """
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args: float, **kwargs: float) -> None:
        """Log a message with level WARNING.

        Parameters
        ----------
        msg : str
            The message to log
        *args : float
            Variable length argument list
        **kwargs : float
            Arbitrary keyword arguments

        """
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args: float, **kwargs: float) -> None:
        """Log a message with level ERROR.

        Parameters
        ----------
        msg : str
            The message to log
        *args : float
            Variable length argument list
        **kwargs : float
            Arbitrary keyword arguments

        """
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args: float, **kwargs: float) -> None:
        """Log a message with level CRITICAL.

        Parameters
        ----------
        msg : str
            The message to log
        *args : float
            Variable length argument list
        **kwargs : float
            Arbitrary keyword arguments

        """
        self.logger.critical(msg, *args, **kwargs)

    def exception(self, msg: str, *args: float, **kwargs: float) -> None:
        """Log a message with level EXCEPTION.

        Parameters
        ----------
        msg : str
            The message to log
        *args : float
            Variable length argument list
        **kwargs : float
            Arbitrary keyword arguments

        """
        self.logger.exception(msg, *args, **kwargs)


if __name__ == "__main__":
    # Create a logger instance with a file output
    log = Logger(name="MyLogger")

    log.debug("This is a debug message.")
    log.info("This is an info message.")
    log.warning("This is a warning message.")
    log.error("This is an error message.")
    log.critical("This is a critical message.")
    log.exception("This is an exception message.")
