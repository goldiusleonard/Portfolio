import logging


def setup_logger(log_filename="sentiment_analysis2.log"):
    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create file handler for logging to a file
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)

    # Create console handler for logging to terminal
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create a formatter for log messages
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Set the formatter for both handlers
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Log a separator for readability
    logger.info("------------------------------------------------------------")
    return logger
