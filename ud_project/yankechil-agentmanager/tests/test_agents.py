from unittest import mock

import pytest
import requests

from agents.Agents import (
    CategoryAgent,
    CommentRiskAgent,
    JustificationAgent,
    LawRegulatedAgent,
    SentimentAgent,
    SummaryAgent,
)
from agents.baseAgent import BaseAgent


# Test the health_check method for each agent
@pytest.mark.parametrize(
    "agent_class, url, expected_status",
    [
        (SummaryAgent, "http://example.com/summary", {"status": "healthy"}),
        (SentimentAgent, "http://example.com/sentiment", {"status": "healthy"}),
        (CategoryAgent, "http://example.com/category", {"status": "healthy"}),
        (LawRegulatedAgent, "http://example.com/law_regulated", {"status": "healthy"}),
        (JustificationAgent, "http://example.com/justification", {"status": "healthy"}),
        (CommentRiskAgent, "http://example.com/comment_risk", {"status": "healthy"}),
    ],
)
def test_health_check_success(agent_class, url, expected_status):
    # Mock the response of requests.post or requests.get to simulate a successful health check
    with mock.patch(
        "requests.post"
        if agent_class in [SummaryAgent, LawRegulatedAgent]
        else "requests.get",
    ) as mock_request:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        agent = agent_class(url)
        result = agent.health_check()

        assert result == expected_status


@pytest.mark.parametrize(
    "agent_class, url, expected_status",
    [
        (SummaryAgent, "http://example.com/summary", {"status": "unhealthy"}),
        (SentimentAgent, "http://example.com/sentiment", {"status": "unhealthy"}),
        (CategoryAgent, "http://example.com/category", {"status": "unhealthy"}),
        (
            LawRegulatedAgent,
            "http://example.com/law_regulated",
            {"status": "unhealthy"},
        ),
        (
            JustificationAgent,
            "http://example.com/justification",
            {"status": "unhealthy"},
        ),
        (CommentRiskAgent, "http://example.com/comment_risk", {"status": "unhealthy"}),
    ],
)
def test_health_check_failure(agent_class, url, expected_status):
    # Mock the response of requests.post or requests.get to simulate an unsuccessful health check
    with mock.patch(
        "requests.post"
        if agent_class in [SummaryAgent, LawRegulatedAgent]
        else "requests.get",
    ) as mock_request:
        mock_response = mock.Mock()
        mock_response.status_code = 500  # Simulate server error
        mock_request.return_value = mock_response

        agent = agent_class(url)
        result = agent.health_check()

        assert result == expected_status


# Test health_check when there is an exception (e.g., network failure)
@pytest.mark.parametrize(
    "agent_class, url, expected_status",
    [
        (SummaryAgent, "http://example.com/summary", {"status": "unhealthy"}),
        (SentimentAgent, "http://example.com/sentiment", {"status": "unhealthy"}),
        (CategoryAgent, "http://example.com/category", {"status": "unhealthy"}),
        (
            LawRegulatedAgent,
            "http://example.com/law_regulated",
            {"status": "unhealthy"},
        ),
        (
            JustificationAgent,
            "http://example.com/justification",
            {"status": "unhealthy"},
        ),
        (CommentRiskAgent, "http://example.com/comment_risk", {"status": "unhealthy"}),
    ],
)
def test_health_check_exception(agent_class, url, expected_status):
    # Mock the response of requests.post or requests.get to simulate an exception
    with mock.patch(
        "requests.post"
        if agent_class in [SummaryAgent, LawRegulatedAgent]
        else "requests.get",
    ) as mock_request:
        mock_request.side_effect = requests.exceptions.RequestException(
            "Connection failed",
        )

        agent = agent_class(url)
        result = agent.health_check()

        assert result == expected_status


# Test the execute method for each agent
@pytest.mark.parametrize(
    "agent_class, url, params, expected_method",
    [
        (SummaryAgent, "http://example.com/summary", {"text": "test"}, "POST"),
        (SentimentAgent, "http://example.com/sentiment", {"text": "test"}, "GET"),
        (CategoryAgent, "http://example.com/category", {"text": "test"}, "GET"),
        (
            LawRegulatedAgent,
            "http://example.com/law_regulated",
            {"document_ids": ["penal_code"], "text": "test"},
            "POST",
        ),
        (
            JustificationAgent,
            "http://example.com/justification",
            {"text": "test"},
            "GET",
        ),
        (CommentRiskAgent, "http://example.com/comment_risk", {"text": "test"}, "GET"),
    ],
)
def test_execute(agent_class, url, params, expected_method):
    # Mock the execute method to avoid making real HTTP requests
    with mock.patch.object(
        BaseAgent,
        "execute",
        return_value={"result": "success"},
    ) as mock_execute:
        agent = agent_class(url)
        result = agent.execute(params)

        # Assert that the execute method was called with the correct HTTP method
        mock_execute.assert_called_with(params, method=expected_method)
        assert result == {"result": "success"}
