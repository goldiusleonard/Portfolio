import pytest
from fastapi.testclient import TestClient
from mongomock import MongoClient as MockMongoClient
from unittest.mock import patch, mock_open, MagicMock
import os
from dotenv import load_dotenv
from modules.api_logging_and_modules.log_api_modules import (
    setup_modules,
    read_module_ids_from_env,
    insert_modules_into_mongo,
)
from main import app

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)


@pytest.fixture(autouse=True)
def set_env_and_mock_mongo(monkeypatch):
    """Automatically mock environment variables and MongoDB client for all tests."""
    load_dotenv()
    monkeypatch.setattr(
        "pymongo.MongoClient", lambda *args, **kwargs: MockMongoClient()
    )
    monkeypatch.setenv("ENV_FILE_PATH", ".env")
    yield


client = TestClient(app)


def test_root():
    """Test the root endpoint."""
    response = client.get("/log/")
    assert response.status_code == 200
    assert response.json() == {"message": "Logging API is ready to be used!"}


def test_log_chart_entry():
    """Test logging a chart entry."""
    with patch(
        "modules.api_logging_and_modules.log_api.MongoClient"
    ) as MockMongoClient:
        mock_db = MagicMock()
        mock_collection = MagicMock()

        MockMongoClient.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        log_data: dict = {
            "chart_id": "c0d1c246-38cf-4110-b284-e22431916d10",
            "user_id": "goldius.leo@userdata.tech",
            "session_id": "6cacaafc-c85c-4dd0-b9f3-c323f458b60a",
            "user_query": " The user's primary intent is to analyze the product penetration rate based on the 'Income Level' dimension of the 'Customer Financial Product Usage Analysis' table. They have implicitly requested to view or examine the data grouped by income levels. The user is currently awaiting the delivery of a customized data asset visualization that focuses on the specified income range to gain insights into the product usage trends among different income groups.",
            "narrative": "The analysis of banking industry performance is crucial for understanding trends and making informed decisions. To gain insights, we will examine various key performance indicators (KPIs) and metrics that provide a comprehensive view of the industry's health.",
            "question": "What is the distribution of loan amounts across different occupations?",
            "time_frame": "",
            "time_duration": "Over the Last 5 Years",
            "chart_name": "Visual 3",
            "chart_title": "Distribution of Loan Amounts by Occupation",
            "chart_category": "distribution",
            "chart_type": "histogram_chart",
            "chart_position": 1,
            "chart_axis": '{"xAxis_title": "Loan Amount Distribution", "xAxis_column": "no_dependents"}',
            "sql_query": "SELECT no_dependents AS xAxis FROM ada_banks_data_asset.report_cross_selling_performance_product_type_new",
            "status": "Success",
            "chart_json": "{'Subscription_ID': '', 'Subscription_Name': '', 'Chart_ID': 'c0d1c246-38cf-4110-b284-e22431916d10', 'Shared_User_ID': '', 'Chart_Name': 'Visual 3', 'Chart_Axis': {'xAxis_title': 'Loan Amount Distribution', 'xAxis_column': 'no_dependents'}, 'Chart_SQL_Library': 'MySQL', 'Chart_Position': '1', 'Number_of_Bins': {'sqrt': 1069, 'sturges': 22, 'rice': 210}, 'xAxis': 'Loan Amount Distribution', 'yAxis': 'Frequency', 'Aggregated_Table_JSON': {'Shared_User_ID': '', 'Chart_Axis': {}, 'Chart_Type': 'aggregated_table_chart', 'Chart_Size': 9504856, 'Database_Identifier': 'label1'}, 'Aggregated_Table_Column': ['no_dependents'], 'Database_Identifier': 'label1'}",
            "module_version": "0.7.0",
            "total_inference_time": 123.23521733299998,
            "table_name": "report_cross_selling_performance_product_type_new",
        }

        response = client.post("/log/chart", json=log_data)

        response_status = response.json()["status"]
        response_chart_id = response.json()["chart_id"]

        assert response.status_code == 200
        assert response_status == "Success" or response_status == "Updated"
        assert response_chart_id == log_data["chart_id"]


def test_log_chart_LLMcalls_entry():
    """Test logging a chart LLM call entry."""
    with patch(
        "modules.api_logging_and_modules.log_api.MongoClient"
    ) as MockMongoClient:
        mock_db = MagicMock()
        mock_collection = MagicMock()

        MockMongoClient.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        log_data: dict = {
            "chart_id": "2e0461bc-d227-48d7-acd4-dc9e814ca296",
            "module_id": 100,
            "messages": [
                {"role": "user", "content": "test user prompt"},
                {"role": "assistant", "content": "test assistant prompt"},
                {"role": "system", "content": "test system prompt"},
            ],
            "output": "test output",
            "inference_time": 2.5,
            "llm_model": "gpt-3.5 turbo",
            "input_tokens": 4000,
            "output_tokens": 4000,
        }

        response = client.put("/log/chart-llm-calls", json=log_data)

        response_status = response.json()["status"]
        response_chart_id = response.json()["chart_id"]

        assert response.status_code == 200
        assert response_status == "Success"
        assert response_chart_id == log_data["chart_id"]


def test_log_chart_insights_entry():
    """Test logging a chart insights entry."""
    with patch(
        "modules.api_logging_and_modules.log_api.MongoClient"
    ) as MockMongoClient:
        mock_db = MagicMock()
        mock_collection = MagicMock()

        chart_id: str = "35904505-0d39-4197-88c7-b37c4114029c"

        log_data: dict = {
            "chart_id": chart_id,
            "user_id": "goldius.leo@userdata.tech",
            "session_id": "6cacaafc-c85c-4dd0-b9f3-c323f458b60a",
            "user_query": " The user's primary intent is to analyze the product penetration rate based on the 'Income Level' dimension of the 'Customer Financial Product Usage Analysis' table. They have implicitly requested to view or examine the data grouped by income levels. The user is currently awaiting the delivery of a customized data asset visualization that focuses on the specified income range to gain insights into the product usage trends among different income groups.",
            "narrative": "The analysis of banking industry performance is crucial for understanding trends and making informed decisions. To gain insights, we will examine various key performance indicators (KPIs) and metrics that provide a comprehensive view of the industry's health.",
            "question": "What is the distribution of loan amounts across different occupations?",
            "time_frame": "",
            "time_duration": "Over the Last 5 Years",
            "chart_name": "Visual 3",
            "chart_title": "Distribution of Loan Amounts by Occupation",
            "chart_category": "distribution",
            "chart_type": "histogram_chart",
            "chart_position": 1,
            "chart_axis": '{"xAxis_title": "Loan Amount Distribution", "xAxis_column": "no_dependents"}',
            "sql_query": "SELECT no_dependents AS xAxis FROM ada_banks_data_asset.report_cross_selling_performance_product_type_new",
            "status": "Success",
            "chart_json": "{'Subscription_ID': '', 'Subscription_Name': '', 'Chart_ID': 'c0d1c246-38cf-4110-b284-e22431916d10', 'Shared_User_ID': '', 'Chart_Name': 'Visual 3', 'Chart_Axis': {'xAxis_title': 'Loan Amount Distribution', 'xAxis_column': 'no_dependents'}, 'Chart_SQL_Library': 'MySQL', 'Chart_Position': '1', 'Number_of_Bins': {'sqrt': 1069, 'sturges': 22, 'rice': 210}, 'xAxis': 'Loan Amount Distribution', 'yAxis': 'Frequency', 'Aggregated_Table_JSON': {'Shared_User_ID': '', 'Chart_Axis': {}, 'Chart_Type': 'aggregated_table_chart', 'Chart_Size': 9504856, 'Database_Identifier': 'label1'}, 'Aggregated_Table_Column': ['no_dependents'], 'Database_Identifier': 'label1'}",
            "module_version": "0.7.0",
            "total_inference_time": 123.23521733299998,
            "table_name": "report_cross_selling_performance_product_type_new",
        }

        mock_db = MockMongoClient().get_database(
            os.getenv("CHART_LOGGING_MONGODB_DATABASE")
        )
        mock_db[os.getenv("CHART_LOGGING_MONGODB_COLLECTION")].insert_one(log_data)

        MockMongoClient.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        insight_log_data: dict = {
            "chart_id": chart_id,
            "visual_description": "A bar chart representing monthly sales figures for a retail company over a year. The chart features 12 vertical bars, each labeled at the base with the months from January to December. The Y-axis, positioned on the left, indicates sales in thousands of dollars, ranging from 0 to 100. Each bar is color-coded in a gradient of blue, with darker shades representing higher sales.",
            "business_recommendation": "The analysis of monthly sales reveals strong performance in December ($90,000) but a significant dip in February ($25,000).",
            "visual_story": "The bar chart showing monthly sales for 2024 is based on data collected from sales records. The data is organized to show the total sales for each month, starting from January and ending in December. All the individual sales for a month are added together to get one number representing the total for that month. The months are arranged in order, so the chart flows logically through the year. The chart's bars represent these totals, with their heights showing how much was sold in each month. This clear visual helps to easily spot trends, like which months performed best and which ones could use more attention.",
        }

        response = client.put("/log/insights", json=insight_log_data)

        response_status = response.json()["status"]
        response_chart_id = response.json()["chart_id"]

        assert response.status_code == 200
        assert response_status == "Success"
        assert response_chart_id == chart_id


def test_get_module_by_id():
    """Test retrieving a module by its ID."""
    module_id = 1
    response = client.get(f"/log/module-id/{module_id}")
    assert response.status_code == 200
    assert response.json() == {
        "module_id": module_id,
        "module_name": "generate_narrative_question_d3",
    }


def test_get_module_by_name():
    """Test retrieving a module by its name."""
    module_name = "generate_narrative_question_d3"
    response = client.get(f"/log/module-name/{module_name}")
    assert response.status_code == 200
    assert response.json() == {"module_id": 1, "module_name": module_name}


def test_get_data_from_logs():
    """Test retrieving chart data from logs."""
    chart_id = "35904505-0d39-4197-88c7-b37c4114029c"

    mock_db = MockMongoClient().get_database(
        os.getenv("CHART_LOGGING_MONGODB_DATABASE")
    )
    mock_db[os.getenv("CHART_LOGGING_MONGODB_COLLECTION")].insert_one(
        {
            "chart_id": chart_id,
            "user_id": "test.user@example.com",
            "session_id": "fb680974-7123-439e-bccb-9c0347ab0295",
            "chart_title": "Average Number of Products per Customer by Marital Status",
            "chart_category": "comparison",
            "status": "Fail",
        }
    )

    response = client.get(f"/log/chart/{chart_id}")
    assert response.status_code == 200
    assert "chart_data" in response.json()
    assert response.json()["chart_data"]["chart_id"] == chart_id


def test_insert_modules_into_mongo():
    """Test inserting modules into MongoDB."""
    mock_db = MockMongoClient().get_database(
        os.getenv("CHART_LLM_CALL_MODULE_MONGODB_DATABASE")
    )
    mock_collection_name = "test_modules"
    mock_collection = mock_db[mock_collection_name]
    modules = [
        {"module_name": "generate_narrative_question_d3", "module_id": 1},
        {"module_name": "select_axis_from_chart", "module_id": 2},
    ]

    insert_modules_into_mongo(mock_db, modules, mock_collection_name)
    assert mock_collection.count_documents({}) == len(modules)

    mock_collection.insert_one({"module_name": "test_module", "module_id": 10})
    insert_modules_into_mongo(mock_db, modules, mock_collection_name)
    assert mock_collection.count_documents({}) > len(modules)


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="MODULEID_GENERATE_TEST_MODULE=1\nMODULEID_GENERATE_MOCKUP_MODULE=2",
)
def test_read_module_ids_from_env(mock_open_file):
    """Test reading module IDs from the environment file."""
    result = read_module_ids_from_env()
    mock_open_file.assert_called_once()
    assert result == [
        {"module_name": "generate_test_module", "module_id": 1},
        {"module_name": "generate_mockup_module", "module_id": 2},
    ]


@patch("modules.api_logging_and_modules.log_api_modules.collection_exists")
@patch("modules.api_logging_and_modules.log_api_modules.insert_modules_into_mongo")
@patch("modules.api_logging_and_modules.log_api_modules.read_module_ids_from_env")
def test_setup_modules(
    mock_read_module_ids_from_env,
    mock_insert_modules_into_mongo,
    mock_collection_exists,
):
    """Test setting up modules."""
    mock_read_module_ids_from_env.return_value = [1, 2, 3, 4]
    setup_modules()
    mock_read_module_ids_from_env.assert_called_once()
    mock_collection_exists.assert_called_once()
    mock_insert_modules_into_mongo.assert_called_once()


if __name__ == "__main__":
    # Run all tests using pytest
    pytest.main(["-v", __file__])
