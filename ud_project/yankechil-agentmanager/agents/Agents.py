from typing import Any, Dict

import requests
from dotenv import load_dotenv

from agents.baseAgent import BaseAgent
from log_mongo import logger

load_dotenv()


class AgentsNameV0:
    """Enum class for tiktok Agents Names"""

    summary = "summary"
    category = "Amu"
    sentiment = "sentiment"
    justification = "justification"
    law_regulated = "law_regulated"
    comment_risk = "comment_risk"


# Define a function to check connection
def check_connection(url: str) -> bool:
    """Check if a connection can be established with the given URL
    :param url: URL to check connection
    :return: True if connection is successful, False otherwise
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return True
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {e}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return False


class SummaryAgent(BaseAgent):
    def __init__(self, url: str):
        super().__init__(AgentsNameV0.summary, url)

    def execute(self, params: Dict) -> Dict[str, Any]:
        return super().execute(params, method="POST")

    def health_check(self) -> Dict[str, Any]:
        """Perform a basic health check for the agent."""
        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(self.url, json={"text": "This video is very good"}, headers=headers)
            if response.status_code == 200:
                return {"status": "healthy"}
            return {"status": "unhealthy"}
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            return {"status": "unhealthy"}


class SentimentAgent(BaseAgent):
    def __init__(self, url: str):
        super().__init__(AgentsNameV0.sentiment, url)

    def execute(self, params: Dict) -> Dict[str, Any]:
        return super().execute(params, method="GET")

    def health_check(self) -> Dict[str, Any]:
        """Perform a basic health check for the agent."""
        try:
            response = requests.get(self.url, params={"text": "Happy day"})
            if response.status_code == 200:
                return {"status": "healthy"}
            return {"status": "unhealthy"}
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            return {"status": "unhealthy"}


class CategoryAgent(BaseAgent):
    def __init__(self, url: str):
        super().__init__(AgentsNameV0.category, url)

    def execute(self, params: Dict) -> Dict[str, Any]:
        return super().execute(params, method="GET")

    def health_check(self) -> Dict[str, Any]:
        """Perform a basic health check for the agent."""
        try:
            response = requests.get(self.url, params={"text": "I like royal family"})
            if response.status_code == 200:
                return {"status": "healthy"}
            return {"status": "unhealthy"}
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            return {"status": "unhealthy"}


class LawRegulatedAgent(BaseAgent):
    def __init__(self, url: str):
        super().__init__(AgentsNameV0.law_regulated, url)

    def execute(self, params: Dict) -> Dict[str, Any]:
        return super().execute(params, method="POST")

    def health_check(self) -> Dict[str, Any]:
        """Perform a basic health check for the agent."""
        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                self.url,
                json={"document_ids": ["Penal_Code.json.law_document.extraction.test", 
                                    "akta-15-akta-hasutan-1948.v1.en.law_document"], "text": "This is video summary"},
                headers=headers,
            )
            if response.status_code == 200:
                return {"status": "healthy"}
            return {"status": "unhealthy"}
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            return {"status": "unhealthy"}


class JustificationAgent(BaseAgent):
    def __init__(self, url: str):
        super().__init__(AgentsNameV0.justification, url)

    def execute(self, params: Dict) -> Dict[str, Any]:
        return super().execute(params, method="GET")

    def health_check(self) -> Dict[str, Any]:
        """Perform a basic health check for the agent."""
        try:
            response = requests.get(self.url, params={"text": "none"})
            if response.status_code == 200:
                return {"status": "healthy"}
            return {"status": "unhealthy"}
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            return {"status": "unhealthy"}


class CommentRiskAgent(BaseAgent):
    def __init__(self, url: str):
        super().__init__(AgentsNameV0.comment_risk, url)

    def execute(self, params: Dict) -> Dict[str, Any]:
        return super().execute(params, method="GET")

    def health_check(self) -> Dict[str, Any]:
        """Perform a basic health check for the agent."""
        try:
            response = requests.get(self.url, params={"text": "none"})
            if response.status_code == 200:
                return {"status": "healthy"}
            return {"status": "unhealthy"}
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            return {"status": "unhealthy"}
