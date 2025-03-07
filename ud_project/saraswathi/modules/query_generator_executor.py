import traceback

from fastapi import HTTPException, APIRouter
from time import perf_counter
from dotenv import load_dotenv
from openai import OpenAI
from typing import Dict, Any
from components.datamodel import DataSummary
from components.summarizer import (
    summarize,
)
from components.utils import (
    get_env_variable,
)
from components.sql_query import generate_sql_query
from components.executor import execute_sql_query
from components.postprocess import postprocess_chart_data
from qdrant_client import QdrantClient
from logging_library.applogger.log_manager import LogManager

load_dotenv()

router = APIRouter()

# Fetch and validate environment variables
mixtral_8x7b_llm_url: str = get_env_variable(
    "LLAMA70B_LLM_BASE_URL", "LLM URL is not provided!"
)
mixtral_8x7b_llm_api_key: str = get_env_variable(
    "LLAMA70B_LLM_API_KEY", "LLM API is not provided!"
)
embedding_model_url: str = get_env_variable(
    "EMBEDDING_BASE_URL", "EMBEDDING API is not provided!"
)
qdrant_host: str = get_env_variable("QDRANT_HOST", "Qdrant host is not provided!")
qdrant_api_key: str = get_env_variable(
    "QDRANT_API_KEY", "Qdrant API key is not provided!"
)
table_collection: str = get_env_variable(
    "QDRANT_TABLE_COLLECTION", "Table collection is not provided!"
)
column_collection: str = get_env_variable(
    "QDRANT_COLUMN_COLLECTION", "Column collection is not provided!"
)
logging_url: str = get_env_variable("LOGGING_URL", "Logging URL is not provided!")
code_level_logger_name: str = get_env_variable(
    "CODE_LEVEL_LOGGER_NAME", "CODE LEVEL LOGGER NAME is not provided!"
)

llama70b_client = OpenAI(
    base_url=mixtral_8x7b_llm_url, api_key=mixtral_8x7b_llm_api_key
)

qdrant_client = QdrantClient(url=qdrant_host, api_key=qdrant_api_key)


@router.post("/query_generator_executor")
def query_generator_executor(
    user_intent: str,
    database_name: str,
    table_name: str,
    db_tag: str,
    session_id: str,
):
    if not isinstance(user_intent, str):
        raise HTTPException(
            status_code=500,
            detail="User intent format is not valid. Must be in 'str' format!",
        )

    if not isinstance(database_name, str):
        raise HTTPException(
            status_code=500,
            detail="Database name format is not valid. Must be in 'str' format!",
        )

    if not isinstance(table_name, str):
        raise HTTPException(
            status_code=500,
            detail="Table name format is not valid. Must be in 'str' format!",
        )

    if not isinstance(db_tag, str):
        raise HTTPException(
            status_code=500,
            detail="Database identifier format is not valid. Must be in 'str' format!",
        )

    code_level_logger = LogManager(session_id=session_id).get_logger_by_name(
        code_level_logger_name
    )

    try:
        start_query_generator_executor = perf_counter()

        start_summary = perf_counter()

        for trial in range(2):
            try:
                data_summary: DataSummary = summarize(
                    qdrant_client,
                    database_name,
                    db_tag,
                    table_collection,
                    column_collection,
                    table_name,
                    embedding_model_url,
                    logging_url,
                    session_id,
                    code_level_logger,
                )
                break
            except Exception:
                print(traceback.format_exc())

        summary_inference_time = perf_counter() - start_summary
        print(f"Summary Inference Time: {summary_inference_time}")

        story_question: Dict[str, Any] = {
            "main_instruction": user_intent,
            "main_chart_type": "table_chart",
            "main_chart_category": "",
            "main_chart_timeframe": "",
            "main_chart_duration": "",
            "chart_id": None,
            "sub_questions": [],
            "main_chart_axis": {
                "xAxis_title": "all",
                "xAxis_column": "all",
                "yAxis_title": "all",
                "yAxis_column": "all",
            },
        }

        chart_axis = story_question.get("main_chart_axis", {})

        start_sql = perf_counter()
        # Generate Chart SQL
        chart_sql = generate_sql_query(
            llama70b_client,
            data_summary,
            story_question,
            {},
            [],
            database_name,
            table_name,
            logging_url,
            session_id,
            code_level_logger,
        )
        chart_sql_inference_time = perf_counter() - start_sql
        print(f"Story Chart SQLs Inference Time: {chart_sql_inference_time}")

        start_sql_exec = perf_counter()
        # Execute Chart SQL
        chart_data = execute_sql_query(
            llama70b_client,
            data_summary,
            {},
            [],
            database_name,
            table_name,
            chart_sql,
            data_summary.sql_library,
            data_summary.database_properties,
            chart_axis,
            logging_url,
            session_id,
            code_level_logger,
        )
        chart_sql_execution_time = perf_counter() - start_sql_exec
        print(f"Story Chart SQLs Execution Time: {chart_sql_execution_time}")

        start_postprocess_data = perf_counter()
        # Execute Chart SQL
        chart_data = postprocess_chart_data(
            chart_data,
            session_id,
            code_level_logger,
        )
        chart_postprocess_data_time = perf_counter() - start_postprocess_data
        print(f"Story Chart Data Postprocess Time: {chart_postprocess_data_time}")

        chart_query = chart_data.get("main_chart_sql")
        data_dict = chart_data.get("chart_data", {})

        json_data = data_dict.to_dict(orient="records")

        response = {"Chart_Query": chart_query, "data": json_data}

        query_generator_executor_inference_time = (
            perf_counter() - start_query_generator_executor
        )
        print(
            f"Question Answering Inference Time: {query_generator_executor_inference_time}"
        )

        return response

    except Exception:
        raise HTTPException(
            status_code=500, detail="An error occurred while processing the request."
        )
