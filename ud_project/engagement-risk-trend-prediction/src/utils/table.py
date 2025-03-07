import logging
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text, Engine
from typing import Union

# Configure logging
logging.basicConfig(level=logging.INFO)


def fetch_data_asset_table(
    engine: Engine,
    data_asset_table_name: str,
    days: int = 365,
    category: Union[str, None] = None,
    sub_category: Union[str, None] = None,
    topic: Union[str, None] = None,
    user_handle: Union[str, None] = None,
):
    """
    Fetch data from the database filtered for the last `days` days and according to category, sub-category, topic, and user_handle.

    :param engine: Database connection engine.
    :param data_asset_table_name: Data asset table name to query.
    :param days: Number of days to filter data, defaults to 365.
    :param category: Optional category filter.
    :param sub_category: Optional sub-category filter.
    :param topic: Optional topic filter.
    :param user_handle: Optional user_handle filter.
    :return: Filtered DataFrame.
    """
    filter_date = datetime.today() - timedelta(days=days)

    # Start building the query with basic date filter
    query = f"""
        SELECT * 
        FROM {data_asset_table_name}
        WHERE video_posted_timestamp >= :filter_date
    """

    # Add category filter if provided
    if category:
        query += " AND category = :category"

    # Add sub-category filter if provided
    if sub_category:
        query += " AND sub_category = :sub_category"

    # Add topic filter if provided
    if topic:
        query += " AND topic_category = :topic"

    # Add user_handle filter if provided
    if user_handle:
        query += " AND user_handle = :user_handle"

    query = text(query)

    with engine.connect() as connection:
        params: dict = {"filter_date": filter_date}

        # Include filters in the parameters dictionary if they exist
        if category:
            params["category"] = category
        if sub_category:
            params["sub_category"] = sub_category
        if topic:
            params["topic"] = topic
        if user_handle:
            params["user_handle"] = user_handle

        result = connection.execute(query, params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())

    logging.info(
        f"Fetched {len(df)} records from the database filtered for the last {days} days with filters: {params}"
    )

    # Convert necessary columns
    df["video_id"] = df["video_id"].astype(str)
    df["sub_category"] = df["sub_category"].str.lower()
    df["video_posted_timestamp"] = pd.to_datetime(df["video_posted_timestamp"])
    return df
