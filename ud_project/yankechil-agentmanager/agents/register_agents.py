from typing import Any, Dict

from dotenv import load_dotenv

from manager.manager import AgentManager

load_dotenv()


import logging

logger = logging.getLogger(__name__)


def create_agent_manager_v0(agent_configs: Dict[str, Dict[str, Any]]) -> AgentManager:
    """Create an instance of AgentManager and register all agents dynamically.

    Args:
        agent_configs (Dict[str, Dict[str, Any]]): Configuration for agents with keys as agent names
            and values as dictionaries containing agent class and initialization arguments.

    Returns:
        AgentManager: Instance of AgentManager with all agents registered.

    """
    logger.info("Starting agent manager creation.")
    agent_manager = AgentManager()

    total_agents = len(agent_configs)
    logger.info(f"Total agents to register: {total_agents}")

    for agent_name, config in agent_configs.items():
        if "class" not in config:
            raise KeyError(f"Missing 'class' for agent {agent_name}")
        if "init_args" not in config:
            raise KeyError(f"Missing 'init_args' for agent {agent_name}")

        try:
            agent_class = config["class"]
            init_args = config.get("init_args", {})

            logger.info(
                f"Creating agent: {agent_name} with class {agent_class} and init_args {init_args}",
            )

            # Create agent instance
            agent_instance = agent_class(**init_args)

            # Ensure the agent_name is a string before registering
            agent_manager.register_agent(str(agent_name), agent_instance)
            logger.info(f"Agent {agent_name} successfully registered.")

        except Exception as e:
            logger.error(f"Error creating or registering agent {agent_name}: {e}")

    logger.info("Finished creating and registering agents.")
    return agent_manager
