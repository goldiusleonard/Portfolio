from typing import Any, Dict

import requests

from log_mongo import logger


class BaseAgent:
    """Base class for all agents."""

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url

    def execute(
        self,
        params: Dict,
        method: str = "GET",
        headers: Dict = None,
    ) -> Dict[str, Any]:
        """Execute the agent with the given parameters and HTTP method.
        :param params: Parameters for the request
        :param method: HTTP method ('GET', 'POST', etc.)
        :param headers: Optional headers for the request
        :return: Response from the agent
        """
        if headers is None:
            headers = {"Content-Type": "application/json"}

        try:
            if method.upper() == "POST":
                response = requests.post(self.url, json=params, headers=headers)
            elif method.upper() == "GET":
                response = requests.get(self.url, params=params, headers=headers)
            else:
                # Add support for other HTTP methods if needed
                response = requests.request(
                    method.upper(),
                    self.url,
                    json=params,
                    headers=headers,
                )

            # Return the response JSON or an error
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Request to {self.url} failed: {e}")
            return {"error": str(e)}
