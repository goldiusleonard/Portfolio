import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from sqlalchemy.orm import sessionmaker

load_dotenv()


def get_mysql_engine():
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    host = os.getenv("MYSQL_HOST")
    port = os.getenv("MYSQL_PORT")
    database = os.getenv("MYSQL_DATABASE")

    encoded_username = quote_plus(user)
    encoded_password = quote_plus(password)

    # Create the SQLAlchemy engine
    engine = create_engine(
        f"mysql+pymysql://{encoded_username}:{encoded_password}@{host}:{port}/{database}"
    )
    return engine


def get_mysql_session():
    engine = get_mysql_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    return session
