import logging
import json
import tiktoken

logger = logging.getLogger("saraswati-agent")


def tokens_count_for_message(message, encoding):
    """Return the number of tokens used by a single message."""
    tokens_per_message = 3

    num_tokens = 0
    num_tokens += tokens_per_message
    for key, value in message.items():
        if key == "function_call":
            num_tokens += len(encoding.encode(value["name"]))
            num_tokens += len(encoding.encode(value["arguments"]))
        elif key == "content" or key == "name":
            num_tokens += len(encoding.encode(value))

    return num_tokens


def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613"):
    """Return the number of tokens used by a list of messages for both user and assistant."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")

    user_tokens = 0
    assistant_tokens = 0
    for i, message in enumerate(messages):
        # Check if the current message involves a service call
        is_service_call = "assistant" in message["role"]

        # Include tokens from previous messages only when a service call is made
        if is_service_call:
            assistant_tokens += tokens_count_for_message(message, encoding)
            for j in range(i):
                user_tokens += tokens_count_for_message(messages[j], encoding)

        # Count tokens for the current message
        user_tokens += tokens_count_for_message(message, encoding)

    assistant_tokens += 3  # every reply is primed with assistant

    return user_tokens, assistant_tokens, user_tokens + assistant_tokens


def calculate_token_usage(*texts, model="llama_3.1_70b"):
    """
    Calculates the total token usage for given texts, ensuring all inputs are converted to strings.

    Args:
        texts: Variable-length list of text inputs (can be strings, dictionaries, etc.).
        model (str): The model for which token encoding is calculated (default: "llama_3.1_70b").

    Returns:
        int: Total token usage for all texts combined.
    """
    # Load the encoding for a model. Assume cl100k_base as an approximation for Llama.
    encoding = tiktoken.get_encoding("cl100k_base")

    # Initialize total token count
    total_tokens = 0

    # Loop through each input and calculate token count
    for text in texts:
        # Convert non-string inputs (e.g., dict, list) to JSON strings
        if not isinstance(text, str):
            text = json.dumps(text, ensure_ascii=False)

        # Skip empty strings
        if text == "":
            continue

        # Encode the text to get tokens
        tokens = encoding.encode(text)

        # Add the number of tokens to the total
        total_tokens += len(tokens)

    # Return the total token count
    return total_tokens
