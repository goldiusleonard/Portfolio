"""Run SQL Procedures for Content."""

import logging
import os

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.engine import Engine

from connections.azure_connections import get_azure_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

load_dotenv()


def update_content_data_asset(connection: Engine) -> list:
    """Run procedure and return id and video_id."""
    result = connection.execute(text("CALL update_ba_content_data_asset();"))
    rows = result.fetchall()

    return [(row[0], row[1]) for row in rows] if rows else []


def call_update() -> dict:
    """Run updating procedures."""
    db_host = os.getenv("MYSQL_DB_HOST")
    db_port = os.getenv("MYSQL_DB_PORT")
    db_user = os.getenv("MYSQL_DB_USER")
    db_password = os.getenv("MYSQL_DB_PASSWORD")
    db_name = os.getenv("MCMC_BUSINESS_AGENT_DB_NAME")
    engine = get_azure_engine(db_name, db_user, db_password, db_host, db_port)
    video_ids_list = []
    with engine.connect() as connection:
        try:
            connection.execute(text("CALL update_content_video_engagement_rate();"))
            connection.execute(text("CALL update_content_risk_weight_score();"))
            connection.execute(text("CALL update_content_posted_recency_days();"))
            connection.execute(
                text("CALL update_content_posted_video_recency_score();"),
            )
            connection.execute(text("CALL update_content_subcategory_weight_score();"))
            connection.execute(text("CALL update_content_video_engagement_risk();"))
            connection.execute(text("CALL update_content_topic();"))
            try:
                ids_and_videos = update_content_data_asset(connection)
                if ids_and_videos:
                    for _, _video_id in ids_and_videos:
                        video_ids_list.append(_video_id)
                    message = {
                        "message": f"Inserted {len(ids_and_videos)} new records",
                        "ids_list": video_ids_list,
                    }
                else:
                    message = {
                        "message": "No new records to insert",
                        "ids_list": video_ids_list,
                    }
            except Exception:
                logging.exception("Unexpected error.")
                message = {"message": "Unexpected error.", "ids_list": video_ids_list}
                connection.rollback()
            connection.commit()
        except Exception:
            connection.rollback()
            logging.exception("Unexpected error.")
            message = {
                "error": "Unexpected error",
                "ids_list": video_ids_list,
            }
    return message
