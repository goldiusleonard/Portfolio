import asyncio
import os
from typing import Dict, List
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
    validate_columns,
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
        df_unbiased = db.get_data_from_table(preprocessed_unbiased_table_name)[:]
        if df_unbiased.empty:
            logger.error(f"{preprocessed_unbiased_table_name} is empty.")
        df_mapped = db.get_data_from_table(mapped_table_name)
        if df_mapped.empty:
            logger.error(f"{mapped_table_name} is empty.")
        df_comments = db.get_data_from_table(comments_table_name)[:]
        if df_comments.empty:
            logger.error(f"{comments_table_name} is empty.")
        df_category = db.get_data_from_table(category_table_name)
        if df_category.empty:
            logger.error(f"{category_table_name} is empty.")
        df_sub_category = db.get_data_from_table(sub_category_table_name)
        if df_sub_category.empty:
            logger.error(f"{sub_category_table_name} is empty.")

        # df_mapped = pd.read_csv("mapped_cat_sub.csv")
        # df_unbiased = pd.read_csv("preprocessed_unbiased.csv")[:]  # Limit for testing
        # df_comments = pd.read_csv("comments.csv")[:]
        # df_category = pd.read_csv("category.csv")
        # df_sub_category = pd.read_csv("sub_category.csv")

        return df_mapped, df_unbiased, df_comments, df_sub_category, df_category
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
        del pipeline_v1
        raise
    try:
        pipeline_v1.process_unbiased_data_and_store(mapped_df)
        logger.info("Pipeline_v1 processing unbiased data completed.")
        del pipeline_v1
    except Exception as e:
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


async def run_async_filtered_processor(config):
    # List of output schemas (tables for storing results)
    output_schemas = [AnalysisTableSchema, MappedTableSchemaOut]

    if not db_url:
        logger.error("MYSQL URL is not available.")
        raise

    # Initialize database and agents process
    db = Database(db_url, output_schemas, None)
    comments_db = Database(db_url, [CommentsTableSchemaOut], None)  # HIGHLIGHTED

    # Create AgentManager with all agents registered
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
        # Load data
        (
            df_mapped,
            df_unbiased,
            df_comments,
            df_sub_category,
            df_category,
        ) = await load_all_data(db)

        post_date_unbiased_column_name = "video_posted_timestamp"
        post_date_comments_column_name = "comment_posted_timestamp"
        agent_builder_name = config.agent_builder_name
        risk_levels = config.risk_levels

        print(df_mapped.head())
        print(df_unbiased.head())
        print(df_comments.head())
        print(df_category.head())
        print(df_sub_category.head())

        # Validate columns
        logger.info("Validating columns...")
        validate_columns(
            df_unbiased,
            df_comments,
            post_date_unbiased_column_name,
            post_date_comments_column_name,
            agent_builder_name,
        )

        # Filter by dates
        logger.info("Filtering data by date range...")
        if not config.start_date and not config.end_date:
            filtered_unbiased = df_unbiased
            filtered_comments = df_comments
        else:
            filtered_unbiased = filter_by_date(
                df_unbiased,
                config,
                post_date_unbiased_column_name,
            )
            filtered_comments = filter_by_date(
                df_comments,
                config,
                post_date_comments_column_name,
            )

        print(filtered_unbiased.empty)
        print(df_mapped.empty)

        # Raise the custom exception
        if filtered_unbiased.empty:
            logger.warning("No data found after filtering!")
            logger.info("Triggering crawler to update data.")
            raise NoDataFoundException

        # Apply category and subcategory filters
        logger.info("Applying category and subcategory filters...")
        if not config.category and not config.subcategory:
            filtered_unbiased = filtered_unbiased
            filtered_mapped = df_mapped
            filtered_comments = filtered_comments
        else:
            filtered_unbiased, filtered_mapped = apply_filters(
                filtered_unbiased,
                df_mapped,
                df_sub_category,
                df_category,
                config,
            )
            filtered_comments = filtered_comments[
                (df_comments["category"] == config.category)
                & (df_comments["subcategory"] == config.subcategory)
            ]

        print(filtered_unbiased.empty)
        print(filtered_mapped.empty)
        print(filtered_comments.empty)
        print("^^^^^^^^^^^^^^^^^^^^")
        unbiased_unique_video_ids = len(df_unbiased["video_id"].unique())
        print(unbiased_unique_video_ids)
        mapped_unique_video_ids = len(df_mapped["video_id"].unique())
        print(mapped_unique_video_ids)
        print(len(filtered_unbiased))
        print(len(filtered_mapped))
        print(len(filtered_comments))
        print("^^^^^^^^^^^^^^^^^^^^")

        # Raise the custom exception
        if filtered_unbiased.empty or filtered_mapped.empty:
            logger.warning("No data found after filtering!")
            logger.info("Triggering crawler to update data.")
            raise NoDataFoundException

        comment_key_id = "comment_mongodb_id"

        # Run pipeline concurrently (you can uncomment the second pipeline when it's needed)
        await asyncio.gather(
            run_filtering_pipeline_for_analysis(
                agentsprocess,
                db,
                filtered_unbiased,
                filtered_mapped,
                config,
            ),
            run_filtering_pipeline_for_comments(
                agentsprocess,
                comments_db,
                filtered_comments,
                config,
            ),
        )

    except Exception as e:
        logger.error(f"Error in run_async_filtered_processor: {e}")
        raise  # Re-raise the exception to propagate it to process_status
    finally:
        # Ensure the database is closed even if an error occurs
        db.close()
        comments_db.close()
        logger.info("Database connection closed.")

    logger.info("Running filter processor completed.")
