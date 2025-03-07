import time
from logging_section import setup_logging
from mongodb import MongoDBConnection
from mysql import MySQLConnection

logger = setup_logging()


class DataLoader:
    @staticmethod
    def load_mongo_data(database_name: str) -> dict:
        """Load collections from MongoDB."""
        mongo_handler = MongoDBConnection(database_name)
        data = mongo_handler.load_mongo_collections(["comment", "video", "profile"])
        mongo_handler.close()
        return data

    @staticmethod
    def load_mysql_data(schema_name: str, schema_name_dev: str) -> dict:
        """Load tables from MySQL, skipping category and subcategory tables if they do not exist."""
        data = {}
        mysql_handler = MySQLConnection(schema_name=schema_name)
        data["crawling_data"] = mysql_handler.fetch_table("crawling_data")
        data["tags"] = mysql_handler.fetch_table("tags")

        # Load additional tables from the default schema dev
        mysql_handler = MySQLConnection(schema_name=schema_name_dev)
        optional_tables = ["category", "sub_category"]
        for table in optional_tables:
            try:
                data[f"{table}_df"] = mysql_handler.fetch_table(table)
            except Exception:
                pass  # Skip silently as in directlink does not have this

        # data["description_df"] = mysql_handler.fetch_table("video_captions")
        # data["transcription_df"] = mysql_handler.fetch_table("volga_results_dev")
        return data

    @staticmethod
    def wait_for_table_completion(
        table_name: str, mongo_video_df, mysql_handler, interval=120, timeout=600
    ):
        """Wait until the table has all required IDs populated with descriptions."""
        logger.info(f"Waiting for table '{table_name}' to be ready...")
        required_ids = mongo_video_df["_id"].astype(str).tolist()

        start_time = time.time()
        while time.time() - start_time < timeout:
            if mysql_handler.is_table_populated(table_name, required_ids):
                logger.info(f"Table '{table_name}' is ready.")
                return True
            logger.info(f"Waiting for table '{table_name}' to be ready...")
            time.sleep(interval)

        raise TimeoutError(
            f"Timeout: Table '{table_name}' did not become ready within {timeout} seconds."
        )
