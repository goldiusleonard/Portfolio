import os
import uuid

from datetime import datetime
from typing import Dict, Optional, List
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()


@router.get("/")
def root(response: Response):
    """The function sets response headers for cache control and CORS, and returns a message indicating
    that the Logging API is ready to be used.

    :param response: The `response` parameter in the `root` function is an object that represents the
                     HTTP response that will be sent back to the client. In this case, the code is
                     setting various headers on the response object before returning a JSON response
                     with the message that the Logging API can be used.
    :type response: Response
    :return: A message indicating that the Logging API is ready for use.
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = "0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"

    return {"message": "Logging API is ready to be used!"}


class LogInsight_Chart(BaseModel):
    chart_id: Optional[str] = None
    visual_description: Optional[str] = None
    business_recommendation: Optional[str] = None
    visual_story: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.now)


class LogEntry_Chart(BaseModel):
    chart_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_time: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    user_query: Optional[str] = None
    narrative: Optional[str] = None
    question: Optional[str] = None
    time_frame: Optional[str] = None
    time_duration: Optional[str] = None
    chart_name: Optional[str] = None
    chart_title: Optional[str] = None
    chart_category: Optional[str] = None
    chart_type: Optional[str] = None
    chart_position: Optional[int] = None
    chart_axis: Optional[str] = None
    sql_query: Optional[str] = None
    status: Optional[str] = None
    chart_json: Optional[str] = None
    module_version: Optional[str] = None
    total_inference_time: Optional[float] = None
    table_name: Optional[str] = None


class LogEntry_LLMcalls(BaseModel):
    chart_id: str
    module_id: int
    messages: List[Dict]
    output: str
    inference_time: float
    llm_model: str
    input_tokens: int
    output_tokens: int


def log_chart_insights(log: LogInsight_Chart):
    """Log chart insights into specified MongoDB collection"""
    client = MongoClient(os.getenv("MONGODB_URL"))
    db_name = os.getenv("CHART_INSIGHTS_LOGGING_MONGODB_DATABASE", "")

    if db_name == "":
        raise ValueError("CHART_INSIGHTS_LOGGING_MONGODB_DATABASE is invalid!")

    collection_name = os.getenv("CHART_INSIGHTS_LOGGING_MONGODB_COLLECTION", "")
    if collection_name == "":
        raise ValueError("CHART_INSIGHTS_LOGGING_MONGODB_COLLECTION is invalid!")

    try:
        db = client.get_database(db_name)

        if collection_name not in db.list_collection_names():
            db.create_collection(collection_name)

        collection = db[collection_name]
        update_data = log.model_dump(exclude_unset=True)

        if log.chart_id is None:
            raise HTTPException(status_code=400, detail="chart_id is required")

        existing_log = collection.find_one({"chart_id": log.chart_id})

        if existing_log is None:
            collection.insert_one(update_data)
        else:
            if isinstance(log, LogInsight_Chart):
                if "chart_id" in update_data:
                    existing_log["chart_id"] = update_data["chart_id"]
                if "visual_description" in update_data:
                    existing_log["visual_description"] = update_data[
                        "visual_description"
                    ]
                if "business_recommendation" in update_data:
                    existing_log["business_recommendation"] = update_data[
                        "business_recommendation"
                    ]
                if "visual_story" in update_data:
                    existing_log["visual_story"] = update_data["visual_story"]
            existing_log["last_updated"] = datetime.now()
            collection.update_one({"chart_id": log.chart_id}, {"$set": existing_log})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "status": "Success",
        "chart_id": log.chart_id,
        "message": "Chart insight log entry created successfully.",
        "timestamp": existing_log.get("request_time", datetime.now()),
    }


def log_entry_chart(log: LogEntry_Chart):
    """Log an entry into the specified MongoDB collection or update an existing one based on chart_id.

    This endpoint accepts log entry details and stores them in a specified MongoDB collection.
    It can either create a new log entry for a new chart_id or update an existing entry if it already exists.

    :param chart_id: The unique identifier for the chart being logged.
    :param log: The log entry containing details like time of request, user ID, user query,
                narrative generated, questions generated, chart types, titles, SQL queries, and prompts.
    :type chart_id: str
    :type log: LogEntry
    :raises HTTPException: If there is an error during logging.
    :return: A dictionary indicating the status of the logging operation, including the chart ID,
             message, and timestamp.
    """
    client = MongoClient(os.getenv("MONGODB_URL"))
    db_name = os.getenv("CHART_LOGGING_MONGODB_DATABASE", "")

    if db_name == "":
        raise ValueError("CHART_LOGGING_MONGODB_DATABASE is invalid!")

    collection_name = os.getenv("CHART_LOGGING_MONGODB_COLLECTION", "")

    if collection_name == "":
        raise ValueError("CHART_LOGGING_MONGODB_COLLECTION is invalid!")

    try:
        db = client.get_database(db_name)

        if collection_name not in db.list_collection_names():
            db.create_collection(collection_name)

        collection = db[collection_name]
        update_data = log.model_dump(exclude_unset=True)

        if log.chart_id is None:
            log_data = log.model_dump()
            log_data["last_updated"] = datetime.now()
            log_data["chart_id"] = str(uuid.uuid4())
            log_data["status"] = "Failed"

            collection.insert_one(log_data)

            return {
                "status": "Success",
                "chart_id": log_data["chart_id"],
                "message": "Log entry created successfully.",
                "timestamp": log_data.get("request_time", datetime.now()),
            }
        existing_log = collection.find_one({"chart_id": log.chart_id})
        if isinstance(log, LogEntry_Chart):
            if "user_id" in update_data:
                existing_log["user_id"] = update_data["user_id"]

            if "session_id" in update_data:
                existing_log["session_id"] = update_data["session_id"]

            if "user_query" in update_data:
                existing_log["user_query"] = update_data["user_query"]

            if "narrative" in update_data:
                existing_log["narrative"] = update_data["narrative"]

            if "question" in update_data:
                existing_log["question"] = update_data["question"]

            if "time_frame" in update_data:
                existing_log["time_frame"] = update_data["time_frame"]

            if "time_duration" in update_data:
                existing_log["time_duration"] = update_data["time_duration"]

            if "chart_name" in update_data:
                existing_log["chart_name"] = update_data["chart_name"]

            if "chart_title" in update_data:
                existing_log["chart_title"] = update_data["chart_title"]

            if "chart_category" in update_data:
                existing_log["chart_category"] = update_data["chart_category"]

            if "chart_type" in update_data:
                existing_log["chart_type"] = update_data["chart_type"]

            if "chart_position" in update_data:
                existing_log["chart_position"] = update_data["chart_position"]

            if "chart_axis" in update_data:
                existing_log["chart_axis"] = update_data["chart_axis"]

            if "sql_query" in update_data:
                existing_log["sql_query"] = update_data["sql_query"]

            if "status" in update_data:
                existing_log["status"] = update_data["status"]

            if "chart_json" in update_data:
                existing_log["chart_json"] = update_data["chart_json"]

            if "module_version" in update_data:
                existing_log["module_version"] = update_data["module_version"]

            if "total_inference_time" in update_data:
                existing_log["total_inference_time"] = update_data[
                    "total_inference_time"
                ]

        existing_log["last_updated"] = datetime.now()

        collection.update_one({"chart_id": log.chart_id}, {"$set": existing_log})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    client.close()

    return {
        "status": "Updated",
        "chart_id": log.chart_id,
        "message": "Log entry updated successfully.",
        "timestamp": existing_log.get("request_time", datetime.now()),
    }


def log_entry_LLMcalls(log: LogEntry_LLMcalls):
    """
    Log an entry into the specified MongoDB collection or update an existing one based on chart_id.

    This endpoint accepts log entry details and stores them in a specified MongoDB collection.
    It can either create a new log entry for a new chart_id or update an existing entry if it already exists.

    :param chart_id: The unique identifier for the chart being logged.
    :param log: The log entry containing details like time of request, user ID, user query,
                narrative generated, questions generated, chart types, titles, SQL queries, and prompts.
    :type chart_id: str
    :type log: LogEntry
    :raises HTTPException: If there is an error during logging.
    :return: A dictionary indicating the status of the logging operation, including the chart ID,
             message, and timestamp.
    """
    client = MongoClient(os.getenv("MONGODB_URL"))
    db_name = os.getenv("CHART_LLM_CALL_LOGGING_MONGODB_DATABASE")
    collection_name = os.getenv("CHART_LLM_CALL_LOGGING_MONGODB_COLLECTION")

    try:
        db = client.get_database(db_name)

        if collection_name not in db.list_collection_names():
            db.create_collection(collection_name)

        collection = db[collection_name]

        log_data = log.model_dump()
        log_data["request_time"] = datetime.now()
        collection.insert_one(log_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    client.close()

    return {
        "status": "Success",
        "chart_id": log.chart_id,
        "message": "LLM call log entry created successfully.",
        "timestamp": log_data.get("request_time", datetime.now()),
    }


@router.post("/chart")
def log_chart_entry(log: LogEntry_Chart):
    result = log_entry_chart(log)
    return result


@router.put("/chart-llm-calls")
def log_chart_LLMcalls_entry(log: LogEntry_LLMcalls):
    result = log_entry_LLMcalls(log)
    return result


@router.put("/insights")
def log_chart_insights_entry(log: LogInsight_Chart):
    result = log_chart_insights(log)
    return result


@router.get("/module-id/{module_id}")
def get_module_by_id(module_id: int):
    """Retrieve module details by its ID.
    :param module_id: The unique identifier for the module.
    :return: A dictionary containing the module_id and module_name.
    :raises HTTPException: If the module ID is not found.
    """
    client = MongoClient(os.getenv("MONGODB_URL"))
    db_name = os.getenv("CHART_LLM_CALL_MODULE_MONGODB_DATABASE")
    collection_name = os.getenv("CHART_LLM_CALL_MODULE_MONGODB_COLLECTION")

    try:
        db = client.get_database(db_name)

        if collection_name not in db.list_collection_names():
            db.create_collection(collection_name)

        collection = db[collection_name]
        module = collection.find_one({"module_id": module_id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    client.close()

    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    return {"module_id": module["module_id"], "module_name": module["module_name"]}


@router.get("/module-name/{module_name}")
def get_module_by_name(module_name: str):
    """Retrieve module details by its name.
    :param module_name: The name of the module to retrieve.
    :return: A dictionary containing the module_id and module_name.
    :raises HTTPException: If the module name is not found.
    """
    client = MongoClient(os.getenv("MONGODB_URL"))
    db_name = os.getenv("CHART_LLM_CALL_MODULE_MONGODB_DATABASE")
    collection_name = os.getenv("CHART_LLM_CALL_MODULE_MONGODB_COLLECTION")

    try:
        db = client.get_database(db_name)

        if collection_name not in db.list_collection_names():
            db.create_collection(collection_name)

        collection = db[collection_name]
        module = collection.find_one({"module_name": module_name})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    client.close()

    return {"module_id": module["module_id"], "module_name": module["module_name"]}


@router.get("/chart/{chart_id}")
def get_data_from_logs(chart_id: str):
    """
    Retrieve log data for a specific chart by its ID.

    :param chart_id: The unique identifier of the chart for which to retrieve data.
    :return: A dictionary containing the `chart_id` and associated chart data.
    :raises HTTPException: If data for the provided chart_id is not found.
    """
    client = MongoClient(os.getenv("MONGODB_URL"))
    db_name = os.getenv("CHART_LOGGING_MONGODB_DATABASE")
    collection_name = os.getenv("CHART_LOGGING_MONGODB_COLLECTION")

    try:
        db = client.get_database(db_name)

        if collection_name not in db.list_collection_names():
            db.create_collection(collection_name)

        collection = db[collection_name]

        result = collection.find_one({"chart_id": chart_id})

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Data not found for the provided chart_id",
            )

        result.pop("_id", None)

    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")

    client.close()

    return {"chart_id": chart_id, "chart_data": result}
