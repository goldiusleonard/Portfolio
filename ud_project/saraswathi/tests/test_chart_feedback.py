import os
import pytest
import qdrant_client

from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from mongomock import MongoClient as MockMongoClient
from dotenv import load_dotenv
from main import app

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)


@pytest.fixture(autouse=True)
def set_env_and_mock(monkeypatch):
    """Automatically mock environment variables and MongoDB client for all tests."""
    load_dotenv()
    monkeypatch.setattr(
        "pymongo.MongoClient", lambda *args, **kwargs: MockMongoClient()
    )

    # Mock the Qdrant client initialization
    monkeypatch.setattr(
        qdrant_client.QdrantClient,
        "__init__",
        MagicMock(return_value=None),  # Mock the client init method
    )

    # Optionally mock Qdrant-specific operations here
    mock_qdrant = MagicMock()
    monkeypatch.setattr(qdrant_client, "QdrantClient", mock_qdrant)

    monkeypatch.setenv("ENV_FILE_PATH", ".env")
    yield


client = TestClient(app)


def test_save_feedback():
    # Mock MongoDB Client
    with patch("modules.chart_feedback.chart_feedback.MongoClient") as MockMongoClient:
        with patch(
            "modules.chart_feedback.chart_feedback.QdrantClient"
        ) as MockQdrantClient:
            mock_feedback_db = MagicMock()

            mock_feedback_collection = MagicMock()
            # mock_chart_logging_collection = MagicMock()

            MockMongoClient.return_value.__getitem__.return_value = mock_feedback_db
            mock_feedback_db.__getitem__.return_value = mock_feedback_collection

            # Mock Qdrant Client
            MockQdrantClient.return_value = MagicMock()

            # input data
            chart_feedback_data = {
                "chart_id": "a0f0d92f-50c2-4af9-b543-844d6518152d",
                "like": False,
                "feedback": {
                    "chart_title": {
                        "selected_options": ["Irrelevant to my question", "Too long"],
                        "other": "test reasons",
                    },
                    "xaxis_title": {
                        "selected_options": ["Not descriptive enough"],
                        "other": "test reasons",
                    },
                    "yaxis_title": {
                        "selected_options": ["Too short"],
                        "other": "test reasons",
                    },
                    "xaxis_data": {
                        "selected_options": ["Data misrepresented"],
                        "other": "test reasons",
                    },
                    "yaxis_data": {"selected_options": [], "other": "test reasons"},
                    "overall_chart": {
                        "selected_options": ["Poor labelling"],
                        "other": "test reasons",
                    },
                },
            }

            response = client.put("/feedback/save", json=chart_feedback_data)
            assert response.status_code == 200


def test_get_feedback_by_id():
    """Test retrieving a feedback by chart ID."""
    # Unique chart ID for the test
    chart_id: str = "867806ff-1182-4592-8e01-8e80384dde38"

    # Input chart data
    chart_data: dict = {
        "chart_id": chart_id,
        "user_query": "Test user query",
        "question": "Test question",
        "chart_title": "Test Chart Title",
    }

    chart_feedback_data: dict = {
        "chart_id": "",
        "like": None,
        "feedback": {
            "chart_title": {
                "selected_options": [],
                "other": "",
            },
            "xaxis_title": {
                "selected_options": [],
                "other": "",
            },
            "yaxis_title": {
                "selected_options": [],
                "other": "",
            },
            "xaxis_data": {
                "selected_options": [],
                "other": "",
            },
            "yaxis_data": {"selected_options": [], "other": ""},
            "overall_chart": {
                "selected_options": [],
                "other": "",
            },
            "zaxis_data": {"other": "", "selected_options": []},
            "zaxis_title": {
                "other": "",
                "selected_options": [],
            },
        },
    }

    # Patch the required dependencies
    with patch("modules.chart_feedback.chart_feedback.MongoClient") as MockMongoClient:
        # Create mock databases and collections
        mock_feedback_db = MagicMock()
        mock_chart_logging_db = MagicMock()

        mock_feedback_collection = MagicMock()
        mock_chart_logging_collection = MagicMock()

        # Setup mock return values
        mock_feedback_collection.find_one.return_value = chart_feedback_data
        mock_chart_logging_collection.find_one.return_value = chart_data

        # Setup database and collection retrieval
        MockMongoClient.return_value.__getitem__.side_effect = lambda db_name: (
            mock_feedback_db
            if db_name == os.getenv("FEEDBACK_MONGODB_DATABASE")
            else mock_chart_logging_db
        )

        mock_feedback_db.__getitem__.return_value = mock_feedback_collection
        mock_chart_logging_db.__getitem__.return_value = mock_chart_logging_collection

        # Prepare environment setup
        with patch.dict(
            os.environ,
            {
                "FEEDBACK_MONGODB_COLLECTION": "feedback_collection",
                "CHART_LOGGING_MONGODB_COLLECTION": "chart_logging_collection",
            },
        ):
            # Make the API request
            response = client.get(f"/feedback/chart_id/{chart_id}")

            # Assertions
            assert response.status_code == 200

            # Compare the returned feedback without '_id'
            returned_feedback = response.json()
            if "_id" in returned_feedback:
                del returned_feedback["_id"]
            assert returned_feedback == chart_feedback_data


def test_search_user_query():
    """Test retrieving a chart list by query."""
    # Mock external dependencies
    with patch(
        "modules.chart_feedback.chart_feedback.requests.get"
    ) as mock_embedding_request, patch(
        "modules.chart_feedback.chart_feedback.QdrantClient"
    ) as MockQdrantClient, patch(
        "modules.chart_feedback.chart_feedback.get_chart_feedback_mongodb"
    ) as mock_get_chart_feedback, patch(
        "modules.chart_feedback.chart_feedback.os.getenv"
    ) as mock_getenv:
        # Mock environment variables
        mock_getenv.side_effect = lambda var, default=None: {
            "FEEDBACK_QDRANT_USER_QUERY_COLLECTION": "test_collection",
            "EMBEDDING_MODEL_NAME": "test_model",
        }.get(var, default)

        # Test user query
        test_user_query = "The user wants to perform cross sell analysis"

        # Mock embedding request
        mock_embedding_response = MagicMock()
        mock_embedding_response.content = str([0.1, 0.2, 0.3]).encode("utf-8")
        mock_embedding_request.return_value = mock_embedding_response

        # Mock Qdrant Client
        mock_qdrant_client = MockQdrantClient.return_value
        mock_qdrant_client.collection_exists.return_value = True
        mock_search_result = MagicMock()
        mock_search_result.payload = {"chart_id": "test_chart_1"}
        mock_qdrant_client.search.return_value = [mock_search_result]

        # Mock MongoDB chart feedback
        mock_get_chart_feedback.return_value = {
            "chart_id": "test_chart_1",
            "feedback": "Sample feedback",
        }

        # Make the request using path parameter
        response = client.get(f"/feedback/search/user_query/{test_user_query}")

        # Assert successful response
        assert response.status_code == 200

        # Check response structure
        response_data = response.json()

        # Modify assertion to match the actual response structure
        assert "results" in response_data, "Response should contain 'results' key"
        results = response_data["results"]

        # Check that results is a list
        assert isinstance(results, list), "Results should be a list"
        assert len(results) > 0, "Results list should not be empty"


def test_search_question():
    """Test retrieving a chart list by question."""
    # Mock external dependencies
    with patch(
        "modules.chart_feedback.chart_feedback.requests.get"
    ) as mock_embedding_request, patch(
        "modules.chart_feedback.chart_feedback.QdrantClient"
    ) as MockQdrantClient, patch(
        "modules.chart_feedback.chart_feedback.get_chart_feedback_mongodb"
    ) as mock_get_chart_feedback, patch(
        "modules.chart_feedback.chart_feedback.os.getenv"
    ) as mock_getenv:
        # Mock environment variables
        mock_getenv.side_effect = lambda var, default=None: {
            "FEEDBACK_QDRANT_QUESTION_COLLECTION": "test_collection",
            "EMBEDDING_MODEL_NAME": "test_model",
        }.get(var, default)

        # Test user query
        test_question = " What is the cross sell analysis in 2023?"

        # Mock embedding request
        mock_embedding_response = MagicMock()
        mock_embedding_response.content = str([0.1, 0.2, 0.3]).encode("utf-8")
        mock_embedding_request.return_value = mock_embedding_response

        # Mock Qdrant Client
        mock_qdrant_client = MockQdrantClient.return_value
        mock_qdrant_client.collection_exists.return_value = True
        mock_search_result = MagicMock()
        mock_search_result.payload = {"chart_id": "test_chart_1"}
        mock_qdrant_client.search.return_value = [mock_search_result]

        # Mock MongoDB chart feedback
        mock_get_chart_feedback.return_value = {
            "chart_id": "test_chart_1",
            "feedback": "Sample feedback",
        }

        # Make the request using path parameter
        response = client.get(f"/feedback/search/question/{test_question}")

        # Assert successful response
        assert response.status_code == 200

        # Check response structure
        response_data = response.json()

        # Modifying the assertion to match the actual response structure
        assert "results" in response_data, "Response should contain 'results' key"
        results = response_data["results"]

        # Check that results is a list
        assert isinstance(results, list), "Results should be a list"
        assert len(results) > 0, "Results list should not be empty"
