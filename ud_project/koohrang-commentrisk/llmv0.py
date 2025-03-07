from basellm import OpenAIClient
from maxtokens import num_tokens_from_string


class VMLLM:
    """A class to interact with the virtual machine LLM model API.

    Attributes:
    base_url (str): The base URL of the OpenAI API.
    api_key (str): The API key for authentication.
    model (str): The model name to use for completion.
    logger: A logger instance to log system events.
    openai_client: An instance of the OpenAIClient class.

    """

    def __init__(self, base_url: str, api_key: str, model: str, logger):
        """Initializes a new instance of the virtual machine LLM class.

        Args:
        base_url (str): The base URL of the OpenAI API.
        api_key (str): The API key for authentication.
        model (str): The model name to use for completion.
        logger: A logger instance to log system events.

        """
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.logger = logger
        self.openai_client = OpenAIClient(base_url, api_key, model)

    def _create_prompt(self, system_prompt: str, question: str) -> list:
        """Creates a list of messages for ChatCompletion by combining the system prompt and the question.

        Args:
            system_prompt (str): The system prompt to use.
            question (str): The question to ask.

        Returns:
            list: A list of dictionaries representing the messages.
        """
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]

    def _calculate_max_tokens(self, question: str) -> int:
        """Calculates the maximum number of tokens for a given question.

        Args:
        question (str): The question to ask.

        Returns:
        int: The maximum number of tokens.

        """
        return 3900 - num_tokens_from_string(question, "gpt-3.5-turbo")

    def call_api(self, system_prompt: str, question: str):
        """Calls the OpenAI API with a prompt and returns the response.

        Args:
        system_prompt (str): The system prompt to use.
        question (str): The question to ask.

        Returns:
        str: The response from the API.

        Raises:
        Exception: If an error occurs while calling the API.

        """
        try:
            prompt = self._create_prompt(system_prompt, question)
            max_tokens = self._calculate_max_tokens(question)
            completion = self.openai_client.create_completion(prompt, max_tokens, 0.1)
            response = completion.choices[0].message.content
            return response
        except Exception as e:
            self.logger.error("Error calling OpenAI API: {}", e)
            raise
