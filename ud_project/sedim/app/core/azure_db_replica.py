"""Azure database replica."""

# IMPORT THE SQALCHEMY LIBRARY's CREATE_ENGINE METHOD
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv(override=True)
# DEFINE THE DATABASE CREDENTIALS
user = os.getenv("REPLICA_USER")
password = os.getenv("REPLICA_PASSWORD")
host = os.getenv("REPLICA_HOST")
port = os.getenv("REPLICA_PORT")
database = os.getenv("REPLICA_DATABASE")

encoded_username = quote_plus(user)
encoded_password = quote_plus(password)

connect_args = {"ssl": {"fake_flag_to_enable_tls": True}}
engine = create_engine(
    f"mysql+pymysql://{encoded_username}:{encoded_password}@{host}:{port}/{database}",
    connect_args=connect_args,
)


SessionLocal_replica = sessionmaker(autocommit=False, autoflush=False, bind=engine)
