import os
import subprocess

import pandas as pd
from data_loader import DataLoader
from data_preprocessing import DataPreprocessor
from logging_section import setup_logging
from mysql import MySQLConnection

# from schema_mysql import DirectLinkComment, DirectLinkRequestID, DirectLinkReplies, DirectLinkPreprocessed
from Karun_summary_agent import SummaryAgent

pd.options.mode.chained_assignment = None  # Disable the warning
pd.set_option("future.no_silent_downcasting", True)

# initialization
logger = setup_logging()
url = os.getenv("SUMMARY_URL")
summary_agent = SummaryAgent(url)
yankechil = os.getenv("YANKECHIL")
# mongodb
database_name = os.getenv("MONGODB_DATABASE_DL")
# mysql
sql_db = os.getenv("MARKETPLACE_DATABASE_DL")
sql_db_dev = os.getenv("MARKETPLACE_DATABASE_DEV_DL")
mysql_handler = MySQLConnection(sql_db_dev)


def trigger_fastapi() -> bool:
    """Trigger the FastAPI endpoint Yan Kechil using curl.

    Returns:
        bool: True if the trigger is successful, False otherwise.

    """
    curl_command = ["curl", "-G", yankechil]

    logger.info("Triggering FastAPI endpoint using curl...")

    try:
        result = subprocess.run(
            curl_command,
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info(f"FastAPI response: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to trigger FastAPI endpoint: {e.stderr}")
        return False


def run_haraz_directlink():
    try:
        logger.info("Starting pipeline..")

        # Load collection mongo
        mongo_data = DataLoader.load_mongo_data(database_name)

        # wait for description and transcription completed, the load all table needed
        if DataLoader.wait_for_table_completion(
            "video_captions", mongo_data["video"], mysql_handler
        ):
            # Load table mysql
            mysql_data = DataLoader.load_mysql_data(sql_db, sql_db_dev)

        # preprocess data
        logger.info("Starting data preprocessing...")
        preprocessed_df, cleaned_comments_df, replies_df, request_id_df = (
            DataPreprocessor.directlink_preprocess(mongo_data, mysql_data)
        )

        # keep for debugging
        preprocessed_df.to_csv("preprocessed_df.csv")
        cleaned_comments_df.to_csv("cleaned_comments_df.csv")
        replies_df.to_csv("replies_df.csv")
        request_id_df.to_csv("request_id_df.csv")

        # Check if the tables exist in the database
        if mysql_handler.table_exists(
            "directlink_preprocessed_test"
        ) and mysql_handler.table_exists("directlink_comments_test"):
            # Before generating the summary, get the video_id that is already processed and inside the db
            preprocessed_df = mysql_handler.filter_new_data(
                preprocessed_df, "directlink_preprocessed_test", "video_id"
            )
            cleaned_comments_df = mysql_handler.filter_new_data(
                cleaned_comments_df, "directlink_comments_test", "comment_mongodb_id"
            )

        # Generate summaries #
        preprocessed_df, cleaned_comments_df = summary_agent.generate_summaries(
            preprocessed_df, cleaned_comments_df
        )

        push_success = True

        # Push data to MySQL
        push_success = all(
            [
                mysql_handler.push_table(
                    table_name="directlink_comments_test",
                    df=cleaned_comments_df,
                    primary_key="comment_mongodb_id",
                ),
                mysql_handler.push_table(
                    table_name="directlink_user_requestid_test",
                    df=request_id_df,
                    primary_key="video_mongodb_id",
                ),
                mysql_handler.push_table(
                    table_name="directlink_replies_test",
                    df=replies_df,
                    primary_key="id",
                ),
                mysql_handler.push_table(
                    table_name="directlink_preprocessed_test",
                    df=preprocessed_df,
                    primary_key="video_id",
                ),
            ]
        )

        if push_success:
            logger.info("All data successfully pushed to MySQL.")

            # trigger YanKechil FastAPI #
            fastapi_success = trigger_fastapi()

            # Return success response for DB even if FastAPI trigger fails
            return {
                "message": "Pipeline executed successfully",
                "records_processed": len(preprocessed_df),
                "fastapi_triggered": fastapi_success,
            }

        logger.error("Pipeline execution failed.")
        return {
            "message": "Pipeline execution failed.",
            "records_processed": 0,
        }

    except Exception as e:
        logger.error(f"Error occurred during data preprocessing: {e}")


# if __name__ == "__main__":
#     run_haraz_directlink()
