import logging

# Configure logging


def setup_logging(log_file="app.log", log_level=logging.INFO):
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),  # Save logs to the specified file
            logging.StreamHandler(),  # Also print logs to the console
        ],
    )
    # Return the root logger for global use
    return logging.getLogger("Amu")
