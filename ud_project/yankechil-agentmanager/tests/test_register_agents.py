from unittest import mock

import pytest

from agents.Agents import (
    CategoryAgent,
    CommentRiskAgent,
    JustificationAgent,
    LawRegulatedAgent,
    SentimentAgent,
    SummaryAgent,
)
from agents.register_agents import create_agent_manager_v0
from manager.manager import AgentManager


@pytest.fixture
def mock_agent_manager():
    """Fixture for creating an AgentManager instance."""
    return AgentManager()


# Mock the logger
@pytest.fixture
def mock_logger():
    with mock.patch("manager.manager.logger") as mock_log:
        yield mock_log


# Mock agent classes to test the agent creation process
@pytest.fixture
def mock_agent_classes():
    return {
        "summary": SummaryAgent,
        "sentiment": SentimentAgent,
        "category": CategoryAgent,
        "justification": JustificationAgent,
        "law_regulated": LawRegulatedAgent,
        "comment_risk": CommentRiskAgent,
    }


def test_create_agent_manager_v0_success(mock_agent_classes):
    # Sample agent configuration
    agent_configs = {
        "summary": {
            "class": mock_agent_classes["summary"],
            "init_args": {"url": "http://example.com"},
        },
        "sentiment": {
            "class": mock_agent_classes["sentiment"],
            "init_args": {"url": "http://example.com"},
        },
        "justification": {
            "class": mock_agent_classes["justification"],
            "init_args": {"url": "http://example.com"},
        },
        "law_regulated": {
            "class": mock_agent_classes["law_regulated"],
            "init_args": {"url": "http://example.com"},
        },
        "category": {
            "class": mock_agent_classes["category"],
            "init_args": {"url": "http://example.com"},
        },
        "comment_risk": {
            "class": mock_agent_classes["comment_risk"],
            "init_args": {"url": "http://example.com"},
        },
    }

    # Mock AgentManager and its register_agent method
    with mock.patch.object(AgentManager, "register_agent") as mock_register_agent:
        # Call the function that is supposed to register the agents
        agent_manager = create_agent_manager_v0(agent_configs)

        # Assert the total number of calls
        assert mock_register_agent.call_count == 6

        # Assert each specific call
        mock_register_agent.assert_any_call("summary", mock.ANY)
        mock_register_agent.assert_any_call("sentiment", mock.ANY)
        mock_register_agent.assert_any_call("justification", mock.ANY)
        mock_register_agent.assert_any_call("law_regulated", mock.ANY)
        mock_register_agent.assert_any_call("category", mock.ANY)
        mock_register_agent.assert_any_call("comment_risk", mock.ANY)


def test_create_agent_manager_v0_missing_class():
    # Agent configuration missing 'class' key
    agent_configs = {
        "summary": {
            # 'class' is missing here
            "init_args": {"url": "http://example.com"},
        },
        "sentiment": {
            "init_args": {"url": "http://example.com"},
        },
        "justification": {
            "init_args": {"url": "http://example.com"},
        },
        "law_regulated": {
            "init_args": {"url": "http://example.com"},
        },
        "category": {
            "init_args": {"url": "http://example.com"},
        },
        "comment_risk": {
            "init_args": {"url": "http://example.com"},
        },
    }

    # Expect KeyError because 'class' is missing in the config
    with pytest.raises(KeyError, match="Missing 'class' for agent summary"):
        create_agent_manager_v0(agent_configs)


def test_create_agent_manager_v0_missing_init_args():
    # Agent configuration missing 'init_args' key
    agent_configs = {
        "summary": {
            "class": SummaryAgent,
            # 'init_args' is missing here
        },
        "sentiment": {
            "class": SentimentAgent,
        },
        "justification": {
            "class": JustificationAgent,
        },
        "law_regulated": {
            "class": LawRegulatedAgent,
        },
        "category": {
            "class": CategoryAgent,
        },
        "comment_risk": {
            "class": CommentRiskAgent,
        },
    }

    # Expect KeyError because 'init_args' is missing
    with pytest.raises(KeyError, match="Missing 'init_args' for agent summary"):
        create_agent_manager_v0(agent_configs)


@mock.patch("agents.register_agents.logger")
@mock.patch.object(AgentManager, "register_agent")
def test_create_agent_manager_v0_exception_handling(mock_register_agent, mock_logger):
    # Simulate an exception during the agent registration
    mock_register_agent.side_effect = Exception("Error registering agent")

    # Sample agent configuration
    agent_configs = {
        "summary": {
            "class": SummaryAgent,
            "init_args": {"url": "http://example.com"},
        },
        "sentiment": {
            "class": SentimentAgent,
            "init_args": {"url": "http://example.com"},
        },
        "justification": {
            "class": JustificationAgent,
            "init_args": {"url": "http://example.com"},
        },
        "law_regulated": {
            "class": LawRegulatedAgent,
            "init_args": {"url": "http://example.com"},
        },
        "category": {
            "class": CategoryAgent,
            "init_args": {"url": "http://example.com"},
        },
        "comment_risk": {
            "class": CommentRiskAgent,
            "init_args": {"url": "http://example.com"},
        },
    }

    # Call the function
    create_agent_manager_v0(agent_configs)

    # Assert that the logger.error was called 6 times
    assert mock_logger.error.call_count == 6

    # Check the logged error messages for each agent
    expected_calls = [
        mock.call(
            "Error creating or registering agent summary: Error registering agent",
        ),
        mock.call(
            "Error creating or registering agent sentiment: Error registering agent",
        ),
        mock.call(
            "Error creating or registering agent justification: Error registering agent",
        ),
        mock.call(
            "Error creating or registering agent law_regulated: Error registering agent",
        ),
        mock.call(
            "Error creating or registering agent category: Error registering agent",
        ),
        mock.call(
            "Error creating or registering agent comment_risk: Error registering agent",
        ),
    ]

    mock_logger.error.assert_has_calls(expected_calls, any_order=False)
