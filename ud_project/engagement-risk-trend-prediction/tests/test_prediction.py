import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pandas as pd
from main import app

# Create a TestClient
client = TestClient(app)

mock_data = pd.DataFrame(
    {
        "video_id": ["1", "2", "3"],
        "category": ["hate speech", "hate speech", "hate speech"],
        "sub_category": ["race", "religion", "royal"],
        "ai_topic": ["topic1", "topic2", "topic3"],
        "video_posted_timestamp": pd.to_datetime(
            ["2023-01-01", "2023-01-02", "2023-01-03"]
        ),
        "video_like_count": [100, 200, 300],
        "video_share_count": [50, 100, 150],
        "video_view_count": [1000, 2000, 3000],
        "comment_count": [10, 20, 30],
        "user_handle": ["user1", "user2", "user3"],
    }
)


@pytest.fixture
def mock_predict():
    with patch(
        "src.modules.engagement_prediction.EngagementAndRiskPrediction.predict"
    ) as mock_func:
        mock_forecast = [
            {
                "Date": "2025-01-01",
                "predict_total_comments": 0,
                "predict_total_likes": 7895.800579417604,
                "predict_total_shares": 0,
                "predict_total_videos": 19.970251462490122,
                "predict_total_views": 21058872.66356933,
                "risk_status_predicted": "low",
            },
            {
                "Date": "2025-01-02",
                "predict_total_comments": 0,
                "predict_total_likes": 276046.70952734,
                "predict_total_shares": 1180298.1884669608,
                "predict_total_videos": 14.598846048917334,
                "predict_total_views": 0,
                "risk_status_predicted": "low",
            },
            {
                "Date": "2025-01-03",
                "predict_total_comments": 0,
                "predict_total_likes": 630881.6253211518,
                "predict_total_shares": 698588.7713368686,
                "predict_total_videos": 10.571626221536961,
                "predict_total_views": 0,
                "risk_status_predicted": "low",
            },
            # Add the remaining entries here for all 10 dates...
        ]
        mock_func.return_value = mock_forecast
        yield mock_func


@pytest.fixture
def mock_fetch_table():
    with patch("src.modules.engagement_prediction.fetch_data_asset_table") as mock_func:
        mock_func.return_value = mock_data
        yield mock_func


@pytest.fixture
def mock_mysql_engine():
    with patch("src.utils.mysql_connection.get_mysql_engine") as mock_func:
        mock_engine = MagicMock()
        mock_func.return_value = mock_engine
        yield mock_func


def test_valid_request(mock_fetch_table, mock_predict, mock_mysql_engine):
    params = {
        "category": "Scam",
        "start_date": "2025-01-01",
        "end_date": "2025-01-03",
    }

    # API request
    response = client.get("/predictions/engagement-risk", params=params)

    # Validate the response
    assert (
        response.status_code == 200
    ), f"Unexpected status code: {response.status_code}, Response: {response.text}"

    # Parse and validate the JSON response
    json_data = response.json()

    assert len(json_data["data"]) == 3, "Expected 3 predictions in the response."


# Test case 01: Missing parameters
def test_missing_required_parameter():
    params = {
        "start_date": "2025-01-01",
        "end_date": "2025-01-05",
    }

    response = client.get("/predictions/engagement-risk", params=params)
    assert response.status_code == 400, "Expected 400 Bad Request for missing filter"
    assert "detail" in response.json()
    assert (
        response.json()["detail"]
        == "You must provide 'category' only, or 'category' and 'sub_category', or 'category', 'sub_category', and 'topic'."
    )


# Test case 02: Invalid category
def test_invalid_category():
    params = {
        "category": "invalid_category",  # Invalid category
        "start_date": "2025-01-01",
        "end_date": "2025-01-03",
    }

    response = client.get("/predictions/engagement-risk", params=params)
    assert response.status_code == 404, "Expected 404 Not Found for invalid category"
    assert response.json()["detail"] == "No data found."


# Test case 03: Invalid topic
def test_invalid_topic_selection():
    params = {
        "category": "hate speech",
        "sub_category": "race",
        "topic": "invalid_topic",  # Invalid topic
        "start_date": "2025-01-01",
        "end_date": "2025-01-03",
    }

    response = client.get("/predictions/engagement-risk", params=params)
    assert (
        response.status_code == 404
    ), f"Expected 404 Not Found, got {response.status_code} instead."
    assert response.json()["detail"] == "No data found."


# Test case 04:  Invalid date range
def test_invalid_date_range():
    params = {
        "category": "hate speech",
        "sub_category": "race",
        "start_date": "2025-01-05",  # invalid date range
        "end_date": "2025-01-01",
    }

    response = client.get("/predictions/engagement-risk", params=params)
    assert (
        response.status_code == 400
    ), "Expected 400 Bad Request for invalid date range"
    assert "detail" in response.json()
    assert (
        response.json()["detail"] == "Start date must be before or equal to end date."
    )


# Test case 05: checking with valid category
def test_valid_request_category_only(mock_fetch_table, mock_predict, mock_mysql_engine):
    params = {
        "category": "Scam",
        "start_date": "2025-01-01",
        "end_date": "2025-01-03",
    }

    response = client.get("/predictions/engagement-risk", params=params)
    assert (
        response.status_code == 200
    ), "Expected 200 OK for valid category-only request"
    json_data = response.json()
    assert len(json_data["data"]) == 3, "Expected 3 predictions in the response."


# Test case 06: missing category
def test_missing_category():
    params = {
        "sub_category": "race",  # Missing 'category'
        "start_date": "2025-01-01",
        "end_date": "2025-01-03",
    }

    response = client.get("/predictions/engagement-risk", params=params)
    assert (
        response.status_code == 400
    ), "Expected 400 Bad Request for missing 'category'"
    assert "detail" in response.json()
    assert (
        response.json()["detail"]
        == "You must provide 'category' only, or 'category' and 'sub_category', or 'category', 'sub_category', and 'topic'."
    )


# Test case 07: Missing 'category' and 'sub_category'
def test_missing_category_and_sub_category():
    params = {
        "topic": "topic1",  # Missing 'category' and 'sub_category'
        "start_date": "2025-01-01",
        "end_date": "2025-01-03",
    }

    response = client.get("/predictions/engagement-risk", params=params)
    assert (
        response.status_code == 400
    ), "Expected 400 Bad Request for missing 'category' and 'sub_category'"
    assert "detail" in response.json()
    assert (
        response.json()["detail"]
        == "You must provide 'category' only, or 'category' and 'sub_category', or 'category', 'sub_category', and 'topic'."
    )


# test case 09: Invalid Username
def test_invalid_username_with_spaces():
    params = {
        "category": "hate speech",
        "sub_category": "race",
        "user_handle": "invalid user",  # Invalid username (contains spaces)
        "start_date": "2025-01-01",
        "end_date": "2025-01-03",
    }

    response = client.get("/predictions/engagement-risk", params=params)
    assert (
        response.status_code == 404
    ), "Expected 404 Not Found for username with spaces"
    assert "detail" in response.json()
    assert response.json()["detail"] == "No data found."


# test case 10: Invalid Username and topic with Correct Category
def test_invalid_topic_with_correct_category():
    params = {
        "category": "hate speech",  # Valid category
        "sub_category": "race",
        "topic": "invalid_topic",  # Invalid topic
        "start_date": "2025-01-01",
        "end_date": "2025-01-03",
    }

    response = client.get("/predictions/engagement-risk", params=params)
    assert response.status_code == 404, "Expected 404 Not Found for invalid topic"
    assert "detail" in response.json()
    assert response.json()["detail"] == "No data found."


# test case 11: Missing sub_category with Provided category and user_handle
def test_missing_sub_category_with_provided_category_and_username():
    params = {
        "category": "hate speech",  # Valid category
        "user_handle": "user1",  # Valid username
        "start_date": "2025-01-01",
        "end_date": "2025-01-03",
    }

    response = client.get("/predictions/engagement-risk", params=params)
    assert (
        response.status_code == 404
    ), "Expected 404 Not Found for missing 'sub_category'"
    assert "detail" in response.json()
    assert response.json()["detail"] == "No data found."


# test case 12: Missing topic with Provided category, sub_category, and user_handle
def test_missing_topic_with_provided_category_sub_category_and_username():
    params = {
        "category": "hate speech",  # Valid category
        "sub_category": "race",  # Valid sub-category
        "user_handle": "user2",  # Valid username
        "start_date": "2025-01-01",
        "end_date": "2025-01-03",
    }

    response = client.get("/predictions/engagement-risk", params=params)
    assert response.status_code == 404, "Expected 404 Not Found for missing 'topic'"
    assert "detail" in response.json()
    assert response.json()["detail"] == "No data found."
