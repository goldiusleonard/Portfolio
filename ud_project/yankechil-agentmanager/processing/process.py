import json

import pandas as pd

from log_mongo import logger


def ensure_columns_exist(df: pd.DataFrame, columns: list, default_value="None"):
    """Ensure specified columns exist in the DataFrame."""
    for col in columns:
        if col not in df.columns:
            df[col] = default_value


# Function to recursively remove quotes from string values
def remove_quotes(value):
    if isinstance(value, str):
        # Remove all double quotes from the string
        return value.replace('"', "")
    if isinstance(value, list):
        # If it's a list, process each item
        return [remove_quotes(item) for item in value]
    if isinstance(value, dict):
        # If it's a dictionary, apply the function to each key-value pair
        return {key: remove_quotes(val) for key, val in value.items()}
    # Return the value as is if it's neither a string, list, nor dictionary
    return value


def handle_none_values(data):
    if not data:
        data = "None"  # Replace None with None string
    return data


def process_with_agent(agent_method, input_text, df, index, columns):
    """Generalized function to process data using an agent method and update the DataFrame."""
    try:
        # Get the response from the agent
        agent_response = agent_method(input_text)
        print(agent_response)
        if isinstance(agent_response, tuple):
            agent_response = agent_response[0]  # Unpack tuple response

        if isinstance(agent_response, dict):
            ensure_columns_exist(df, list(columns.keys()))
            for key, column_name in columns.items():
                # Check if the column_name has a dot, indicating a nested structure
                if "." in column_name:
                    keys = column_name.split(".")  # Split the nested key
                    value = agent_response  # Start with the full dictionary

                    # Navigate through the nested dictionary
                    for k in keys:
                        if isinstance(value, dict):
                            value = value.get(
                                k,
                                "None",
                            )  # Drill down into the nested dictionary
                        else:
                            value = "None"  # Fallback if the structure is unexpected

                else:
                    # For non-nested keys, simply get the value directly
                    value = agent_response.get(column_name, "None")
                if isinstance(value, list):
                    value = json.dumps(
                        value,
                        ensure_ascii=False,
                    )  # Convert lists to JSON strings
                df.loc[index, key] = str(handle_none_values(remove_quotes(value)))
        else:
            logger.error(f"Unexpected agent response format: {agent_response}")
    except Exception as e:
        logger.error(f"Error processing with agent: {e}")


# def process_with_agent(agent_method, input_text, df, index, columns):
#     """Generalized function to process data using an agent method and update the DataFrame."""
#     try:
#         # Get the response from the agent
#         agent_response = agent_method(input_text)
#         print(agent_response)
#         if isinstance(agent_response, tuple):
#             agent_response = agent_response[0]  # Unpack tuple response

#         if isinstance(agent_response, dict):
#             ensure_columns_exist(df, list(columns.keys()))
#             for key in columns:
#                 print(key)
#                 value = agent_response.get(key, "None")
#                 print(agent_response.get(key))
#                 print(f"key: {key}, value: ", value)
#                 if isinstance(value, list):
#                     value = json.dumps(value, ensure_ascii=False)  # Convert lists to JSON strings
#                 df.loc[index, key] = str(value)
#         else:
#             logger.error(f"Unexpected agent response format: {agent_response}")
#     except Exception as e:
#         logger.error(f"Error processing with agent: {e}")
