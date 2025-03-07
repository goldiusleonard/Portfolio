from unittest import mock

import requests
from requests.models import Response

from agents.baseAgent import BaseAgent
from log_mongo import logger


# Test for initialization of the BaseAgent
def test_base_agent_initialization():
    agent = BaseAgent(name="test_agent", url="http://example.com")
    assert agent.name == "test_agent"
    assert agent.url == "http://example.com"


# Mocking requests.get for GET method in BaseAgent
@mock.patch("requests.get")
def test_execute_get_success(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"key": "value"}

    agent = BaseAgent(name="test_agent", url="http://example.com")
    params = {"param1": "value1"}

    result = agent.execute(params=params, method="GET")

    # Assert that the requests.get was called with the expected parameters
    mock_get.assert_called_once_with(
        "http://example.com",
        params=params,
        headers={"Content-Type": "application/json"},
    )

    # Assert that the result is as expected
    assert result == {"key": "value"}


# Mocking requests.post for POST method in BaseAgent
@mock.patch("requests.post")
def test_execute_post_success(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"key": "value"}

    agent = BaseAgent(name="test_agent", url="http://example.com")
    params = {"param1": "value1"}

    result = agent.execute(params=params, method="POST")

    # Assert that the requests.post was called with the expected parameters
    mock_post.assert_called_once_with(
        "http://example.com",
        json=params,
        headers={"Content-Type": "application/json"},
    )

    # Assert that the result is as expected
    assert result == {"key": "value"}


# Mocking requests.get for failure case
@mock.patch("requests.get")
def test_execute_get_failure(mock_get):
    # Simulate a failure in the request (e.g., request exception)
    mock_get.side_effect = requests.exceptions.RequestException("Request failed")

    agent = BaseAgent(name="test_agent", url="http://example.com")
    params = {"param1": "value1"}

    # Call the execute method with GET
    result = agent.execute(params=params, method="GET")

    # Verify that the requests.get was called with the expected arguments
    mock_get.assert_called_once_with(
        "http://example.com",
        params=params,
        headers={"Content-Type": "application/json"},
    )

    # Assert that the result contains the error message
    assert result == {"error": "Request failed"}


@mock.patch(
    "requests.post",
)  # Mocking requests.post in the context where it's used (i.e., in BaseAgent)
def test_execute_post_failure(mock_post):
    # Simulate a failure in the POST request
    mock_post.side_effect = requests.exceptions.RequestException("Request failed")

    # Create instance of BaseAgent
    agent = BaseAgent(name="test_agent", url="http://example.com")
    params = {"param1": "value1"}

    # Call the execute method with POST
    result = agent.execute(params=params, method="POST")

    # Assert that requests.post was called with the correct arguments
    mock_post.assert_called_once_with(
        "http://example.com",
        json=params,
        headers={"Content-Type": "application/json"},
    )

    # Assert that the result contains the error message
    assert result == {"error": "Request failed"}


# Test for logging errors when a request fails
def test_execute_logging_on_failure():
    agent = BaseAgent(name="test_agent", url="http://example.com")

    # Mocking requests.get to simulate a failed request
    mock_response = mock.Mock(spec=Response)
    mock_response.raise_for_status.side_effect = requests.exceptions.RequestException(
        "Request failed",
    )

    with mock.patch("requests.get", return_value=mock_response):
        with mock.patch.object(logger, "error") as mock_logger_error:
            result = agent.execute(params={"key": "value"}, method="GET")
            mock_logger_error.assert_called_once_with(
                "Request to http://example.com failed: Request failed",
            )


@mock.patch(
    "requests.request",
)  # Mocking requests.request in the context where it's used (i.e., in BaseAgent)
def test_execute_invalid_method(mock_request):
    # Simulate an invalid method (using `requests.request` directly)
    mock_request.return_value.status_code = 400
    mock_request.return_value.json.return_value = {"error": "Method not supported"}

    # Create instance of BaseAgent
    agent = BaseAgent(name="test_agent", url="http://example.com")
    params = {"param1": "value1"}

    # Call the execute method with an invalid HTTP method
    result = agent.execute(params=params, method="INVALID")

    # Assert that requests.request was called with the invalid method
    mock_request.assert_called_once_with(
        "INVALID",
        "http://example.com",
        json=params,
        headers={"Content-Type": "application/json"},
    )

    # Assert that the result contains the error message
    assert result == {"error": "Method not supported"}
