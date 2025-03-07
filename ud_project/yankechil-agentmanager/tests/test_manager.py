from unittest import mock

import pytest

from agents.baseAgent import BaseAgent
from log_mongo import logger
from manager.manager import AgentManager


# Mock BaseAgent for testing purposes
class MockBaseAgent(BaseAgent):
    def __init__(self, agent_name: str):
        self.agent_name = agent_name


@pytest.fixture
def agent_manager():
    """Fixture for creating an AgentManager instance."""
    return AgentManager()


# Test the register_agent method with valid inputs
def test_register_agent_valid(agent_manager):
    # Create a mock agent
    agent = MockBaseAgent("test_agent")

    # Register the agent
    agent_manager.register_agent("test_agent", agent)

    # Assert that the agent is correctly registered
    assert "test_agent" in agent_manager.agents
    assert agent_manager.agents["test_agent"] == agent


# Test register_agent raises TypeError when agent_name is not a string
def test_register_agent_invalid_name(agent_manager):
    # Create a mock agent
    agent = MockBaseAgent("test_agent")

    # Mock logger to capture logs
    with mock.patch.object(logger, "error") as mock_logger:
        with pytest.raises(TypeError):
            agent_manager.register_agent(
                123,
                agent,
            )  # Invalid agent name (not a string)

        mock_logger.assert_called_with("Agent name must be a string.")


# Test register_agent raises TypeError when agent is not a BaseAgent instance
def test_register_agent_invalid_agent(agent_manager):
    # Register an invalid agent (not an instance of BaseAgent)
    with mock.patch.object(logger, "error") as mock_logger:
        with pytest.raises(TypeError):
            agent_manager.register_agent(
                "test_agent",
                "not_a_base_agent",
            )  # Invalid agent type

        mock_logger.assert_called_with("Agent must be a BaseAgent instance.")


# Test get_agent returns the correct agent
def test_get_agent_valid(agent_manager):
    # Create and register a mock agent
    agent = MockBaseAgent("test_agent")
    agent_manager.register_agent("test_agent", agent)

    # Retrieve the agent
    retrieved_agent = agent_manager.get_agent("test_agent")

    # Assert that the retrieved agent is correct
    assert retrieved_agent == agent


# Test get_agent returns None and logs error when agent is not found
def test_get_agent_not_found(agent_manager):
    # Try to get a non-existent agent
    with mock.patch.object(logger, "error") as mock_logger:
        retrieved_agent = agent_manager.get_agent("non_existent_agent")

        # Assert that the result is None
        assert retrieved_agent is None
        mock_logger.assert_called_with("Agent non_existent_agent not found.")


# Test get_agent raises TypeError when agent_name is not a string
def test_get_agent_invalid_name(agent_manager):
    # Create a mock agent
    agent = MockBaseAgent("test_agent")
    agent_manager.register_agent("test_agent", agent)

    # Mock logger to capture logs
    with mock.patch.object(logger, "error") as mock_logger:
        with pytest.raises(TypeError):
            agent_manager.get_agent(123)  # Invalid agent name (not a string)

        mock_logger.assert_called_with("Agent name must be a string.")
