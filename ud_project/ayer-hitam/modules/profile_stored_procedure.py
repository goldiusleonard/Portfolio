#!/usr/bin/env python3
"""Docstring for stored procedure in MySQL.

List of profile stored procedure:
- update_profile_engagement_risk()
- update_profile_engagement_score()
- update_profile_ranking()
- update profile_latest_video_posted_date()
- update_ba_profile_data_asset()
"""

import logging
from typing import Generator

from sqlalchemy import text
from sqlalchemy.orm import Session

from connections.mysql_connection import mysql_engine

database1 = "mcmc_business_agent"


def get_mysql_session() -> Generator[Session, None, None]:
    """Get MySQL Session."""
    logging.info("Opening a new database session.")
    with mysql_engine(database_name=database1).connect() as session:
        try:
            yield session
        except Exception as e:
            error_message = f"An error occured: {e}"
            logging.exception(error_message)
            session.rollback()
        finally:
            session.close()
            logging.info("Closing the database session.")


def call_update_profile_data_asset() -> dict:
    """Call and update profile data asset through stored procedure SQL."""
    try:
        engine = mysql_engine(database_name=database1)  # Get the engine.

        with engine.connect() as connection:
            # Call the stored procedure in SQL.
            connection.execute(text("CALL update_profile_engagement_risk();"))
            connection.execute(text("CALL update_profile_engagement_score();"))
            connection.execute(text("CALL update_profile_threat_level();"))
            connection.execute(text("CALL update_profile_latest_video_posted_date();"))
            connection.execute(text("CALL update_ba_profile_data_asset();"))
            connection.commit()
        message = {"message": "Profile data updated successfully."}
    except Exception as e:
        connection.rollback()
        logging.exception("Error.")
        message = {"error": str(e)}
    return message
