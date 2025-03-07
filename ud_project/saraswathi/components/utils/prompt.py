# Function to format the column metadata as prompt
def generate_column_information_prompt(
    column_description_dict: dict,
    column_sample_dict: dict,
    column_display_name_dict: dict,
    column_n_unique_value_dict: dict,
    column_data_tribes: dict,
) -> str:
    col_names = list(column_description_dict.keys())

    column_information_prompt = "Column Information (column name, column display name, column sample value, column number of unique value):\n"

    if col_names == []:
        raise ValueError("No column information extracted!")

    for col_name in col_names:
        column_information_prompt += f"- {col_name} (Display Name: {column_display_name_dict[col_name]}): {column_description_dict[col_name]} (e.g., {column_sample_dict[col_name]}). Number of Unique Values: {column_n_unique_value_dict[col_name]}. Column Data Tribes: {column_data_tribes[col_name]}\n"

    return column_information_prompt
