import asyncio
import os
import pandas as pd
from typing import Dict, List
from urllib.parse import quote_plus

import aiohttp
import requests
from dotenv import load_dotenv
from pydantic import BaseModel
from sqlalchemy import text
from agents.Agents import (
    AgentsNameV0,
    CategoryAgent,
    CommentRiskAgent,
    JustificationAgent,
    LawRegulatedAgent,
    SentimentAgent,
    SummaryAgent,
)
from agents.AgentsProcess import AgentsProcessV0
from agents.register_agents import create_agent_manager_v0
from db.db import Database
from log_mongo import logger
from processing.pipeline_direct import DataProcessorPipeline_v01
from schema.output_schemas import (
    TikTokTableSchemaOut,
)

load_dotenv()

mysql_user = os.getenv("mysql_user")
mysql_password = os.getenv("mysql_password")
mysql_host = os.getenv("mysql_host")
input_mysql_database = os.getenv("mysql_database")
output_mysql_database = os.getenv("output_mysql_database")

db_url = f"mysql+pymysql://{mysql_user}:{quote_plus(mysql_password)}@{mysql_host}/{input_mysql_database}"


api_ip = os.getenv("api_ip")
if not api_ip:
    logger.error("IP address not found")

frontend_url = os.getenv("frontend_url")

preprocessed_unbiased_table_name = os.getenv("table_name_input_1")
if not preprocessed_unbiased_table_name:
    logger.error("preprocessed_unbiased_table_name not defined in env")
comments_table_name = os.getenv("table_name_input_2")
if not comments_table_name:
    logger.error("comments_table_name not defined in env")
mapped_table_name = os.getenv("table_name_input_3")
if not mapped_table_name:
    logger.error("mapped_table_name not defined in env")
category_table_name = os.getenv("table_name_input_4")
if not category_table_name:
    logger.error("category_table_name not defined in env")
sub_category_table_name = os.getenv("table_name_input_5")
if not sub_category_table_name:
    logger.error("sub_category_table_name not defined in env")
tiktok_table_name = os.getenv("table_name_input_6")
if not tiktok_table_name:
    logger.error("tiktok_table_name not defined in env")


class ConfigEndpoints:
    """Configuration class for application endpoints loaded from environment variables."""

    summary_app_url = os.getenv("summary_app_url")
    if not summary_app_url:
        logger.error("summary_app_url not defined in env")

    justification_app_url = os.getenv("justification_app_url")
    if not justification_app_url:
        logger.error("justification_app_url not defined in env")

    category_app_url = os.getenv("category_app_url")
    if not category_app_url:
        logger.error("category_app_url not defined in env")

    law_regulated_app_url = os.getenv("law_regulated_direct_app_url")
    if not law_regulated_app_url:
        logger.error("law_regulated_direct_app_url not defined in env")

    sentiment_app_url = os.getenv("sentiment_app_url")
    if not sentiment_app_url:
        logger.error("sentiment_app_url not defined in env")

    comment_risk_app_url = os.getenv("comment_risk_app_url")
    if not comment_risk_app_url:
        logger.error("comment_risk_app_url not defined in env")


# Define the agent configurations with .name for the enum values
agent_configs = {
    str(AgentsNameV0.summary): {  # Use .name to get the string representation
        "class": SummaryAgent,
        "init_args": {"url": ConfigEndpoints.summary_app_url},
    },
    str(AgentsNameV0.category): {
        "class": CategoryAgent,
        "init_args": {"url": ConfigEndpoints.category_app_url},
    },
    str(AgentsNameV0.sentiment): {
        "class": SentimentAgent,
        "init_args": {"url": ConfigEndpoints.sentiment_app_url},
    },
    str(AgentsNameV0.justification): {
        "class": JustificationAgent,
        "init_args": {"url": ConfigEndpoints.justification_app_url},
    },
    str(AgentsNameV0.law_regulated): {
        "class": LawRegulatedAgent,
        "init_args": {"url": ConfigEndpoints.law_regulated_app_url},
    },
    str(AgentsNameV0.comment_risk): {
        "class": CommentRiskAgent,
        "init_args": {"url": ConfigEndpoints.comment_risk_app_url},
    },
}


class TableConfig:
    def __init__(self, table_source_name, table_target_name):
        self.table_source_name = table_source_name
        self.table_target_name = table_target_name


class DatabaseConfig:
    def __init__(self, base, schema):
        self.db_base = base
        self.schema = schema
        self.db_url = db_url


class TriggerInputConfig:
    def __init__(
        self,
        process_mapping,
        processes_to_run,
    ):
        self.process_mapping = process_mapping
        self.processes_to_run = processes_to_run


class FilterInputConfig:
    def __init__(
        self,
        files_name,
        start_date,
        end_date,
        category,
        subcategory,
        risk_levels,
        agent_builder_name,
    ):
        self.files_name = files_name
        self.start_date = start_date
        self.end_date = end_date
        self.category = category
        self.subcategory = subcategory
        self.risk_levels = risk_levels
        self.agent_builder_name = agent_builder_name


class PostDate(BaseModel):
    start_date: str
    end_date: str


# Define a model for the filters (optional, for validation and type hints)
class Filters(BaseModel):
    files_name: List[str]
    risk_levels: Dict
    category: str
    subcategory: str
    post_date: PostDate
    agent_builder_name: str


class CrawlerConfig:
    host: str = "localhost"
    port: int = "8000"
    endpoint_name: str = "crawling"


# Define a request body for the endpoint
class TriggerRequest(BaseModel):
    trigger: str


async def trigger_crawler_api_to_fill_data(end_date):
    """Function to trigger another API to fill the dataframe when data is missing for end_date."""
    logger.info("Triggering another API to fill the dataframe...")
    try:
        # API call
        response = requests.get(
            f"http://{CrawlerConfig.api_ip}:{CrawlerConfig.port}/{CrawlerConfig.endpoint_name}",
            params={"end_date": str(end_date)},
        )
        print(response.json())
    except ValueError as e:
        logger.error({f"error call api with its respons {response.json()}": str(e)})
    await asyncio.sleep(1)  # Simulate API call
    logger.info("Other API has been triggered to fill the missing data.")


async def load_data(db, table_name):
    """Load necessary CSV data."""
    try:
        # # Load input data
        df = db.get_data_from_table(table_name)[:]
        # df = pd.read_csv("comments_table.csv")
        return df
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise


class CustomProcessorException(Exception):
    """Base class for all custom processor exceptions."""

    def __init__(self, status):
        self.status = status
        super().__init__(self.status)


class NoDataFoundException(CustomProcessorException):
    """Raised when no data is found."""

    def __init__(self):
        super().__init__(status="Empty")


class ProcessingException(CustomProcessorException):
    """Raised during a processing error."""

    def __init__(self):
        super().__init__(status="Processing")


class ReadyException(CustomProcessorException):
    """Raised when the status is ready."""

    def __init__(self):
        super().__init__(status="Ready")


class FaildException(CustomProcessorException):
    """Raised when a process fails."""

    def __init__(self):
        super().__init__(status="Faild")


async def notify_status(status: str):
    """Sends status updates to the frontend.

    Args:
        status (str): The status to be sent (e.g., "Processing", "Ready", etc.)

    """
    try:
        # Simulate sending the status to the frontend (via API, WebSocket, etc.)
        async with aiohttp.ClientSession() as session:
            payload = {"status": status}
            async with session.post(frontend_url, json=payload) as response:
                if response.status != 200:
                    logger.error(f"Failed to notify frontend: {response.status}")
    except Exception as e:
        logger.error(f"Error while notifying frontend: {e!s}")


async def run_async_direct_processor_v0(table_config):
    try:
        logger.info("Starting run_async_direct_processor_v0 function...")
        batch_size = 100
        batch_size_store = 5
        key_id = "_id"  # Primary key used to identify rows
        logger.info("Initializing database")
        db = Database(db_url, [TikTokTableSchemaOut], None)
        logger.info("Initializing manager")
        # Initialize agents process and pipeline
        agent_manager = create_agent_manager_v0(agent_configs)
        logger.info("Initializing AgentsProcessV0")
        agentsprocess = AgentsProcessV0(agent_manager)
        logger.info("Initializing DataProcessorPipeline_v01")
        pipeline = DataProcessorPipeline_v01(agentsprocess, db)

        # Check the health of agents at the start
        health_status = agentsprocess.check_agents_health(
            agent_names=[
                AgentsNameV0.sentiment,
                AgentsNameV0.justification,
                AgentsNameV0.law_regulated,
                AgentsNameV0.category,
            ]
        )
        # Log the agent health status
        logger.info("Agent Health Status: %s", health_status)
        # Terminate if any agent is unhealthy
        if not all(health_status.values()):
            logger.error("One or more agents are unavailable. Terminating the process.")
            raise SystemExit("Agent health check failed. Process terminated.")

        # Track the last processed key_id
        with db.engine.connect() as connection:
            result = connection.execute(
                text(
                    f"SELECT COALESCE(MAX({key_id}), '') FROM {table_config.table_target_name}"
                )
            )
            last_processed_id = result.scalar()

        # Get the total row count of the source table
        total_rows_query = text(
            f"SELECT COUNT(*) AS total_rows FROM {table_config.table_source_name}"
        )
        total_rows_df = pd.read_sql(total_rows_query, db.engine)
        total_rows = total_rows_df["total_rows"].iloc[0]
        logger.info(f"Total rows in source table: {total_rows}")

        processed_rows = 0  # Counter for processed rows
        while True:
            # Fetch the next batch of rows
            query = text(f"""
                SELECT *
                FROM {table_config.table_source_name}
                WHERE {key_id} > :last_processed_id
                ORDER BY {key_id} ASC
                LIMIT :batch_size;
            """)
            batch_df = pd.read_sql(
                query,
                db.engine,
                params={
                    "last_processed_id": last_processed_id,
                    "batch_size": batch_size,
                },
            )

            if batch_df.empty:
                logger.info("No more new data to process.")
                break

            # Log batch details
            logger.info(f"Processing batch with size {len(batch_df)}.")

            # Run the pipeline on the current batch
            # pipeline.run_all_agents_pipeline(key_id, batch_df)
            
            pipeline.run_all_agents_pipeline_batch(key_id, batch_df, batch_size_store)

            # Update the last processed ID
            last_processed_id = batch_df[key_id].max()

            # Increment processed rows counter
            processed_rows += len(batch_df)

            # Safety check: Break if processed rows exceed total rows
            if processed_rows > total_rows:
                logger.error(
                    f"Processed rows ({processed_rows}) exceed total rows ({total_rows}). Terminating."
                )
                raise RuntimeError(
                    "Infinite loop detected: Processed rows exceeded total source table rows."
                )

    except Exception as e:
        logger.error(f"Error in run_async_direct_processor_v0: {e}")
        raise  # Re-raise the exception to propagate it to process_status
    finally:
        # Ensure the database connection is closed even if an error occurs
        db.close()
        logger.info("Database connection closed.")

    logger.info("Preprocess data processor completed.")


# Assuming TriggerRequest is defined as follows:
class TriggerRequest:
    def __init__(self, trigger: str):
        self.trigger = trigger.lower() == "true"


async def process_trigger(trigger: bool, processor_fn) -> Dict:
    """Handles the triggering logic for any processor asynchronously."""
    try:
        input_data = TriggerRequest(trigger=str(trigger))
        if input_data.trigger:
            await asyncio.sleep(1)  # Non-blocking sleep
            # Run the processor asynchronously
            await processor_fn
            return {"status": "Completed"}
    except Exception as e:
        # Handle unexpected errors in the process_trigger function
        logger.error(
            f"The status of {processor_fn.__name__.replace('_', ' ').title()} failed: {e!s}",
        )
        return {"status": "Faild"}
