import os


def load_and_verify_env_var(
    var_name: str, default_value=None, var_type=str, allowed_values=None, required=False
):
    """
    Load and verify an environment variable with additional checks for mandatory values.

    :param var_name: The name of the environment variable.
    :param default_value: The default value to return if the variable is not set and it's not required.
    :param var_type: The expected type of the variable (e.g., int, float, str). Defaults to str.
    :param allowed_values: Optional list or set of allowed values for validation.
    :param required: If True, the environment variable is mandatory, and an exception is raised if it's missing.
    :return: The verified value of the environment variable.
    :raises ValueError: If the environment variable value is invalid or type conversion fails, or if the variable is required but not set.
    """
    try:
        # Load environment variable
        value = os.getenv(var_name, default_value)

        # Check if the variable is required and not set
        if value is None and required:
            raise ValueError(
                f"Environment variable '{var_name}' is required but not set."
            )

        # If value is None and not required, return default_value
        if value is None:
            return default_value

        # Convert the value to the specified type
        if var_type is not str:  # Skip conversion if the expected type is str
            value = var_type(value)

        # Validate against allowed values, if provided
        if allowed_values is not None and value not in allowed_values:
            raise ValueError(
                f"Environment variable '{var_name}' has an invalid value: {value}. "
                f"Allowed values are: {allowed_values}"
            )

        return value
    except Exception as e:
        raise ValueError(f"Error loading environment variable '{var_name}': {e}")
