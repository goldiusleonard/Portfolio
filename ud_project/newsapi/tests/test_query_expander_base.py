import pytest
from unittest.mock import patch, MagicMock
import os
from src.query_expander.base import expand_topic


# Mock environment variables for testing
@pytest.fixture(autouse=True)
def mock_env_vars():
    with patch.dict(
        os.environ,
        {
            "LLAMA70B_MODEL": "mock_model",
            "LLAMA70B_LLM_BASE_URL": "mock_url",
            "LLAMA70B_LLM_API_KEY": "mock_api_key",
        },
    ):
        yield


# # Mocking OpenAI client for testing
# @pytest.fixture
# def mock_llama_client():
#     with patch("your_module.OpenAI") as mock_client:
#         mock_instance = MagicMock()
#         mock_client.return_value = mock_instance
#         yield mock_instance


# Test for topic_expander function
@patch("src.query_expander.base.llama70b_client.chat.completions.create")
def test_topic_expander(mock_create):
    # Define the mock return value
    mock_create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="expanded query 1"))]
    )

    topic_to_expand = "Royal Betrayal"

    # calling the function here
    result = expand_topic(topic_to_expand)

    # Assertions
    assert result == "expanded query 1"
