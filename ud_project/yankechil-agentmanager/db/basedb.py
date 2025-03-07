import sys

sys.stdout.reconfigure(encoding="utf-8")


class BaseDatabase:
    def __init__(self, db_url: str, db2_url: str):
        """Initialize the base database with a connection URL."""
        self.db_url = db_url
        self.db2_url = db2_url
        self.metadata = None  # Metadata to be set by child classes
