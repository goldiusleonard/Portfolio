import os


def get_env_variable(env_name: str, error_message: str) -> str:
    """Fetches an environment variable and raises an error if not set."""
    value = os.getenv(env_name, "")
    if not value:
        raise RuntimeError(error_message)
    return value
