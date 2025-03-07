import asyncio
import os
import json
import traceback
from datetime import datetime
from typing import Dict, Optional
from urllib.parse import quote_plus
import uuid
import uvicorn
from celery import Celery
from celery.result import AsyncResult
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from fastapi.middleware.cors import CORSMiddleware
from fastapi import Form
from pydantic import BaseModel, field_validator

from agents.Agents import (
    AgentsNameV0,
    CategoryAgent,
    CommentRiskAgent,
    JustificationAgent,
    LawRegulatedAgent,
    SentimentAgent,
    SummaryAgent,
)

from select_app import run_async_select_processor_v0
from direct_batch_app import *
from filter_batch_app import *
from log_mongo import logger
from schema.input_schemas import TikTokTableSchemaIn
from schema.output_schemas import TikTokTableSchemaOut

load_dotenv()

# Fetch Redis configuration from environment variables
redis_host = os.getenv("redis_host")
redis_port = os.getenv("redis_port")
redis_db = os.getenv("redis_db")
redis_password = os.getenv("redis_password")

# Redis URL
redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"

# MySQL configuration
mysql_user = os.getenv("mysql_user")
mysql_password = os.getenv("mysql_password")
mysql_host = os.getenv("mysql_host")
mysql_port = os.getenv("mysql_port")
input_mysql_database = os.getenv("mysql_database")
output_mysql_database = os.getenv("output_mysql_database")

db_url = f"mysql+pymysql://{mysql_user}:{quote_plus(mysql_password)}@{mysql_host}:{mysql_port}/{input_mysql_database}"

api_ip = os.getenv("api_ip")
port_manager = int(os.getenv("port_manager") or 8001)
if not api_ip:
    logger.error("IP address not found")

frontend_url = os.getenv("frontend_url")

# Celery configuration (using Redis as broker and backend)
celery_app = Celery(
    "tasks",
    broker=redis_url,
    backend=redis_url,
)

celery_app.conf.update(
    result_expires=36000,
    task_default_retry_delay=10,  # Delay between retries
    task_max_retries=3, # Max retries for each task
    task_serializer="json",
    accept_content=["json"],
)

# This can help with ensuring tasks are registered
celery_app.conf.task_routes = {
    'tasks.process_direct_task': {'queue': 'default'},
    'tasks.process_filter_task': {'queue': 'default'}
}

# FastAPI app initialization
app = FastAPI()

# Health check endpoint for AWS Load Balancer
@app.get("/health")
async def health_check():
    return {"status": "healthy"}




# Endpoint to get task status
@app.get("/task_status/{task_id}")
async def get_task_status(task_id: str):
    try:
        # Fetch task result using Celery's AsyncResult
        task_result = AsyncResult(task_id, app=celery_app)
        
        # Check task status and return appropriate response
        if task_result.state == 'STARTED':
            return {"status": "Task started"}
        elif task_result.state == 'SUCCESS':
            return {"status": "Task completed", "result": task_result.result}
        elif task_result.state == 'FAILURE':
            return {"status": "Task failed", "result": str(task_result.result)}
        else:
            return {"status": f"Task is in state {task_result.state}"}
    except Exception as e:
        logger.error(f"Error fetching task status: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching task status: {e}")






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
    def __init__(self, files_name, start_date, end_date, category, subcategory, risk_levels, agent_builder_name):
        self.files_name = files_name
        self.start_date = start_date
        self.end_date = end_date
        self.category = category
        self.subcategory = subcategory
        self.risk_levels = risk_levels
        self.agent_builder_name = agent_builder_name

    def to_dict(self):
        # Convert object to dictionary for serialization
        return {
            'files_name': self.files_name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'category': self.category,
            'subcategory': self.subcategory,
            'risk_levels': self.risk_levels,
            'agent_builder_name': self.agent_builder_name
        }

    @classmethod
    def from_dict(cls, data):
        # Convert dictionary back to object
        return cls(
            files_name=data['files_name'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            category=data['category'],
            subcategory=data['subcategory'],
            risk_levels=data['risk_levels'],
            agent_builder_name=data['agent_builder_name']
        )

class PostDate(BaseModel):
    start_date: Optional[str] = None  # Optional, defaults to None
    end_date: Optional[str] = None  # Optional, defaults to None

    @field_validator("start_date", "end_date", mode="before")
    def validate_date(cls, value):
        if not value or value.strip().lower() == "string":
            return None  # Treat invalid or empty values as None
        try:
            # Parse the date to ensure it's valid
            datetime.strptime(value, "%Y-%m-%d")  # Adjust format as needed
            return value
        except ValueError:
            return None  # Treat invalid dates as None



class TableConfig:
    def __init__(self, table_source_name, table_target_name):
        self.table_source_name = table_source_name
        self.table_target_name = table_target_name
    
    def to_dict(self):
        return {
            'table_source_name': self.table_source_name,
            'table_target_name': self.table_target_name
        }
    @classmethod
    def from_dict(cls, dict_data):
        return cls(dict_data['table_source_name'], dict_data['table_target_name'])
    



class Filters(BaseModel):
    files_name: Optional[List[str]] = []  # Optional, defaults to an empty list
    risk_levels: Optional[Dict] = {}  # Optional, defaults to an empty dictionary
    category: Optional[str] = "Scam"  # Optional, defaults to None
    subcategory: Optional[str] = "Forex"  # Optional, defaults to None
    post_date: Optional[PostDate] = None  # Optional, defaults to None
    agent_builder_name: Optional[str] = None  # Optional, defaults to None


class AppConfig:
    host: str = api_ip
    port: int = port_manager
    sleep_time: int = 1


class CrawlerConfig:
    host: str = "localhost"
    port: int = "8000"
    endpoint_name: str = "crawling"


# Define a request body for the endpoint
class TriggerRequest(BaseModel):
    trigger: str




origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    # f"http://{api_ip}:{port_manager}",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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





def check_required_fields(filters):
    required_fields = ['risk_levels', 'category', 'subcategory', 'agent_builder_name']
    
    for field in required_fields:
        value = getattr(filters, field, None)  # Get the value of the field

        if isinstance(value, dict) and not value:
            raise ValueError(f"The field '{field}' is empty.")
        
        # Check if value is None or empty
        if not value:
            raise ValueError(f"The field '{field}' is missing or empty.")
        
        # Additional check for empty lists or dicts (for fields that can be lists or dicts)
        if isinstance(value, (list, dict)) and len(value) == 0:
            raise ValueError(f"The field '{field}' is empty.")
    return True


# @celery_app.task(bind=True, name="tasks.process_filter_task")
# def process_filter_task(self, task_id, config):
def process_filter_task(task_id, config):
    """Process filter task asynchronously."""
    try:
        # Update task status to 'Started'
        # self.update_state(state="STARTED", meta={"status": "Started"})
        logger.info(f"Task {task_id} status set to 'Started'")

        logger.info(f"Processing filter task {task_id} with config: {config}")

        try:
            config_data = json.loads(config)
            config = FilterInputConfig.from_dict(config_data)

            # Run the filter processor asynchronously
            # loop = asyncio.get_event_loop()
            # asyncio.ensure_future(run_async_filtered_processor(config))
            run_filtered_processor(config)

        except Exception as e:
            error_message = f"Failed: {str(e)}"
            # self.update_state(state="FAILURE", meta={"status": error_message})
            logger.error(error_message, exc_info=True)
            traceback.print_exc()
            raise traceback.print_exc()
        finally:
            try:
                loop.close()
            except:
                pass

        # Update task status to 'Completed'
        # self.update_state(state="SUCCESS", meta={"status": "Completed"})
        logger.info(f"Task {task_id} completed successfully.")

    except Exception as e:
        error_message = f"Unexpected failure: {str(e)}"
        # self.update_state(state="FAILURE", meta={"status": error_message})
        logger.error(error_message, exc_info=True)
        traceback.print_exc()
        # raise self.retry(exc=e)  # Ensure retry on failure with the correct exception
        raise traceback.print_exc()


@app.post("/yankechil_processor/filter_preproceed_data")
async def yankechil_processor_filter_preproceed_data(filters: Filters):
    """API endpoint to filter the preprocessed data."""
    try:
        # Log the raw filters object to inspect the data
        logger.info(f"Received filters: {filters}")

        # Extract values safely
        start_date = filters.post_date.start_date
        end_date = filters.post_date.end_date
        files_name = filters.files_name or [
            "Penal_Code.json.law_document.extraction.test",
            "akta-15-akta-hasutan-1948.v1.en.law_document",
        ]
        check_required_fields(filters)
        risk_levels = filters.risk_levels
        category = filters.category
        subcategory = filters.subcategory
        agent_builder_name = filters.agent_builder_name

    except AttributeError as e:
        logger.error(f"Error extracting input values from frontend: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid input format: {e!s}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {e!s}",
        )

    try:
        # Create a config object for filtering
        config = FilterInputConfig(
            files_name=files_name,
            start_date=start_date,
            end_date=end_date,
            category=category,
            subcategory=subcategory,
            risk_levels=risk_levels,
            agent_builder_name=agent_builder_name,
        )
    except Exception as e:
        logger.error(f"Error creating FilterInputConfig: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating filter configuration: {e!s}",
        )

    try:
        # Generate a unique task ID
        task_id = str(uuid.uuid4())

        config_json = json.dumps(config.to_dict())

        # Enqueue the filter task to Celery
        # process_filter_task.apply_async(args=[task_id, config_json], task_id=task_id, queue='default')
        process_filter_task(task_id, config_json)

        # Respond immediately while the task runs in the background
        return {"message": "Filter task is being processed in the background.", "task_id": task_id}

    except Exception as e:
        logger.error(f"Error processing filtering api: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing filtering api: {e!s}")



@celery_app.task(bind=True, name="tasks.process_direct_task")
def process_direct_task(self, task_id, table_config):
    """Process the direct task asynchronously."""
    try:
        self.update_state(state="STARTED", meta={"status": "Started"})
        logger.info(f"Processing direct task {task_id} with config: {table_config}")

        try:
            table_config_dict = json.loads(table_config)  # Deserialize back to dictionary
            # Reconstruct the original TableConfig object
            table_config = TableConfig.from_dict(table_config_dict)
            loop = asyncio.get_event_loop()
            future = loop.create_task(run_async_direct_processor_v0(table_config))
            loop.run_until_complete(future)

            # loop = asyncio.get_event_loop()
            # if loop.is_running():
            #     # Directly schedule the async function using ensure_future
            #     asyncio.ensure_future(run_async_direct_processor_v0(table_config))
            # else:
            #     # Fallback to running the task in an event loop if not running
            #     asyncio.run(run_async_direct_processor_v0(table_config))

        except Exception as e:
            error_message = f"Failed: {str(e)}"
            self.update_state(state="FAILURE", meta={"status": error_message})
            logger.error(f"Error in run_async_direct_processor_v0 for task {task_id}: {e}", exc_info=True)
            raise self.retry(exc=e)
            return

        self.update_state(state="SUCCESS", meta={"status": "Completed"})
        logger.info(f"Task {task_id} completed successfully.")

    except Exception as e:
        error_message = f"Unexpected failure: {str(e)}"
        self.update_state(state="FAILURE", meta={"status": error_message})
        logger.error(f"Unexpected error during processing direct task {task_id}: {e}", exc_info=True)
        raise self.retry(exc=e)





@app.get("/yankechil_processor/direct_preproceed_data")
async def yankechil_processor_trigger_preproceed_data():
    try:
        # Log the attempt to create the table config
        logger.info("Creating TableConfig for TikTok processor.")

        # Ensure the correct initialization of TableConfig
        table_config = TableConfig(
            TikTokTableSchemaIn.__tablename__,
            TikTokTableSchemaOut.__tablename__,
        )
        logger.info(f"TableConfig created: {table_config}")  # Log the table_config for debugging
    
        # Generate a unique task ID
        task_id = str(uuid.uuid4())

        # Log task ID and process initiation
        logger.info(f"Enqueuing direct task with task ID {task_id} to Celery.")

        table_config_dict = table_config.to_dict()
        task_data = json.dumps(table_config_dict)  
        # Enqueue the direct task to Celery
        process_direct_task.apply_async(args=[task_id, task_data], task_id=task_id, queue='default')

        # Respond immediately while the task runs in the background
        logger.info(f"Task {task_id} is now processing in the background.")
        return {"message": "Direct task is being processed in the background.", "task_id": task_id}

    except Exception as e:
        # Log any errors that occur during the task initiation
        logger.error(f"Error in direct agent API: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing direct agent API: {e!s}")



class ParsedInputs(BaseModel):
    agent_name: str
    input_table_name: str
    output_table_name: str
    input_columns_name: List[str]
    database_name: str
    row_start: int
    row_end: int
    merge_key: str


@app.post("/yankechil_processor/select_agent")
async def yankechil_processor_select_agent(
    agent_name: str = Form(...),
    input_table_name: str = Form(...),
    output_table_name: str = Form(...),
    input_columns_name: List[str] = Form(...),  # Accepts multiple values for this field
    database_name: str = Form(...),
    row_start: Optional[int] = Form(None),  # Optional row_start, default is None
    row_end: Optional[int] = Form(None),    # Optional row_end, default is None
    merge_key: str = Form(...),
):
    try:
        # Convert comma-separated string to list for `input_columns_name`
        # input_columns_name = input_columns_name.split(",")
        parsed_inputs = ParsedInputs(
            agent_name=agent_name,
            input_table_name=input_table_name,
            output_table_name=output_table_name,
            input_columns_name=input_columns_name,
            database_name=database_name,
            row_start=row_start,
            row_end=row_end,
            merge_key=merge_key,
        )
    except Exception as e:
        logger.error(f"Error creating select agent configuration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating select agent configuration: {e!s}",
        )
    try:
        return await run_async_select_processor_v0(parsed_inputs)
    except Exception as e:
        logger.error(f"Error processing select agent api: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing select agent api: {e!s}")




@app.get("/healthz", response_class=JSONResponse)
async def healthz() -> dict:
    """Health check endpoint to verify the application's status.
    Returns a 200 OK status with a message if the app is healthy.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host=AppConfig.host, port=AppConfig.port)
