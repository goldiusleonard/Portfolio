import ast
import os
import random
import re
import traceback
import pandas as pd
import requests

from typing import Any
from time import perf_counter
from pydantic import BaseModel, Field
from .general import check_negative_value
from .pandas import determine_date_frequency
from .token import calculate_token_usage


def adjust_axis_title_and_data(
    llama70b_client: Any,
    chart_id: str,
    chart_data: pd.DataFrame,
    chart_axis: dict,
    chart_title: str,
    logging_url: str,
):
    chart_data_columns = list(chart_data.columns)

    if "xAxis" in chart_data_columns:
        xAxis_column_name = "xAxis"
    elif (
        "xAxis_column" in chart_axis
        and isinstance(chart_axis["xAxis_column"], str)
        and chart_axis["xAxis_column"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_column"]
    elif (
        "xAxis_title" in chart_axis and chart_axis["xAxis_title"] in chart_data.columns
    ):
        xAxis_column_name = chart_axis["xAxis_title"]
    else:
        raise RuntimeError(
            "X-axis is not found in adjust_axis_title_and_data function!",
        )

    first_column = chart_data[xAxis_column_name]

    frequency, adjusted_dates = determine_date_frequency(first_column)

    if frequency == "daily":
        chart_axis["xAxis_title"] = "Date"
    elif frequency == "monthly":
        chart_axis["xAxis_title"] = "Month"
    elif frequency == "yearly":
        chart_axis["xAxis_title"] = "Year"
    else:
        chart_axis["xAxis_title"] = "Date"

    if "xAxis" in chart_data_columns:
        chart_data["xAxis"] = adjusted_dates
    elif (
        "xAxis_column" in chart_axis
        and isinstance(chart_axis["xAxis_column"], str)
        and chart_axis["xAxis_column"] in chart_data_columns
    ):
        chart_data[chart_axis["xAxis_column"]] = adjusted_dates

    for trial in range(1):
        try:
            chart_title = adjust_chart_title(
                llama70b_client,
                chart_id,
                chart_title,
                chart_axis["xAxis_title"],
                logging_url,
            )
            break
        except Exception:
            print(traceback.format_exc())

    return chart_data, chart_axis, chart_title


def adjust_chart_title(
    llama70b_client: Any,
    chart_id: str,
    chart_title: str,
    time_frame: str,
    logging_url: str,
):
    class Schema(BaseModel):
        chart_title: str = Field(
            ...,
            title="chart_title",
            description="The adjusted title for the chart.",
        )

    schema_json = Schema.model_json_schema()

    FORMAT_INSTRUCTIONS = """{"chart_title": "string"}"""

    prompt = f"""Acting as an experienced data analyst, edit the given chart title based on the given time frame (e.g., 'Monthly', 'Yearly', 'Weekly', 'Daily', 'Quarterly', etc). Each chart title given may contain time frame (e.g., 'quarterly', 'monthly', 'weekly', 'daily', 'yearly', 'annually', 'biweekly', 'bimonthly', etc) and/or time duration (e.g., '2022 - 2023', 'Past Two Years', '2024 H2', '2021 Q1 - 2022 Q2', 'January 2023 - March 2023', etc). Follow the instructions below in editing the given chart title.

- NEVER CHANGE or ADD ANY PART of the time duration such as 'Past Two Years' into 'Past Two Monthly'.
- Chart title MUST ONLY CONTAIN EXACTLY ONE time frame phrase. NEVER SPECIFY TIME FRAME using range or specific periods (e.g., 'Q1-Q4', 'Q1, Q2, Q3, Q4', 'January-December', etc).
- AVOID GENERATING incomplete time frame phrases. ENSURE GENERATING complete time frame phrases.
- ENSURE no DUPLICATE time frame phrases in the edited chart title.
- ENSURE chart title generated ALWAYS contain time frame (e.g., 'Quarterly', 'Weekly', 'Daily', 'Yearly', 'Anually', etc) WHEN x-axis of the chart derived from the chart title will be date related.
- ENSURE every chart titles generated are free from unreadable characters and suitable to be a chart title.

Chart Title: {chart_title}
Time Frame: {time_frame}

NEVER INCLUDE ANY EXPLANATIONS or NOTES on your response. ENSURE the chart title is generated in a VALID JSON dictionary format given below.

{FORMAT_INSTRUCTIONS}

"""
    start_narrative = perf_counter()

    messages = [{"role": "user", "content": prompt}]

    response = (
        llama70b_client.chat.completions.create(
            messages=messages,
            model=os.getenv("LLAMA70B_MODEL"),
            max_tokens=100,
            temperature=0.2,
            extra_body={
                "guided_json": schema_json,
            },
        )
        .choices[0]
        .message.content
    )

    input_tokens = 0
    output_tokens = 0

    input_tokens = calculate_token_usage(prompt)
    output_tokens = calculate_token_usage(response)

    adjust_chart_title_inference_time = perf_counter() - start_narrative

    MODULEID_ADJUST_CHART_TITLE = os.getenv("MODULEID_ADJUST_CHART_TITLE", "")

    if MODULEID_ADJUST_CHART_TITLE == "":
        raise ValueError("MODULEID_ADJUST_CHART_TITLE is invalid!")

    formatted_data = {
        "chart_id": chart_id,
        "module_id": int(MODULEID_ADJUST_CHART_TITLE),
        "messages": messages,
        "output": response,
        "inference_time": adjust_chart_title_inference_time,
        "llm_model": os.getenv("LLAMA70B_MODEL"),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }

    logging_url = logging_url + "chart-llm-calls"
    requests.put(
        logging_url,
        json=formatted_data,
        verify=False,
    )

    try:
        pattern: str = r"\{[^{}]*\}"
        match = re.search(pattern, response)

        if match is None:
            raise RuntimeError("Adjust chart title is not generated correctly!")

        json_string: str = match.group()
        json_string = json_string.replace("None", "null")
        json_string = json_string.replace("NaN", "null")
        json_string = json_string.replace(r"\_", "_")
        json_string = json_string.replace("\\\\_", "_")
        json_string = json_string.replace("’", "'")
        json_string = json_string.replace('" "', '""')
        json_string = json_string.strip()
        result = ast.literal_eval(json_string)
        new_chart_title = result["chart_title"]
    except Exception:
        print("Error Adjust Chart Title Response")
        print(response)
        print(traceback.format_exc())
        raise RuntimeError("Adjust chart title is not generated correctly!")

    return new_chart_title


# Remove Duplicate Chart in single visual (e.g., chart 1 and chart 2 in visual 1)
def remove_duplicate_charts(chart_json: list) -> list:
    chart_temp: dict = {}

    new_chart_json = chart_json.copy()

    # Start from sub chart one
    for chart_idx, chart in enumerate(chart_json, start=0):
        chart_type = chart["Chart_Type"]

        if chart_type not in chart_temp:
            chart_temp[chart_type] = [chart]
        elif chart_type in ["bar_chart", "pyramidfunnel_chart", "pie_chart"]:
            chart_temp_data_list = chart_temp[chart_type]

            for chart_temp_data in chart_temp_data_list:
                if (
                    chart["X"] == chart_temp_data["X"]
                    and chart["Y"] == chart_temp_data["Y"]
                ):
                    chart_type_replace_choice = [
                        "bar_chart",
                        "pyramidfunnel_chart",
                        "pie_chart",
                    ]
                    chart_type_replace_choice.remove(chart_type)

                    # Pie chart looks not good with more than 8 categories
                    if len(chart["X"]) > 8:
                        if "pie_chart" in chart_type_replace_choice:
                            chart_type_replace_choice.remove("pie_chart")

                        if "pyramidfunnel_chart" in chart_type_replace_choice:
                            chart_type_replace_choice.remove("pyramidfunnel_chart")

                    selected_new_chart_type = random.choice(
                        chart_type_replace_choice,
                    )

                    if selected_new_chart_type == chart_type:
                        new_chart_json.remove(chart)
                    else:
                        new_chart_json[chart_idx]["Chart_Type"] = (
                            selected_new_chart_type
                        )
                    break
        elif (
            chart_type in ["column_chart"]
            or chart_type in ["histogram_chart"]
            or chart_type in ["scatterplot_chart"]
            or chart_type in ["TreemapMulti_chart"]
        ):
            chart_temp_data_list = chart_temp[chart_type]
            for chart_temp_data in chart_temp_data_list:
                if (
                    chart["X"] == chart_temp_data["X"]
                    and chart["Y"] == chart_temp_data["Y"]
                ):
                    new_chart_json.remove(chart)
                    break
        elif chart_type in [
            "area_chart",
            "line_chart",
            "radar_chart",
            "grouped_column_chart",
            "grouped_bar_chart",
            "spline_chart",
        ]:
            chart_temp_data_list = chart_temp[chart_type]

            for chart_temp_data in chart_temp_data_list:
                if (
                    chart["X"] == chart_temp_data["X"]
                    and chart["Y"] == chart_temp_data["Y"]
                ):
                    chart_type_replace_choice = [
                        "area_chart",
                        "line_chart",
                        "radar_chart",
                        "grouped_column_chart",
                        "grouped_bar_chart",
                    ]
                    chart_type_replace_choice.remove(chart_type)

                    has_negative = False
                    for key in chart.keys():
                        if not re.search(r"Y([23456789])?", key, re.IGNORECASE):
                            continue

                        if check_negative_value(chart[key]):
                            has_negative = True
                            break

                    if has_negative:
                        if chart_type == "grouped_column_chart":
                            new_chart_json.remove(chart)

                        break

                    selected_new_chart_type = random.choice(
                        chart_type_replace_choice,
                    )

                    if selected_new_chart_type == chart_type:
                        new_chart_json.remove(chart)
                    else:
                        new_chart_json[chart_idx]["Chart_Type"] = (
                            selected_new_chart_type
                        )
                    break
        elif chart_type in ["barlinecombo_chart"]:
            chart_temp_data_list = chart_temp[chart_type]
            for chart_temp_data in chart_temp_data_list:
                if (
                    chart["X"] == chart_temp_data["X"]
                    and chart["Y"] == chart_temp_data["Y"]
                ):
                    new_chart_json.remove(chart)
                    break
        elif chart_type in [
            "table_chart",
            "full_table_chart",
            "aggregated_table_chart",
        ]:
            chart_temp_data_list = chart_temp[chart_type]
            for chart_temp_data in chart_temp_data_list:
                if chart["data"] == chart_temp_data["data"]:
                    new_chart_json.remove(chart)
                    break
        elif chart_type in ["card_chart"]:
            chart_temp_data_list = chart_temp[chart_type]
            for chart_temp_data in chart_temp_data_list:
                if chart["Y"] == chart_temp_data["Y"]:
                    new_chart_json.remove(chart)
                    break
        else:
            raise RuntimeError(
                f"'{chart_type}' Chart Type is not supported in Remove Duplicate Charts!",
            )

    # Rearrange chart position
    for new_chart_json_data_idx, new_chart_json_data in enumerate(new_chart_json):
        new_chart_json[new_chart_json_data_idx]["Chart_Position"] = str(
            new_chart_json_data_idx + 1,
        )

    return new_chart_json


def change_main_chart(
    chart_json: list,
) -> list:
    # Only 1 chart
    if len(chart_json) == 1:
        pass
    # Multiple charts
    else:
        new_main_chart_json = {}
        highest_data_point = 1
        highest_data_point_position = 0

        for chart_json_data_idx, chart_json_data in enumerate(chart_json[1:], start=1):
            chart_type = chart_json_data["Chart_Type"]
            if chart_type == "card_chart":
                continue

            if chart_type in [
                "bar_chart",
                "pyramidfunnel_chart",
                "pie_chart",
                "column_chart",
                "scatterplot_chart",
                "area_chart",
                "line_chart",
                "radar_chart",
                "grouped_column_chart",
                "grouped_bar_chart",
                "TreemapMulti_chart",
                "spline_chart",
                "barlinecombo_chart",
            ] or chart_type in ["histogram_chart"]:
                if len(chart_json_data["X"]) > highest_data_point:
                    new_main_chart_json = chart_json_data.copy()
                    highest_data_point = len(chart_json_data["X"])
                    highest_data_point_position = chart_json_data_idx
            elif chart_type in [
                "table_chart",
                "full_table_chart",
                "aggregated_table_chart",
            ]:
                if len(chart_json_data["data"]) > highest_data_point:
                    new_main_chart_json = chart_json_data.copy()
                    highest_data_point = len(chart_json_data["data"])
                    highest_data_point_position = chart_json_data_idx
            else:
                raise RuntimeError(
                    f"'{chart_type}' Chart Type is not supported in Change Main Chart!",
                )

        if new_main_chart_json == {}:
            pass
        else:
            # Replace highest data point chart with main chart
            chart_json[highest_data_point_position] = chart_json[0]
            chart_json[highest_data_point_position]["Chart_Position"] = str(
                highest_data_point_position + 1,
            )

            if (
                "Aggregated_Table_JSON"
                in chart_json[highest_data_point_position].keys()
                and "Chart_Position"
                in chart_json[highest_data_point_position][
                    "Aggregated_Table_JSON"
                ].keys()
            ):
                chart_json[highest_data_point_position]["Aggregated_Table_JSON"][
                    "Chart_Position"
                ] = str(highest_data_point_position + 1)

            # Replace main chart with highest data point chart
            chart_json[0] = new_main_chart_json
            chart_json[0]["Chart_Position"] = "1"
            if (
                "Aggregated_Table_JSON" in chart_json[0].keys()
                and "Chart_Position" in chart_json[0]["Aggregated_Table_JSON"].keys()
            ):
                chart_json[0]["Aggregated_Table_JSON"]["Chart_Position"] = "1"

    return chart_json


# def transform_chart(json_data):
#     chart_type_mapping = {
#         "barlinecombo_chart": transform_barlinecombo_chart,
#         "line_chart": transform_line_chart,
#         "grouped_column_chart": transform_grouped_column_chart,
#         "grouped_bar_chart": transform_grouped_bar_chart,
#         "radar_chart": transform_radar_chart,
#         "scatterplot_chart": transform_scatterplot_chart,
#         "radar_chart": transform_radar_chart,
#         "histogram_chart": transform_histogram_chart,
#         "area_chart": transform_area_chart,
#         "pie_chart": transform_pie_chart,
#         "bubble_chart": transform_bubble_chart,
#         "text_content": transform_text_content_chart,
#         "pyramidfunnel_chart": transform_pyramid_chart,
#         "TreemapMulti_chart": transform_treemap_chart,
#         "table_chart": transform_table_chart,
#         "full_table_chart": transform_table_chart,
#         "aggregated_table_chart": transform_table_chart,
#         "card_chart": transform_card_chart,
#     }

#     chart_type = json_data.get("Chart_Type")

#     if chart_type in chart_type_mapping:
#         transform_function = chart_type_mapping[chart_type]
#         return transform_function(json_data)
#     else:
#         raise ValueError(f"Unsupported chart type: {chart_type}")


# def transform_bubble_chart(input_json: dict):
#     output_json = {
#         "Subscription_ID": input_json.get("Subscription_ID", ""),
#         "Subscription_Name": input_json.get("Subscription_Name", ""),
#         "Client_ID": input_json.get("Client_ID", ""),
#         "User_ID": input_json.get("User_ID", ""),
#         "Shared_User_ID": input_json.get("Shared_User_ID", ""),
#         "Chart_Name": input_json.get("Chart_Name", ""),
#         "Chart_Axis": input_json.get("Chart_Axis", {}),
#         "Chart_Query": input_json.get("Chart_Query", ""),
#         "Chart_SQL_Library": input_json.get("Chart_SQL_Library", ""),
#         "Chart_Position": input_json.get("Chart_Position", ""),
#         "Chart_Type": input_json.get("Chart_Type", ""),
#         "Chart_Title": input_json.get("Chart_Title", ""),
#         "xAxis": input_json.get("xAxis", ""),
#         "yAxis": input_json.get("yAxis", ""),
#         "Chart_Data": [],
#         "Aggregated_Table_JSON": input_json.get("Aggregated_Table_JSON", {}),
#         "Aggregated_Table_Column": input_json.get("Aggregated_Table_Column", []),
#         "Database_Identifier": input_json.get("Database_Identifier", {}),
#     }

#     x_keys = [key for key in input_json.keys() if key.startswith("X")]
#     y_keys = [key for key in input_json.keys() if key.startswith("Y")]

#     # Generate y_names for each Y series
#     y_names = [
#         input_json.get("yName") if i == 0 else input_json.get(f"y{i+1}Name")
#         for i in range(len(y_keys))
#     ]  # Start with yName for Y and then y2Name, y3Name, etc.

#     # Loop through X and Y pairs and append the corresponding data to output_json
#     for j, (x_key, y_key) in enumerate(zip(x_keys, y_keys)):
#         x_values = input_json[x_key]  # Get values for X, X2, etc.
#         y_values = input_json[y_key]  # Get values for Y, Y2, etc.

#         for i, x_value in enumerate(x_values):
#             # Ensure there's a corresponding Y value for each X
#             if len(y_values) > i:
#                 # Create Chart_Data
#                 output_json["Chart_Data"].append(
#                     {
#                         "X_Value": x_value,
#                         "Y_Value": y_values[i],
#                         "Group_Name": (
#                             y_names[j] if y_names[j] is not None else f"Series {j+1}"
#                         ),
#                     }
#                 )

#     return output_json


# def transform_grouped_bar_chart(input_json: dict):
#     output_json = {
#         "Subscription_ID": input_json.get("Subscription_ID", ""),
#         "Subscription_Name": input_json.get("Subscription_Name", ""),
#         "Client_ID": input_json.get("Client_ID", ""),
#         "User_ID": input_json.get("User_ID", ""),
#         "Shared_User_ID": input_json.get("Shared_User_ID", ""),
#         "Chart_Name": input_json.get("Chart_Name", ""),
#         "Chart_Axis": input_json.get("Chart_Axis", {}),
#         "Chart_Query": input_json.get("Chart_Query", ""),
#         "Chart_SQL_Library": input_json.get("Chart_SQL_Library", ""),
#         "Chart_Position": input_json.get("Chart_Position", ""),
#         "Chart_Type": input_json.get("Chart_Type", ""),
#         "Chart_Title": input_json.get("Chart_Title", ""),
#         "xAxis": input_json.get("xAxis", ""),
#         "yAxis": input_json.get("yAxis", ""),
#         "Chart_Data": [],
#         "Aggregated_Table_JSON": input_json.get("Aggregated_Table_JSON", {}),
#         "Aggregated_Table_Column": input_json.get("Aggregated_Table_Column", []),
#         "Database_Identifier": input_json.get("Database_Identifier", {}),
#     }

#     x_values = input_json["X"]
#     y_keys = [key for key in input_json.keys() if key.startswith("Y")]
#     y_names = [
#         input_json.get("yName") if i == 0 else input_json.get(f"y{i+1}Name")
#         for i in range(len(y_keys))
#     ]  # Start with yName for Y and then y2Name, y3Name, etc.

#     # Initialize the structure for grouped Chart_Data as list of lists
#     grouped_data = [[] for _ in range(len(y_keys))]

#     for i, x_value in enumerate(x_values):
#         for j, y_key in enumerate(y_keys):
#             # Create the corresponding data point
#             if len(input_json[y_key]) > i:
#                 group_name = y_names[j] if j < len(y_names) else f"Series {j+1}"
#                 grouped_data[j].append(
#                     {
#                         "X_Value": x_value,
#                         "Y_Value": input_json[y_key][i],
#                         "Group_Name": group_name,
#                     }
#                 )

#     # Remove empty lists from grouped_data
#     grouped_data = [group for group in grouped_data if group]

#     # Convert the grouped data into the desired output format
#     output_json["Chart_Data"] = grouped_data

#     return output_json


# def transform_grouped_column_chart(input_json: dict):
#     output_json = {
#         "Subscription_ID": input_json.get("Subscription_ID", ""),
#         "Subscription_Name": input_json.get("Subscription_Name", ""),
#         "Client_ID": input_json.get("Client_ID", ""),
#         "User_ID": input_json.get("User_ID", ""),
#         "Shared_User_ID": input_json.get("Shared_User_ID", ""),
#         "Chart_Name": input_json.get("Chart_Name", ""),
#         "Chart_Axis": input_json.get("Chart_Axis", {}),
#         "Chart_Query": input_json.get("Chart_Query", ""),
#         "Chart_SQL_Library": input_json.get("Chart_SQL_Library", ""),
#         "Chart_Position": input_json.get("Chart_Position", ""),
#         "Chart_Type": input_json.get("Chart_Type", ""),
#         "Chart_Title": input_json.get("Chart_Title", ""),
#         "xAxis": input_json.get("xAxis", ""),
#         "yAxis": input_json.get("yAxis", ""),
#         "Chart_Data": [],
#         "Aggregated_Table_JSON": input_json.get("Aggregated_Table_JSON", {}),
#         "Aggregated_Table_Column": input_json.get("Aggregated_Table_Column", []),
#         "Database_Identifier": input_json.get("Database_Identifier", {}),
#     }

#     x_values = input_json["X"]
#     y_keys = [key for key in input_json.keys() if key.startswith("Y")]
#     y_names = [
#         input_json.get("yName") if i == 0 else input_json.get(f"y{i+1}Name")
#         for i in range(len(y_keys))
#     ]  # Start with yName for Y and then y2Name, y3Name, etc.

#     # Initialize the structure for grouped Chart_Data as list of lists
#     grouped_data = [[] for _ in range(len(y_keys))]

#     for i, x_value in enumerate(x_values):
#         for j, y_key in enumerate(y_keys):
#             # Create the corresponding data point
#             if len(input_json[y_key]) > i:
#                 group_name = y_names[j] if j < len(y_names) else f"Series {j+1}"
#                 grouped_data[j].append(
#                     {
#                         "X_Value": x_value,
#                         "Y_Value": input_json[y_key][i],
#                         "Group_Name": group_name,
#                     }
#                 )

#     # Remove empty lists from grouped_data
#     grouped_data = [group for group in grouped_data if group]

#     # Convert the grouped data into the desired output format
#     output_json["Chart_Data"] = grouped_data

#     return output_json


# def transform_barlinecombo_chart(input_json: dict):
#     output_json = {
#         "Subscription_ID": input_json.get("Subscription_ID", ""),
#         "Subscription_Name": input_json.get("Subscription_Name", ""),
#         "Client_ID": input_json.get("Client_ID", ""),
#         "User_ID": input_json.get("User_ID", ""),
#         "Shared_User_ID": input_json.get("Shared_User_ID", ""),
#         "Chart_Name": input_json.get("Chart_Name", ""),
#         "Chart_Axis": input_json.get("Chart_Axis", {}),
#         "Chart_Query": input_json.get("Chart_Query", ""),
#         "Chart_SQL_Library": input_json.get("Chart_SQL_Library", ""),
#         "Chart_Position": input_json.get("Chart_Position", ""),
#         "Chart_Type": input_json.get("Chart_Type", ""),
#         "Chart_Title": input_json.get("Chart_Title", ""),
#         "xAxis": input_json.get("xAxis", ""),
#         "yAxis": input_json.get("yAxis", ""),
#         "y2Axis": input_json.get("y2Axis", ""),
#         "Chart_Data": [],
#         "Aggregated_Table_JSON": input_json.get("Aggregated_Table_JSON", {}),
#         "Aggregated_Table_Column": input_json.get("Aggregated_Table_Column", []),
#         "Database_Identifier": input_json.get("Database_Identifier", {}),
#     }

#     x_values = input_json["X"]
#     y_values = input_json["Y"]
#     y2_values = input_json["Y2"]

#     for x_value, y_value, y2_value in zip(x_values, y_values, y2_values):
#         # Create Chart_Data
#         output_json["Chart_Data"].append(
#             {"X_Value": x_value, "Y_Value": y_value, "Y2_Value": y2_value}
#         )

#     return output_json


# def transform_line_chart(input_json: dict):
#     output_json = {
#         "Subscription_ID": input_json.get("Subscription_ID", ""),
#         "Subscription_Name": input_json.get("Subscription_Name", ""),
#         "Client_ID": input_json.get("Client_ID", ""),
#         "User_ID": input_json.get("User_ID", ""),
#         "Shared_User_ID": input_json.get("Shared_User_ID", ""),
#         "Chart_Name": input_json.get("Chart_Name", ""),
#         "Chart_Axis": input_json.get("Chart_Axis", {}),
#         "Chart_Query": input_json.get("Chart_Query", ""),
#         "Chart_SQL_Library": input_json.get("Chart_SQL_Library", ""),
#         "Chart_Position": input_json.get("Chart_Position", ""),
#         "Chart_Type": input_json.get("Chart_Type", ""),
#         "Chart_Title": input_json.get("Chart_Title", ""),
#         "xAxis": input_json.get("xAxis", ""),
#         "yAxis": input_json.get("yAxis", ""),
#         "Chart_Data": [],
#         "Aggregated_Table_JSON": input_json.get("Aggregated_Table_JSON", {}),
#         "Aggregated_Table_Column": input_json.get("Aggregated_Table_Column", []),
#         "Database_Identifier": input_json.get("Database_Identifier", {}),
#     }

#     x_values = input_json["X"]
#     y_keys = [key for key in input_json.keys() if key.startswith("Y")]
#     y_names = [
#         input_json.get("yName") if i == 0 else input_json.get(f"y{i+1}Name")
#         for i in range(len(y_keys))
#     ]  # Start with yName for Y and then y2Name, y3Name, etc.

#     # Initialize the structure for grouped Chart_Data as list of lists
#     grouped_data = [[] for _ in range(len(y_keys))]

#     for i, x_value in enumerate(x_values):
#         for j, y_key in enumerate(y_keys):
#             # Create the corresponding data point
#             if len(input_json[y_key]) > i:
#                 group_name = y_names[j] if j < len(y_names) else f"Series {j+1}"
#                 grouped_data[j].append(
#                     {
#                         "X_Value": x_value,
#                         "Y_Value": input_json[y_key][i],
#                         "Group_Name": group_name,
#                     }
#                 )

#     # Remove empty lists from grouped_data
#     grouped_data = [group for group in grouped_data if group]

#     # Convert the grouped data into the desired output format
#     output_json["Chart_Data"] = grouped_data

#     return output_json


# def transform_radar_chart(input_json: dict):
#     output_json = {
#         "Subscription_ID": input_json.get("Subscription_ID", ""),
#         "Subscription_Name": input_json.get("Subscription_Name", ""),
#         "Client_ID": input_json.get("Client_ID", ""),
#         "User_ID": input_json.get("User_ID", ""),
#         "Shared_User_ID": input_json.get("Shared_User_ID", ""),
#         "Chart_Name": input_json.get("Chart_Name", ""),
#         "Chart_Axis": input_json.get("Chart_Axis", {}),
#         "Chart_Query": input_json.get("Chart_Query", ""),
#         "Chart_SQL_Library": input_json.get("Chart_SQL_Library", ""),
#         "Chart_Position": input_json.get("Chart_Position", ""),
#         "Chart_Type": input_json.get("Chart_Type", ""),
#         "Chart_Title": input_json.get("Chart_Title", ""),
#         "xAxis": input_json.get("xAxis", ""),
#         "yAxis": input_json.get("yAxis", ""),
#         "Chart_Data": [],
#         "Aggregated_Table_JSON": input_json.get("Aggregated_Table_JSON", {}),
#         "Aggregated_Table_Column": input_json.get("Aggregated_Table_Column", []),
#         "Database_Identifier": input_json.get("Database_Identifier", {}),
#     }

#     x_values = input_json["X"]
#     y_keys = [key for key in input_json.keys() if key.startswith("Y")]
#     y_names = [
#         input_json.get("yName") if i == 0 else input_json.get(f"y{i+1}Name")
#         for i in range(len(y_keys))
#     ]  # Start with yName for Y and then y2Name, y3Name, etc.

#     # Initialize the structure for grouped Chart_Data as list of lists
#     grouped_data = [[] for _ in range(len(y_keys))]

#     for i, x_value in enumerate(x_values):
#         for j, y_key in enumerate(y_keys):
#             # Create the corresponding data point
#             if len(input_json[y_key]) > i:
#                 group_name = y_names[j] if j < len(y_names) else f"Series {j+1}"
#                 grouped_data[j].append(
#                     {
#                         "X_Value": x_value,
#                         "Y_Value": input_json[y_key][i],
#                         "Group_Name": group_name,
#                     }
#                 )

#     # Remove empty lists from grouped_data
#     grouped_data = [group for group in grouped_data if group]

#     # Convert the grouped data into the desired output format
#     output_json["Chart_Data"] = grouped_data

#     return output_json


# def transform_scatterplot_chart(input_json: dict):
#     output_json = {
#         "Subscription_ID": input_json.get("Subscription_ID", ""),
#         "Subscription_Name": input_json.get("Subscription_Name", ""),
#         "Client_ID": input_json.get("Client_ID", ""),
#         "User_ID": input_json.get("User_ID", ""),
#         "Shared_User_ID": input_json.get("Shared_User_ID", ""),
#         "Chart_Name": input_json.get("Chart_Name", ""),
#         "Chart_Axis": input_json.get("Chart_Axis", {}),
#         "Chart_Query": input_json.get("Chart_Query", ""),
#         "Chart_SQL_Library": input_json.get("Chart_SQL_Library", ""),
#         "Chart_Position": input_json.get("Chart_Position", ""),
#         "Chart_Type": input_json.get("Chart_Type", ""),
#         "Chart_Title": input_json.get("Chart_Title", ""),
#         "xAxis": input_json.get("xAxis", ""),
#         "yAxis": input_json.get("yAxis", ""),
#         "Chart_Data": [],
#         "Aggregated_Table_JSON": input_json.get("Aggregated_Table_JSON", {}),
#         "Aggregated_Table_Column": input_json.get("Aggregated_Table_Column", []),
#         "Database_Identifier": input_json.get("Database_Identifier", {}),
#     }

#     x_keys = [key for key in input_json.keys() if key.startswith("X")]
#     y_keys = [key for key in input_json.keys() if key.startswith("Y")]

#     # Generate y_names for each Y series
#     y_names = [
#         input_json.get("yName") if i == 0 else input_json.get(f"y{i+1}Name")
#         for i in range(len(y_keys))
#     ]  # Start with yName for Y and then y2Name, y3Name, etc.

#     # Loop through X and Y pairs and append the corresponding data to output_json
#     for j, (x_key, y_key) in enumerate(zip(x_keys, y_keys)):
#         x_values = input_json[x_key]  # Get values for X, X2, etc.
#         y_values = input_json[y_key]  # Get values for Y, Y2, etc.

#         for i, x_value in enumerate(x_values):
#             # Ensure there's a corresponding Y value for each X
#             if len(y_values) > i:
#                 # Create Chart_Data
#                 output_json["Chart_Data"].append(
#                     {
#                         "X_Value": x_value,
#                         "Y_Value": y_values[i],
#                         "Group_Name": (
#                             y_names[j] if y_names[j] is not None else f"Series {j+1}"
#                         ),
#                     }
#                 )

#     return output_json


# def transform_histogram_chart(input_json: dict):
#     output_json = {
#         "Subscription_ID": input_json.get("Subscription_ID", ""),
#         "Subscription_Name": input_json.get("Subscription_Name", ""),
#         "Client_ID": input_json.get("Client_ID", ""),
#         "User_ID": input_json.get("User_ID", ""),
#         "Shared_User_ID": input_json.get("Shared_User_ID", ""),
#         "Chart_Name": input_json.get("Chart_Name", ""),
#         "Chart_Axis": input_json.get("Chart_Axis", {}),
#         "Chart_Query": input_json.get("Chart_Query", ""),
#         "Chart_SQL_Library": input_json.get("Chart_SQL_Library", ""),
#         "Chart_Position": input_json.get("Chart_Position", ""),
#         "Chart_Type": input_json.get("Chart_Type", ""),
#         "Chart_Title": input_json.get("Chart_Title", ""),
#         "xAxis": input_json.get("xAxis", ""),
#         "yAxis": input_json.get("yAxis", ""),
#         "Chart_Data": [],
#         "Aggregated_Table_JSON": input_json.get("Aggregated_Table_JSON", {}),
#         "Aggregated_Table_Column": input_json.get("Aggregated_Table_Column", []),
#         "Database_Identifier": input_json.get("Database_Identifier", {}),
#     }

#     x_values = input_json["X"]
#     y_values = input_json["Y"]

#     for x_value, y_value in zip(x_values, y_values):
#         # Create Chart_Data
#         output_json["Chart_Data"].append({"X_Value": x_value, "Y_Value": y_value})

#     return output_json


# def transform_area_chart(input_json: dict):
#     output_json = {
#         "Subscription_ID": input_json.get("Subscription_ID", ""),
#         "Subscription_Name": input_json.get("Subscription_Name", ""),
#         "Client_ID": input_json.get("Client_ID", ""),
#         "User_ID": input_json.get("User_ID", ""),
#         "Shared_User_ID": input_json.get("Shared_User_ID", ""),
#         "Chart_Name": input_json.get("Chart_Name", ""),
#         "Chart_Axis": input_json.get("Chart_Axis", {}),
#         "Chart_Query": input_json.get("Chart_Query", ""),
#         "Chart_SQL_Library": input_json.get("Chart_SQL_Library", ""),
#         "Chart_Position": input_json.get("Chart_Position", ""),
#         "Chart_Type": input_json.get("Chart_Type", ""),
#         "Chart_Title": input_json.get("Chart_Title", ""),
#         "xAxis": input_json.get("xAxis", ""),
#         "yAxis": input_json.get("yAxis", ""),
#         "Chart_Data": [],
#         "Aggregated_Table_JSON": input_json.get("Aggregated_Table_JSON", {}),
#         "Aggregated_Table_Column": input_json.get("Aggregated_Table_Column", []),
#         "Database_Identifier": input_json.get("Database_Identifier", {}),
#     }

#     x_values = input_json["X"]
#     y_keys = [key for key in input_json.keys() if key.startswith("Y")]
#     y_names = [
#         input_json.get("yName") if i == 0 else input_json.get(f"y{i+1}Name")
#         for i in range(len(y_keys))
#     ]  # Start with yName for Y and then y2Name, y3Name, etc.

#     # Initialize the structure for grouped Chart_Data as list of lists
#     grouped_data = [[] for _ in range(len(y_keys))]

#     for i, x_value in enumerate(x_values):
#         for j, y_key in enumerate(y_keys):
#             # Create the corresponding data point
#             if len(input_json[y_key]) > i:
#                 group_name = y_names[j] if j < len(y_names) else f"Series {j+1}"
#                 grouped_data[j].append(
#                     {
#                         "X_Value": x_value,
#                         "Y_Value": input_json[y_key][i],
#                         "Group_Name": group_name,
#                     }
#                 )

#     # Remove empty lists from grouped_data
#     grouped_data = [group for group in grouped_data if group]

#     # Convert the grouped data into the desired output format
#     output_json["Chart_Data"] = grouped_data

#     return output_json


# def transform_pie_chart(input_json: dict):
#     output_json = {
#         "Subscription_ID": input_json.get("Subscription_ID", ""),
#         "Subscription_Name": input_json.get("Subscription_Name", ""),
#         "Client_ID": input_json.get("Client_ID", ""),
#         "User_ID": input_json.get("User_ID", ""),
#         "Shared_User_ID": input_json.get("Shared_User_ID", ""),
#         "Chart_Name": input_json.get("Chart_Name", ""),
#         "Chart_Axis": input_json.get("Chart_Axis", {}),
#         "Chart_Query": input_json.get("Chart_Query", ""),
#         "Chart_SQL_Library": input_json.get("Chart_SQL_Library", ""),
#         "Chart_Position": input_json.get("Chart_Position", ""),
#         "Chart_Type": input_json.get("Chart_Type", ""),
#         "Chart_Title": input_json.get("Chart_Title", ""),
#         "xAxis": input_json.get("xAxis", ""),
#         "yAxis": input_json.get("yAxis", ""),
#         "Chart_Data": [],
#         "Aggregated_Table_JSON": input_json.get("Aggregated_Table_JSON", {}),
#         "Aggregated_Table_Column": input_json.get("Aggregated_Table_Column", []),
#         "Database_Identifier": input_json.get("Database_Identifier", {}),
#     }

#     x_values = input_json["X"]
#     y_values = input_json["Y"]

#     for x_value, y_value in zip(x_values, y_values):
#         # Create Chart_Data
#         output_json["Chart_Data"].append({"X_Value": x_value, "Y_Value": y_value})

#     return output_json


# def transform_pyramid_chart(input_json: dict):
#     output_json = {
#         "Subscription_ID": input_json.get("Subscription_ID", ""),
#         "Subscription_Name": input_json.get("Subscription_Name", ""),
#         "Client_ID": input_json.get("Client_ID", ""),
#         "User_ID": input_json.get("User_ID", ""),
#         "Shared_User_ID": input_json.get("Shared_User_ID", ""),
#         "Chart_Name": input_json.get("Chart_Name", ""),
#         "Chart_Axis": input_json.get("Chart_Axis", {}),
#         "Chart_Query": input_json.get("Chart_Query", ""),
#         "Chart_SQL_Library": input_json.get("Chart_SQL_Library", ""),
#         "Chart_Position": input_json.get("Chart_Position", ""),
#         "Chart_Type": input_json.get("Chart_Type", ""),
#         "Chart_Title": input_json.get("Chart_Title", ""),
#         "xAxis": input_json.get("xAxis", ""),
#         "yAxis": input_json.get("yAxis", ""),
#         "Chart_Data": [],
#         "Aggregated_Table_JSON": input_json.get("Aggregated_Table_JSON", {}),
#         "Aggregated_Table_Column": input_json.get("Aggregated_Table_Column", []),
#         "Database_Identifier": input_json.get("Database_Identifier", {}),
#     }

#     x_values = input_json["X"]
#     y_values = input_json["Y"]

#     for x_value, y_value in zip(x_values, y_values):
#         # Create Chart_Data
#         output_json["Chart_Data"].append({"X_Value": x_value, "Y_Value": y_value})

#     return output_json


# def transform_treemap_chart(input_json: dict):
#     output_json = {
#         "Subscription_ID": input_json.get("Subscription_ID", ""),
#         "Subscription_Name": input_json.get("Subscription_Name", ""),
#         "Client_ID": input_json.get("Client_ID", ""),
#         "User_ID": input_json.get("User_ID", ""),
#         "Shared_User_ID": input_json.get("Shared_User_ID", ""),
#         "Chart_Name": input_json.get("Chart_Name", ""),
#         "Chart_Axis": input_json.get("Chart_Axis", {}),
#         "Chart_Query": input_json.get("Chart_Query", ""),
#         "Chart_SQL_Library": input_json.get("Chart_SQL_Library", ""),
#         "Chart_Position": input_json.get("Chart_Position", ""),
#         "Chart_Type": input_json.get("Chart_Type", ""),
#         "Chart_Title": input_json.get("Chart_Title", ""),
#         "xAxis": input_json.get("xAxis", ""),
#         "yAxis": input_json.get("yAxis", ""),
#         "Chart_Data": [],
#         "Aggregated_Table_JSON": input_json.get("Aggregated_Table_JSON", {}),
#         "Aggregated_Table_Column": input_json.get("Aggregated_Table_Column", []),
#         "Database_Identifier": input_json.get("Database_Identifier", {}),
#     }

#     x_keys = [key for key in input_json.keys() if key.startswith("X")]
#     y_keys = [key for key in input_json.keys() if key.startswith("Y")]

#     # Generate y_names for each Y series
#     y_names = [
#         input_json.get("yName") if i == 0 else input_json.get(f"y{i+1}Name")
#         for i in range(len(y_keys))
#     ]  # Start with yName for Y and then y2Name, y3Name, etc.

#     # Loop through X and Y pairs and append the corresponding data to output_json
#     for j, (x_key, y_key) in enumerate(zip(x_keys, y_keys)):
#         x_values = input_json[x_key]  # Get values for X, X2, etc.
#         y_values = input_json[y_key]  # Get values for Y, Y2, etc.

#         for i, x_value in enumerate(x_values):
#             # Ensure there's a corresponding Y value for each X
#             if len(y_values) > i:
#                 # Create Chart_Data
#                 output_json["Chart_Data"].append(
#                     {
#                         "X_Value": x_value,
#                         "Y_Value": y_values[i],
#                         "Group_Name": (
#                             y_names[j] if y_names[j] is not None else f"Series {j+1}"
#                         ),
#                     }
#                 )

#     return output_json


# def transform_table_chart(input_json: dict):
#     return input_json


# def transform_card_chart(input_json: dict):
#     return input_json


# def transform_text_content_chart(input_json: dict):
#     return input_json
