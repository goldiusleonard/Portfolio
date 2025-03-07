"""VM database."""

# IMPORT THE SQALCHEMY LIBRARY's CREATE_ENGINE METHOD
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()
# DEFINE THE DATABASE CREDENTIALS
user = os.getenv("VM_USER")
password = os.getenv("VM_PASSWORD")
host = os.getenv("VM_HOST")
port = os.getenv("VM_PORT")

encoded_username = quote_plus(user)
encoded_password = quote_plus(password)

connect_args = {"ssl": {"fake_flag_to_enable_tls": True}}
engine = create_engine(
    f"mysql+pymysql://{encoded_username}:{encoded_password}@{host}:{port}/",
    connect_args=connect_args,
)


Session_Vm = sessionmaker(autocommit=False, autoflush=False, bind=engine)
