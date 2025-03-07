import asyncio
import os
import pandas as pd
from typing import Dict, List
import asyncio
from sqlalchemy import text

from urllib.parse import quote_plus

import requests
from dotenv import load_dotenv
from pydantic import BaseModel

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
from processing.pipeline_direct import DataProcessorPipeline_v00
from processing.pipeline_filter import (
    DataProcessorPipeline_v01,
    apply_filters,
    filter_by_date,
)
from schema.output_schemas import (
    AnalysisTableSchema,
    CommentsTableSchemaOut,
    MappedTableSchemaOut,
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

    law_regulated_app_url = os.getenv("law_regulated_app_url")
    if not law_regulated_app_url:
        logger.error("law_regulated_app_url not defined in env")

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


async def load_all_data(db):
    """Load necessary CSV data."""
    try:
        # Load input data
        df_category = db.get_data_from_table(category_table_name)
        if df_category.empty:
            logger.error(f"{category_table_name} is empty.")
        df_sub_category = db.get_data_from_table(sub_category_table_name)
        if df_sub_category.empty:
            logger.error(f"{sub_category_table_name} is empty.")

        # df_category = pd.read_csv("category.csv")
        # df_sub_category = pd.read_csv("sub_category.csv")

        return df_sub_category, df_category
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise


async def run_filtering_pipeline_for_analysis(
    agentsprocess,
    db,
    df_unbiased,
    mapped_df,
    config,
):
    """Run pipeline_v1."""
    try:
        pipeline_v1 = DataProcessorPipeline_v01(agentsprocess, db, df_unbiased, config)
        logger.info("The pipeline_v1 created successfully.")
    except Exception as e:
        logger.error(f"Error creating pipeline_v1.: {e}")
        print(f"Error creating pipeline_v1.: {e}")
        del pipeline_v1
        raise
    try:
        pipeline_v1.process_unbiased_data_and_store(mapped_df)
        logger.info("Pipeline_v1 processing unbiased data completed.")
        del pipeline_v1
    except Exception as e:
        print(f"Error proces unbiased data in pipeline_v1.: {e}")
        logger.error(f"Error proces unbiased data in pipeline_v1.: {e}")
        del pipeline_v1
        raise


async def run_filtering_pipeline_for_comments(agentsprocess, db, df_comments, config):
    """Run pipeline_v1."""
    try:
        pipeline_v1 = DataProcessorPipeline_v01(agentsprocess, db, df_comments, config)
        logger.info("The pipeline_v1 created successfully.")
    except Exception as e:
        logger.error(f"Error creating pipeline_v1.: {e}")
        del pipeline_v1
        raise
    try:
        pipeline_v1.process_comments_data_and_store()
        logger.info("Pipeline_v1 processing comments data completed.")
        del pipeline_v1
    except Exception as e:
        logger.error(f"Error proces unbiased data in pipeline_v1.: {e}")
        del pipeline_v1
        raise


async def run_filtering_pipeline_for_comments_v0(
    agentsprocess,
    db,
    df_comments,
    key_id,
    config,
):
    """Run pipeline_v0."""
    pipeline_v0 = DataProcessorPipeline_v00(agentsprocess, db, df_comments, config)
    pipeline_v0.run_comment_risk_agent_pipeline(key_id)
    logger.info("Pipeline_v0 processing comments data completed.")


async def process_comments_table(
    comments_db, comments_table_name, config, batch_size, agentsprocess
):
    offset_comments = 0
    any_data_processed = False

    # Get the total length of the comments table
    with comments_db.engine.connect() as connection:
        total_comments_query = text(f"SELECT COUNT(*) FROM {comments_table_name}")
        total_comments_length = connection.execute(total_comments_query).scalar()
    logger.info(f"Total rows in comments table: {total_comments_length}")

    while offset_comments < total_comments_length:
        # while True:
        df_comments = comments_db.get_batch_data_from_table(
            comments_table_name, batch_size, offset_comments
        )

        if df_comments.empty:
            logger.info("No more comments data to process.")
            break

        offset_comments += len(df_comments)

        logger.info(f"Processing {len(df_comments)} rows from the comments table.")

        # Filter the DataFrame by agent name
        logger.info("Filtering by agent name from the comments table.")
        df_comments = df_comments[df_comments['agent_name'] == config.agent_builder_name]
        logger.info(f"Filtering by agent name has {len(df_comments)} rows from the comments table.")
        logger.debug(f"agent name: {config.agent_builder_name}")

        # Filter by dates
        post_date_comments_column_name = "comment_posted_timestamp"
        if config.start_date or config.end_date:
            logger.info("Filtering by date from the comments table.")
            df_comments = filter_by_date(
                df_comments, config, post_date_comments_column_name
            )
            logger.info(f"Filtering by date has {len(df_comments)} rows from the comments table.")


        # Apply category and subcategory filters
        if config.category and config.subcategory:
            logger.info("Filtering by category and subcategory from the comments table.")
            df_comments = df_comments[
                (df_comments["category"] == config.category)
                & (df_comments["subcategory"] == config.subcategory)
            ]
            logger.info(f"Filtering by category has {len(df_comments)} rows from the comments table.")


        # print("^^^^^^^^^^1^^^^^^^^^^")
        # print("len comments", len(df_comments))
        # print("^^^^^^^^^1^^^^^^^^^^^")

        if df_comments.empty:
            logger.info("Filtered comments are empty for this batch. Skipping...")
            continue

        # Process the filtered comments
        await run_filtering_pipeline_for_comments(
            agentsprocess, comments_db, df_comments, config
        )
        any_data_processed = True  # Data was processed in this batch  <-- New line

    # After processing all batches, raise an error if no data was processed
    if not any_data_processed:  # <-- New block
        raise ValueError("All batches were empty. No comments data was processed.")  # <-- New line      

    logger.info("Finished processing the comments table.")


async def process_unbiased_and_mapped_tables(
    db,
    preprocessed_unbiased_table_name,
    mapped_table_name,
    config,
    batch_size,
    agentsprocess,
):
    offset_unbiased = 0
    any_data_processed = False  # Flag to track if any data was processed


    # Load static data once
    df_sub_category, df_category = await load_all_data(db)

    while True:
        df_unbiased = db.get_batch_data_from_table(
            preprocessed_unbiased_table_name, batch_size, offset_unbiased
        )

        if df_unbiased.empty:
            logger.info("No more data in the unbiased table.")
            break

        offset_unbiased += len(df_unbiased)

        # Fetch mapped data using IDs from the unbiased table
        unbiased_ids = df_unbiased["id"].tolist()
        if unbiased_ids:
            query = f"""
                SELECT *
                FROM {mapped_table_name}
                WHERE preprocessed_unbiased_id IN ({', '.join(map(str, unbiased_ids))})
            """
            df_mapped = pd.read_sql(query, db.engine)
        else:
            df_mapped = pd.DataFrame()

        if df_mapped.empty:
            logger.warning("No mapped data found for the current batch.")
            continue

        # Filter the DataFrame by agent name
        logger.info("Filtering by agent name from the unbiased table.")
        df_unbiased = df_unbiased[df_unbiased['agent_name'] == config.agent_builder_name]
        logger.info(f"Filtering by agent name has {len(df_unbiased)} rows from the unbiased table.")
        logger.debug(f"agent name: {config.agent_builder_name}")

        # Filter by dates
        post_date_unbiased_column_name = "video_posted_timestamp"
        if config.start_date or config.end_date:
            logger.info("Filtering by date from the unbiased table.")
            df_unbiased = filter_by_date(
                df_unbiased, config, post_date_unbiased_column_name
            )
            logger.info(f"Filtering by date has {len(df_unbiased)} rows from the unbiased table.")


        # Apply category and subcategory filters
        if config.category and config.subcategory:
            logger.info("Filtering by category and subcategory from the unbiased table.")
            df_unbiased, df_mapped = apply_filters(
                df_unbiased, df_mapped, df_sub_category, df_category, config
            )
            logger.info(f"Filtering by category has {len(df_unbiased)} rows from the unbiased table.")


        print("^^^^^^^^^^0^^^^^^^^^^")
        print("len unbiased", len(df_unbiased))
        print("len mapped", len(df_mapped))
        print("^^^^^^^^^0^^^^^^^^^^^")

        if df_unbiased.empty or df_mapped.empty:
            logger.info("Filtered data is empty for this batch. Skipping...")
            continue

        # Process the filtered unbiased and mapped data
        await run_filtering_pipeline_for_analysis(
            agentsprocess, db, df_unbiased, df_mapped, config
        )
        any_data_processed = True  # Data was processed in this batch  <-- New line

    # After processing all batches, raise an error if no data was processed
    if not any_data_processed:  # <-- New block
        raise ValueError("All batches were empty. No unbiased data was processed.")  # <-- New line      

    logger.info("Finished processing the unbiased and mapped tables.")


async def run_async_filtered_processor(config):
    batch_size = 100
    output_schemas = [AnalysisTableSchema, MappedTableSchemaOut]

    if not db_url:
        logger.error("MYSQL URL is not available.")
        raise ValueError("Database URL is missing.")

    db = Database(db_url, output_schemas, None)
    comments_db = Database(db_url, [CommentsTableSchemaOut], None)

    agent_manager = create_agent_manager_v0(agent_configs)
    agentsprocess = AgentsProcessV0(agent_manager)

    # Check the health of agents at the start
    health_status = agentsprocess.check_agents_health(
        agent_names=[
            AgentsNameV0.sentiment,
            AgentsNameV0.justification,
            AgentsNameV0.law_regulated,
            AgentsNameV0.comment_risk,
        ]
    )

    # Log the agent health status
    logger.info("Agent Health Status: %s", health_status)
    # If any agent is unhealthy, stop execution or raise an error
    if not all(health_status.values()):
        logger.error("One or more agents are unavailable. Terminating the process.")
        raise SystemExit("Agent health check failed. Process terminated.")

    try:
        # Run the processing for comments and unbiased/mapped tables in parallel
        await asyncio.gather(
            process_unbiased_and_mapped_tables(
                db,
                preprocessed_unbiased_table_name,
                mapped_table_name,
                config,
                batch_size,
                agentsprocess,
            ),
            process_comments_table(
                comments_db, comments_table_name, config, batch_size, agentsprocess
            ),
        )
    except Exception as e:
        logger.error(f"Error during batch processing: {e}")
        raise
    finally:
        db.close()
        comments_db.close()
        logger.info("Database connections closed.")

    logger.info("Batch processing completed.")

def run_filtered_processor(config):
    batch_size = 100
    output_schemas = [AnalysisTableSchema, MappedTableSchemaOut]

    if not db_url:
        logger.error("MYSQL URL is not available.")
        raise ValueError("Database URL is missing.")

    db = Database(db_url, output_schemas, None)
    comments_db = Database(db_url, [CommentsTableSchemaOut], None)

    agent_manager = create_agent_manager_v0(agent_configs)
    agentsprocess = AgentsProcessV0(agent_manager)

    # Check the health of agents at the start
    health_status = agentsprocess.check_agents_health(
        agent_names=[
            AgentsNameV0.sentiment,
            AgentsNameV0.justification,
            AgentsNameV0.law_regulated,
            AgentsNameV0.comment_risk,
        ]
    )

    print(health_status)

    # Log the agent health status
    logger.info("Agent Health Status: %s", health_status)
    # If any agent is unhealthy, stop execution or raise an error
    if not all(health_status.values()):
        logger.error("One or more agents are unavailable. Terminating the process.")
        raise SystemExit("Agent health check failed. Process terminated.")

    try:
        # Run the processing for comments and unbiased/mapped tables in parallel
        process_unbiased_and_mapped_tables(
            db,
            preprocessed_unbiased_table_name,
            mapped_table_name,
            config,
            batch_size,
            agentsprocess,
        )
        process_comments_table(
            comments_db, comments_table_name, config, batch_size, agentsprocess
        )
    except Exception as e:
        logger.error(f"Error during batch processing: {e}")
        raise
    finally:
        db.close()
        comments_db.close()
        logger.info("Database connections closed.")

    logger.info("Batch processing completed.")
