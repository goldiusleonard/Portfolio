import os
import asyncio
import pandas as pd
from NileVolga_process import NileVolgaProcessor
from data_loader import DataLoader
from data_preprocessing import DataPreprocessor
from logging_section import setup_logging
from mysql import MySQLConnection
# API call
from Karun_summary_agent import SummaryAgent
pd.options.mode.chained_assignment = None  # Disable the warning
pd.set_option("future.no_silent_downcasting", True)

# initialization
logger = setup_logging()

karun_url = os.getenv("KARUN_URL")
summary_agent = SummaryAgent(karun_url)

# Databse credantials
# mysql db
sql_db_dev = os.getenv("MARKETPLACE_DATABASE_DEV")
sql_db = os.getenv("MARKETPLACE_DATABASE")
mysql_handler = MySQLConnection(sql_db_dev)
# mongodb
database_name = os.getenv("MONGODB_DATABASE")


def run_haraz_AI():
    try:
        logger.info("Starting pipeline..")

        # Load collection mongo
        mongo_data = DataLoader.load_mongo_data(database_name)

        # # Wait for description and transcription completed, then load all table needed
        # if DataLoader.wait_for_table_completion(
        #     "video_captions", mongo_data["video"], mysql_handler
        # ):
        #     # if DataLoader.wait_for_table_completion("test1", mongo_data["video"], mysql_handler):
        #     # Load table mysql
        #     mysql_data = DataLoader.load_mysql_data(sql_db, sql_db_dev)
        
        mysql_data = DataLoader.load_mysql_data(sql_db, sql_db_dev)

        # Preprocess data
        logger.info("Starting data preprocessing...")
        preprocessed_df, cleaned_comments_df, replies_df, mapping_df, request_id_df = (
            DataPreprocessor.preprocess_and_merge(mongo_data, mysql_data)
        )

        # Before generating the description, transcription and summary, get the video_id that already processed and inside the db
        # Check if the tables exist in the database
        if mysql_handler.table_exists(
            "test_preprocessed_unbiased"
        ) and mysql_handler.table_exists("test_comments_cat_subcat"):
            # Before generating the summary, get the video_id that is already processed and inside the db
            preprocessed_df = mysql_handler.filter_new_data(
                preprocessed_df, "test_preprocessed_unbiased", "video_id"
            )
            cleaned_comments_df = mysql_handler.filter_new_data(
                cleaned_comments_df, "test_comments_cat_subcat", "comment_mongodb_id"
            )

        # # Generate the description #
        # preprocessed_df = asyncio.run(description_agent.process_videos(preprocessed_df))

        # # Generate the transcription #
        # preprocessed_df = asyncio.run(transcription_agent.process_videos(preprocessed_df))

        # Run the async processing for description & transcription
        preprocessed_df = asyncio.run(NileVolgaProcessor.process_all_videos(preprocessed_df))

        # Generate summaries #
        preprocessed_df, cleaned_comments_df = summary_agent.generate_summaries(
            preprocessed_df, cleaned_comments_df
        )

        # keep for debugging
        preprocessed_df.to_csv("csv_file/preprocessed_summary.csv")
        cleaned_comments_df.to_csv("csv_file/comments_summary.csv")

        push_success = True
        # Push data to MySQL table for testing
        push_success = all(
            [
                mysql_handler.push_table(
                    table_name="test_comments_cat_subcat",
                    df=cleaned_comments_df,
                    primary_key="comment_mongodb_id",
                ),
                mysql_handler.push_table(
                    table_name="test_user_requestid",
                    df=request_id_df,
                    primary_key="video_mongodb_id",
                ),
                mysql_handler.push_table(
                    table_name="test_replies", df=replies_df, primary_key="id"
                ),
                mysql_handler.push_table(
                    table_name="test_mapped_cat_sub", df=mapping_df, primary_key="id"
                ),
                mysql_handler.push_table(
                    table_name="test_preprocessed_unbiased",
                    df=preprocessed_df,
                    primary_key="video_id",
                ),
            ]
        )
                           
        # push_success = all([
        #      mysql_handler.push_table(table_name="comments_cat_subcat",
        #                              df=cleaned_comments_df,
        #                              primary_key="comment_mongodb_id"),

        #     mysql_handler.push_table(table_name="user_requestid",
        #                              df=request_id_df,
        #                              primary_key="video_mongodb_id"),

        #     mysql_handler.push_table(table_name="replies",
        #                              df=replies_df,
        #                              primary_key="id"),

        #     mysql_handler.push_table(table_name="mapped_cat_sub",
        #                              df=mapping_df,
        #                              primary_key="id"),

        #     mysql_handler.push_table(table_name="preprocessed_unbiased",
        #                              df=preprocessed_df,
        #                              primary_key="video_id")

        #     ])

        if push_success:
            logger.info("All data successfully pushed to MySQL.")
            # Return success response for DB even if FastAPI trigger fails
            return {
                "message": "Pipeline executed successfully",
                "records_processed": len(preprocessed_df),
            }

        logger.error("Pipeline execution failed.")
        return {
            "message": "Pipeline execution failed.",
        }

    except Exception as e:
        logger.error(f"Error occurred during data preprocessing: {e}")


if __name__ == "__main__":
    run_haraz_AI()
