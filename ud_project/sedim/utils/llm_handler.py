"""Handles interaction with the LLM."""

from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from openai import OpenAI

if TYPE_CHECKING:
    from logger import Logger

MAX_RETRIES = 3


class LLMHandler:
    """Handles interaction with the LLM."""

    def __init__(self, logger: Logger) -> None:
        """Initialize the LLMHandler.

        :param logger: Logger instance
        """
        self.logger = logger
        load_dotenv(override=True)

        # Load environment variables
        llm_base_url: str = os.getenv("LLAMA31_70B_LLM_BASE_URL")
        llm_api_key: str = os.getenv("LLAMA31_70B_LLM_API_KEY")
        self.llm_model: str = os.getenv("LLAMA31_70B_MODEL")
        self.prompt_base_dir: str = os.getenv("PROMPT_BASE_DIRECTORY")

        # Initialize the LLM client
        self.llm_client: OpenAI = OpenAI(
            base_url=llm_base_url,
            api_key=llm_api_key,
        )

    def _read_prompt(self, category: str, prompt_type: str) -> str:
        """Read the prompt file (system/user) for a given category.

        :param category: Topic category for the prompt
        :param prompt_type: Type of prompt to read (system/user)
        :return: Formatted prompt string
        """
        file_path = Path(self.prompt_base_dir) / category / f"{prompt_type}.txt"
        try:
            with file_path.open() as file:
                return file.read()
        except FileNotFoundError:
            self.logger.exception("Prompt file not found: %s", file_path)
            raise

    def _prepare_prompt(
        self,
        prompt_category: str,
        **kwargs: str,
    ) -> str:
        """Prepare a complete prompt by reading system and user templates and formatting them.

        :param prompt_category: Topic category for the prompt
        :param kwargs: Keyword arguments to format the user prompt
        :return: Formatted prompt string
        """
        # Read prompts
        system_prompt = self._read_prompt(prompt_category, "system")
        user_prompt = self._read_prompt(prompt_category, "user")

        try:
            formatted_user_prompt = user_prompt.format(**kwargs)
        except KeyError:
            self.logger.exception("Missing key for user prompt formatting.")
            raise

        return f"{system_prompt}\n\n{formatted_user_prompt}"

    def send_to_llm(self, prompt: str) -> str:
        """Send the given prompt to the LLM and return the response.

        :param prompt: The prompt to send to the LLM
        :return: The response from the LLM
        """
        try:
            # Send the prompt to the LLM
            response = self.llm_client.completions.create(
                prompt=prompt,
                model=self.llm_model,
                max_tokens=100,
                temperature=0,
            )
            # Return the response from the LLM
            return response.choices[0].text.strip()
        except Exception:
            # Log any exceptions that occur during interaction with the LLM
            self.logger.exception("Error interacting with LLM:")
            return ""

    def get_prompt_topic_keywords(
        self,
        video_summary: str = "No description provided",
    ) -> str:
        """Format prompt for topic keywords generation."""
        return self._prepare_prompt(
            prompt_category="topic_keywords",
            video_summary=video_summary,
        )

    def get_prompt_topic_categories(
        self,
        topics: list[str],
        categories: list[str],
        subcategories: list[str],
        number_of_categories: int = 3,
    ) -> str:
        """Format prompt for topic categories generation."""
        number_of_categories_minus_one = number_of_categories - 1
        return self._prepare_prompt(
            prompt_category="topic_category",
            topics=topics,
            categories=categories,
            subcategories=subcategories,
            number_of_categories=number_of_categories,
            number_of_categories_minus_one=number_of_categories_minus_one,
        )

    def get_prompt_topic_assignment(
        self,
        topic: str = "No description provided",
        categories: list[str] | None = None,
    ) -> str:
        """Format prompt for topic assignment."""
        if categories is None:
            categories = ["No description provided"]
        return self._prepare_prompt(
            prompt_category="topic_assignment",
            topic=topic,
            categories=categories,
        )

    def call_llm_with_retry(
        self,
        prompt: str,
        video_id: str | None = None,
    ) -> str:
        """Call the LLM with retries in case of failures.

        :param prompt: The prompt to send to the LLM
        :param video_id: The video ID of the video for which the LLM is being called
        :return: The response from the LLM
        """
        # Make MAX_RETRIES attempts to call the LLM
        for attempt in range(1, MAX_RETRIES + 1):
            self.logger.debug(
                "LLM call attempt %d%s",
                attempt,
                f" for video_id: {video_id}" if video_id else "",
            )
            try:
                # Call the LLM and get the response
                response = self.send_to_llm(prompt)
                # Check if the response is in a valid format
                if self._is_valid_response(response):
                    # If the response is valid, return it
                    return response
            except Exception:
                # Log any exceptions that occur during the LLM call
                self.logger.exception(
                    "Error during LLM call%s on attempt %d:",
                    f" for video_id {video_id}" if video_id else "",
                    attempt,
                )
        # If MAX_RETRIES attempts have been made, log an error message
        # and return an empty string
        self.logger.error("Max retries reached. Returning empty response.")
        return ""

    @staticmethod
    def _is_valid_response(response: str) -> bool:
        """Determine if the response is valid based on predefined criteria.

        Checks the format of a given response string to assess its validity.
        A response is considered valid if it meets any of the following conditions:
        - It is enclosed in square brackets.
        - It starts with specific keywords such as "Output:" or "Category:".
        - It contains a colon character.
        - It consists of a single word.

        :param response: The response string to be validated.
        :return: True if the response is valid, False otherwise.
        """
        # Remove any leading or trailing whitespace from the response
        response = response.strip()

        # Check if the response meets any of the valid format criteria
        return (
            (
                response.startswith("[") and response.endswith("]")
            )  # Enclosed in brackets
            or response.startswith(
                ("Output:", "Category:"),
            )  # Starts with specific keywords
            or ":" in response  # Contains a colon
            or len(response.split()) == 1  # Single word response
        )

    def postprocess_llm_output(
        self,
        output: str,
        category: list[str] | None = None,
        sub_category: list[str] | None = None,
        prompt: str | None = None,
        video_id: str | None = None,
    ) -> list[str]:
        """Postprocess the LLM output to filter out invalid or forbidden terms.

        :param output: The raw output string from the LLM.
        :param category: List of forbidden category terms.
        :param sub_category: List of forbidden sub-category terms.
        :param prompt: The prompt to be used for retrying LLM call if needed.
        :param video_id: The video ID associated with the LLM call.
        :return: A list of clean, valid categories.
        """
        # Combine forbidden category and sub-category terms into a set
        forbidden_terms = set(
            [c.lower() for c in (category or [])]
            + [sc.lower() for sc in (sub_category or [])],
        )
        max_length = 3  # Maximum allowed words in a category

        # Attempt to process the output up to MAX_RETRIES times
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # Safely parse the output as a list of strings
                parsed_output = self._safe_parse_list(output)
                if parsed_output:
                    # Filter categories based on length and forbidden terms
                    clean_categories = [
                        cat
                        for cat in parsed_output
                        if len(cat.split()) <= max_length
                        and cat.lower() not in forbidden_terms
                    ]
                    if clean_categories:
                        return clean_categories
                    self.logger.warning(
                        "All categories are invalid or forbidden. Retrying...",
                    )
                else:
                    self.logger.warning("Output is not a valid list of strings.")
            except Exception:
                self.logger.exception("Error during post-processing.")

            # Retry with a new LLM call if a prompt is available
            self.logger.warning(
                "Invalid LLM output format detected. Retrying attempt %d/%d...",
                attempt,
                MAX_RETRIES,
            )
            if prompt:
                output = self.call_llm_with_retry(
                    prompt=prompt,
                    video_id=video_id,
                )
            else:
                break

        self.logger.error(
            "Postprocessing failed after %d retries. Returning empty list.",
            MAX_RETRIES,
        )
        return []

    @staticmethod
    def _safe_parse_list(output: str) -> list[str] | None:
        """Safely parse the output as a list of strings using `ast.literal_eval`.

        This method is used to safely parse the output from the LLM as a list of strings.
        It uses `ast.literal_eval` instead of `eval` to avoid any potential security issues.
        If the output is not a valid list of strings, it returns `None`.

        :param output: The output from the LLM.
        :return: A list of strings if the output is valid, otherwise `None`.
        """
        output = output.strip()
        try:
            parsed_output = ast.literal_eval(output)
            if isinstance(parsed_output, list) and all(
                isinstance(item, str) for item in parsed_output
            ):
                return parsed_output
        except (ValueError, SyntaxError):
            return None  # Invalid output format
        return None  # Output is not a list of strings
