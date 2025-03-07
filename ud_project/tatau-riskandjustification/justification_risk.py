import os
import textwrap
import json
import re
from abc import ABC, abstractmethod

from dotenv import load_dotenv

import config
from llmv0 import VMLLM
from log_mongo import logger

load_dotenv()


LLAMA_BASE_URL = os.getenv("LLAMA_BASE_URL")
LLAMA_MODEL = os.getenv("LLAMA_MODEL")
LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")

if not LLAMA_API_KEY:
    logger.error("OpenAI API key not found")


def has_text(s):
    """Check if the input text contains non-whitespace characters."""
    return bool(s and s.strip())  # Ensures that text is not empty or whitespace only


def check_list(text):
    """Check if the text doesn't contain the 'None, None, None' placeholder."""
    return "None, None, None" not in text


class ResultParser:
    """A class responsible for parsing results."""

    @staticmethod
    def parse_justification_risk_results(llm_result):
        """Parses the result of the justification and risk analysis.

        Args:
        llm_result (str or dict): The result of the analysis.

        Returns:
        tuple: A tuple containing the justification and risk level, or an error.
        """
        try:
            # Log the raw result for debugging
            logger.debug(f"Raw llm_result: {llm_result}")

            # Clean up backticks and extract JSON portion
            if isinstance(llm_result, str):
                # Remove backticks and language specifier
                cleaned_result = re.sub(r"^```[a-z]*\n|```$", "", llm_result.strip())

                # Extract JSON portion (assume it's the first JSON block)
                match = re.search(r"\{.*\}", cleaned_result, re.DOTALL)
                if match:
                    cleaned_result = match.group(0)
                else:
                    raise ValueError("No JSON block found in the result.")

                # Attempt JSON parsing
                llm_result = json.loads(cleaned_result)

            # Ensure llm_result is a dictionary
            if not isinstance(llm_result, dict):
                raise ValueError("Parsed result is not a dictionary.")

            # Extract values from the dictionary
            English_justification = llm_result.get("English Justification", "Missing")
            Malay_justification = llm_result.get(
                "Bahasa Malay Justification", "Missing"
            )
            Risk_level = llm_result.get("Risk Level", "Missing")
            Irrelevant_score = llm_result.get("Irrelevant Score", "Missing")

            return (
                English_justification,
                Malay_justification,
                Risk_level,
                Irrelevant_score,
            )
        except Exception as e:
            # Log any errors
            logger.error(f"Error parsing results: {e!s}")
            return {"error": str(e)}


# Define an abstract base class for text analyzers
class JustificationAnalyzer(ABC):
    @abstractmethod
    def analyze(self):
        """Analyze the given texts and return the analysis results."""


def openai_llama_vm(system_prompt, user_prompt):
    """Calls the virtual machine OpenAI LLaMA API with a system prompt and a question."""
    try:
        # Create a VMLLM object with the API endpoint, key, model, and logger
        llama_api = VMLLM(
            os.getenv("LLAMA_BASE_URL"),
            os.getenv("LLAMA_API_KEY"),
            os.getenv("LLAMA_MODEL"),
            logger,
        )
        # Call the API with the system prompt and question
        response = llama_api.call_api(system_prompt, user_prompt)
        # Return the API response
        return response
    except Exception as e:
        # Log any errors
        logger.error(f"Error LLaMA response: {e!s}")
        return {"error": str(e)}


class JustificationAndRiskLevelV0(JustificationAnalyzer):
    def __init__(self, system_prompt, labels):
        self.system_prompt = system_prompt
        self.labels = labels
        self.English_justification = ""
        self.Malay_justification = ""
        self.Risk_status = ""
        self.Irrelevant_score = ""

    def justification_risk_prompt_generation(
        self,
        text: str,
        risk_labels: list,
    ) -> str:
        """Generates the system prompt for justification and risk analysis."""
        try:
            risk_labels_str = ", ".join(risk_labels)
            prompt = textwrap.dedent(f"""
                                        {config.user_prompt_desc}

                                        text: {text}

                                        Output:
                                    """)
            return prompt
        except Exception as e:
            logger.error(f"Error prompt generation: {e!s}")
            return {"error": str(e)}

    def analyze(self, text: str):
        """Analyze the Justification and Risk Level of a given text."""
        try:
            # Check if the text is invalid or empty
            if text is None or not has_text(text):
                logger.warning("Text is None, empty, or invalid. Skipping analysis.")
                return {
                    "English Justification": "Missing",
                    "Bahasa Malay Justification": "Missing",
                    "Risk Level": "Missing",
                    "Irrelevant Score": "Missing",
                }

            logger.info("Analyzing text...")
            self.user_prompt = self.justification_risk_prompt_generation(
                text,
                self.labels,
            )

            res = self.check_and_get_four_results(
                text,
                max_retries=config.max_retries,
            )
            return res
        except Exception as e:
            logger.error(f"Error analyzing text: {e!s}")
            return {"error": str(e)}

    def check_and_get_four_results(
        self,
        text,
        max_retries=config.max_retries,
    ):
        """Checks and retries the analysis until valid results are returned."""
        try:
            # Default values for missing analysis results
            (
                english_justification,
                malay_justification,
                risk_status,
                irrelevant_score,
            ) = (
                "None",
                "None",
                "None",
                "None",
            )
            retries = 0
            if check_list(text):
                while retries <= max_retries:
                    try:
                        if has_text(text):
                            res = openai_llama_vm(
                                config.system_prompt,
                                self.user_prompt,
                            )
                            results = ResultParser.parse_justification_risk_results(res)

                            if len(results) == 4:
                                (
                                    english_justification,
                                    malay_justification,
                                    risk_status,
                                    irrelevant_score,
                                ) = results
                                break
                            logger.warning(
                                f"Analysis returned {len(results)} outputs, expected 4. Retrying...",
                            )
                            retries += 1
                        else:
                            break
                    except Exception as e:
                        logger.error(
                            f"Error analyzing justification and risk status: {e}",
                        )
                        retries += 1

                return (
                    english_justification,
                    malay_justification,
                    risk_status,
                    irrelevant_score,
                )
        except Exception as e:
            logger.error(f"Error analyzing text: {e!s}")
            return {"error": str(e)}
