import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

# DEFINE THE DATABASE CREDENTIALS
user = os.getenv("VM_USER")
password = os.getenv("VM_PASSWORD")
host = os.getenv("VM_HOST")
port = os.getenv("VM_PORT")

# Store database schemas
schemas = {
    "marketplace": os.getenv("MARKETPLACE_DATABASE"),
    "marketplace_dev": os.getenv("MARKETPLACE_DATABASE_DEV"),
    "marketplace_dl": os.getenv("MARKETPLACE_DATABASE_DL"),
    "marketplace_dev_dl": os.getenv("MARKETPLACE_DATABASE_DEV_DL"),
}


def get_database_schema(schema_name: str) -> str:
    """Fetch the database schema for a given environment."""
    return schemas.get(schema_name, schemas["marketplace"])  # Default to "marketplace"


def create_engine_for_schema(schema_name: str) -> create_engine:
    """Create and return an SQLAlchemy engine based on the selected schema."""
    database = get_database_schema(schema_name)
    encoded_username = quote_plus(user)
    encoded_password = quote_plus(password)

    connect_args = {"ssl": {"fake_flag_to_enable_tls": True}}

    engine = create_engine(
        f"mysql+pymysql://{encoded_username}:{encoded_password}@{host}:{port}/{database}",
        connect_args=connect_args,
    )
    return engine
