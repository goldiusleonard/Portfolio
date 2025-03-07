"""Module to retrieve keywords in list form."""

import logging
import os
from datetime import timedelta

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import and_

from connections.azure_connection import get_azure_engine, get_azure_session
from credentials.mysql_credentials import get_credentials
from models.word_cloud_table import WordCloud

load_dotenv()
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def fetch_wordcloud(category: str, num_of_days: int) -> list:
    """Fetch keyword list based on filters."""
    # Part 1: Fetch marketpplace tables from MySQL
    ada_da_test_db = os.getenv("MCMC_BA_DB_NAME")
    logging.info("database name: %s", ada_da_test_db)

    user, password, host, port = get_credentials("ada")

    engine = get_azure_engine(ada_da_test_db, user, password, host, port)
    session = get_azure_session(ada_da_test_db, user, password, host, port)

    logging.info("engine: %s", engine)
    logging.info("session: %s", session)

    try:
        if category is not None and num_of_days is not None:
            end_datetime = pd.Timestamp.now().replace(microsecond=0)
            logging.info("end date time: %s", end_datetime)
            start_datetime = end_datetime + timedelta(days=num_of_days)
            logging.info("start date time: %s", end_datetime)
            input_df = pd.read_sql(
                session.query(WordCloud)
                .filter(
                    and_(
                        WordCloud.category == category,
                        WordCloud.processed_timestamp > start_datetime,
                        WordCloud.processed_timestamp < end_datetime,
                    ),
                )
                .statement,
                session.bind,
            )
        elif category is not None:
            input_df = pd.read_sql(
                session.query(WordCloud)
                .filter(WordCloud.category == category)
                .statement,
                session.bind,
            )
        elif num_of_days is not None:
            end_datetime = pd.Timestamp.now().replace(microsecond=0)
            logging.info("end date time: %s", end_datetime)
            start_datetime = end_datetime + timedelta(days=num_of_days)
            logging.info("start date time: %s", end_datetime)
            input_df = pd.read_sql(
                session.query(WordCloud)
                .filter(
                    and_(
                        WordCloud.processed_timestamp > start_datetime,
                        WordCloud.processed_timestamp < end_datetime,
                    ),
                )
                .statement,
                session.bind,
            )
        else:
            input_df = pd.read_sql(
                session.query(WordCloud).statement,
                session.bind,
            )
        logging.info("Table fetched. Shape: %s", input_df.shape)
        logging.info("Table Head: %s", input_df.head(5))
    finally:
        session.close()
        logging.info("session closed")

    return input_df["keyword"].head(150).to_list()


if __name__ == "__main__":
    category = "Scam"
    num_of_days = -7
    fetch_wordcloud(category, num_of_days)
