import sys

sys.stdout.reconfigure(encoding="utf-8")
import concurrent.futures

# import schedule
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from agents.Agents import AgentsNameV0

# from config.config_num import Num
# import config_endpoints as config_endpoints
from log_mongo import logger


class AgentsNameV1(Enum):
    """Enum class for tiktok Agents Names"""

    summary = "summary"
    Amu = "Amu"
    sentiment = "sentiment"
    justification = "justification"
    law_regulated = "law_regulated"
    comment_risk = "comment_risk"

    @classmethod
    def list_agents(cls):
        """Return a list of all agent names."""
        return [member.name for member in cls]


# Define the Module interface
class AgentsProcess(ABC):
    def __init__(self, agent_manager: object):
        """Initialize the AgentsProcess with an agent manager.

        Args:
        agent_manager (object): An instance of the agent manager.

        """
        self.agent_manager = agent_manager

    @abstractmethod
    def _execute_agent(
        self,
        agent,
        inputs: Dict[str, Any],
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
    ):
        pass

    @abstractmethod
    def _get_agent(self, agent_name: AgentsNameV0):
        pass


class AgentsProcessV0(AgentsProcess):
    """Class for processing agents."""

    def __init__(self, agent_manager):
        super().__init__(agent_manager)

    def check_agent_health(self, agent_name: str, agent_instance) -> tuple:
        """Check the health of a single agent and return a tuple of agent name and its health status.

        Args:
            agent_name (str): The name of the agent.
            agent_instance: The agent instance to check.

        Returns:
            tuple: A tuple with the agent name and its health status (True or False).

        """
        try:
            # Perform health check
            health_check_response = agent_instance.health_check()
            if health_check_response.get("status") == "healthy":
                return agent_name, True
            logger.error(f"Agent {agent_name} health check failed.")
            return agent_name, False
        except Exception as e:
            logger.error(f"Failed to check health for agent {agent_name}: {e}")
            return agent_name, False

    def check_agents_health(self, agent_names: List[str] = None) -> Dict[str, bool]:
        """Check the health of all agents or specific agents provided in a list.

        Args:
            agent_names (List[str], optional): A list of agent names to check. If None, checks all agents.

        Returns:
            Dict[str, bool]: A dictionary where keys are agent names and values are True if the agent is running, otherwise False.

        """
        agent_health_status = {}

        try:
            if agent_names:  # If a list of agent names is provided
                agent_names = [
                    name.strip() for name in agent_names
                ]  # Ensure agent names are stripped of whitespace

                # Using ThreadPoolExecutor to check agents concurrently
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = []
                    for agent_name in agent_names:
                        try:
                            agent_name_str = AgentsNameV1[agent_name].name
                            agent_instance = self._get_agent(agent_name_str)
                            if agent_instance:
                                futures.append(
                                    executor.submit(
                                        self.check_agent_health,
                                        agent_name_str,
                                        agent_instance,
                                    ),
                                )
                            else:
                                logger.error(
                                    f"Agent {agent_name_str} is not available.",
                                )
                                agent_health_status[agent_name_str] = False
                        except KeyError:
                            logger.error(f"Invalid agent name provided: {agent_name}")
                            agent_health_status[agent_name] = False
                        except Exception as e:
                            logger.error(
                                f"Failed to check health for agent {agent_name}: {e}",
                            )
                            agent_health_status[agent_name] = False

                    # Collect the results
                    for future in concurrent.futures.as_completed(futures):
                        agent_name, health_status = future.result()
                        agent_health_status[agent_name] = health_status

                    print(agent_health_status)

            else:  # If no list is provided, check all agents
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = []
                    for agent_name_enum in AgentsNameV1:
                        try:
                            agent_name_str = agent_name_enum.name
                            agent_instance = self._get_agent(agent_name_str)
                            if agent_instance:
                                futures.append(
                                    executor.submit(
                                        self.check_agent_health,
                                        agent_name_str,
                                        agent_instance,
                                    ),
                                )
                            else:
                                logger.error(
                                    f"Agent {agent_name_str} is not available.",
                                )
                                agent_health_status[agent_name_str] = False
                        except Exception as e:
                            logger.error(
                                f"Failed to check health for agent {agent_name_str}: {e}",
                            )
                            agent_health_status[agent_name_str] = False

                    # Collect the results
                    for future in concurrent.futures.as_completed(futures):
                        agent_name, health_status = future.result()
                        agent_health_status[agent_name] = health_status

        except Exception as e:
            logger.error(f"Error checking agents health: {e}")

        return agent_health_status

    def _get_agent(self, agent_name: AgentsNameV0) -> Optional[object]:
        """Get an agent from the agent manager.

        Args:
        agent_name (AgentsNameV0): The name of the agent.

        Returns:
        object: The agent instance.

        """
        try:
            agent = self.agent_manager.get_agent(agent_name)
            if not agent:
                logger.error(
                    f"Agent {agent_name.name} is not registered in the manager.",
                )
            return agent
        except Exception as e:
            logger.error(f"Failed to get agent {agent_name.name}: {e}")
            return None

    def _execute_agent(
        self,
        agent: object,
        inputs: Dict[str, Any],
        method: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Execute an agent with the given inputs.

        Args:
            agent (object): The agent instance.
            inputs (Dict[str, Any]): The inputs for the agent.
            method (str): Optional HTTP method ("GET", "POST", etc.).
            headers (Dict[str, str]): Optional HTTP headers.

        Returns:
            Optional[Dict[str, Any]]: The response from the agent.

        """
        try:
            # Adjust the call based on what the agent supports
            if method and headers:
                logger.warning(
                    "`method` and `headers` are ignored unless supported by the agent.",
                )

            # Attempt to execute the agent
            return agent.execute(inputs)  # Standard execute call
        except TypeError as te:
            logger.error(f"Agent execution failed due to unexpected arguments: {te}")
        except Exception as e:
            logger.error(f"Failed to execute agent: {e}")
        return None

    def get_summary_output(self, text: str) -> Optional[str]:
        """Get the summary output for a video.

        Args:
        text (str): Input text for summarization.

        Returns:
        str: The summary output for the video.

        """
        if not text:
            logger.error("Invalid input for get_summary_output")
            return None

        summary_inputs = {"text": text}
        agent = self._get_agent(AgentsNameV0.summary)
        if not agent:
            return None

        # summary_response = self._execute_agent(agent, summary_inputs, method="POST")
        summary_response = self._execute_agent(agent, summary_inputs)
        if not summary_response:
            return None

        return summary_response.get("summary")

    def get_category_output(self, text: str) -> Optional[Dict[str, Any]]:
        """Get the category output for a video summary.

        Args:
        text (str): Input text for categorization.

        Returns:
        dict: A dictionary containing the category and subcategory.

        """
        if not text:
            logger.error("Invalid input for get_category_output")
            return None

        category_inputs = {"text": text}
        agent = self._get_agent(AgentsNameV0.category)
        if not agent:
            logger.error(f"Agent not found with the name {AgentsNameV0.category}.")
            return None

        # category_response = self._execute_agent(agent, category_inputs, method="GET")
        category_response = self._execute_agent(agent, category_inputs)
        if not category_response:
            logger.error("No response from category agent.")
            return None

        return category_response

    def get_sentiment_output(self, text: str) -> Optional[Dict[str, Any]]:
        """Get the sentiment output for a video summary.

        Args:
        text (str): Input text for sentiment analysis.

        Returns:
        dict: The sentiment output.

        """
        if not text:
            logger.error("Invalid input for get_sentiment_output")
            return None

        sentiment_inputs = {"text": text}
        agent = self._get_agent(AgentsNameV0.sentiment)
        if not agent:
            return None

        # sentiment_response = self._execute_agent(agent, sentiment_inputs, method="GET")
        sentiment_response = self._execute_agent(agent, sentiment_inputs)
        if not sentiment_response:
            return None

        return sentiment_response

    def get_justification_risk_output(self, text: str) -> Optional[Dict[str, Any]]:
        """Get the justification and risk output for a video.

        Args:
        text (str): Input text for justification and risk assessment.

        Returns:
        dict: A dictionary containing justification and risk details.

        """
        if not text:
            logger.error("Invalid input for get_justification_risk_output")
            return None

        justification_inputs = {"text": text}
        agent = self._get_agent(AgentsNameV0.justification)
        if not agent:
            return None

        # justification_response = self._execute_agent(agent, justification_inputs, method="GET")
        justification_response = self._execute_agent(agent, justification_inputs)
        if not justification_response:
            return None

        return justification_response

    def get_law_regulated_output(self, text: str) -> Optional[Dict[str, Any]]:
        """Get the law regulated output for a video.

        Args:
        text (str): Input text for law compliance evaluation.

        Returns:
        dict: The law regulated output.

        """
        if not text:
            logger.error("Invalid input for get_law_regulated_output")
            return None

        law_inputs = {"text": text}
        agent = self._get_agent(AgentsNameV0.law_regulated)
        if not agent:
            return None

        # law_response = self._execute_agent(agent, law_inputs, method="POST")
        law_response = self._execute_agent(agent, law_inputs)
        if not law_response:
            return None

        return law_response

    def get_comment_risk_output(self, text: str) -> Optional[Dict[str, Any]]:
        """Get the risk output for a video comment.

        Args:
        text (str): Input text for risk analysis.

        Returns:
        dict: A dictionary containing the risk status.

        """
        if not text:
            logger.error("Invalid input for get_comment_risk_output")
            return None

        comment_risk_inputs = {"text": text}
        agent = self._get_agent(AgentsNameV0.comment_risk)
        if not agent:
            return None

        # comment_response = self._execute_agent(agent, comment_risk_inputs, method="GET")
        comment_response = self._execute_agent(agent, comment_risk_inputs)
        if not comment_response:
            return None

        return comment_response

    def get_law_regulated_output_v1(
        self,
        doc_ids: list,
        text: str,
    ) -> Optional[Dict[str, Any]]:
        """Get the law regulated output with documents for a video.

        Args:
        doc_ids (list): List of document IDs.
        text (str): Input text for law compliance evaluation.

        Returns:
        dict: The law regulated output.

        """
        if not text or not doc_ids:
            logger.error("Invalid input for get_law_regulated_output_v1")
            return None

        law_inputs = {"document_ids": doc_ids, "text": text}
        agent = self._get_agent(AgentsNameV0.law_regulated)
        if not agent:
            return None

        # law_response = self._execute_agent(agent, law_inputs, method="POST")
        law_response = self._execute_agent(agent, law_inputs)
        if not law_response:
            return None

        return law_response
