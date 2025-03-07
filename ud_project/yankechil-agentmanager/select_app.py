import os
from typing import List
from urllib.parse import quote_plus

from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from sqlalchemy import (
        Column,
        Integer,
        Float,
        Boolean,
        String,
        Text,
    )
from db.db import Database

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
from processing.pipeline_select import DataProcessorPipeline_v00
from db.db import Base

# Base = declarative_base()


load_dotenv()

mysql_user = os.getenv("mysql_user")
mysql_password = os.getenv("mysql_password")
mysql_host = os.getenv("mysql_host")
input_mysql_database = os.getenv("mysql_database")
output_mysql_database = os.getenv("output_mysql_database")

db_url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}/{input_mysql_database}"


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


# Function to create a dynamic table schema
def create_dynamic_table(
    table_name: str, column_names: List[str], column_types: List[str], merge_key:str
):
    # Define the dynamic class with the table name and columns
    class DynamicTable(Base):
        __tablename__ = table_name
        __table_args__ = {'extend_existing': True}  # Allow redefining the table if it already exists

        # Create the primary key column '_id' for all tables
        locals()[merge_key] = Column(String(255), primary_key=True)

        # Define a mapping for column types
        type_mapping = {
            "string": String(255),
            "text": Text,
            "integer": Integer,
            "float": Float,
            "boolean": Boolean,
        }

        # Iterate through the column names and types to dynamically create columns
        for column_name, column_type in zip(column_names, column_types):
            # Get the appropriate SQLAlchemy column type
            column_type = type_mapping.get(
                column_type.lower(), String(255)
            )  # Default to String(255) if not found
            locals()[column_name] = Column(column_type)

    # Debug: Ensure DynamicTable is registered with Base
    logger.debug(f"DynamicTable created with __tablename__: {DynamicTable.__tablename__}")
    logger.debug(f"DynamicTable's __class__: {DynamicTable.__class__}")
    logger.debug(f"DynamicTable bases: {DynamicTable.__bases__}")

   # Ensure the dynamic table is registered with Base
    return DynamicTable



# Select relevant columns from the DataFrame based on parsed inputs
def filter_columns_from_df(df, merge_key, columns_name):
    columns_name = columns_name[0].split(",")
    logger.info(f"merge_key: {merge_key}")
    logger.info(f"columns_name: {columns_name}")
    # Ensure the merge_key and input columns exist in the DataFrame
    required_columns = [merge_key] + columns_name
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Missing columns: {', '.join(missing_columns)}")

    # Select the required columns from the DataFrame
    selected_columns_df = df[required_columns]
    return selected_columns_df


async def run_async_select_processor_v0(parsed_inputs):
    try:
        batch_size = 100  # Define the batch size
        agent_input_models = ["sentiment", "summary", "category", "comment_risk", "justification", "law_regulated"]

        # Normalize both the parsed agent name and the agent names in the list
        normalized_agent_name = str(parsed_inputs.agent_name).strip().lower()
        normalized_agent_input_models = [x.lower() for x in agent_input_models]

        logger.debug(f"Normalized parsed agent name: {normalized_agent_name}")
        logger.debug(f"Normalized agent input models: {normalized_agent_input_models}")

        if normalized_agent_name not in normalized_agent_input_models:
            logger.error(f"Invalid agent name provided: {parsed_inputs.agent_name}")
            raise HTTPException(status_code=400, detail="Invalid agent name.")

        # Validate database URL components
        if not all([mysql_user, mysql_password, mysql_host, parsed_inputs.database_name]):
            logger.error("Missing database credentials or database name.")
            raise ValueError("Database URL construction failed.")

        # Prepare database URL
        db_url = f"mysql+pymysql://{mysql_user}:{quote_plus(mysql_password)}@{mysql_host}/{parsed_inputs.database_name}"
        if not db_url:
            logger.error("The MySQL URL is not available.")
            raise ValueError("Database URL construction failed.")

        # Define agent-specific configurations
        config = get_agent_config(parsed_inputs.agent_name, parsed_inputs.output_table_name, parsed_inputs.merge_key)
        logger.debug(f"Agent config schemas: {config['schemas']}")

        # Initialize database and agents
        logger.debug(f"Initializing database with schemas: {config['schemas']}")
        db = Database(db_url, config["schemas"], None)
        logger.debug("Creating agent manager.")
        agent_manager = create_agent_manager_v0(agent_configs)
        logger.debug("Creating agent process.")
        agentsprocess = AgentsProcessV0(agent_manager)

        # Load and filter data
        logger.debug("Loading data from the input table...")
        df = await load_data(db, parsed_inputs.input_table_name)
        if df is None or df.empty:
            logger.error("Data could not be loaded or is empty.")
            raise ValueError("Input table data is missing or invalid.")

        # Retrieve max parsed_inputs.merge_key from the output table to ensure processing only rows after that
        logger.debug(f"Retrieving max {parsed_inputs.merge_key} from {parsed_inputs.output_table_name}...")
        max_id_query = text(f"SELECT MAX({parsed_inputs.merge_key}) FROM {parsed_inputs.output_table_name}")

        # Use session.execute to run the query (adjusted for SQLAlchemy session)
        with db.session as session:
            result = session.execute(max_id_query)
            max_id = result.scalar()  # This gets the first column of the first row
            logger.debug(f"Max {parsed_inputs.merge_key} in {parsed_inputs.output_table_name}: {max_id}")

        # Filter the DataFrame to only include rows with parsed_inputs.merge_key > max_id
        if max_id is not None:
            df = df[df[parsed_inputs.merge_key] > max_id]
            logger.debug(f"Filtered DataFrame to {len(df)} rows, after max {parsed_inputs.merge_key}={max_id}.")
        
        # Apply row filtering if specified
        if parsed_inputs.row_start is not None and parsed_inputs.row_end is not None:
            if not isinstance(parsed_inputs.row_start, int) or not isinstance(parsed_inputs.row_end, int):
                logger.error("Row start and end must be integers.")
                raise ValueError("Row start and end must be integers.")
            df = df[parsed_inputs.row_start:parsed_inputs.row_end]

        df = filter_columns_from_df(df, parsed_inputs.merge_key, parsed_inputs.input_columns_name)

        # Log debugging information
        logger.debug(f"Filtered DataFrame: {len(df)} rows.")
        logger.debug(f"Agent Name: {parsed_inputs.agent_name}")

        # Check agent health
        if parsed_inputs.agent_name=="category":
            health_status = agentsprocess.check_agents_health(["Amu"])
        else:
            health_status = agentsprocess.check_agents_health([parsed_inputs.agent_name])
        if not all(health_status.values()):
            logger.error(f"Agent {parsed_inputs.agent_name} is unavailable. Terminating the process.")
            raise SystemExit("Agent health check failed. Process terminated.")

        # Batch processing
        total_rows = len(df)
        logger.debug(f"Processing in batches of {batch_size} rows.")

        # Iterate over the DataFrame in batches
        for start_row in range(0, total_rows, batch_size):
            end_row = min(start_row + batch_size, total_rows)
            batch_df = df.iloc[start_row:end_row]
            
            # Log batch processing details
            logger.debug(f"Processing batch {start_row // batch_size + 1}: Rows {start_row} to {end_row - 1}")

            # Run the pipeline for the batch
            pipeline = DataProcessorPipeline_v00(agentsprocess, db, batch_df)
            agent_pipeline_function = config["pipeline_function"]
            logger.debug(f"Using pipeline function for agent: {parsed_inputs.agent_name}")
            agent_pipeline_function(pipeline, parsed_inputs.merge_key, parsed_inputs)

        logger.info("Pipeline processing completed.")
        return {"status": "success"}

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        if db:
            db.session.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred.")
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        if db:
            db.close()
            logger.info("Database connection closed.")



def get_agent_schema(agent_name):
    """Return agent-specific schema details."""
    schemas = {
        "comment_risk": (["eng_justification", "malay_justification", "risk_status", "irrelevant_score"], ["text", "text", "string", "string"]),
        "summary": (["summary"], ["text"]),
        "justification": (["eng_justification", "malay_justification", "risk_status", "irrelevant_score"], ["text", "text", "string", "string"]),
        "sentiment": (["sentiment", "sentiment_score", "api_sentiment", "api_sentiment_score"], ["string", "float", "string", "float"]),
        "category": (["category", "subcategory"], ["string", "string"]),
        "law_regulated": (["law_regulated"], ["text"]),        
    }
    return schemas.get(agent_name)

def get_agent_pipeline_function(agent_name):
    """Return agent-specific pipeline function."""
    pipelines = {
        "comment_risk": lambda pipeline, merge_key, inputs: pipeline.run_comment_risk_agent_pipeline(merge_key, inputs),
        "summary": lambda pipeline, merge_key, inputs: pipeline.run_summary_agent_pipeline(merge_key, inputs),
        "sentiment": lambda pipeline, merge_key, inputs: pipeline.run_sentiment_agent_pipeline(merge_key, inputs),
        "category": lambda pipeline, merge_key, inputs: pipeline.run_category_agent_pipeline(merge_key, inputs),
        "justification": lambda pipeline, merge_key, inputs: pipeline.run_justification_risk_agent_pipeline(merge_key, inputs),
        "law_regulated": lambda pipeline, merge_key, inputs: pipeline.run_law_agent_pipeline(merge_key, inputs),
    }
    return pipelines.get(agent_name)

def get_agent_config(agent_name, output_table_name, merge_key):
    """Return agent-specific configurations."""
    schema_details = get_agent_schema(agent_name)
    pipeline_function = get_agent_pipeline_function(agent_name)

    if not schema_details or not pipeline_function:
        raise ValueError(f"Invalid agent name: {agent_name}")

    column_names, column_types = schema_details
    # Correct: Passing the class definition itself
    dynamic_table_class = create_dynamic_table(output_table_name, column_names, column_types, merge_key)
    logger.debug(f"Schema class: {type(dynamic_table_class)}")
    return {
        "schemas": [dynamic_table_class],
        "pipeline_function": pipeline_function,
    }

