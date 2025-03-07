# import config_endpoints as config_endpoints
from agents.baseAgent import BaseAgent
from log_mongo import logger


class AgentManager:
    """A class to manage agents.

    Attributes
    ----------
    agents (Dict[str, BaseAgent]): A dictionary to store agents.

    Methods
    -------
    register_agent(agent_name: str, agent: BaseAgent): Registers an agent.
    get_agent(agent_name: str): Retrieves an agent by name.

    """

    def __init__(self):
        """Initializes the AgentManager instance."""
        self.agents = {}

    def register_agent(self, agent_name: str, agent: BaseAgent) -> None:
        """Registers an agent.

        Args:
        ----
        agent_name (str): The name of the agent.
        agent (BaseAgent): The agent instance.

        Raises:
        ------
        TypeError: If agent_name is not a string or agent is not a BaseAgent instance.

        """
        if not isinstance(agent_name, str):
            logger.error("Agent name must be a string.")
            raise TypeError("Agent name must be a string.")
        if not isinstance(agent, BaseAgent):
            logger.error("Agent must be a BaseAgent instance.")
            raise TypeError("Agent must be a BaseAgent instance.")

        self.agents[agent_name] = agent
        logger.info(f"Agent {agent_name} registered.")

    def get_agent(self, agent_name: str) -> BaseAgent:
        """Retrieves an agent by name.

        Args:
        ----
        agent_name (str): The name of the agent.

        Returns:
        -------
        BaseAgent: The agent instance if found, otherwise None.

        Raises:
        ------
        TypeError: If agent_name is not a string.

        """
        if not isinstance(agent_name, str):
            logger.error("Agent name must be a string.")
            raise TypeError("Agent name must be a string.")

        agent = self.agents.get(agent_name)
        if agent is None:
            logger.error(f"Agent {agent_name} not found.")
        return agent
