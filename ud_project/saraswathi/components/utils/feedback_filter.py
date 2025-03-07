import os
import requests
import json
import logging

from typing import List, Tuple, Dict, Any
from pymongo import MongoClient
from fastapi import HTTPException


def fetch_failed_sql_charts(DB_TAG: str, table_name: str) -> List[Dict]:
    """
    Fetches all charts from the MongoDB collection where the status is not "Success".

    Returns:
        List[Dict]: A list of documents (charts) with status not equal to "Success".
    """
    # Connect to MongoDB
    client = MongoClient(os.getenv("MONGODB_URL"))

    try:
        # Access the database and collection
        db = client.get_database(os.getenv("CHART_LLM_CALL_MODULE_MONGODB_DATABASE"))
        collection = db[os.getenv("CHART_LLM_CALL_MODULE_MONGODB_COLLECTION")]

        data = list(
            collection.find(
                {
                    "status": {"$ne": "Success"},
                    "db_tag": DB_TAG,
                    "table_name": table_name,
                }
            )
        )
        # .sort("request_time", -1)
        # .limit(10)
        # )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Ensure the MongoDB connection is closed
        client.close()

    return data


def fetch_feedback(
    param_name: str, param_value: str, code_level_logger: logging.Logger
) -> List[Dict[str, Any]]:
    """
    Calls the API to fetch feedback based on a given parameter and parses the response data.

    Args:
        param_name (str): The name of the parameter (e.g., 'user_query' or 'question').
        param_value (str): The value of the parameter to be searched in the feedback API.

    Returns:
        List[Dict[str, Any]]: A list of parsed dictionaries from the API response.
    """
    # Define the base URL
    base_url = os.getenv("FEEDBACK_BASED_URL", "")

    # Ensure the base URL is properly configured
    if not base_url:
        code_level_logger.error(
            "FEEDBACK_BASED_URL environment variable is not set or empty."
        )
        raise ValueError("FEEDBACK_BASED_URL environment variable is not set or empty.")

    # Construct the full URL dynamically with the parameter name and value
    url = f"{base_url}{param_name}/{param_value}"

    try:
        # Send a GET request to the API
        response = requests.get(url, verify=False)

        # Check if the request was successful
        response.raise_for_status()

        # Parse the response JSON
        raw_data = response.json()

        # Access the 'results' key
        if "results" in raw_data and isinstance(raw_data["results"], list):
            # Process each item in the 'results' list
            parsed_data = []
            for item in raw_data["results"]:
                try:
                    parsed_data.append(
                        json.loads(item) if isinstance(item, str) else item
                    )
                except (json.JSONDecodeError, TypeError):
                    print(f"Skipping invalid item: {item}")
            return parsed_data

        else:
            code_level_logger.error(
                "Unexpected response format: 'results' key is missing or not a list."
            )
            raise ValueError(
                "Unexpected response format: 'results' key is missing or not a list."
            )

    except requests.exceptions.HTTPError as http_err:
        code_level_logger.error(f"HTTP error occurred: {http_err}")
        print(f"HTTP error occurred: {http_err}")
    except ValueError as val_err:
        code_level_logger.error(f"Value error: {val_err}")
        print(f"Value error: {val_err}")
    except Exception as err:
        code_level_logger.error(f"Other error occurred: {err}")
        print(f"Other error occurred: {err}")

    return []


def filter_feedback(
    chart_data: List[Dict[str, Any]], filter_liked: bool = True
) -> List[Dict[str, Any]]:
    """
    Filters chart data based on the 'like' attribute in the 'feedback' section.

    Args:
        chart_data (List[Dict[str, Any]]): A list of chart dictionaries. Each dictionary contains a 'feedback' key with a 'like' attribute.
        filter_liked (bool): If True, filter for liked feedback (like=True). If False, filter for disliked feedback (like=False).

    Returns:
        List[Dict[str, Any]]: A list of filtered charts where 'like' matches the filter_liked value.
    """

    # Initialize list to store filtered chart data
    filtered_charts: list = []

    # Filter chart data based on the 'like' attribute in each chart's feedback section
    for chart in chart_data:
        feedback = chart.get("feedback", {})
        # Normalize 'like' and 'filter_liked' to boolean for comparison
        like_value = feedback.get("like")
        like_value_normalized = str(like_value).lower() == "true"  # Convert to boolean
        filter_liked_normalized = (
            str(filter_liked).lower() == "true"
        )  # Convert to boolean

        if like_value_normalized == filter_liked_normalized:
            filtered_charts.append(
                chart
            )  # Add entire chart data if 'like' matches filter_liked

    return filtered_charts


def filter_by_chart_duration(
    chart_data: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filters chart data based on the 'time_duration' field, separating charts into those with
    non-empty 'time_duration' and those with an empty 'time_duration'.

    Args:
        chart_data (List[Dict[str, Any]]): A list of chart dictionaries, each containing a 'time_duration' field.

    Returns:
        Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: Two lists - (duration_related_samples, non_duration_related_samples)
            - duration_related_samples: Charts where 'time_duration' is not an empty string.
            - non_duration_related_samples: Charts where 'time_duration' is an empty string.
    """

    # Separate charts based on whether 'time_duration' is empty or not
    duration_related_samples = [
        chart for chart in chart_data if chart.get("time_duration")
    ]
    non_duration_related_samples = [
        chart for chart in chart_data if not chart.get("time_duration")
    ]

    return duration_related_samples, non_duration_related_samples


def filter_feedback_by_options(
    charts: List[Dict[str, Any]],
    feedback_fields: List[str],
    code_level_logger: logging.Logger,
) -> List[Dict[str, Any]]:
    """
    Filters charts to include only those that have selected options or 'other' fields in specified feedback fields.

    Args:
        charts (List[Dict[str, Any]]): A list of chart dictionaries, each containing a 'feedback' section.
        feedback_fields (List[str]): A list of feedback field names to check for 'selected_options' or 'other'.

    Returns:
        List[Dict[str, Any]]: A list of charts where any of the specified feedback fields have 'selected_options' or 'other' populated.
    """
    if not feedback_fields:
        code_level_logger.error("feedback_fields cannot be empty")
        raise ValueError("feedback_fields cannot be empty")

    filtered_charts: list = []

    for chart in charts:
        feedback = chart.get("feedback", {})

        # Check for 'selected_options' or 'other' in any of the specified feedback fields
        has_feedback = any(
            feedback.get(field, {}).get("selected_options")
            or feedback.get(field, {}).get("other")
            for field in feedback_fields
        )

        # If any feedback field meets the condition, include this chart in the result
        if has_feedback:
            filtered_charts.append(chart)
        else:
            # Optionally log or handle the case where no valid feedback exists
            pass

    return filtered_charts
