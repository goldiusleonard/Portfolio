from openai import Client as OpenAI


class OpenAIClient:
    """A client for interacting with the OpenAI API.

    Attributes:
        base_url (str): The base URL for the OpenAI API.
        api_key (str): Your OpenAI API key.
        model (str): The model to use for the API.
        client: An instance of the OpenAI client.

    Methods:
        _create_client: Creates an instance of the OpenAI client.
        create_completion: Creates a completion for a given prompt.

    """

    def __init__(self, base_url, api_key, model):
        """Initializes the OpenAIClient instance.

        Args:
            base_url (str): The base URL for the OpenAI API.
            api_key (str): Your OpenAI API key.
            model (str): The model to use for the API.

        """
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.client = self._create_client()

    def _create_client(self):
        """Creates an instance of the OpenAI client.

        Returns:
            An instance of the OpenAI client.

        """
        return OpenAI(base_url=self.base_url, api_key=self.api_key)

    def create_completion(self, prompt, max_tokens, temperature):
        """Creates a completion for a given prompt.

        Args:
            prompt (str): The prompt for the completion.
            max_tokens (int): The maximum number of tokens for the completion.
            temperature (float): The temperature for the completion.

        Returns:
            The completion response.

        """
        return self.client.chat.completions.create(
            model=self.model,
            messages=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )
