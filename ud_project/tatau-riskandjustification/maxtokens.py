import tiktoken


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Calculate the number of tokens for a given string based on the encoding of a specific model.

    Args:
        string (str): The input string to calculate tokens for.
        encoding_name (str): The name of the encoding to use for tokenization.

    Returns:
        int: The number of tokens in the input string based on the specified encoding.

    Raises:
        ValueError: If an invalid encoding name is provided.

    """
    try:
        encoding = tiktoken.encoding_for_model(encoding_name)
    except ValueError as e:
        raise ValueError(f"Invalid encoding name: {encoding_name}") from e

    num_tokens = len(encoding.encode(string))
    return num_tokens
