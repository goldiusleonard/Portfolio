import datetime
import decimal
import logging
import os
import requests
import re
import sys
import traceback
import numpy as np
import pandas as pd

from time import perf_counter
from typing import Tuple, Union, Any
from ..datamodel import DataSummary
from ..utils import (
    calculate_bins,
    detect_and_sort_pandas_date,
    sort_pandas_date,
    validate_and_fix_xAxis_title,
    calculate_token_usage,
    adjust_axis_title_and_data,
)

from logging_library.performancelogger.performance_logger import PerformanceLogger

logger = logging.getLogger(__name__)

BAR_CHART_TEMPLATE_D3 = COLUMN_CHART_TEMPLATE_D3 = PYRAMIDFUNNEL_CHART_TEMPLATE_D3 = (
    PIE_CHART_TEMPLATE_D3
) = {
    "Subscription_ID": "",
    "Subscription_Name": "",
    "Chart_ID": "",
    "Client_ID": "",
    "User_ID": "",
    "Session_ID": "",
    "Shared_User_ID": "",
    "User_Query": "",
    "Chart_Name": "",
    "Visual_Title": "",
    "Chart_Axis": {},
    "Chart_Data": [],
    "Chart_Query": "",
    "Chart_SQL_Library": "",
    "Chart_Position": "",
    "Chart_Type": "",
    "Chart_Title": "",
    "xAxis": "",
    "yAxis": "",
    "Aggregated_Table_JSON": {},
    "Aggregated_Table_Column": [],
    "Database_Identifier": "",
}

HISTOGRAM_CHART_TEMPLATE_D3 = {
    "Subscription_ID": "",
    "Subscription_Name": "",
    "Chart_ID": "",
    "Client_ID": "",
    "User_ID": "",
    "Session_ID": "",
    "Shared_User_ID": "",
    "User_Query": "",
    "Chart_Name": "",
    "Visual_Title": "",
    "Chart_Axis": {},
    "Chart_Data": [],
    "Chart_Query": "",
    "Chart_SQL_Library": "",
    "Chart_Position": "",
    "Chart_Type": "",
    "Number_of_Bins": "",
    "Chart_Title": "",
    "xAxis": "",
    "yAxis": "",
    "Aggregated_Table_JSON": {},
    "Aggregated_Table_Column": [],
    "Database_Identifier": "",
}

LINE_CHART_TEMPLATE_D3 = SPLINE_CHART_TEMPLATE_D3 = AREA_CHART_TEMPLATE_D3 = (
    RADAR_CHART_TEMPLATE_D3
) = GROUPED_COLUMN_CHART_TEMPLATE_D3 = GROUPED_BAR_CHART_TEMPLATE_D3 = (
    SCATTERPLOT_CHART_TEMPLATE_D3
) = TREEMAPMULTI_CHART_TEMPLATE_D3 = {
    "Subscription_ID": "",
    "Subscription_Name": "",
    "Chart_ID": "",
    "Client_ID": "",
    "User_ID": "",
    "Session_ID": "",
    "Shared_User_ID": "",
    "User_Query": "",
    "Chart_Name": "",
    "Visual_Title": "",
    "Chart_Axis": {},
    "Chart_Data": [],
    "Chart_Query": "",
    "Chart_SQL_Library": "",
    "Chart_Position": "",
    "Chart_Type": "",
    "Chart_Title": "",
    "xAxis": "",
    "yAxis": "",
    "Aggregated_Table_JSON": {},
    "Aggregated_Table_Column": [],
    "Database_Identifier": "",
}

BUBBLE_CHART_TEMPLATE_D3 = {
    "Subscription_ID": "",
    "Subscription_Name": "",
    "Client_ID": "",
    "User_ID": "",
    "Session_ID": "",
    "Shared_User_ID": "",
    "User_Query": "",
    "Chart_Name": "",
    "Visual_Title": "",
    "Chart_ID": "",
    "Chart_Axis": {},
    "Chart_Data": [],
    "Chart_Query": "",
    "Chart_SQL_Library": "",
    "Chart_Position": "",
    "Chart_Type": "",
    "Chart_Title": "",
    "xAxis": "",
    "yAxis": "",
    "zAxis": "",
    "Aggregated_Table_JSON": {},
    "Aggregated_Table_Column": [],
    "Database_Identifier": "",
}

BARLINECOMBO_CHART_TEMPLATE_D3 = {
    "Subscription_ID": "",
    "Subscription_Name": "",
    "Chart_ID": "",
    "Client_ID": "",
    "User_ID": "",
    "Session_ID": "",
    "Shared_User_ID": "",
    "User_Query": "",
    "Chart_Name": "",
    "Visual_Title": "",
    "Chart_Axis": {},
    "Chart_Data": [],
    "Chart_Query": "",
    "Chart_SQL_Library": "",
    "Chart_Position": "",
    "Chart_Type": "",
    "Chart_Title": "",
    "xAxis": "",
    "yAxis": "",
    "y2Axis": "",
    "Aggregated_Table_JSON": {},
    "Aggregated_Table_Column": [],
    "Database_Identifier": "",
}

TABLE_CHART_TEMPLATE_D3 = {
    "Subscription_ID": "",
    "Subscription_Name": "",
    "Chart_ID": "",
    "Client_ID": "",
    "User_ID": "",
    "Session_ID": "",
    "Shared_User_ID": "",
    "User_Query": "",
    "Chart_Name": "",
    "Visual_Title": "",
    "Chart_Axis": {},
    "Chart_Query": "",
    "Chart_SQL_Library": "",
    "Chart_Position": "",
    "Chart_Type": "",
    "Chart_Title": "",
    "Chart_Size": 0,
    "data": [],
    "Database_Identifier": "",
}

CARD_CHART_TEMPLATE_D3 = {
    "Subscription_ID": "",
    "Subscription_Name": "",
    "Chart_ID": "",
    "Client_ID": "",
    "User_ID": "",
    "Session_ID": "",
    "Shared_User_ID": "",
    "User_Query": "",
    "Chart_Name": "",
    "Visual_Title": "",
    "Chart_Axis": {},
    "Chart_Query": "",
    "Chart_SQL_Library": "",
    "Chart_Position": "",
    "Chart_Type": "",
    "Chart_Title": "",
    "yAxis": "",
    "yAxis_Description": "",
    "Y": 0,
    "Database_Identifier": "",
}


def check_negative_value(value_list: list) -> bool:
    """The function `check_negative_value` checks if there is any negative integer or float value in a
    given list.

    :param value_list: A list of values that you want to check for negative numbers
    :type value_list: list
    :return: The function `check_negative_value` returns a boolean value indicating whether there is a
    negative integer or float value present in the input list `value_list`.
    """
    is_negative = False
    for value in value_list:
        if isinstance(value, int) or isinstance(value, float):
            if value < 0:
                is_negative = True
                break

    return is_negative


def check_aggregation_phrases(
    string_input: str,
    keywords: list = [
        "Total",
        "Sum",
        "Cummulative",
        "Overall",
        "Count",
        "Average",
        "Mean",
        "Median",
        "Mode",
        "Maximum",
        "Minimum",
    ],
) -> bool:
    """This Python function checks if a given string contains any aggregation-related keywords.

    :param string_input: The `check_aggregation_phrases` function takes a string input and a list of
    keywords related to aggregation phrases. It checks if any of the keywords are present in the string
    input, ignoring case sensitivity
    :type string_input: str
    :param keywords: The `keywords` parameter in the `check_aggregation_phrases` function is a list of
    common aggregation phrases that are used to indicate some form of calculation or summary in a
    dataset. These keywords are checked against the `string_input` to determine if any of them are
    present in the input string
    :type keywords: list
    :return: The function `check_aggregation_phrases` returns a boolean value indicating whether the
    `string_input` contains any of the keywords related to aggregation phrases specified in the
    `keywords` list.
    """
    has_aggregation: bool = False

    for keyword in keywords:
        if keyword.lower().strip() in string_input.lower():
            has_aggregation = True

    return has_aggregation


def get_aggregated_columns(chart_axis: dict) -> list:
    """The function `get_aggregated_columns` extracts and aggregates column names from a dictionary based
    on specific criteria.

    :param chart_axis: The function `get_aggregated_columns` takes a dictionary `chart_axis` as input
    and returns a list of aggregated columns extracted from the keys of the dictionary
    :type chart_axis: dict
    :return: The function `get_aggregated_columns` returns a list of aggregated columns extracted from
    the `chart_axis` dictionary. The function first checks if the keys in the dictionary contain
    "_column" in their names and if the corresponding values are non-empty strings. If so, those values
    are added to the `aggregated_columns` list after stripping any leading or trailing whitespaces. If
    the values are lists,
    """
    aggregated_columns = []

    for key in chart_axis:
        if "_column" in key.lower() and (
            isinstance(chart_axis[key], str) and chart_axis[key].strip() != ""
        ):
            aggregated_columns.append(chart_axis[key].strip())
        elif "_column" in key.lower() and isinstance(chart_axis[key], list):
            for chart_axis_column in chart_axis[key]:
                aggregated_columns.append(chart_axis_column.strip())

    aggregated_columns = list(set(aggregated_columns))
    return aggregated_columns


def generate_aggregated_table_chart_d3(
    user_query: str,
    sql_query: str,
    chart_id: str,
    chart_title: str,
    chart_data: pd.DataFrame,
    database_properties: dict,
    ups_idx: int,
    chart_position: int,
    overall_title: str,
    client_id: str,
    user_id: str,
    session_id: str,
    sql_library: str,
    chart_axis: dict,
    base_chart_type: str,
    code_level_logger: logging.Logger,
):
    table_chart_json_dict: dict = TABLE_CHART_TEMPLATE_D3.copy()
    table_chart_json_dict["User_Query"] = user_query
    table_chart_json_dict["Chart_Name"] = f"Visual {ups_idx}"
    table_chart_json_dict["Visual_Title"] = overall_title
    table_chart_json_dict["Chart_ID"] = chart_id
    table_chart_json_dict["Chart_SQL_Library"] = sql_library
    table_chart_json_dict["Chart_Query"] = sql_query
    table_chart_json_dict["Chart_Position"] = str(chart_position)
    table_chart_json_dict["Chart_Type"] = "aggregated_table_chart"
    table_chart_json_dict["Chart_Title"] = chart_title
    table_chart_json_dict["data"] = []

    column_names = list(chart_data.columns)
    chart_data_values = chart_data.values.tolist()

    if base_chart_type in [
        "bar_chart",
        "column_chart",
        "pyramidfunnel_chart",
        "pie_chart",
    ]:
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
            "xAxis_title" in chart_axis
            and chart_axis["xAxis_title"] in chart_data.columns
        ):
            xAxis_column_name = chart_axis["xAxis_title"]
        else:
            code_level_logger.error("bar_chart: X-Axis is not found in extraction!")
            raise RuntimeError("bar_chart: X-Axis is not found in extraction!")

        try:
            if len(chart_data[xAxis_column_name][0].split("-")) == 1:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
                )
            elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(
                        lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                    ),
                )
            elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(
                        lambda date: (
                            int(date.split("-")[0]),
                            int(date.split("-")[1]),
                            int(date.split("-")[2]),
                        ),
                    ),
                )
            else:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    ascending=True,
                )
        except Exception:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

        if isinstance(xAxis_column_name, str):
            chart_data = sort_pandas_date(chart_data, xAxis_column_name)

        chart_data_values = chart_data.values.tolist()

        for row in chart_data_values:
            row_data = {}
            for column_idx, column_name in enumerate(column_names):
                try:
                    if column_name == "xAxis" or (
                        "xAxis_column" in chart_axis
                        and column_name in chart_axis["xAxis_column"]
                    ):
                        new_column_name = chart_axis["xAxis_title"]
                    elif column_name.startswith("yAxis"):
                        # Check for yAxis, yAxis2, yAxis3, etc.
                        axis_key = f"{column_name}_title"
                        if axis_key in chart_axis:
                            if "_" in column_name:
                                new_column_name = column_name
                                new_column_name = new_column_name.replace(
                                    new_column_name.split("_")[0],
                                    chart_axis[axis_key],
                                )
                            else:
                                new_column_name = chart_axis[axis_key]
                        else:
                            # Fallback to the original column name if no matching title is found
                            new_column_name = column_name
                    elif column_name == "series" or (
                        "series_column" in chart_axis
                        and column_name in chart_axis["series_column"]
                    ):
                        new_column_name = chart_axis["series_title"]
                    else:
                        new_column_name = column_name
                except Exception:
                    new_column_name = column_name

                new_column_name = new_column_name.replace("_", " ")

                try:
                    if isinstance(row[column_idx], int):
                        # row_data[new_column_name] = '{:,}'.format(row[column_idx])
                        row_data[new_column_name] = row[column_idx]
                    elif isinstance(row[column_idx], float):
                        # row_data[new_column_name] = '{:,}'.format(row[column_idx])
                        # Round off to 6 decimal points
                        row_data[new_column_name] = round(row[column_idx], 6)
                    elif isinstance(row[column_idx], decimal.Decimal):
                        # row_data[new_column_name] = '{:,}'.format(float(row[column_idx]))
                        # Round off to 6 decimal points
                        row_data[new_column_name] = round(float(row[column_idx]), 6)
                    # elif pd.api.types.is_datetime64_any_dtype(row[column_idx]):
                    #     row_data[new_column_name] = row[column_idx].astype(str)
                    elif (
                        isinstance(row[column_idx], datetime.date)
                        or isinstance(row[column_idx], datetime.datetime)
                    ) and not pd.isnull(row[column_idx]):
                        row_data[new_column_name] = row[column_idx].strftime("%m/%d/%Y")
                    else:
                        row_data[new_column_name] = str(row[column_idx])
                except Exception:
                    print(traceback.format_exc())
                    # logger.error(traceback.format_exc())
                    row_data[new_column_name] = str(row[column_idx])

            table_chart_json_dict["data"].append(row_data)
    elif base_chart_type in ["histogram_chart"]:
        chart_data_columns = list(chart_data.columns)

        xAxis_column_name = chart_data_columns[0]

        try:
            if len(chart_data[xAxis_column_name][0].split("-")) == 1:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
                )
            elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(
                        lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                    ),
                )
            elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(
                        lambda date: (
                            int(date.split("-")[0]),
                            int(date.split("-")[1]),
                            int(date.split("-")[2]),
                        ),
                    ),
                )
            else:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    ascending=True,
                )
        except Exception:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

        if isinstance(xAxis_column_name, str):
            chart_data = sort_pandas_date(chart_data, xAxis_column_name)

        if "xAxis" in chart_data_columns:
            xAxis_column_name = "xAxis"
            if (
                isinstance(
                    chart_data[xAxis_column_name].values.tolist()[0],
                    (str, datetime.datetime, datetime.date),
                )
            ) and len(chart_data_columns) > 1:
                chart_data_columns.remove(xAxis_column_name)
        elif "yAxis" in chart_data_columns:
            xAxis_column_name = "yAxis"
        elif (
            "xAxis_column" in chart_axis
            and isinstance(chart_axis["xAxis_column"], str)
            and chart_axis["xAxis_column"] in chart_data_columns
        ):
            xAxis_column_name = chart_axis["xAxis_column"]
            if (
                isinstance(
                    chart_data[xAxis_column_name].values.tolist()[0],
                    (str, datetime.datetime, datetime.date),
                )
            ) and len(chart_data_columns) > 1:
                chart_data_columns.remove(xAxis_column_name)
        elif (
            "xAxis_column" in chart_axis
            and isinstance(chart_axis["xAxis_column"], list)
            and all(elem in chart_data_columns for elem in chart_axis["xAxis_column"])
        ):
            xAxis_column_names = chart_axis["xAxis_column"]
            for xAxis_column_name in xAxis_column_names:
                if (
                    isinstance(
                        chart_data[xAxis_column_name].values.tolist()[0],
                        (str, datetime.datetime, datetime.date),
                    )
                ) and len(chart_data_columns) > 1:
                    chart_data_columns.remove(xAxis_column_name)
        elif (
            "xAxis_title" in chart_axis
            and chart_axis["xAxis_title"] in chart_data_columns
        ):
            xAxis_column_name = chart_axis["xAxis_title"]
            if (
                isinstance(
                    chart_data[xAxis_column_name].values.tolist()[0],
                    (str, datetime.datetime, datetime.date),
                )
            ) and len(chart_data_columns) > 1:
                chart_data_columns.remove(xAxis_column_name)
        else:
            code_level_logger.error(
                "histogram_chart: X-Axis is not found in extraction!"
            )
            raise RuntimeError("histogram_chart: X-Axis is not found in extraction!")

        chart_data_values = chart_data.values.tolist()

        for chart_column_name in chart_data_columns:
            try:
                if not isinstance(
                    chart_data[chart_column_name].values.tolist()[0],
                    datetime.date,
                ) and not isinstance(
                    chart_data[chart_column_name].values.tolist()[0],
                    datetime.datetime,
                ):
                    if isinstance(
                        chart_data[chart_column_name].values.tolist()[0],
                        str,
                    ):
                        chart_data[chart_column_name] = chart_data[
                            chart_column_name
                        ].replace("%", "", regex=True)
                    chart_data[chart_column_name] = pd.to_numeric(
                        chart_data[chart_column_name],
                    )
                    chart_column_data = chart_data[chart_column_name].values.tolist()

                    table_chart_json_dict["data"] = [
                        {chart_axis["xAxis_title"].replace("_", " "): x}
                        for x in chart_column_data
                    ]
                    break
            except Exception:
                print(traceback.format_exc())

    elif base_chart_type in [
        "bubbleplot_chart",
    ]:
        chart_data_columns = list(chart_data.columns)

        # X-Axis Handling
        if "xAxis" in chart_data_columns:
            xAxis_column_name = "xAxis"
        elif (
            "xAxis_column" in chart_axis
            and isinstance(chart_axis["xAxis_column"], str)
            and chart_axis["xAxis_column"] in chart_data_columns
        ):
            xAxis_column_name = chart_axis["xAxis_column"]
        elif (
            "xAxis_title" in chart_axis
            and chart_axis["xAxis_title"] in chart_data.columns
        ):
            xAxis_column_name = chart_axis["xAxis_title"]
        else:
            code_level_logger.error(
                "aggregated table chart: X-Axis is not found in extraction!",
            )
            raise RuntimeError(
                "aggregated table chart: X-Axis is not found in extraction!",
            )

        try:
            if len(chart_data[xAxis_column_name][0].split("-")) == 1:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
                )
            elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(
                        lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                    ),
                )
            elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(
                        lambda date: (
                            int(date.split("-")[0]),
                            int(date.split("-")[1]),
                            int(date.split("-")[2]),
                        )
                    ),
                )
            else:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name, ascending=True
                )
        except Exception:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

        if isinstance(xAxis_column_name, str):
            chart_data = sort_pandas_date(chart_data, xAxis_column_name)

        chart_data_values = chart_data.values.tolist()

        for row in chart_data_values:
            row_data = {}
            for column_idx, column_name in enumerate(column_names):
                try:
                    if "xAxis" == column_name or (
                        "xAxis_column" in chart_axis.keys()
                        and column_name in chart_axis["xAxis_column"]
                    ):
                        new_column_name = chart_axis["xAxis_title"]
                    elif column_name.startswith("yAxis"):
                        # Check for yAxis, yAxis2, yAxis3, etc.
                        axis_key = f"{column_name}_title"
                        if axis_key in chart_axis:
                            if "_" in column_name:
                                new_column_name = column_name
                                new_column_name = new_column_name.replace(
                                    new_column_name.split("_")[0], chart_axis[axis_key]
                                )
                            else:
                                new_column_name = chart_axis[axis_key]
                        else:
                            new_column_name = column_name
                    elif "zAxis" == column_name or (
                        "zAxis_column" in chart_axis.keys()
                        and column_name in chart_axis["zAxis_column"]
                    ):
                        new_column_name = chart_axis["zAxis_title"]
                    elif "series" == column_name or (
                        "series_column" in chart_axis.keys()
                        and column_name in chart_axis["series_column"]
                    ):
                        new_column_name = chart_axis["series_title"]
                    else:
                        new_column_name = column_name
                except Exception:
                    new_column_name = column_name

                new_column_name = new_column_name.replace("_", " ")

                try:
                    if isinstance(row[column_idx], int):
                        row_data[new_column_name] = row[column_idx]
                    elif isinstance(row[column_idx], float):
                        row_data[new_column_name] = round(row[column_idx], 6)
                    elif isinstance(row[column_idx], decimal.Decimal):
                        row_data[new_column_name] = round(float(row[column_idx]), 6)
                    elif (
                        isinstance(row[column_idx], datetime.date)
                        or isinstance(row[column_idx], datetime.datetime)
                    ) and not pd.isnull(row[column_idx]):
                        row_data[new_column_name] = row[column_idx].strftime("%m/%d/%Y")
                    else:
                        row_data[new_column_name] = str(row[column_idx])
                except Exception:
                    row_data[new_column_name] = str(row[column_idx])
            table_chart_json_dict["data"].append(row_data)

    elif base_chart_type in [
        "bubbleplot_chart",
    ]:
        chart_data_columns = list(chart_data.columns)

        # X-Axis Handling
        if "xAxis" in chart_data_columns:
            xAxis_column_name = "xAxis"
        elif (
            "xAxis_column" in chart_axis
            and isinstance(chart_axis["xAxis_column"], str)
            and chart_axis["xAxis_column"] in chart_data_columns
        ):
            xAxis_column_name = chart_axis["xAxis_column"]
        elif (
            "xAxis_title" in chart_axis
            and chart_axis["xAxis_title"] in chart_data.columns
        ):
            xAxis_column_name = chart_axis["xAxis_title"]
        else:
            code_level_logger.error(
                "aggregated table chart: X-Axis is not found in extraction!",
            )
            raise RuntimeError(
                "aggregated table chart: X-Axis is not found in extraction!",
            )

        try:
            if len(chart_data[xAxis_column_name][0].split("-")) == 1:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
                )
            elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(
                        lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                    ),
                )
            elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(
                        lambda date: (
                            int(date.split("-")[0]),
                            int(date.split("-")[1]),
                            int(date.split("-")[2]),
                        ),
                    ),
                )
            else:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    ascending=True,
                )
        except Exception:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

        if isinstance(xAxis_column_name, str):
            chart_data = sort_pandas_date(chart_data, xAxis_column_name)

        chart_data_values = chart_data.values.tolist()

        for row in chart_data_values:
            row_data = {}
            for column_idx, column_name in enumerate(column_names):
                try:
                    if column_name == "xAxis" or (
                        "xAxis_column" in chart_axis
                        and column_name in chart_axis["xAxis_column"]
                    ):
                        new_column_name = chart_axis["xAxis_title"]
                    elif column_name.startswith("yAxis"):
                        # Check for yAxis, yAxis2, yAxis3, etc.
                        axis_key = f"{column_name}_title"
                        if axis_key in chart_axis:
                            if "_" in column_name:
                                new_column_name = column_name
                                new_column_name = new_column_name.replace(
                                    new_column_name.split("_")[0],
                                    chart_axis[axis_key],
                                )
                            else:
                                new_column_name = chart_axis[axis_key]
                        else:
                            new_column_name = column_name
                    elif column_name == "zAxis" or (
                        "zAxis_column" in chart_axis
                        and column_name in chart_axis["zAxis_column"]
                    ):
                        new_column_name = chart_axis["zAxis_title"]
                    elif column_name == "series" or (
                        "series_column" in chart_axis
                        and column_name in chart_axis["series_column"]
                    ):
                        new_column_name = chart_axis["series_title"]
                    else:
                        new_column_name = column_name
                except Exception:
                    new_column_name = column_name

                new_column_name = new_column_name.replace("_", " ")

                try:
                    if isinstance(row[column_idx], int):
                        row_data[new_column_name] = row[column_idx]
                    elif isinstance(row[column_idx], float):
                        row_data[new_column_name] = round(row[column_idx], 6)
                    elif isinstance(row[column_idx], decimal.Decimal):
                        row_data[new_column_name] = round(float(row[column_idx]), 6)
                    elif (
                        isinstance(row[column_idx], datetime.date)
                        or isinstance(row[column_idx], datetime.datetime)
                    ) and not pd.isnull(row[column_idx]):
                        row_data[new_column_name] = row[column_idx].strftime("%m/%d/%Y")
                    else:
                        row_data[new_column_name] = str(row[column_idx])
                except Exception:
                    row_data[new_column_name] = str(row[column_idx])
            table_chart_json_dict["data"].append(row_data)

    elif base_chart_type in [
        "area_chart",
        "line_chart",
        "radar_chart",
        "grouped_column_chart",
        "grouped_bar_chart",
        "TreemapMulti_chart",
        "spline_chart",
    ]:
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
            "xAxis_title" in chart_axis
            and chart_axis["xAxis_title"] in chart_data.columns
        ):
            xAxis_column_name = chart_axis["xAxis_title"]
        else:
            code_level_logger.error(
                "aggregated table chart: X-Axis is not found in extraction!",
            )
            raise RuntimeError(
                "aggregated table chart: X-Axis is not found in extraction!",
            )

        try:
            if len(chart_data[xAxis_column_name][0].split("-")) == 1:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
                )
            elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(
                        lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                    ),
                )
            elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(
                        lambda date: (
                            int(date.split("-")[0]),
                            int(date.split("-")[1]),
                            int(date.split("-")[2]),
                        ),
                    ),
                )
            else:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    ascending=True,
                )
        except Exception:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

        if isinstance(xAxis_column_name, str):
            chart_data = sort_pandas_date(chart_data, xAxis_column_name)

        chart_data_values = chart_data.values.tolist()

        for row in chart_data_values:
            row_data = {}
            for column_idx, column_name in enumerate(column_names):
                try:
                    if column_name == "xAxis" or (
                        "xAxis_column" in chart_axis
                        and column_name in chart_axis["xAxis_column"]
                    ):
                        new_column_name = chart_axis["xAxis_title"]
                    elif column_name.startswith("yAxis"):
                        # Check for yAxis, yAxis2, yAxis3, etc.
                        axis_key = f"{column_name}_title"
                        if axis_key in chart_axis:
                            if "_" in column_name:
                                new_column_name = column_name
                                new_column_name = new_column_name.replace(
                                    new_column_name.split("_")[0],
                                    chart_axis[axis_key],
                                )
                            else:
                                new_column_name = chart_axis[axis_key]
                        else:
                            # Fallback to the original column name if no matching title is found
                            new_column_name = column_name
                    elif column_name == "series" or (
                        "series_column" in chart_axis
                        and column_name in chart_axis["series_column"]
                    ):
                        new_column_name = chart_axis["series_title"]
                    else:
                        new_column_name = column_name
                except Exception:
                    new_column_name = column_name

                new_column_name = new_column_name.replace("_", " ")

                try:
                    if isinstance(row[column_idx], int):
                        # row_data[new_column_name] = '{:,}'.format(row[column_idx])
                        row_data[new_column_name] = row[column_idx]
                    elif isinstance(row[column_idx], float):
                        # row_data[new_column_name] = '{:,}'.format(row[column_idx])
                        # Round off to 6 decimal points
                        row_data[new_column_name] = round(row[column_idx], 6)
                    elif isinstance(row[column_idx], decimal.Decimal):
                        # row_data[new_column_name] = '{:,}'.format(float(row[column_idx]))
                        # Round off to 6 decimal points
                        row_data[new_column_name] = round(float(row[column_idx]), 6)
                    # elif pd.api.types.is_datetime64_any_dtype(row[column_idx]):
                    #     row_data[new_column_name] = row[column_idx].astype(str)
                    elif (
                        isinstance(row[column_idx], datetime.date)
                        or isinstance(row[column_idx], datetime.datetime)
                    ) and not pd.isnull(row[column_idx]):
                        row_data[new_column_name] = row[column_idx].strftime("%m/%d/%Y")
                    else:
                        row_data[new_column_name] = str(row[column_idx])
                except Exception:
                    row_data[new_column_name] = str(row[column_idx])
            table_chart_json_dict["data"].append(row_data)

    elif base_chart_type in [
        "scatterplot_chart",
    ]:
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
            "xAxis_title" in chart_axis
            and chart_axis["xAxis_title"] in chart_data.columns
        ):
            xAxis_column_name = chart_axis["xAxis_title"]
        else:
            code_level_logger.error(
                "aggregated table chart: X-Axis is not found in extraction!",
            )
            raise RuntimeError(
                "aggregated table chart: X-Axis is not found in extraction!",
            )

        if "series" in chart_data_columns:
            series_column_name = "series"
        elif (
            "series_column" in chart_axis
            and isinstance(chart_axis["series_column"], str)
            and chart_axis["series_column"] in chart_data_columns
        ):
            series_column_name = chart_axis["series_column"]
        else:
            series_column_name = ""

        object_columns = chart_data.select_dtypes(include=[object])

        numerical_column_names = list(chart_data.columns)
        if series_column_name in numerical_column_names:
            numerical_column_names.remove(series_column_name)

        for numerical_column_name in numerical_column_names:
            if numerical_column_name in object_columns:
                try:
                    if not isinstance(
                        chart_data[numerical_column_name].values.tolist()[0],
                        datetime.date,
                    ) and not isinstance(
                        chart_data[numerical_column_name].values.tolist()[0],
                        datetime.datetime,
                    ):
                        if isinstance(
                            chart_data[numerical_column_name].values.tolist()[0],
                            str,
                        ):
                            chart_data[numerical_column_name] = chart_data[
                                numerical_column_name
                            ].replace("%", "", regex=True)
                        chart_data[numerical_column_name] = pd.to_numeric(
                            chart_data[numerical_column_name],
                        )
                except Exception:
                    code_level_logger.error(
                        f"scatterplot_chart: {numerical_column_name} is not numerical!",
                    )
                    raise RuntimeError(
                        f"scatterplot_chart: {numerical_column_name} is not numerical!",
                    )

        try:
            if len(chart_data[xAxis_column_name][0].split("-")) == 1:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
                )
            elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(
                        lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                    ),
                )
            elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(
                        lambda date: (
                            int(date.split("-")[0]),
                            int(date.split("-")[1]),
                            int(date.split("-")[2]),
                        ),
                    ),
                )
            else:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    ascending=True,
                )
        except Exception:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

        if isinstance(xAxis_column_name, str):
            chart_data = sort_pandas_date(chart_data, xAxis_column_name)

        chart_data_values = chart_data.values.tolist()

        for row in chart_data_values:
            row_data = {}
            for column_idx, column_name in enumerate(column_names):
                try:
                    if column_name == "xAxis" or (
                        "xAxis_column" in chart_axis
                        and column_name in chart_axis["xAxis_column"]
                    ):
                        new_column_name = chart_axis["xAxis_title"]
                    elif column_name.startswith("yAxis"):
                        # Check for yAxis, yAxis2, yAxis3, etc.
                        axis_key = f"{column_name}_title"
                        if axis_key in chart_axis:
                            if "_" in column_name:
                                new_column_name = column_name
                                new_column_name = new_column_name.replace(
                                    new_column_name.split("_")[0],
                                    chart_axis[axis_key],
                                )
                            else:
                                new_column_name = chart_axis[axis_key]
                        else:
                            # Fallback to the original column name if no matching title is found
                            new_column_name = column_name
                    elif column_name == "series" or (
                        "series_column" in chart_axis
                        and column_name in chart_axis["series_column"]
                    ):
                        new_column_name = chart_axis["series_title"]
                    else:
                        new_column_name = column_name
                except Exception:
                    new_column_name = column_name

                new_column_name = new_column_name.replace("_", " ")

                try:
                    if isinstance(row[column_idx], int):
                        # row_data[new_column_name] = '{:,}'.format(row[column_idx])
                        row_data[new_column_name] = row[column_idx]
                    elif isinstance(row[column_idx], float):
                        # row_data[new_column_name] = '{:,}'.format(row[column_idx])
                        # Round off to 6 decimal points
                        row_data[new_column_name] = round(row[column_idx], 6)
                    elif isinstance(row[column_idx], decimal.Decimal):
                        # row_data[new_column_name] = '{:,}'.format(float(row[column_idx]))
                        # Round off to 6 decimal points
                        row_data[new_column_name] = round(float(row[column_idx]), 6)
                    # elif pd.api.types.is_datetime64_any_dtype(row[column_idx]):
                    #     row_data[new_column_name] = row[column_idx].astype(str)
                    elif (
                        isinstance(row[column_idx], datetime.date)
                        or isinstance(row[column_idx], datetime.datetime)
                    ) and not pd.isnull(row[column_idx]):
                        row_data[new_column_name] = row[column_idx].strftime("%m/%d/%Y")
                    else:
                        row_data[new_column_name] = str(row[column_idx])
                except Exception:
                    row_data[new_column_name] = str(row[column_idx])
            table_chart_json_dict["data"].append(row_data)

    elif base_chart_type in ["barlinecombo_chart"]:
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
            "xAxis_title" in chart_axis
            and chart_axis["xAxis_title"] in chart_data.columns
        ):
            xAxis_column_name = chart_axis["xAxis_title"]
        else:
            code_level_logger.error(
                "barlinecombo_chart: X-Axis is not found in extraction!"
            )
            raise RuntimeError("barlinecombo_chart: X-Axis is not found in extraction!")

        try:
            if len(chart_data[xAxis_column_name][0].split("-")) == 1:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
                )
            elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(
                        lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                    ),
                )
            elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(
                        lambda date: (
                            int(date.split("-")[0]),
                            int(date.split("-")[1]),
                            int(date.split("-")[2]),
                        ),
                    ),
                )
            else:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    ascending=True,
                )
        except Exception:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

        if isinstance(xAxis_column_name, str):
            chart_data = sort_pandas_date(chart_data, xAxis_column_name)

        chart_data_values = chart_data.values.tolist()

        for row in chart_data_values:
            row_data = {}
            for column_idx, column_name in enumerate(column_names):
                try:
                    if column_name == "xAxis" or (
                        "xAxis_column" in chart_axis
                        and column_name in chart_axis["xAxis_column"]
                    ):
                        new_column_name = chart_axis["xAxis_title"]
                    elif column_name.startswith("yAxis"):
                        # Check for yAxis, yAxis2, yAxis3, etc.
                        axis_key = f"{column_name}_title"
                        if axis_key in chart_axis:
                            if "_" in column_name:
                                new_column_name = column_name
                                new_column_name = new_column_name.replace(
                                    new_column_name.split("_")[0],
                                    chart_axis[axis_key],
                                )
                            else:
                                new_column_name = chart_axis[axis_key]
                        else:
                            # Fallback to the original column name if no matching title is found
                            new_column_name = column_name
                    elif column_name == "series" or (
                        "series_column" in chart_axis
                        and column_name in chart_axis["series_column"]
                    ):
                        new_column_name = chart_axis["series_title"]
                    else:
                        new_column_name = column_name
                except Exception:
                    new_column_name = column_name

                new_column_name = new_column_name.replace("_", " ")

                try:
                    if isinstance(row[column_idx], int):
                        # row_data[new_column_name] = '{:,}'.format(row[column_idx])
                        row_data[new_column_name] = row[column_idx]
                    elif isinstance(row[column_idx], float):
                        # row_data[new_column_name] = '{:,}'.format(row[column_idx])
                        # Round off to 6 decimal points
                        row_data[new_column_name] = round(row[column_idx], 6)
                    elif isinstance(row[column_idx], decimal.Decimal):
                        # row_data[new_column_name] = '{:,}'.format(float(row[column_idx]))
                        # Round off to 6 decimal points
                        row_data[new_column_name] = round(float(row[column_idx]), 6)
                    # elif pd.api.types.is_datetime64_any_dtype(row[column_idx]):
                    #     row_data[new_column_name] = row[column_idx].astype(str)
                    elif (
                        isinstance(row[column_idx], datetime.date)
                        or isinstance(row[column_idx], datetime.datetime)
                    ) and not pd.isnull(row[column_idx]):
                        row_data[new_column_name] = row[column_idx].strftime("%m/%d/%Y")
                    else:
                        row_data[new_column_name] = str(row[column_idx])
                except Exception:
                    print(traceback.format_exc())
                    # logger.error(traceback.format_exc())
                    row_data[new_column_name] = str(row[column_idx])
            table_chart_json_dict["data"].append(row_data)
    else:
        code_level_logger.error(
            f"{base_chart_type} Chart Type is not supported in generate aggregated table chart!",
        )
        raise RuntimeError(
            f"{base_chart_type} Chart Type is not supported in generate aggregated table chart!",
        )

    table_chart_json_dict["Database_Identifier"] = database_properties["db_tag"]

    table_chart_json_dict["Chart_Size"] = sys.getsizeof(table_chart_json_dict["data"])

    table_chart_json_dict["Client_ID"] = client_id
    table_chart_json_dict["User_ID"] = user_id
    table_chart_json_dict["Session_ID"] = session_id

    return table_chart_json_dict


def generate_card_chart_from_histogram_chart_d3(
    llama70b_client: Any,
    user_query: str,
    chart_id: str,
    sql_query: str,
    chart_title: str,
    chart_axis: dict,
    chart_data: pd.DataFrame,
    database_properties: dict,
    ups_idx: int,
    chart_position: int,
    overall_title: str,
    client_id: str,
    user_id: str,
    session_id: str,
    sql_library: str,
    original_chart_type: str,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    card_chart_json_dict: dict = CARD_CHART_TEMPLATE_D3.copy()
    card_chart_json_dict["User_Query"] = user_query
    card_chart_json_dict["Chart_Query"] = sql_query
    card_chart_json_dict["Chart_SQL_Library"] = sql_library
    card_chart_json_dict["Chart_Name"] = f"Visual {ups_idx}"
    card_chart_json_dict["Chart_Axis"] = chart_axis
    card_chart_json_dict["Visual_Title"] = overall_title
    card_chart_json_dict["Chart_ID"] = chart_id
    card_chart_json_dict["Chart_Type"] = "card_chart"
    card_chart_json_dict["Original_Chart_Type"] = original_chart_type
    card_chart_json_dict["Chart_Position"] = str(chart_position)
    card_chart_json_dict["Chart_Title"] = chart_title
    card_chart_json_dict["yAxis"] = (
        chart_axis["xAxis_title"] + " (only 1 data point found)"
    )
    card_chart_json_dict["yAxis_Description"] = (
        chart_axis["xAxis_title"] + " (only 1 data point found)"
    )
    card_chart_json_dict["Aggregated_Table_JSON"] = generate_aggregated_table_chart_d3(
        user_query,
        sql_query,
        chart_id,
        chart_title,
        chart_data,
        database_properties,
        ups_idx,
        chart_position,
        overall_title,
        client_id,
        user_id,
        session_id,
        sql_library,
        chart_axis,
        original_chart_type,
        code_level_logger,
    )
    card_chart_json_dict["Aggregated_Table_Column"] = get_aggregated_columns(chart_axis)
    card_chart_json_dict["Database_Identifier"] = database_properties["db_tag"]

    chart_data_columns = list(chart_data.columns)

    if "xAxis" in chart_data_columns:
        xAxis_column_name = "xAxis"
        if (
            isinstance(
                chart_data[xAxis_column_name].values.tolist()[0],
                (str, datetime.datetime, datetime.date),
            )
        ) and len(chart_data_columns) > 1:
            chart_data_columns.remove(xAxis_column_name)
    elif "yAxis" in chart_data_columns:
        xAxis_column_name = "yAxis"
    elif (
        "xAxis_column" in chart_axis
        and isinstance(chart_axis["xAxis_column"], str)
        and chart_axis["xAxis_column"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_column"]
        if (
            isinstance(
                chart_data[xAxis_column_name].values.tolist()[0],
                (str, datetime.datetime, datetime.date),
            )
        ) and len(chart_data_columns) > 1:
            chart_data_columns.remove(xAxis_column_name)
    elif (
        "xAxis_column" in chart_axis
        and isinstance(chart_axis["xAxis_column"], list)
        and all(elem in chart_data_columns for elem in chart_axis["xAxis_column"])
    ):
        xAxis_column_names = chart_axis["xAxis_column"]
        for xAxis_column_name in xAxis_column_names:
            if (
                isinstance(
                    chart_data[xAxis_column_name].values.tolist()[0],
                    (str, datetime.datetime, datetime.date),
                )
            ) and len(chart_data_columns) > 1:
                chart_data_columns.remove(xAxis_column_name)
    elif (
        "xAxis_title" in chart_axis and chart_axis["xAxis_title"] in chart_data.columns
    ) or (
        "xAxis_title" in chart_axis and chart_axis["xAxis_title"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_title"]
        if (
            isinstance(
                chart_data[xAxis_column_name].values.tolist()[0],
                (str, datetime.datetime, datetime.date),
            )
        ) and len(chart_data_columns) > 1:
            chart_data_columns.remove(xAxis_column_name)
    else:
        code_level_logger.error(
            "card_chart_from_histogram_chart: X-Axis is not found in extraction!",
        )
        raise RuntimeError(
            "card_chart_from_histogram_chart: X-Axis is not found in extraction!",
        )

    for chart_column_name in chart_data_columns:
        try:
            if not isinstance(
                chart_data[chart_column_name].values.tolist()[0],
                datetime.date,
            ) and not isinstance(
                chart_data[chart_column_name].values.tolist()[0],
                datetime.datetime,
            ):
                if isinstance(chart_data[chart_column_name].values.tolist()[0], str):
                    chart_data[chart_column_name] = chart_data[
                        chart_column_name
                    ].replace("%", "", regex=True)
                chart_data[chart_column_name] = pd.to_numeric(
                    chart_data[chart_column_name],
                )
                chart_column_data = chart_data[chart_column_name].values.tolist()
                if len(chart_column_data) > 1:
                    chart_json_dict: dict = CHART_TYPE_FUNCTIONS_D3[
                        original_chart_type
                    ](
                        llama70b_client,
                        user_query,
                        sql_query,
                        chart_id,
                        chart_title,
                        chart_axis,
                        chart_data,
                        database_properties,
                        ups_idx,
                        chart_position,
                        overall_title,
                        client_id,
                        user_id,
                        sql_library,
                        logging_url,
                        code_level_logger,
                    )
                    return chart_json_dict
                chart_column_name_found = chart_column_name
                break
        except Exception:
            print(traceback.format_exc())

    if isinstance(
        chart_data[chart_column_name_found].values.tolist()[0],
        float,
    ) or isinstance(
        chart_data[chart_column_name_found].values.tolist()[0],
        decimal.Decimal,
    ):
        card_chart_json_dict["Y"] = (
            f"{round(chart_data[chart_column_name_found].values.tolist()[0], 2)}"
        )
    else:
        card_chart_json_dict["Y"] = (
            f"{chart_data[chart_column_name_found].values.tolist()[0]}"
        )

    if isinstance(card_chart_json_dict["yAxis"], list):
        card_chart_json_dict["yAxis"] = " ".join(card_chart_json_dict["yAxis"])
    elif isinstance(card_chart_json_dict["yAxis_Description"], list):
        card_chart_json_dict["yAxis_Description"] = " ".join(
            card_chart_json_dict["yAxis_Description"],
        )

    card_chart_json_dict["yAxis"] = card_chart_json_dict["yAxis"].replace("_", " ")
    card_chart_json_dict["yAxis_Description"] = card_chart_json_dict[
        "yAxis_Description"
    ].replace("_", " ")

    if not check_aggregation_phrases(card_chart_json_dict["yAxis"]):
        card_chart_json_dict["yAxis"] = "Total " + card_chart_json_dict["yAxis"]
        card_chart_json_dict["yAxis_Description"] = (
            "Total " + card_chart_json_dict["yAxis_Description"]
        )

    card_chart_json_dict["Client_ID"] = client_id
    card_chart_json_dict["User_ID"] = user_id
    card_chart_json_dict["Session_ID"] = session_id

    return card_chart_json_dict


def generate_card_chart_d3(
    llama70b_client: Any,
    user_query: str,
    chart_id: str,
    sql_query: str,
    chart_title: str,
    chart_axis: dict,
    chart_data: pd.DataFrame,
    database_properties: dict,
    ups_idx: int,
    chart_position: int,
    overall_title: str,
    client_id: str,
    user_id: str,
    session_id: str,
    sql_library: str,
    original_chart_type: str,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    # Special case for card chart from histogram chart
    if original_chart_type == "histogram_chart":
        return generate_card_chart_from_histogram_chart_d3(
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            original_chart_type,
            logging_url,
            code_level_logger,
        )

    card_chart_json_dict: dict = CARD_CHART_TEMPLATE_D3.copy()
    card_chart_json_dict["User_Query"] = user_query
    card_chart_json_dict["Chart_Query"] = sql_query
    card_chart_json_dict["Chart_SQL_Library"] = sql_library
    card_chart_json_dict["Chart_Name"] = f"Visual {ups_idx}"
    card_chart_json_dict["Chart_Axis"] = chart_axis
    card_chart_json_dict["Visual_Title"] = overall_title
    card_chart_json_dict["Chart_ID"] = chart_id
    card_chart_json_dict["Chart_Type"] = "card_chart"
    card_chart_json_dict["Original_Chart_Type"] = original_chart_type
    card_chart_json_dict["Chart_Position"] = str(chart_position)
    card_chart_json_dict["Chart_Title"] = chart_title
    card_chart_json_dict["yAxis"] = chart_title
    card_chart_json_dict["yAxis_Description"] = chart_title
    card_chart_json_dict["Aggregated_Table_JSON"] = generate_aggregated_table_chart_d3(
        user_query,
        sql_query,
        chart_id,
        chart_title,
        chart_data,
        database_properties,
        ups_idx,
        chart_position,
        overall_title,
        client_id,
        user_id,
        session_id,
        sql_library,
        chart_axis,
        original_chart_type,
        code_level_logger,
    )
    card_chart_json_dict["Aggregated_Table_Column"] = get_aggregated_columns(chart_axis)
    card_chart_json_dict["Database_Identifier"] = database_properties["db_tag"]

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
        code_level_logger.error("card_chart: X-Axis is not found in extraction!")
        raise RuntimeError("card_chart: X-Axis is not found in extraction!")

    if "yAxis" in chart_data_columns:
        yAxis_column_name = "yAxis"
    elif (
        "yAxis_column" in chart_axis
        and isinstance(chart_axis["yAxis_column"], str)
        and chart_axis["yAxis_column"] in chart_data_columns
    ):
        yAxis_column_name = chart_axis["yAxis_column"]
    else:
        code_level_logger.error("card_chart: Y-Axis is not found in extraction!")
        raise RuntimeError("card_chart: Y-Axis is not found in extraction!")

    y_values = chart_data[yAxis_column_name].values.tolist()

    if len(y_values) > 1:
        new_chart_json_dict: dict = CHART_TYPE_FUNCTIONS_D3[original_chart_type](
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            sql_library,
            logging_url,
            code_level_logger,
        )
        return new_chart_json_dict
    single_value = y_values[0]

    if isinstance(single_value, int):
        card_chart_json_dict["Y"] = f"{int(single_value):,}"
    elif isinstance(single_value, (float, decimal.Decimal)):
        card_chart_json_dict["Y"] = f"{round(float(single_value), 2):,.2f}"
    else:
        card_chart_json_dict["Y"] = str(single_value)

    if not (
        str(chart_data[xAxis_column_name].values.tolist()[0]) == "0"
        or str(chart_data[xAxis_column_name].values.tolist()[0]) == "nan"
    ):
        description = str(chart_data[xAxis_column_name].values.tolist()[0]).strip()
        card_chart_json_dict["Y"] = f"{card_chart_json_dict['Y']!s}\n({description})"

    # Set it empty as the chart title and yAxis are redundant
    card_chart_json_dict["yAxis"] = ""
    card_chart_json_dict["yAxis_Description"] = ""

    card_chart_json_dict["Client_ID"] = client_id
    card_chart_json_dict["User_ID"] = user_id
    card_chart_json_dict["Session_ID"] = session_id

    return card_chart_json_dict


def generate_combo_chart_d3(
    llama70b_client: Any,
    user_query: str,
    chart_id: str,
    sql_query: str,
    chart_title: str,
    chart_axis: dict,
    chart_data: pd.DataFrame,
    database_properties: dict,
    ups_idx: int,
    chart_position: int,
    overall_title: str,
    client_id: str,
    user_id: str,
    session_id: str,
    sql_library: str,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    combo_chart_json_dict: dict = BARLINECOMBO_CHART_TEMPLATE_D3.copy()
    combo_chart_json_dict["User_Query"] = user_query
    combo_chart_json_dict["Chart_Query"] = sql_query
    combo_chart_json_dict["Chart_Name"] = f"Visual {ups_idx}"
    combo_chart_json_dict["Visual_Title"] = overall_title
    combo_chart_json_dict["Chart_ID"] = chart_id
    combo_chart_json_dict["Chart_Axis"] = chart_axis
    combo_chart_json_dict["Chart_SQL_Library"] = sql_library
    combo_chart_json_dict["Chart_Type"] = "barlinecombo_chart"
    combo_chart_json_dict["Chart_Position"] = str(chart_position)
    combo_chart_json_dict["Chart_Title"] = chart_title
    combo_chart_json_dict["xAxis"] = chart_axis["xAxis_title"].replace("_", " ")
    combo_chart_json_dict["Aggregated_Table_JSON"] = generate_aggregated_table_chart_d3(
        user_query,
        sql_query,
        chart_id,
        chart_title,
        chart_data,
        database_properties,
        ups_idx,
        chart_position,
        overall_title,
        client_id,
        user_id,
        session_id,
        sql_library,
        chart_axis,
        combo_chart_json_dict["Chart_Type"],
        code_level_logger,
    )
    combo_chart_json_dict["Aggregated_Table_Column"] = get_aggregated_columns(
        chart_axis,
    )

    if "yAxisBar_title" in chart_axis:
        if check_aggregation_phrases(chart_axis["yAxisBar_title"].replace("_", " ")):
            yAxisBar_title = chart_axis["yAxisBar_title"].replace("_", " ")
        elif "yAxisBar_aggregation" in chart_axis:
            if chart_axis["yAxisBar_aggregation"] in ["SUM"]:
                yAxisBar_title = "Total " + chart_axis["yAxisBar_title"].replace(
                    "_",
                    " ",
                )
            elif chart_axis["yAxisBar_aggregation"] in ["AVG", "MEAN"]:
                yAxisBar_title = "Average " + chart_axis["yAxisBar_title"].replace(
                    "_",
                    " ",
                )
            elif chart_axis["yAxisBar_aggregation"] in ["MEDIAN"]:
                yAxisBar_title = "Median " + chart_axis["yAxisBar_title"].replace(
                    "_",
                    " ",
                )
            elif chart_axis["yAxisBar_aggregation"] in ["MIN"]:
                yAxisBar_title = "Minimum " + chart_axis["yAxisBar_title"].replace(
                    "_",
                    " ",
                )
            elif chart_axis["yAxisBar_aggregation"] in ["MAX"]:
                yAxisBar_title = "Maximum " + chart_axis["yAxisBar_title"].replace(
                    "_",
                    " ",
                )
            else:
                yAxisBar_title = "Total " + chart_axis["yAxisBar_title"].replace(
                    "_",
                    " ",
                )
        else:
            yAxisBar_title = "Total " + chart_axis["yAxisBar_title"].replace(
                "_",
                " ",
            )

        combo_chart_json_dict["yAxis"] = yAxisBar_title
        combo_chart_json_dict["yName"] = yAxisBar_title
    else:
        if check_aggregation_phrases(chart_axis["yAxis_title"].replace("_", " ")):
            yAxisBar_title = chart_axis["yAxis_title"].replace("_", " ")
        elif "yAxis_aggregation" in chart_axis:
            if chart_axis["yAxis_aggregation"] in ["SUM"]:
                yAxisBar_title = "Total " + chart_axis["yAxis_title"].replace(
                    "_",
                    " ",
                )
            elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
                yAxisBar_title = "Average " + chart_axis["yAxis_title"].replace(
                    "_",
                    " ",
                )
            elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
                yAxisBar_title = "Median " + chart_axis["yAxis_title"].replace(
                    "_",
                    " ",
                )
            elif chart_axis["yAxis_aggregation"] in ["MIN"]:
                yAxisBar_title = "Minimum " + chart_axis["yAxis_title"].replace(
                    "_",
                    " ",
                )
            elif chart_axis["yAxis_aggregation"] in ["MAX"]:
                yAxisBar_title = "Maximum " + chart_axis["yAxis_title"].replace(
                    "_",
                    " ",
                )
            else:
                yAxisBar_title = "Total " + chart_axis["yAxis_title"].replace(
                    "_",
                    " ",
                )
        else:
            yAxisBar_title = "Total " + chart_axis["yAxis_title"].replace("_", " ")

        combo_chart_json_dict["yAxis"] = yAxisBar_title
        combo_chart_json_dict["yName"] = yAxisBar_title

    if "yAxisLine_title" in chart_axis:
        if check_aggregation_phrases(chart_axis["yAxisLine_title"].replace("_", " ")):
            yAxisLine_title = chart_axis["yAxisLine_title"].replace("_", " ")
        elif "yAxisLine_aggregation" in chart_axis:
            if chart_axis["yAxisLine_aggregation"] in ["SUM"]:
                yAxisLine_title = "Total " + chart_axis["yAxisLine_title"].replace(
                    "_",
                    " ",
                )
            elif chart_axis["yAxisLine_aggregation"] in ["AVG", "MEAN"]:
                yAxisLine_title = "Average " + chart_axis["yAxisLine_title"].replace(
                    "_",
                    " ",
                )
            elif chart_axis["yAxisLine_aggregation"] in ["MEDIAN"]:
                yAxisLine_title = "Median " + chart_axis["yAxisLine_title"].replace(
                    "_",
                    " ",
                )
            elif chart_axis["yAxisLine_aggregation"] in ["MIN"]:
                yAxisLine_title = "Minimum " + chart_axis["yAxisLine_title"].replace(
                    "_",
                    " ",
                )
            elif chart_axis["yAxisLine_aggregation"] in ["MAX"]:
                yAxisLine_title = "Maximum " + chart_axis["yAxisLine_title"].replace(
                    "_",
                    " ",
                )
            else:
                yAxisLine_title = "Total " + chart_axis["yAxisLine_title"].replace(
                    "_",
                    " ",
                )
        else:
            yAxisLine_title = "Total " + chart_axis["yAxisLine_title"].replace(
                "_",
                " ",
            )

        combo_chart_json_dict["y2Axis"] = yAxisLine_title
        combo_chart_json_dict["y2Name"] = yAxisLine_title
    else:
        if check_aggregation_phrases(chart_axis["yAxis2_title"].replace("_", " ")):
            yAxisLine_title = chart_axis["yAxis2_title"].replace("_", " ")
        elif "yAxis2_aggregation" in chart_axis:
            if chart_axis["yAxis2_aggregation"] in ["SUM"]:
                yAxisLine_title = "Total " + chart_axis["yAxis2_title"].replace(
                    "_",
                    " ",
                )
            elif chart_axis["yAxis2_aggregation"] in ["AVG", "MEAN"]:
                yAxisLine_title = "Average " + chart_axis["yAxis2_title"].replace(
                    "_",
                    " ",
                )
            elif chart_axis["yAxis2_aggregation"] in ["MEDIAN"]:
                yAxisLine_title = "Median " + chart_axis["yAxis2_title"].replace(
                    "_",
                    " ",
                )
            elif chart_axis["yAxis2_aggregation"] in ["MIN"]:
                yAxisLine_title = "Minimum " + chart_axis["yAxis2_title"].replace(
                    "_",
                    " ",
                )
            elif chart_axis["yAxis2_aggregation"] in ["MAX"]:
                yAxisLine_title = "Maximum " + chart_axis["yAxis2_title"].replace(
                    "_",
                    " ",
                )
            else:
                yAxisLine_title = "Total " + chart_axis["yAxis2_title"].replace(
                    "_",
                    " ",
                )
        else:
            yAxisLine_title = "Total " + chart_axis["yAxis2_title"].replace(
                "_",
                " ",
            )

        combo_chart_json_dict["y2Axis"] = yAxisLine_title
        combo_chart_json_dict["y2Name"] = yAxisLine_title

    combo_chart_json_dict["Database_Identifier"] = database_properties["db_tag"]

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
        code_level_logger.error(
            "barlinecombo_chart: X-Axis is not found in extraction!"
        )
        raise RuntimeError("barlinecombo_chart: X-Axis is not found in extraction!")

    if "yAxisBar" in chart_data_columns:
        yAxisBar_column_name = "yAxisBar"
    elif (
        "yAxisBar_column" in chart_axis
        and isinstance(chart_axis["yAxisBar_column"], str)
        and chart_axis["yAxisBar_column"] in chart_data_columns
    ):
        yAxisBar_column_name = chart_axis["yAxisBar_column"]
    elif "yAxis" in chart_data_columns:
        yAxisBar_column_name = "yAxis"
    elif (
        "yAxis_column" in chart_axis
        and isinstance(chart_axis["yAxis_column"], str)
        and chart_axis["yAxis_column"] in chart_data_columns
    ):
        yAxisBar_column_name = chart_axis["yAxis_column"]
    else:
        code_level_logger.error(
            "barlinecombo_chart: yAxisBar is not found in extraction!"
        )
        raise RuntimeError("barlinecombo_chart: yAxisBar is not found in extraction!")

    object_columns = chart_data.select_dtypes(include=[object])

    if yAxisBar_column_name in object_columns:
        try:
            if not isinstance(
                chart_data[yAxisBar_column_name].values.tolist()[0],
                datetime.date,
            ) and not isinstance(
                chart_data[yAxisBar_column_name].values.tolist()[0],
                datetime.datetime,
            ):
                if isinstance(chart_data[yAxisBar_column_name].values.tolist()[0], str):
                    chart_data[yAxisBar_column_name] = chart_data[
                        yAxisBar_column_name
                    ].replace("%", "", regex=True)
                chart_data[yAxisBar_column_name] = pd.to_numeric(
                    chart_data[yAxisBar_column_name],
                )
        except Exception:
            code_level_logger.error("barlinecombo_chart: yAxisBar is not numerical!")
            raise RuntimeError("barlinecombo_chart: yAxisBar is not numerical!")

    if "yAxisLine" in chart_data_columns:
        yAxisLine_column_name = "yAxisLine"
    elif (
        "yAxisLine_column" in chart_axis
        and isinstance(chart_axis["yAxisLine_column"], str)
        and chart_axis["yAxisLine_column"] in chart_data_columns
    ):
        yAxisLine_column_name = chart_axis["yAxisLine_column"]
    elif "y2Axis" in chart_data_columns:
        yAxisLine_column_name = "y2Axis"
    elif (
        "y2Axis_column" in chart_axis
        and isinstance(chart_axis["y2Axis_column"], str)
        and chart_axis["y2Axis_column"] in chart_data_columns
    ):
        yAxisLine_column_name = chart_axis["y2Axis_column"]
    else:
        code_level_logger.error(
            "barlinecombo_chart: yAxisLine is not found in extraction!"
        )
        raise RuntimeError("barlinecombo_chart: yAxisLine is not found in extraction!")

    if yAxisLine_column_name in object_columns:
        try:
            if not isinstance(
                chart_data[yAxisLine_column_name].values.tolist()[0],
                datetime.date,
            ) and not isinstance(
                chart_data[yAxisLine_column_name].values.tolist()[0],
                datetime.datetime,
            ):
                if isinstance(
                    chart_data[yAxisLine_column_name].values.tolist()[0],
                    str,
                ):
                    chart_data[yAxisLine_column_name] = chart_data[
                        yAxisLine_column_name
                    ].replace("%", "", regex=True)
                chart_data[yAxisLine_column_name] = pd.to_numeric(
                    chart_data[yAxisLine_column_name],
                )
        except Exception:
            code_level_logger.error("barlinecombo_chart: yAxisLine is not numerical!")
            raise RuntimeError("barlinecombo_chart: yAxisLine is not numerical!")

    if (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{4}-\d{2}-\d{2}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%Y-%m-%d",
        )
    elif (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{2}/\d{2}/\d{4}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%d/%m/%Y",
        )

    if all(
        isinstance(val, (datetime.date, datetime.datetime))
        for val in chart_data[xAxis_column_name]
    ):
        chart_data, new_chart_axis, new_chart_title = adjust_axis_title_and_data(
            llama70b_client,
            chart_id,
            chart_data,
            chart_axis,
            chart_title,
            logging_url,
        )
        combo_chart_json_dict["xAxis"] = new_chart_axis["xAxis_title"].replace("_", " ")
        combo_chart_json_dict["Chart_Title"] = new_chart_title
    else:
        chart_data_columns = chart_data.columns

        if "yAxisBar" in chart_data_columns:
            chart_data.rename(columns={"yAxisBar": "yAxis"}, inplace=True)
            sql_query = sql_query.replace("yAxisBar", "yAxis")
        elif (
            "yAxisBar_column" in chart_axis
            and isinstance(chart_axis["yAxisBar_column"], str)
            and chart_axis["yAxisBar_column"] in chart_data_columns
        ):
            chart_data.rename(
                columns={chart_axis["yAxisBar_column"]: "yAxis"},
                inplace=True,
            )
            sql_query = sql_query.replace(chart_axis["yAxisBar_column"], "yAxis")
        elif (
            "yAxis_column" in chart_axis
            and isinstance(chart_axis["yAxis_column"], str)
            and chart_axis["yAxis_column"] in chart_data_columns
        ):
            chart_data.rename(
                columns={chart_axis["yAxis_column"]: "yAxis"},
                inplace=True,
            )
            sql_query = sql_query.replace(chart_axis["yAxis_column"], "yAxis")
        else:
            code_level_logger.error(
                "barlinecombo_chart: Unable to convert to grouped_bar_chart due to no yAxis not found!",
            )
            raise RuntimeError(
                "barlinecombo_chart: Unable to convert to grouped_bar_chart due to no yAxis not found!",
            )

        if "yAxisLine" in chart_data_columns:
            chart_data.rename(columns={"yAxisLine": "yAxis2"}, inplace=True)
            sql_query = sql_query.replace("yAxisLine", "yAxis2")
        elif (
            "yAxisLine_column" in chart_axis
            and isinstance(chart_axis["yAxisLine_column"], str)
            and chart_axis["yAxisLine_column"] in chart_data_columns
        ):
            chart_data.rename(
                columns={chart_axis["yAxisLine_column"]: "yAxis2"},
                inplace=True,
            )
            sql_query = sql_query.replace(chart_axis["yAxisLine_column"], "yAxis2")
        elif "y2Axis" in chart_data_columns:
            chart_data.rename(columns={"y2Axis": "yAxis2"}, inplace=True)
            sql_query = sql_query.replace("y2Axis", "yAxis2")
        elif (
            "y2Axis_column" in chart_axis
            and chart_axis["y2Axis_column"]
            and chart_axis["y2Axis_column"] in chart_data_columns
        ):
            chart_data.rename(
                columns={chart_axis["y2Axis_column"]: "yAxis2"},
                inplace=True,
            )
            sql_query = sql_query.replace(chart_axis["y2Axis_column"], "yAxis2")
        else:
            code_level_logger.error(
                "barlinecombo_chart: Unable to convert to grouped_bar_chart due to no yAxis2 not found!",
            )
            raise RuntimeError(
                "barlinecombo_chart: Unable to convert to grouped_bar_chart due to no yAxis2 not found!",
            )

        if "yAxisBar_title" in chart_axis:
            chart_axis["yAxis_title"] = chart_axis["yAxisBar_title"]
        if "yAxisBar_column" in chart_axis:
            chart_axis["yAxis_column"] = chart_axis["yAxisBar_column"]
        if "yAxisBar_aggregation" in chart_axis:
            chart_axis["yAxis_aggregation"] = chart_axis["yAxisBar_aggregation"]
        if "yAxisLine_title" in chart_axis:
            chart_axis["yAxis2_title"] = chart_axis["yAxisLine_title"]
        elif "y2Axis_title" in chart_axis:
            chart_axis["yAxis2_title"] = chart_axis["y2Axis_title"]
        if "yAxisLine_column" in chart_axis:
            chart_axis["yAxis2_column"] = chart_axis["yAxisLine_column"]
        elif "y2Axis_column" in chart_axis:
            chart_axis["yAxis2_column"] = chart_axis["y2Axis_column"]
        if "yAxisLine_aggregation" in chart_axis:
            chart_axis["yAxis2_aggregation"] = chart_axis["yAxisLine_aggregation"]
        elif "y2Axis_aggregation" in chart_axis:
            chart_axis["yAxis2_aggregation"] = chart_axis["y2Axis_aggregation"]
        chart_axis["series_title"] = ""
        chart_axis["series_column"] = ""

        return generate_group_bar_chart_d3(
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            logging_url,
            code_level_logger,
        )

    try:
        if len(chart_data[xAxis_column_name][0].split("-")) == 1:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                ),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (
                        int(date.split("-")[0]),
                        int(date.split("-")[1]),
                        int(date.split("-")[2]),
                    ),
                ),
            )
        else:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)
    except Exception:
        chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

    if isinstance(xAxis_column_name, str):
        chart_data = sort_pandas_date(chart_data, xAxis_column_name)

    combo_chart_json_dict["Chart_Data"] = []

    x_values = [str(x_data) for x_data in chart_data[xAxis_column_name].values.tolist()]

    if len(x_values) >= 1 and len(x_values) <= 2:
        return generate_group_bar_chart_d3(
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            logging_url,
            code_level_logger,
        )

    y_values = [
        float(val) if isinstance(val, decimal.Decimal) else val
        for val in chart_data[yAxisBar_column_name].values.tolist()
    ]
    y2_values = [
        float(val) if isinstance(val, decimal.Decimal) else val
        for val in chart_data[yAxisLine_column_name].values.tolist()
    ]

    if y2_values == []:
        # combo_chart_json_dict["Chart_Type"] = "bar_chart"
        combo_chart_json_dict["Chart_Type"] = "grouped_bar_chart"

        # if check_negative_value(combo_chart_json_dict["Y"]):
        #     # combo_chart_json_dict["Chart_Type"] = "column_chart"
        #     combo_chart_json_dict["Chart_Type"] = "grouped_column_chart"

        if len(y_values) == 1:
            return generate_card_chart_d3(
                llama70b_client,
                user_query,
                chart_id,
                sql_query,
                chart_title,
                chart_axis,
                chart_data,
                database_properties,
                ups_idx,
                chart_position,
                overall_title,
                client_id,
                user_id,
                session_id,
                sql_library,
                combo_chart_json_dict["Chart_Type"],
                logging_url,
                code_level_logger,
            )
    else:
        # if check_negative_value(combo_chart_json_dict["Y"]) or check_negative_value(
        #     combo_chart_json_dict["Y2"]
        # ):
        #     combo_chart_json_dict["Chart_Type"] = "grouped_column_chart"
        pass

    if isinstance(combo_chart_json_dict["xAxis"], list):
        combo_chart_json_dict["xAxis"] = "/".join(combo_chart_json_dict["xAxis"])

    if isinstance(combo_chart_json_dict["yAxis"], list):
        combo_chart_json_dict["yAxis"] = "/".join(combo_chart_json_dict["yAxis"])

    if isinstance(combo_chart_json_dict["y2Axis"], list):
        combo_chart_json_dict["y2Axis"] = "/".join(combo_chart_json_dict["y2Axis"])

    combo_chart_json_dict["Client_ID"] = client_id
    combo_chart_json_dict["User_ID"] = user_id
    combo_chart_json_dict["Session_ID"] = session_id

    if not (isinstance(y_values[0], int) or isinstance(y_values[0], float)):
        code_level_logger.error("combo_chart: Y-axis is not integer or float!")
        raise RuntimeError("combo_chart: Y-axis is not integer or float!")

    if not (isinstance(y2_values[0], int) or isinstance(y2_values[0], float)):
        code_level_logger.error("combo_chart: Y2-axis is not integer or float!")
        raise RuntimeError("combo_chart: Y2-axis is not integer or float!")

    if x_values == [] or x_values == [""]:
        code_level_logger.error("combo_chart: One or more X-axis values are empty!")
        raise RuntimeError("combo_chart: One or more X-axis values are empty!")

    return combo_chart_json_dict


def generate_line_chart_d3(
    llama70b_client: Any,
    user_query: str,
    chart_id: str,
    sql_query: str,
    chart_title: str,
    chart_axis: dict,
    chart_data: pd.DataFrame,
    database_properties: dict,
    ups_idx: int,
    chart_position: int,
    overall_title: str,
    client_id: str,
    user_id: str,
    session_id: str,
    sql_library: str,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    line_chart_json_dict: dict = LINE_CHART_TEMPLATE_D3.copy()
    line_chart_json_dict["User_Query"] = user_query
    line_chart_json_dict["Chart_Query"] = sql_query
    line_chart_json_dict["Chart_Name"] = f"Visual {ups_idx}"
    line_chart_json_dict["Chart_Axis"] = chart_axis
    line_chart_json_dict["Chart_SQL_Library"] = sql_library
    line_chart_json_dict["Visual_Title"] = overall_title
    line_chart_json_dict["Chart_ID"] = chart_id
    line_chart_json_dict["Chart_Type"] = "line_chart"
    line_chart_json_dict["Chart_Position"] = str(chart_position)
    line_chart_json_dict["Chart_Title"] = chart_title

    line_chart_json_dict["xAxis"] = chart_axis["xAxis_title"].replace("_", " ")
    line_chart_json_dict["Aggregated_Table_JSON"] = generate_aggregated_table_chart_d3(
        user_query,
        sql_query,
        chart_id,
        chart_title,
        chart_data,
        database_properties,
        ups_idx,
        chart_position,
        overall_title,
        client_id,
        user_id,
        session_id,
        sql_library,
        chart_axis,
        line_chart_json_dict["Chart_Type"],
        code_level_logger,
    )
    line_chart_json_dict["Aggregated_Table_Column"] = get_aggregated_columns(chart_axis)

    yAxis_title = ""

    for chart_axis_key in chart_axis:
        if (
            chart_axis_key.lower()[0] != "y"
            or "title" not in chart_axis_key.lower()
            or chart_axis[chart_axis_key] == ""
        ):
            continue
        if yAxis_title == "":
            yAxis_title += chart_axis[chart_axis_key]
        else:
            # yAxis_title += f"/{chart_axis[chart_axis_key]}"
            yAxis_title = "Amount"
            break
    if (
        check_aggregation_phrases(yAxis_title.replace("_", " "))
        or yAxis_title == "Amount"
    ):
        line_chart_json_dict["yAxis"] = yAxis_title.replace("_", " ")
    elif "yAxis_aggregation" in chart_axis:
        if chart_axis["yAxis_aggregation"] in ["SUM"]:
            line_chart_json_dict["yAxis"] = "Total " + yAxis_title.replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
            line_chart_json_dict["yAxis"] = "Average " + yAxis_title.replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
            line_chart_json_dict["yAxis"] = "Median " + yAxis_title.replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["MIN"]:
            line_chart_json_dict["yAxis"] = "Minimum " + yAxis_title.replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["MAX"]:
            line_chart_json_dict["yAxis"] = "Maximum " + yAxis_title.replace(
                "_",
                " ",
            )
        else:
            line_chart_json_dict["yAxis"] = "Total " + yAxis_title.replace("_", " ")
    else:
        line_chart_json_dict["yAxis"] = "Total " + yAxis_title.replace("_", " ")

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
        code_level_logger.error("line_chart: X-Axis is not found in extraction!")
        raise RuntimeError("line_chart: X-Axis is not found in extraction!")

    if "series" in chart_data_columns:
        series_column_name = "series"
    elif (
        "series_column" in chart_axis
        and isinstance(chart_axis["series_column"], str)
        and chart_axis["series_column"] in chart_data_columns
    ):
        series_column_name = chart_axis["series_column"]
    else:
        series_column_name = ""

    object_columns = chart_data.select_dtypes(include=[object])

    yAxis_column_names = list(chart_data.columns)
    yAxis_column_names.remove(xAxis_column_name)
    if series_column_name in yAxis_column_names:
        yAxis_column_names.remove(series_column_name)

    for yAxis_column_name in yAxis_column_names:
        if yAxis_column_name in object_columns:
            try:
                if not isinstance(
                    chart_data[yAxis_column_name].values.tolist()[0],
                    datetime.date,
                ) and not isinstance(
                    chart_data[yAxis_column_name].values.tolist()[0],
                    datetime.datetime,
                ):
                    if isinstance(
                        chart_data[yAxis_column_name].values.tolist()[0],
                        str,
                    ):
                        chart_data[yAxis_column_name] = chart_data[
                            yAxis_column_name
                        ].replace("%", "", regex=True)
                    chart_data[yAxis_column_name] = pd.to_numeric(
                        chart_data[yAxis_column_name],
                    )
            except Exception:
                code_level_logger.error(
                    f"line_chart: {yAxis_column_name} is not numerical!"
                )
                raise RuntimeError(f"line_chart: {yAxis_column_name} is not numerical!")

    if (
        series_column_name != ""
        and series_column_name in chart_data.columns
        and chart_data[series_column_name].nunique() > 1
    ):
        new_chart_data = pd.DataFrame()

        pivot_data = chart_data.pivot_table(
            index=xAxis_column_name,
            columns=series_column_name,
            values=yAxis_column_names,
        )
        pivot_data = pivot_data.reset_index()
        new_chart_data[xAxis_column_name] = [
            float(val) if isinstance(val, decimal.Decimal) else val
            for val in pivot_data[xAxis_column_name].values.tolist()
        ]

        for yAxis_column_name in yAxis_column_names:
            yAxis_pivot_table = pivot_data[yAxis_column_name]
            for yAxis_pivot_column in list(yAxis_pivot_table.columns):
                new_columns = {
                    f"{yAxis_column_name}_{yAxis_pivot_column}": [
                        float(val) if isinstance(val, decimal.Decimal) else val
                        for val in yAxis_pivot_table[yAxis_pivot_column].values.tolist()
                    ],
                }
                added_chart_data = pd.DataFrame(new_columns)
                new_chart_data = pd.concat([new_chart_data, added_chart_data], axis=1)

        chart_data = new_chart_data.fillna(
            {
                col: (
                    0 if new_chart_data[col].dtype in [np.float64, np.int64] else "null"
                )
                for col in new_chart_data.columns
            },
        )

    if (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{4}-\d{2}-\d{2}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%Y-%m-%d",
        )
    elif (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{2}/\d{2}/\d{4}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%d/%m/%Y",
        )

    if all(
        isinstance(val, (datetime.date, datetime.datetime))
        for val in chart_data[xAxis_column_name]
    ):
        chart_data, new_chart_axis, new_chart_title = adjust_axis_title_and_data(
            llama70b_client,
            chart_id,
            chart_data,
            chart_axis,
            chart_title,
            logging_url,
        )
        line_chart_json_dict["xAxis"] = new_chart_axis["xAxis_title"].replace("_", " ")
        line_chart_json_dict["Chart_Title"] = new_chart_title

    try:
        if len(chart_data[xAxis_column_name][0].split("-")) == 1:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                ),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (
                        int(date.split("-")[0]),
                        int(date.split("-")[1]),
                        int(date.split("-")[2]),
                    ),
                ),
            )
        else:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)
    except Exception:
        chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

    if isinstance(xAxis_column_name, str):
        chart_data = sort_pandas_date(chart_data, xAxis_column_name)

    line_chart_json_dict["X"] = [
        str(x_data) for x_data in chart_data[xAxis_column_name].values.tolist()
    ]

    if len(line_chart_json_dict["X"]) >= 1 and len(line_chart_json_dict["X"]) <= 2:
        return generate_group_bar_chart_d3(
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            logging_url,
            code_level_logger,
        )

    yAxis_idx = 1

    for column_name in list(chart_data.columns):
        if not re.search(r"yAxis([23456789])?", column_name, re.IGNORECASE):
            continue

        if yAxis_idx <= 1:
            line_chart_json_dict["Y"] = [
                float(val) if isinstance(val, decimal.Decimal) else val
                for val in chart_data[column_name].values.tolist()
            ]

            underscore_index = column_name.find("_")

            # No Series
            if underscore_index == -1:
                if check_aggregation_phrases(
                    chart_axis[f"{column_name}_title"].replace("_", " "),
                ):
                    line_chart_json_dict["yName"] = chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")
                elif f"{column_name}_aggregation" in chart_axis:
                    if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                        line_chart_json_dict["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["AVG", "MEAN"]:
                        line_chart_json_dict["yName"] = "Average " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                        line_chart_json_dict["yName"] = "Median " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                        line_chart_json_dict["yName"] = "Minimum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                        line_chart_json_dict["yName"] = "Maximum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    else:
                        line_chart_json_dict["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                else:
                    line_chart_json_dict["yName"] = "Total " + chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")
            # Has Series
            else:
                original_column_name = column_name[:underscore_index]
                series_name = column_name[underscore_index + 1 :]

                # Add Series Title to Series Name
                if "series_title" in chart_axis and chart_axis["series_title"] != "":
                    series_name = f"""{chart_axis["series_title"]}: {series_name}"""

                if (
                    f"{original_column_name}_title" in chart_axis
                    and check_aggregation_phrases(
                        f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        ),
                    )
                ):
                    line_chart_json_dict["yName"] = (
                        f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        )
                    )
                elif f"{original_column_name}_aggregation" in chart_axis:
                    if chart_axis[f"{original_column_name}_aggregation"] in ["SUM"]:
                        line_chart_json_dict["yName"] = (
                            "Total "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in [
                        "AVG",
                        "MEAN",
                    ]:
                        line_chart_json_dict["yName"] = (
                            "Average "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in [
                        "MEDIAN",
                    ]:
                        line_chart_json_dict["yName"] = (
                            "Median "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in ["MIN"]:
                        line_chart_json_dict["yName"] = (
                            "Minimum "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in ["MAX"]:
                        line_chart_json_dict["yName"] = (
                            "Maximum "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    else:
                        line_chart_json_dict["yName"] = (
                            "Total "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                else:
                    line_chart_json_dict["yName"] = (
                        "Total "
                        + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        )
                    )

            if not (
                isinstance(line_chart_json_dict["Y"][0], int)
                or isinstance(line_chart_json_dict["Y"][0], float)
            ):
                code_level_logger.error("line_chart: Y-axis is not integer or float!")
                raise RuntimeError("line_chart: Y-axis is not integer or float!")

            # if check_negative_value(line_chart_json_dict["Y"]):
            #     # line_chart_json_dict["Chart_Type"] = "column_chart"
            #     line_chart_json_dict["Chart_Type"] = "grouped_column_chart"
        else:
            line_chart_json_dict[f"Y{yAxis_idx}"] = [
                float(val) if isinstance(val, decimal.Decimal) else val
                for val in chart_data[column_name].values.tolist()
            ]

            underscore_index = column_name.find("_")

            # No Series
            if underscore_index == -1:
                line_chart_json_dict[f"y{yAxis_idx}Name"] = chart_axis[
                    f"{column_name}_title"
                ].replace("_", " ")
                if line_chart_json_dict[f"y{yAxis_idx}Name"] == "":
                    line_chart_json_dict[f"y{yAxis_idx}Name"] = line_chart_json_dict[
                        "yName"
                    ].replace("_", " ")

                if not check_aggregation_phrases(
                    line_chart_json_dict[f"y{yAxis_idx}Name"],
                ):
                    if f"{column_name}_aggregation" in chart_axis:
                        if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                            line_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Total " + line_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            line_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Average " + line_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                            line_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Median " + line_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                            line_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Minimum " + line_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                            line_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Maximum " + line_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        else:
                            line_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Total " + line_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                    else:
                        line_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Total " + line_chart_json_dict[f"y{yAxis_idx}Name"]
                        )
            # Has Series
            else:
                original_column_name = column_name[:underscore_index]
                series_name = column_name[underscore_index + 1 :]

                # Add Series Title to Series Name
                if "series_title" in chart_axis and chart_axis["series_title"] != "":
                    series_name = f"""{chart_axis["series_title"]}: {series_name}"""

                line_chart_json_dict[f"y{yAxis_idx}Name"] = (
                    f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                        "_",
                        " ",
                    )
                )
                if line_chart_json_dict[f"y{yAxis_idx}Name"] == "":
                    line_chart_json_dict[f"y{yAxis_idx}Name"] = line_chart_json_dict[
                        "yName"
                    ].replace("_", " ")

                if not check_aggregation_phrases(
                    line_chart_json_dict[f"y{yAxis_idx}Name"],
                ):
                    if f"{original_column_name}_aggregation" in chart_axis:
                        if chart_axis[f"{original_column_name}_aggregation"] in ["SUM"]:
                            line_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Total " + line_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            line_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Average " + line_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MEDIAN",
                        ]:
                            line_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Median " + line_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MIN",
                        ]:
                            line_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Minimum " + line_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MAX",
                        ]:
                            line_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Maximum " + line_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        else:
                            line_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Total " + line_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                    else:
                        line_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Total " + line_chart_json_dict[f"y{yAxis_idx}Name"]
                        )

            # if line_chart_json_dict["Chart_Type"] == "line_chart":
            #     line_chart_json_dict["Chart_Type"] = "stackedline_chart"

            if not (
                isinstance(line_chart_json_dict[f"Y{yAxis_idx}"][0], int)
                or isinstance(line_chart_json_dict[f"Y{yAxis_idx}"][0], float)
            ):
                code_level_logger.error(
                    f"line_chart: Y{yAxis_idx}-axis is not integer or float!",
                )
                raise RuntimeError(
                    f"line_chart: Y{yAxis_idx}-axis is not integer or float!",
                )

            # if (
            #     check_negative_value(line_chart_json_dict[f"Y{yAxis_idx}"])
            #     or line_chart_json_dict["Chart_Type"] == "column_chart"
            # ):
            #     line_chart_json_dict["Chart_Type"] = "grouped_column_chart"

        yAxis_idx += 1

    if any(
        line_chart_json_dict[key] == [] or line_chart_json_dict[key] == [""]
        for key in line_chart_json_dict
        if re.match(r"^X\d*$", key)
    ):
        code_level_logger.error("line_chart: One or more X-axis values are empty!")
        raise RuntimeError("line_chart: One or more X-axis values are empty!")

    if len(line_chart_json_dict["Y"]) == 1 and line_chart_json_dict["Y2"] == []:
        return generate_card_chart_d3(
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            line_chart_json_dict["Chart_Type"],
            logging_url,
            code_level_logger,
        )

    chart_data_lists = []

    x_values = line_chart_json_dict["X"]

    if "Y" in line_chart_json_dict:
        main_y_data = []
        for i in range(len(x_values)):
            x_value = x_values[i]
            main_y_value = line_chart_json_dict["Y"][i]
            main_group_name = line_chart_json_dict.get("yName", "Series 1")
            main_y_data.append(
                {
                    "X_Value": x_value,
                    "Y_Value": main_y_value,
                    "Group_Name": main_group_name,
                },
            )
        chart_data_lists.append(main_y_data)

    j = 2
    while f"Y{j}" in line_chart_json_dict:
        additional_y_data = []

        for i in range(len(x_values)):
            x_value = x_values[i]

            y_key = f"Y{j}"
            if y_key in line_chart_json_dict:
                additional_y_value = line_chart_json_dict[y_key][i]
                group_name_key = f"y{j}Name"
                group_name = line_chart_json_dict.get(group_name_key, f"Series {j}")
                additional_y_data.append(
                    {
                        "X_Value": x_value,
                        "Y_Value": additional_y_value,
                        "Group_Name": group_name,
                    },
                )

        if additional_y_data:
            chart_data_lists.append(additional_y_data)

        j += 1

    line_chart_json_dict["Chart_Data"] = chart_data_lists

    line_chart_json_dict["Database_Identifier"] = database_properties["db_tag"]

    line_chart_json_dict["Client_ID"] = client_id
    line_chart_json_dict["User_ID"] = user_id
    line_chart_json_dict["Session_ID"] = session_id

    if len(line_chart_json_dict["Y"]) == 1 and line_chart_json_dict["Y2"] == []:
        return generate_card_chart_d3(
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            line_chart_json_dict["Chart_Type"],
            logging_url,
            code_level_logger,
        )

    keys_to_remove = ["X", "Y", "yName"]

    i = 2
    while f"y{i}Name" in line_chart_json_dict:
        keys_to_remove.append(f"y{i}Name")
        i += 1

    j = 2
    while f"Y{j}" in line_chart_json_dict:
        keys_to_remove.append(f"Y{j}")
        j += 1

    # Remove all specified keys ['X', 'Y', 'yName'] and etc. from the dictionary
    for key in keys_to_remove:
        if key in line_chart_json_dict:
            del line_chart_json_dict[key]

    return line_chart_json_dict


def generate_scatterplot_chart_d3(
    llama70b_client: Any,
    user_query: str,
    chart_id: str,
    sql_query: str,
    chart_title: str,
    chart_axis: dict,
    chart_data: pd.DataFrame,
    database_properties: dict,
    ups_idx: int,
    chart_position: int,
    overall_title: str,
    client_id: str,
    user_id: str,
    session_id: str,
    sql_library: str,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    scatterplot_chart_json_dict: dict = SCATTERPLOT_CHART_TEMPLATE_D3.copy()
    scatterplot_chart_json_dict["User_Query"] = user_query
    scatterplot_chart_json_dict["Chart_Query"] = sql_query
    scatterplot_chart_json_dict["Chart_Name"] = f"Visual {ups_idx}"
    scatterplot_chart_json_dict["Visual_Title"] = overall_title
    scatterplot_chart_json_dict["Chart_ID"] = chart_id
    scatterplot_chart_json_dict["Chart_Axis"] = chart_axis
    scatterplot_chart_json_dict["Chart_SQL_Library"] = sql_library
    scatterplot_chart_json_dict["Chart_Type"] = "scatterplot_chart"
    scatterplot_chart_json_dict["Chart_Position"] = str(chart_position)
    scatterplot_chart_json_dict["Chart_Title"] = chart_title

    scatterplot_chart_json_dict["xAxis"] = chart_axis["xAxis_title"].replace("_", " ")
    scatterplot_chart_json_dict["Chart_Data"] = []
    scatterplot_chart_json_dict["Aggregated_Table_JSON"] = (
        generate_aggregated_table_chart_d3(
            user_query,
            sql_query,
            chart_id,
            chart_title,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            chart_axis,
            scatterplot_chart_json_dict["Chart_Type"],
            code_level_logger,
        )
    )
    scatterplot_chart_json_dict["Aggregated_Table_Column"] = get_aggregated_columns(
        chart_axis,
    )

    yAxis_title = ""

    for chart_axis_key in chart_axis:
        if (
            chart_axis_key.lower()[0] != "y"
            or "title" not in chart_axis_key.lower()
            or chart_axis[chart_axis_key] == ""
        ):
            continue
        if yAxis_title == "":
            yAxis_title += chart_axis[chart_axis_key]
        else:
            # yAxis_title += f"/{chart_axis[chart_axis_key]}"
            yAxis_title = "Amount"
            break

    if (
        check_aggregation_phrases(yAxis_title.replace("_", " "))
        or yAxis_title == "Amount"
    ):
        scatterplot_chart_json_dict["yAxis"] = yAxis_title.replace("_", " ")
    elif "yAxis_aggregation" in chart_axis:
        if chart_axis["yAxis_aggregation"] in ["SUM"]:
            scatterplot_chart_json_dict["yAxis"] = "Total " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            scatterplot_chart_json_dict["yName"] = "Total " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
            scatterplot_chart_json_dict["yAxis"] = "Average " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            scatterplot_chart_json_dict["yName"] = "Average " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
            scatterplot_chart_json_dict["yAxis"] = "Median " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            scatterplot_chart_json_dict["yName"] = "Median " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["MIN"]:
            scatterplot_chart_json_dict["yAxis"] = "Minimum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            scatterplot_chart_json_dict["yName"] = "Minimum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["MAX"]:
            scatterplot_chart_json_dict["yAxis"] = "Maximum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            scatterplot_chart_json_dict["yName"] = "Maximum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        else:
            scatterplot_chart_json_dict["yAxis"] = "Total " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            scatterplot_chart_json_dict["yName"] = "Total " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
    else:
        scatterplot_chart_json_dict["yAxis"] = "Total " + chart_axis[
            "yAxis_title"
        ].replace("_", " ")
        scatterplot_chart_json_dict["yName"] = "Total " + chart_axis[
            "yAxis_title"
        ].replace("_", " ")

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
        code_level_logger.error("scatterplot_chart: X-Axis is not found in extraction!")
        raise RuntimeError("scatterplot_chart: X-Axis is not found in extraction!")

    if "yAxis" in chart_data_columns:
        yAxis_column_name = "yAxis"
    elif (
        "yAxis_column" in chart_axis
        and isinstance(chart_axis["yAxis_column"], str)
        and chart_axis["yAxis_column"] in chart_data_columns
    ):
        yAxis_column_name = chart_axis["yAxis_column"]
    else:
        code_level_logger.error("scatterplot_chart: Y-Axis is not found in extraction!")
        raise RuntimeError("scatterplot_chart: Y-Axis is not found in extraction!")

    if "series" in chart_data_columns:
        series_column_name = "series"
    elif (
        "series_column" in chart_axis
        and isinstance(chart_axis["series_column"], str)
        and chart_axis["series_column"] in chart_data_columns
    ):
        series_column_name = chart_axis["series_column"]
    else:
        series_column_name = ""

    object_columns = chart_data.select_dtypes(include=[object])

    numerical_column_names = list(chart_data.columns)
    if series_column_name in numerical_column_names:
        numerical_column_names.remove(series_column_name)

    for numerical_column_name in numerical_column_names:
        if numerical_column_name in object_columns:
            try:
                if not isinstance(
                    chart_data[numerical_column_name].values.tolist()[0],
                    datetime.date,
                ) and not isinstance(
                    chart_data[numerical_column_name].values.tolist()[0],
                    datetime.datetime,
                ):
                    if isinstance(
                        chart_data[numerical_column_name].values.tolist()[0],
                        str,
                    ):
                        chart_data[numerical_column_name] = chart_data[
                            numerical_column_name
                        ].replace("%", "", regex=True)
                    chart_data[numerical_column_name] = pd.to_numeric(
                        chart_data[numerical_column_name],
                    )
            except Exception:
                code_level_logger.error(
                    f"scatterplot_chart: {numerical_column_name} is not numerical!",
                )
                raise RuntimeError(
                    f"scatterplot_chart: {numerical_column_name} is not numerical!",
                )

    chart_data = chart_data.fillna(
        {
            col: 0 if chart_data[col].dtype in [np.float64, np.int64] else "null"
            for col in chart_data.columns
        },
    )
    chart_data = chart_data.sort_values(by=yAxis_column_name, ascending=False)

    if (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{4}-\d{2}-\d{2}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%Y-%m-%d",
        )
    elif (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{2}/\d{2}/\d{4}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%d/%m/%Y",
        )

    if all(
        isinstance(val, (datetime.date, datetime.datetime))
        for val in chart_data[xAxis_column_name]
    ):
        chart_data, new_chart_axis, new_chart_title = adjust_axis_title_and_data(
            llama70b_client,
            chart_id,
            chart_data,
            chart_axis,
            chart_title,
            logging_url,
        )
        scatterplot_chart_json_dict["xAxis"] = new_chart_axis["xAxis_title"].replace(
            "_",
            " ",
        )
        scatterplot_chart_json_dict["Chart_Title"] = new_chart_title

    try:
        if len(chart_data[xAxis_column_name][0].split("-")) == 1:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                ),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (
                        int(date.split("-")[0]),
                        int(date.split("-")[1]),
                        int(date.split("-")[2]),
                    ),
                ),
            )
        else:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)
    except Exception:
        chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

    if isinstance(xAxis_column_name, str):
        chart_data = sort_pandas_date(chart_data, xAxis_column_name)

    if (
        series_column_name != ""
        and series_column_name in chart_data.columns
        and chart_data[series_column_name].nunique() > 1
    ):
        unique_series = chart_data[series_column_name].unique().tolist()

        yAxis_idx = 1

        for series_value in unique_series:
            series_chart_data: pd.DataFrame = chart_data[
                chart_data[series_column_name] == series_value
            ]

            if (
                not isinstance(
                    series_chart_data[xAxis_column_name].reset_index().iloc[0],
                    datetime.date,
                )
                and not isinstance(
                    series_chart_data[xAxis_column_name].reset_index().iloc[0],
                    datetime.datetime,
                )
            ) and (
                re.search(
                    r"^\d{4}-\d{2}-\d{2}$",
                    str(series_chart_data[xAxis_column_name].values.tolist()[0]),
                    re.IGNORECASE,
                )
            ):
                series_chart_data[xAxis_column_name] = pd.to_datetime(
                    series_chart_data[xAxis_column_name],
                    format="%Y-%m-%d",
                )
            elif (
                not isinstance(
                    series_chart_data[xAxis_column_name].reset_index().iloc[0],
                    datetime.date,
                )
                and not isinstance(
                    series_chart_data[xAxis_column_name].reset_index().iloc[0],
                    datetime.datetime,
                )
            ) and (
                re.search(
                    r"^\d{2}/\d{2}/\d{4}$",
                    str(series_chart_data[xAxis_column_name].values.tolist()[0]),
                    re.IGNORECASE,
                )
            ):
                series_chart_data[xAxis_column_name] = pd.to_datetime(
                    series_chart_data[xAxis_column_name],
                    format="%d/%m/%Y",
                )

            if all(
                isinstance(val, (datetime.date, datetime.datetime))
                for val in series_chart_data[xAxis_column_name]
            ):
                series_chart_data, new_chart_axis, new_chart_title = (
                    adjust_axis_title_and_data(
                        llama70b_client,
                        chart_id,
                        chart_data,
                        chart_axis,
                        chart_title,
                        logging_url,
                    )
                )
                scatterplot_chart_json_dict["xAxis"] = new_chart_axis[
                    "xAxis_title"
                ].replace("_", " ")
                scatterplot_chart_json_dict["Chart_Title"] = new_chart_title

            try:
                if len(series_chart_data[xAxis_column_name][0].split("-")) == 1:
                    series_chart_data = series_chart_data.sort_values(
                        by=xAxis_column_name,
                        key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
                    )
                elif len(series_chart_data[xAxis_column_name][0].split("-")) == 2:
                    series_chart_data = series_chart_data.sort_values(
                        by=xAxis_column_name,
                        key=lambda x: x.apply(
                            lambda date: (
                                int(date.split("-")[0]),
                                int(date.split("-")[1]),
                            ),
                        ),
                    )
                elif len(series_chart_data[xAxis_column_name][0].split("-")) == 3:
                    series_chart_data = series_chart_data.sort_values(
                        by=xAxis_column_name,
                        key=lambda x: x.apply(
                            lambda date: (
                                int(date.split("-")[0]),
                                int(date.split("-")[1]),
                                int(date.split("-")[2]),
                            ),
                        ),
                    )
                else:
                    series_chart_data = series_chart_data.sort_values(
                        by=xAxis_column_name,
                        ascending=True,
                    )
            except Exception:
                series_chart_data = series_chart_data.sort_values(
                    by=xAxis_column_name,
                    ascending=True,
                )

            if isinstance(xAxis_column_name, str):
                series_chart_data = sort_pandas_date(
                    series_chart_data,
                    xAxis_column_name,
                )

            for series_chart_column in list(series_chart_data.columns):
                if not re.search(
                    r"yAxis([23456789])?",
                    series_chart_column,
                    re.IGNORECASE,
                ):
                    continue

                if yAxis_idx <= 1:
                    scatterplot_chart_json_dict["X"] = [
                        float(x_data) if isinstance(x_data, decimal.Decimal) else x_data
                        for x_data in series_chart_data[
                            xAxis_column_name
                        ].values.tolist()
                    ]

                    scatterplot_chart_json_dict["Y"] = [
                        float(val) if isinstance(val, decimal.Decimal) else val
                        for val in series_chart_data[
                            series_chart_column
                        ].values.tolist()
                    ]

                    # Add Series Title to Series Value
                    if (
                        "series_title" in chart_axis
                        and chart_axis["series_title"] != ""
                    ):
                        series_value = (
                            f"""{chart_axis["series_title"]}: {series_value}"""
                        )

                    if (
                        f"{series_chart_column}_title" in chart_axis
                        and check_aggregation_phrases(
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})",
                        )
                    ):
                        scatterplot_chart_json_dict["yName"] = (
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif f"{series_chart_column}_aggregation" in chart_axis:
                        if chart_axis[f"{series_chart_column}_aggregation"] in ["SUM"]:
                            scatterplot_chart_json_dict["yName"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            scatterplot_chart_json_dict["yName"] = (
                                f"Average {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "MEDIAN",
                        ]:
                            scatterplot_chart_json_dict["yName"] = (
                                f"Median {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "MIN",
                        ]:
                            scatterplot_chart_json_dict["yName"] = (
                                f"Minimum {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "MAX",
                        ]:
                            scatterplot_chart_json_dict["yName"] = (
                                f"Maximum {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        else:
                            scatterplot_chart_json_dict["yName"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                    else:
                        scatterplot_chart_json_dict["yName"] = (
                            f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                "_",
                                " ",
                            )
                        )

                    if not (
                        isinstance(scatterplot_chart_json_dict["Y"][0], int)
                        or isinstance(scatterplot_chart_json_dict["Y"][0], float)
                    ):
                        code_level_logger.error(
                            "scatterplot_chart: Y-axis is not integer or float!",
                        )
                        raise RuntimeError(
                            "scatterplot_chart: Y-axis is not integer or float!",
                        )

                    # if check_negative_value(scatterplot_chart_json_dict["Y"]):
                    #     # scatterplot_chart_json_dict["Chart_Type"] = "column_chart"
                    #     scatterplot_chart_json_dict["Chart_Type"] = "grouped_column_chart"
                else:
                    scatterplot_chart_json_dict[f"X{yAxis_idx}"] = [
                        float(val) if isinstance(val, decimal.Decimal) else val
                        for val in series_chart_data[xAxis_column_name].values.tolist()
                    ]

                    scatterplot_chart_json_dict[f"Y{yAxis_idx}"] = [
                        float(val) if isinstance(val, decimal.Decimal) else val
                        for val in series_chart_data[
                            series_chart_column
                        ].values.tolist()
                    ]

                    # Add Series Title to Series Value
                    if (
                        "series_title" in chart_axis
                        and chart_axis["series_title"] != ""
                    ):
                        series_value = (
                            f"""{chart_axis["series_title"]}: {series_value}"""
                        )

                    if (
                        f"{series_chart_column}_title" in chart_axis
                        and check_aggregation_phrases(
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})",
                        )
                    ):
                        scatterplot_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif "yAxis_aggregation" in chart_axis:
                        if chart_axis["yAxis_aggregation"] in ["SUM"]:
                            scatterplot_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
                            scatterplot_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                f"Average {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
                            scatterplot_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                f"Median {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis["yAxis_aggregation"] in ["MIN"]:
                            scatterplot_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                f"Minimum {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis["yAxis_aggregation"] in ["MAX"]:
                            scatterplot_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                f"Maximum {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        else:
                            scatterplot_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                    else:
                        scatterplot_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                "_",
                                " ",
                            )
                        )

                    if not (
                        isinstance(scatterplot_chart_json_dict[f"Y{yAxis_idx}"][0], int)
                        or isinstance(
                            scatterplot_chart_json_dict[f"Y{yAxis_idx}"][0],
                            float,
                        )
                    ):
                        code_level_logger.error(
                            f"scatterplot_chart: Y{yAxis_idx}-axis is not integer or float!",
                        )
                        raise RuntimeError(
                            f"scatterplot_chart: Y{yAxis_idx}-axis is not integer or float!",
                        )

                    # if (
                    #     check_negative_value(scatterplot_chart_json_dict[f"Y{yAxis_idx}"])
                    #     or scatterplot_chart_json_dict["Chart_Type"] == "column_chart"
                    # ):
                    #     return generate_group_column_chart_d3(
                    #         llama70b_client,
                    #         user_query,
                    #         chart_id,
                    #         sql_query,
                    #         chart_title,
                    #         chart_axis,
                    #         chart_data,
                    #         database_properties,
                    #         ups_idx,
                    #         chart_position,
                    #         overall_title,
                    #         client_id,
                    #         user_id,
                    #         sql_library,
                    #         logging_url,
                    #     )

                yAxis_idx += 1
    else:
        yAxis_idx = 1

        try:
            if len(chart_data[xAxis_column_name][0].split("-")) == 1:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
                )
            elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(
                        lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                    ),
                )
            elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(
                        lambda date: (
                            int(date.split("-")[0]),
                            int(date.split("-")[1]),
                            int(date.split("-")[2]),
                        ),
                    ),
                )
            else:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    ascending=True,
                )
        except Exception:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

        if isinstance(xAxis_column_name, str):
            chart_data = sort_pandas_date(chart_data, xAxis_column_name)

        for column_name in list(chart_data.columns):
            if not re.search(r"yAxis([23456789])?", column_name, re.IGNORECASE):
                continue

            if yAxis_idx <= 1:
                scatterplot_chart_json_dict["X"] = [
                    float(val) if isinstance(val, decimal.Decimal) else val
                    for val in chart_data[xAxis_column_name].values.tolist()
                ]

                scatterplot_chart_json_dict["Y"] = [
                    float(val) if isinstance(val, decimal.Decimal) else val
                    for val in chart_data[yAxis_column_name].values.tolist()
                ]

                if check_aggregation_phrases(chart_axis[f"{column_name}_title"]):
                    scatterplot_chart_json_dict["yName"] = chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")
                elif "yAxis_aggregation" in chart_axis:
                    if chart_axis["yAxis_aggregation"] in ["SUM"]:
                        scatterplot_chart_json_dict["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
                        scatterplot_chart_json_dict["yName"] = "Average " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
                        scatterplot_chart_json_dict["yName"] = "Median " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["MIN"]:
                        scatterplot_chart_json_dict["yName"] = "Minimum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["MAX"]:
                        scatterplot_chart_json_dict["yName"] = "Maximum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    else:
                        scatterplot_chart_json_dict["yName"] = chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                else:
                    scatterplot_chart_json_dict["yName"] = "Total " + chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")

                if not (
                    isinstance(scatterplot_chart_json_dict["Y"][0], int)
                    or isinstance(scatterplot_chart_json_dict["Y"][0], float)
                ):
                    code_level_logger.error(
                        "scatterplot_chart: Y-axis is not integer or float!",
                    )
                    raise RuntimeError(
                        "scatterplot_chart: Y-axis is not integer or float!",
                    )

                # if check_negative_value(scatterplot_chart_json_dict["Y"]):
                #     # scatterplot_chart_json_dict["Chart_Type"] = "column_chart"
                #     scatterplot_chart_json_dict["Chart_Type"] = "grouped_column_chart"
            else:
                scatterplot_chart_json_dict[f"X{yAxis_idx}"] = [
                    float(val) if isinstance(val, decimal.Decimal) else val
                    for val in chart_data[xAxis_column_name].values.tolist()
                ]

                scatterplot_chart_json_dict[f"Y{yAxis_idx}"] = [
                    float(val) if isinstance(val, decimal.Decimal) else val
                    for val in chart_data[column_name].values.tolist()
                ]

                if check_aggregation_phrases(chart_axis[f"{column_name}_title"]):
                    scatterplot_chart_json_dict[f"y{yAxis_idx}Name"] = chart_axis[
                        f"{column_name}_title"
                    ]
                elif f"{column_name}_aggregation" in chart_axis:
                    if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                        scatterplot_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Total "
                            + chart_axis[f"{column_name}_title"].replace("_", " ")
                        )
                    elif chart_axis[f"{column_name}_aggregation"] in ["AVG", "MEAN"]:
                        scatterplot_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Average "
                            + chart_axis[f"{column_name}_title"].replace("_", " ")
                        )
                    elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                        scatterplot_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Median "
                            + chart_axis[f"{column_name}_title"].replace("_", " ")
                        )
                    elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                        scatterplot_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Minimum "
                            + chart_axis[f"{column_name}_title"].replace("_", " ")
                        )
                    elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                        scatterplot_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Maximum "
                            + chart_axis[f"{column_name}_title"].replace("_", " ")
                        )
                    else:
                        scatterplot_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Total "
                            + chart_axis[f"{column_name}_title"].replace("_", " ")
                        )
                else:
                    scatterplot_chart_json_dict[f"y{yAxis_idx}Name"] = (
                        "Total " + chart_axis[f"{column_name}_title"].replace("_", " ")
                    )

                if not (
                    isinstance(scatterplot_chart_json_dict[f"Y{yAxis_idx}"][0], int)
                    or isinstance(
                        scatterplot_chart_json_dict[f"Y{yAxis_idx}"][0],
                        float,
                    )
                ):
                    code_level_logger.error(
                        f"scatterplot_chart: Y{yAxis_idx}-axis is not integer or float!",
                    )
                    raise RuntimeError(
                        f"scatterplot_chart: Y{yAxis_idx}-axis is not integer or float!",
                    )

                # if (
                #     check_negative_value(scatterplot_chart_json_dict[f"Y{yAxis_idx}"])
                #     or scatterplot_chart_json_dict["Chart_Type"] == "column_chart"
                # ):
                #     return generate_group_column_chart_d3(
                #         llama70b_client,
                #         user_query,
                #         chart_id,
                #         sql_query,
                #         chart_title,
                #         chart_axis,
                #         chart_data,
                #         database_properties,
                #         ups_idx,
                #         chart_position,
                #         overall_title,
                #         client_id,
                #         user_id,
                #         sql_library,
                #         logging_url,
                #     )

            yAxis_idx += 1

    if scatterplot_chart_json_dict["Y"] == []:
        code_level_logger.error("scatterplot_chart: Y-Axis is not found in extraction!")
        raise RuntimeError("scatterplot_chart: Y-Axis is not found in extraction!")

    if any(
        scatterplot_chart_json_dict[key] == []
        or scatterplot_chart_json_dict[key] == [""]
        for key in scatterplot_chart_json_dict
        if re.match(r"^X\d*$", key)
    ):
        code_level_logger.error(
            "scatterplot_chart: One or more X-axis values are empty!"
        )
        raise RuntimeError("scatterplot_chart: One or more X-axis values are empty!")

    chart_data_lists = []

    # Check for the main Y and its corresponding X
    if "Y" in scatterplot_chart_json_dict:
        x_values = scatterplot_chart_json_dict["X"]
        main_group_name = scatterplot_chart_json_dict.get("yName", "Series 1")

        for i in range(len(x_values)):
            x_value = float(x_values[i])
            main_y_value = scatterplot_chart_json_dict["Y"][i]
            chart_data_lists.append(
                {
                    "X_Value": x_value,
                    "Y_Value": main_y_value,
                    "Group_Name": main_group_name,
                },
            )

    # Check for additional Y values (Y2, Y3, ...)
    j = 2
    while f"Y{j}" in scatterplot_chart_json_dict:
        # Corresponding X values for Y2, Y3, etc.
        x_key = f"X{j}"
        if x_key in scatterplot_chart_json_dict:
            x_values = scatterplot_chart_json_dict[x_key]
            group_name_key = f"y{j}Name"
            group_name = scatterplot_chart_json_dict.get(group_name_key, f"Series {j}")

            for i in range(len(x_values)):
                x_value = float(x_values[i])
                y_key = f"Y{j}"
                if y_key in scatterplot_chart_json_dict:
                    additional_y_value = scatterplot_chart_json_dict[y_key][i]
                    chart_data_lists.append(
                        {
                            "X_Value": x_value,
                            "Y_Value": additional_y_value,
                            "Group_Name": group_name,
                        },
                    )

        j += 1

    # Store chart data in the original dict
    scatterplot_chart_json_dict["Chart_Data"] = chart_data_lists

    scatterplot_chart_json_dict["Database_Identifier"] = database_properties["db_tag"]

    scatterplot_chart_json_dict["Client_ID"] = client_id
    scatterplot_chart_json_dict["User_ID"] = user_id
    scatterplot_chart_json_dict["Session_ID"] = session_id

    if (
        len(scatterplot_chart_json_dict["Y"]) == 1
        and scatterplot_chart_json_dict["Y2"] == []
    ):
        return generate_card_chart_d3(
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            scatterplot_chart_json_dict["Chart_Type"],
            logging_url,
            code_level_logger,
        )

    keys_to_remove = ["X", "Y", "yName"]

    i = 2
    while f"y{i}Name" in scatterplot_chart_json_dict:
        keys_to_remove.append(f"y{i}Name")
        i += 1

    j = 2
    while f"X{j}" and f"Y{j}" in scatterplot_chart_json_dict:
        keys_to_remove.append(f"X{j}")
        keys_to_remove.append(f"Y{j}")
        j += 1

    # Remove all specified keys ['X', 'Y', 'yName'] and etc. from the dictionary
    for key in keys_to_remove:
        if key in scatterplot_chart_json_dict:
            del scatterplot_chart_json_dict[key]

    return scatterplot_chart_json_dict


def generate_spline_chart_d3(
    llama70b_client: Any,
    user_query: str,
    chart_id: str,
    sql_query: str,
    chart_title: str,
    chart_axis: dict,
    chart_data: pd.DataFrame,
    database_properties: dict,
    ups_idx: int,
    chart_position: int,
    overall_title: str,
    client_id: str,
    user_id: str,
    session_id: str,
    sql_library: str,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    spline_chart_json_dict: dict = SPLINE_CHART_TEMPLATE_D3.copy()
    spline_chart_json_dict["User_Query"] = user_query
    spline_chart_json_dict["Chart_Query"] = sql_query
    spline_chart_json_dict["Chart_Name"] = f"Visual {ups_idx}"
    spline_chart_json_dict["Chart_Axis"] = chart_axis
    spline_chart_json_dict["Chart_SQL_Library"] = sql_library
    spline_chart_json_dict["Visual_Title"] = overall_title
    spline_chart_json_dict["Chart_ID"] = chart_id
    spline_chart_json_dict["Chart_Type"] = "line_chart"
    spline_chart_json_dict["Chart_Position"] = str(chart_position)
    spline_chart_json_dict["Chart_Title"] = chart_title

    spline_chart_json_dict["xAxis"] = chart_axis["xAxis_title"].replace("_", " ")
    spline_chart_json_dict["Aggregated_Table_JSON"] = (
        generate_aggregated_table_chart_d3(
            user_query,
            sql_query,
            chart_id,
            chart_title,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            chart_axis,
            spline_chart_json_dict["Chart_Type"],
            code_level_logger,
        )
    )
    spline_chart_json_dict["Aggregated_Table_Column"] = get_aggregated_columns(
        chart_axis,
    )

    yAxis_title = ""

    for chart_axis_key in chart_axis:
        if (
            chart_axis_key.lower()[0] != "y"
            or "title" not in chart_axis_key.lower()
            or chart_axis[chart_axis_key] == ""
        ):
            continue
        if yAxis_title == "":
            yAxis_title += chart_axis[chart_axis_key]
        else:
            # yAxis_title += f"/{chart_axis[chart_axis_key]}"
            yAxis_title = "Amount"
            break

    if (
        check_aggregation_phrases(yAxis_title.replace("_", " "))
        or yAxis_title == "Amount"
    ):
        spline_chart_json_dict["yAxis"] = yAxis_title.replace("_", " ")
    elif "yAxis_aggregation" in chart_axis:
        if chart_axis["yAxis_aggregation"] in ["SUM"]:
            spline_chart_json_dict["yAxis"] = "Total " + yAxis_title.replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
            spline_chart_json_dict["yAxis"] = "Average " + yAxis_title.replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
            spline_chart_json_dict["yAxis"] = "Median " + yAxis_title.replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["MIN"]:
            spline_chart_json_dict["yAxis"] = "Minimum " + yAxis_title.replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["MAX"]:
            spline_chart_json_dict["yAxis"] = "Maximum " + yAxis_title.replace(
                "_",
                " ",
            )
        else:
            spline_chart_json_dict["yAxis"] = "Total " + yAxis_title.replace(
                "_",
                " ",
            )
    else:
        spline_chart_json_dict["yAxis"] = "Total " + yAxis_title.replace("_", " ")

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
        code_level_logger.error("line_chart: X-Axis is not found in extraction!")
        raise RuntimeError("line_chart: X-Axis is not found in extraction!")

    if "series" in chart_data_columns:
        series_column_name = "series"
    elif (
        "series_column" in chart_axis
        and isinstance(chart_axis["series_column"], str)
        and chart_axis["series_column"] in chart_data_columns
    ):
        series_column_name = chart_axis["series_column"]
    else:
        series_column_name = ""

    object_columns = chart_data.select_dtypes(include=[object])

    yAxis_column_names = list(chart_data.columns)
    yAxis_column_names.remove(xAxis_column_name)
    if series_column_name in yAxis_column_names:
        yAxis_column_names.remove(series_column_name)

    for yAxis_column_name in yAxis_column_names:
        if yAxis_column_name in object_columns:
            try:
                if not isinstance(
                    chart_data[yAxis_column_name].values.tolist()[0],
                    datetime.date,
                ) and not isinstance(
                    chart_data[yAxis_column_name].values.tolist()[0],
                    datetime.datetime,
                ):
                    if isinstance(
                        chart_data[yAxis_column_name].values.tolist()[0],
                        str,
                    ):
                        chart_data[yAxis_column_name] = chart_data[
                            yAxis_column_name
                        ].replace("%", "", regex=True)
                    chart_data[yAxis_column_name] = pd.to_numeric(
                        chart_data[yAxis_column_name],
                    )
            except Exception:
                code_level_logger.error(
                    f"line_chart: {yAxis_column_name} is not numerical!"
                )
                raise RuntimeError(f"line_chart: {yAxis_column_name} is not numerical!")

    if (
        series_column_name != ""
        and series_column_name in chart_data.columns
        and chart_data[series_column_name].nunique() > 1
    ):
        new_chart_data = pd.DataFrame()

        pivot_data = chart_data.pivot_table(
            index=xAxis_column_name,
            columns=series_column_name,
            values=yAxis_column_names,
        )
        pivot_data = pivot_data.reset_index()
        new_chart_data[xAxis_column_name] = [
            float(val) if isinstance(val, decimal.Decimal) else val
            for val in pivot_data[xAxis_column_name].values.tolist()
        ]

        for yAxis_column_name in yAxis_column_names:
            yAxis_pivot_table = pivot_data[yAxis_column_name]
            for yAxis_pivot_column in list(yAxis_pivot_table.columns):
                new_columns = {
                    f"{yAxis_column_name}_{yAxis_pivot_column}": [
                        float(val) if isinstance(val, decimal.Decimal) else val
                        for val in yAxis_pivot_table[yAxis_pivot_column].values.tolist()
                    ],
                }
                added_chart_data = pd.DataFrame(new_columns)
                new_chart_data = pd.concat([new_chart_data, added_chart_data], axis=1)

        chart_data = new_chart_data.fillna(
            {
                col: (
                    0 if new_chart_data[col].dtype in [np.float64, np.int64] else "null"
                )
                for col in new_chart_data.columns
            },
        )

    if (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{4}-\d{2}-\d{2}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%Y-%m-%d",
        )
    elif (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{2}/\d{2}/\d{4}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%d/%m/%Y",
        )

    if all(
        isinstance(val, (datetime.date, datetime.datetime))
        for val in chart_data[xAxis_column_name]
    ):
        chart_data, new_chart_axis, new_chart_title = adjust_axis_title_and_data(
            llama70b_client,
            chart_id,
            chart_data,
            chart_axis,
            chart_title,
            logging_url,
        )
        spline_chart_json_dict["xAxis"] = new_chart_axis["xAxis_title"].replace(
            "_",
            " ",
        )
        spline_chart_json_dict["Chart_Title"] = new_chart_title

    try:
        if len(chart_data[xAxis_column_name][0].split("-")) == 1:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                ),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (
                        int(date.split("-")[0]),
                        int(date.split("-")[1]),
                        int(date.split("-")[2]),
                    ),
                ),
            )
        else:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)
    except Exception:
        chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

    if isinstance(xAxis_column_name, str):
        chart_data = sort_pandas_date(chart_data, xAxis_column_name)

    spline_chart_json_dict["X"] = [
        str(x_data) for x_data in chart_data[xAxis_column_name].values.tolist()
    ]

    if len(spline_chart_json_dict["X"]) >= 1 and len(spline_chart_json_dict["X"]) <= 2:
        return generate_group_bar_chart_d3(
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            logging_url,
            code_level_logger,
        )

    yAxis_idx = 1

    for column_name in list(chart_data.columns):
        if not re.search(r"yAxis([23456789])?", column_name, re.IGNORECASE):
            continue

        if yAxis_idx <= 1:
            spline_chart_json_dict["Y"] = [
                float(val) if isinstance(val, decimal.Decimal) else val
                for val in chart_data[column_name].values.tolist()
            ]

            underscore_index = column_name.find("_")

            # No Series
            if underscore_index == -1:
                if check_aggregation_phrases(
                    chart_axis[f"{column_name}_title"].replace("_", " "),
                ):
                    spline_chart_json_dict["yName"] = chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")
                elif f"{column_name}_aggregation" in chart_axis:
                    if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                        spline_chart_json_dict["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["AVG", "MEAN"]:
                        spline_chart_json_dict["yName"] = "Average " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                        spline_chart_json_dict["yName"] = "Median " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                        spline_chart_json_dict["yName"] = "Minimum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                        spline_chart_json_dict["yName"] = "Maximum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    else:
                        spline_chart_json_dict["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                else:
                    spline_chart_json_dict["yName"] = "Total " + chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")
            # Has Series
            else:
                original_column_name = column_name[:underscore_index]
                series_name = column_name[underscore_index + 1 :]

                # Add Series Title to Series Name
                if "series_title" in chart_axis and chart_axis["series_title"] != "":
                    series_name = f"""{chart_axis["series_title"]}: {series_name}"""

                if (
                    f"{original_column_name}_title" in chart_axis
                    and check_aggregation_phrases(
                        f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        ),
                    )
                ):
                    spline_chart_json_dict["yName"] = (
                        f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        )
                    )
                elif f"{original_column_name}_aggregation" in chart_axis:
                    if chart_axis[f"{original_column_name}_aggregation"] in ["SUM"]:
                        spline_chart_json_dict["yName"] = (
                            "Total "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in [
                        "AVG",
                        "MEAN",
                    ]:
                        spline_chart_json_dict["yName"] = (
                            "Average "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in [
                        "MEDIAN",
                    ]:
                        spline_chart_json_dict["yName"] = (
                            "Median "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in ["MIN"]:
                        spline_chart_json_dict["yName"] = (
                            "Minimum "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in ["MAX"]:
                        spline_chart_json_dict["yName"] = (
                            "Maximum "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    else:
                        spline_chart_json_dict["yName"] = (
                            "Total "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                else:
                    spline_chart_json_dict["yName"] = (
                        "Total "
                        + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        )
                    )

            if not (
                isinstance(spline_chart_json_dict["Y"][0], int)
                or isinstance(spline_chart_json_dict["Y"][0], float)
            ):
                code_level_logger.error("spline_chart: Y-axis is not integer or float!")
                raise RuntimeError("spline_chart: Y-axis is not integer or float!")

            # if check_negative_value(spline_chart_json_dict["Y"]):
            #     # spline_chart_json_dict["Chart_Type"] = "column_chart"
            #     spline_chart_json_dict["Chart_Type"] = "grouped_column_chart"
        else:
            spline_chart_json_dict[f"Y{yAxis_idx}"] = [
                float(val) if isinstance(val, decimal.Decimal) else val
                for val in chart_data[column_name].values.tolist()
            ]

            underscore_index = column_name.find("_")

            # No Series
            if underscore_index == -1:
                spline_chart_json_dict[f"y{yAxis_idx}Name"] = chart_axis[
                    f"{column_name}_title"
                ].replace("_", " ")
                if spline_chart_json_dict[f"y{yAxis_idx}Name"] == "":
                    spline_chart_json_dict[f"y{yAxis_idx}Name"] = (
                        spline_chart_json_dict["yName"].replace("_", " ")
                    )

                if not check_aggregation_phrases(
                    spline_chart_json_dict[f"y{yAxis_idx}Name"],
                ):
                    if f"{column_name}_aggregation" in chart_axis:
                        if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                            spline_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Total " + spline_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            spline_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Average " + spline_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                            spline_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Median " + spline_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                            spline_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Minimum " + spline_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                            spline_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Maximum " + spline_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        else:
                            spline_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Total " + spline_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                    else:
                        spline_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Total " + spline_chart_json_dict[f"y{yAxis_idx}Name"]
                        )
            # Has Series
            else:
                original_column_name = column_name[:underscore_index]
                series_name = column_name[underscore_index + 1 :]

                # Add Series Title to Series Name
                if "series_title" in chart_axis and chart_axis["series_title"] != "":
                    series_name = f"""{chart_axis["series_title"]}: {series_name}"""

                spline_chart_json_dict[f"y{yAxis_idx}Name"] = (
                    f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                        "_",
                        " ",
                    )
                )
                if spline_chart_json_dict[f"y{yAxis_idx}Name"] == "":
                    spline_chart_json_dict[f"y{yAxis_idx}Name"] = (
                        spline_chart_json_dict["yName"].replace("_", " ")
                    )

                if not check_aggregation_phrases(
                    spline_chart_json_dict[f"y{yAxis_idx}Name"],
                ):
                    if f"{original_column_name}_aggregation" in chart_axis:
                        if chart_axis[f"{original_column_name}_aggregation"] in ["SUM"]:
                            spline_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Total " + spline_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            spline_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Average " + spline_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MEDIAN",
                        ]:
                            spline_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Median " + spline_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MIN",
                        ]:
                            spline_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Minimum " + spline_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MAX",
                        ]:
                            spline_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Maximum " + spline_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        else:
                            spline_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Total " + spline_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                    else:
                        spline_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Total " + spline_chart_json_dict[f"y{yAxis_idx}Name"]
                        )

            # if spline_chart_json_dict["Chart_Type"] == "line_chart":
            #     spline_chart_json_dict["Chart_Type"] = "stackedline_chart"

            if not (
                isinstance(spline_chart_json_dict[f"Y{yAxis_idx}"][0], int)
                or isinstance(spline_chart_json_dict[f"Y{yAxis_idx}"][0], float)
            ):
                code_level_logger.error(
                    f"spline_chart: Y{yAxis_idx}-axis is not integer or float!",
                )
                raise RuntimeError(
                    f"spline_chart: Y{yAxis_idx}-axis is not integer or float!",
                )

            # if (
            #     check_negative_value(spline_chart_json_dict[f"Y{yAxis_idx}"])
            #     or spline_chart_json_dict["Chart_Type"] == "column_chart"
            # ):
            #     spline_chart_json_dict["Chart_Type"] = "grouped_column_chart"

        yAxis_idx += 1

    if any(
        spline_chart_json_dict[key] == [] or spline_chart_json_dict[key] == [""]
        for key in spline_chart_json_dict
        if re.match(r"^X\d*$", key)
    ):
        code_level_logger.error("spline_chart: One or more X-axis values are empty!")
        raise RuntimeError("spline_chart: One or more X-axis values are empty!")

    if len(spline_chart_json_dict["Y"]) == 1 and spline_chart_json_dict["Y2"] == []:
        return generate_card_chart_d3(
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            spline_chart_json_dict["Chart_Type"],
            logging_url,
            code_level_logger,
        )

    chart_data_lists = []

    x_values = spline_chart_json_dict["X"]

    if "Y" in spline_chart_json_dict:
        main_y_data = []
        for i in range(len(x_values)):
            x_value = x_values[i]
            main_y_value = spline_chart_json_dict["Y"][i]
            main_group_name = spline_chart_json_dict.get("yName", "Series 1")
            main_y_data.append(
                {
                    "X_Value": x_value,
                    "Y_Value": main_y_value,
                    "Group_Name": main_group_name,
                },
            )
        chart_data_lists.append(main_y_data)

    j = 2
    while f"Y{j}" in spline_chart_json_dict:
        additional_y_data = []

        for i in range(len(x_values)):
            x_value = x_values[i]

            y_key = f"Y{j}"
            if y_key in spline_chart_json_dict:
                additional_y_value = spline_chart_json_dict[y_key][i]
                group_name_key = f"y{j}Name"
                group_name = spline_chart_json_dict.get(group_name_key, f"Series {j}")
                additional_y_data.append(
                    {
                        "X_Value": x_value,
                        "Y_Value": additional_y_value,
                        "Group_Name": group_name,
                    },
                )

        if additional_y_data:
            chart_data_lists.append(additional_y_data)

        j += 1

    spline_chart_json_dict["Chart_Data"] = chart_data_lists

    spline_chart_json_dict["Database_Identifier"] = database_properties["db_tag"]

    spline_chart_json_dict["Client_ID"] = client_id
    spline_chart_json_dict["User_ID"] = user_id
    spline_chart_json_dict["Session_ID"] = session_id

    return spline_chart_json_dict


def generate_bar_chart_d3(
    llama70b_client: Any,
    user_query: str,
    chart_id: str,
    sql_query: str,
    chart_title: str,
    chart_axis: dict,
    chart_data: pd.DataFrame,
    database_properties: dict,
    ups_idx: int,
    chart_position: int,
    overall_title: str,
    client_id: str,
    user_id: str,
    session_id: str,
    sql_library: str,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    bar_chart_json_dict: dict = BAR_CHART_TEMPLATE_D3.copy()
    bar_chart_json_dict["User_Query"] = user_query
    bar_chart_json_dict["Chart_Query"] = sql_query
    bar_chart_json_dict["Chart_SQL_Library"] = sql_library
    bar_chart_json_dict["Chart_Name"] = f"Visual {ups_idx}"
    bar_chart_json_dict["Chart_Axis"] = chart_axis
    bar_chart_json_dict["Visual_Title"] = overall_title
    bar_chart_json_dict["Chart_ID"] = chart_id
    bar_chart_json_dict["Chart_Type"] = "bar_chart"
    bar_chart_json_dict["Chart_Position"] = str(chart_position)
    bar_chart_json_dict["Chart_Title"] = chart_title
    bar_chart_json_dict["xAxis"] = chart_axis["xAxis_title"].replace("_", " ")
    if check_aggregation_phrases(chart_axis["yAxis_title"].replace("_", " ")):
        bar_chart_json_dict["yAxis"] = chart_axis["yAxis_title"].replace("_", " ")
        bar_chart_json_dict["yName"] = chart_axis["yAxis_title"].replace("_", " ")
    elif "yAxis_aggregation" in chart_axis:
        if chart_axis["yAxis_aggregation"] in ["SUM"]:
            bar_chart_json_dict["yAxis"] = "Total " + chart_axis["yAxis_title"].replace(
                "_",
                " ",
            )
            bar_chart_json_dict["yName"] = "Total " + chart_axis["yAxis_title"].replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
            bar_chart_json_dict["yAxis"] = "Average " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            bar_chart_json_dict["yName"] = "Average " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
            bar_chart_json_dict["yAxis"] = "Median " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            bar_chart_json_dict["yName"] = "Median " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["MIN"]:
            bar_chart_json_dict["yAxis"] = "Minimum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            bar_chart_json_dict["yName"] = "Minimum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["MAX"]:
            bar_chart_json_dict["yAxis"] = "Maximum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            bar_chart_json_dict["yName"] = "Maximum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        else:
            bar_chart_json_dict["yAxis"] = "Total " + chart_axis["yAxis_title"].replace(
                "_",
                " ",
            )
            bar_chart_json_dict["yName"] = "Total " + chart_axis["yAxis_title"].replace(
                "_",
                " ",
            )
    else:
        bar_chart_json_dict["yAxis"] = "Total " + chart_axis["yAxis_title"].replace(
            "_",
            " ",
        )
        bar_chart_json_dict["yName"] = "Total " + chart_axis["yAxis_title"].replace(
            "_",
            " ",
        )
    bar_chart_json_dict["Aggregated_Table_JSON"] = generate_aggregated_table_chart_d3(
        user_query,
        sql_query,
        chart_id,
        chart_title,
        chart_data,
        database_properties,
        ups_idx,
        chart_position,
        overall_title,
        client_id,
        user_id,
        session_id,
        sql_library,
        chart_axis,
        bar_chart_json_dict["Chart_Type"],
        code_level_logger,
    )
    bar_chart_json_dict["Aggregated_Table_Column"] = get_aggregated_columns(chart_axis)
    bar_chart_json_dict["Database_Identifier"] = database_properties["db_tag"]

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
        code_level_logger.error("bar_chart: X-Axis is not found in extraction!")
        raise RuntimeError("bar_chart: X-Axis is not found in extraction!")

    if "yAxis" in chart_data_columns:
        yAxis_column_name = "yAxis"
    elif (
        "yAxis_column" in chart_axis
        and isinstance(chart_axis["yAxis_column"], str)
        and chart_axis["yAxis_column"] in chart_data_columns
    ):
        yAxis_column_name = chart_axis["yAxis_column"]
    else:
        code_level_logger.error("bar_chart: Y-Axis is not found in extraction!")
        raise RuntimeError("bar_chart: Y-Axis is not found in extraction!")

    object_columns = chart_data.select_dtypes(include=[object])

    if yAxis_column_name in object_columns:
        try:
            if not isinstance(
                chart_data[yAxis_column_name].values.tolist()[0],
                datetime.date,
            ) and not isinstance(
                chart_data[yAxis_column_name].values.tolist()[0],
                datetime.datetime,
            ):
                if isinstance(chart_data[yAxis_column_name].values.tolist()[0], str):
                    chart_data[yAxis_column_name] = chart_data[
                        yAxis_column_name
                    ].replace("%", "", regex=True)
                chart_data[yAxis_column_name] = pd.to_numeric(
                    chart_data[yAxis_column_name],
                )
        except Exception:
            code_level_logger.error(f"bar_chart: {yAxis_column_name} is not numerical!")
            raise RuntimeError(f"bar_chart: {yAxis_column_name} is not numerical!")

    y_values = chart_data[yAxis_column_name].values.tolist()

    if (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{4}-\d{2}-\d{2}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%Y-%m-%d",
        )
    elif (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{2}/\d{2}/\d{4}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%d/%m/%Y",
        )

    if all(
        isinstance(val, (datetime.date, datetime.datetime))
        for val in chart_data[xAxis_column_name]
    ):
        chart_data, new_chart_axis, new_chart_title = adjust_axis_title_and_data(
            llama70b_client,
            chart_id,
            chart_data,
            chart_axis,
            chart_title,
            logging_url,
        )
        bar_chart_json_dict["xAxis"] = new_chart_axis["xAxis_title"].replace("_", " ")
        bar_chart_json_dict["Chart_Title"] = new_chart_title

    try:
        if len(chart_data[xAxis_column_name][0].split("-")) == 1:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                ),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (
                        int(date.split("-")[0]),
                        int(date.split("-")[1]),
                        int(date.split("-")[2]),
                    ),
                ),
            )
        else:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)
    except Exception:
        chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

    if isinstance(xAxis_column_name, str):
        chart_data = sort_pandas_date(chart_data, xAxis_column_name)

    bar_chart_json_dict["X"] = [
        str(x_data) for x_data in chart_data[xAxis_column_name].values.tolist()
    ]
    bar_chart_json_dict["Y"] = [
        float(val) if isinstance(val, decimal.Decimal) else val for val in y_values
    ]

    if not (
        isinstance(bar_chart_json_dict["Y"][0], int)
        or isinstance(bar_chart_json_dict["Y"][0], float)
    ):
        code_level_logger.error("bar_chart: Y-axis is not integer or float!")
        raise RuntimeError("bar_chart: Y-axis is not integer or float!")

    if isinstance(bar_chart_json_dict["xAxis"], list):
        bar_chart_json_dict["xAxis"] = " ".join(bar_chart_json_dict["xAxis"])

    if isinstance(bar_chart_json_dict["yAxis"], list):
        bar_chart_json_dict["yAxis"] = " ".join(bar_chart_json_dict["yAxis"])

    # if check_negative_value(bar_chart_json_dict["Y"]):
    #     # bar_chart_json_dict["Chart_Type"] = "column_chart"
    #     bar_chart_json_dict["Chart_Type"] = "grouped_column_chart"

    if any(
        bar_chart_json_dict[key] == [] or bar_chart_json_dict[key] == [""]
        for key in bar_chart_json_dict
        if re.match(r"^X\d*$", key)
    ):
        code_level_logger.error("bar_chart: One or more X-axis values are empty!")
        raise RuntimeError("bar_chart: One or more X-axis values are empty!")

    bar_chart_json_dict["Client_ID"] = client_id
    bar_chart_json_dict["User_ID"] = user_id
    bar_chart_json_dict["Session_ID"] = session_id

    if len(y_values) <= 1:
        card_chart_json_dict: dict = generate_card_chart_d3(
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            bar_chart_json_dict["Chart_Type"],
            logging_url,
            code_level_logger,
        )
        return card_chart_json_dict

    return bar_chart_json_dict


def generate_column_chart_d3(
    llama70b_client: Any,
    user_query: str,
    chart_id: str,
    sql_query: str,
    chart_title: str,
    chart_axis: dict,
    chart_data: pd.DataFrame,
    database_properties: dict,
    ups_idx: int,
    chart_position: int,
    overall_title: str,
    client_id: str,
    user_id: str,
    session_id: str,
    sql_library: str,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    column_chart_json_dict: dict = COLUMN_CHART_TEMPLATE_D3.copy()
    column_chart_json_dict["User_Query"] = user_query
    column_chart_json_dict["Chart_Query"] = sql_query
    column_chart_json_dict["Chart_SQL_Library"] = sql_library
    column_chart_json_dict["Chart_Name"] = f"Visual {ups_idx}"
    column_chart_json_dict["Chart_Axis"] = chart_axis
    column_chart_json_dict["Visual_Title"] = overall_title
    column_chart_json_dict["Chart_ID"] = chart_id
    column_chart_json_dict["Chart_Type"] = "column_chart"
    column_chart_json_dict["Chart_Position"] = str(chart_position)
    column_chart_json_dict["Chart_Title"] = chart_title
    column_chart_json_dict["xAxis"] = chart_axis["xAxis_title"].replace("_", " ")
    if check_aggregation_phrases(chart_axis["yAxis_title"].replace("_", " ")):
        column_chart_json_dict["yAxis"] = chart_axis["yAxis_title"].replace("_", " ")
        column_chart_json_dict["yName"] = chart_axis["yAxis_title"].replace("_", " ")
    elif "yAxis_aggregation" in chart_axis:
        if chart_axis["yAxis_aggregation"] in ["SUM"]:
            column_chart_json_dict["yAxis"] = "Total " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            column_chart_json_dict["yName"] = "Total " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
            column_chart_json_dict["yAxis"] = "Average " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            column_chart_json_dict["yName"] = "Average " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
            column_chart_json_dict["yAxis"] = "Median " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            column_chart_json_dict["yName"] = "Median " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["MIN"]:
            column_chart_json_dict["yAxis"] = "Minimum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            column_chart_json_dict["yName"] = "Minimum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["MAX"]:
            column_chart_json_dict["yAxis"] = "Maximum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            column_chart_json_dict["yName"] = "Maximum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        else:
            column_chart_json_dict["yAxis"] = "Total " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            column_chart_json_dict["yName"] = "Total " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
    else:
        column_chart_json_dict["yAxis"] = "Total " + chart_axis["yAxis_title"].replace(
            "_",
            " ",
        )
        column_chart_json_dict["yName"] = "Total " + chart_axis["yAxis_title"].replace(
            "_",
            " ",
        )

    column_chart_json_dict["Aggregated_Table_JSON"] = (
        generate_aggregated_table_chart_d3(
            user_query,
            sql_query,
            chart_id,
            chart_title,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            chart_axis,
            column_chart_json_dict["Chart_Type"],
            code_level_logger,
        )
    )
    column_chart_json_dict["Aggregated_Table_Column"] = get_aggregated_columns(
        chart_axis,
    )
    column_chart_json_dict["Database_Identifier"] = database_properties["db_tag"]

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
        code_level_logger.error("column_chart: X-Axis is not found in extraction!")
        raise RuntimeError("column_chart: X-Axis is not found in extraction!")

    if "yAxis" in chart_data_columns:
        yAxis_column_name = "yAxis"
    elif (
        "yAxis_column" in chart_axis
        and isinstance(chart_axis["yAxis_column"], str)
        and chart_axis["yAxis_column"] in chart_data_columns
    ):
        yAxis_column_name = chart_axis["yAxis_column"]
    else:
        code_level_logger.error("column_chart: Y-Axis is not found in extraction!")
        raise RuntimeError("column_chart: Y-Axis is not found in extraction!")

    object_columns = chart_data.select_dtypes(include=[object])

    if yAxis_column_name in object_columns:
        try:
            if not isinstance(
                chart_data[yAxis_column_name].values.tolist()[0],
                datetime.date,
            ) and not isinstance(
                chart_data[yAxis_column_name].values.tolist()[0],
                datetime.datetime,
            ):
                if isinstance(chart_data[yAxis_column_name].values.tolist()[0], str):
                    chart_data[yAxis_column_name] = chart_data[
                        yAxis_column_name
                    ].replace("%", "", regex=True)
                chart_data[yAxis_column_name] = pd.to_numeric(
                    chart_data[yAxis_column_name],
                )
        except Exception:
            code_level_logger.error(
                f"column_chart: Y-axis {yAxis_column_name} is not numerical!",
            )
            raise RuntimeError(
                f"column_chart: Y-axis {yAxis_column_name} is not numerical!",
            )

    y_values = chart_data[yAxis_column_name].values.tolist()

    if (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{4}-\d{2}-\d{2}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%Y-%m-%d",
        )
    elif (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{2}/\d{2}/\d{4}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%d/%m/%Y",
        )

    if all(
        isinstance(val, (datetime.date, datetime.datetime))
        for val in chart_data[xAxis_column_name]
    ):
        chart_data, new_chart_axis, new_chart_title = adjust_axis_title_and_data(
            llama70b_client,
            chart_id,
            chart_data,
            chart_axis,
            chart_title,
            logging_url,
        )
        column_chart_json_dict["xAxis"] = new_chart_axis["xAxis_title"].replace(
            "_",
            " ",
        )
        column_chart_json_dict["Chart_Title"] = new_chart_title

    try:
        if len(chart_data[xAxis_column_name][0].split("-")) == 1:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                ),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (
                        int(date.split("-")[0]),
                        int(date.split("-")[1]),
                        int(date.split("-")[2]),
                    ),
                ),
            )
        else:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)
    except Exception:
        chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

    if isinstance(xAxis_column_name, str):
        chart_data = sort_pandas_date(chart_data, xAxis_column_name)

    column_chart_json_dict["X"] = [
        str(x_data) for x_data in chart_data[xAxis_column_name].values.tolist()
    ]
    column_chart_json_dict["Y"] = [
        float(val) if isinstance(val, decimal.Decimal) else val for val in y_values
    ]

    if not (
        isinstance(column_chart_json_dict["Y"][0], int)
        or isinstance(column_chart_json_dict["Y"][0], float)
    ):
        code_level_logger.error("column_chart: Y-axis is not integer or float!")
        raise RuntimeError("column_chart: Y-axis is not integer or float!")

    if isinstance(column_chart_json_dict["xAxis"], list):
        column_chart_json_dict["xAxis"] = " ".join(column_chart_json_dict["xAxis"])

    if isinstance(column_chart_json_dict["yAxis"], list):
        column_chart_json_dict["yAxis"] = " ".join(column_chart_json_dict["yAxis"])

    if any(
        column_chart_json_dict[key] == [] or column_chart_json_dict[key] == [""]
        for key in column_chart_json_dict
        if re.match(r"^X\d*$", key)
    ):
        code_level_logger.error("column_chart: One or more X-axis values are empty!")
        raise RuntimeError("column_chart: One or more X-axis values are empty!")

    column_chart_json_dict["Client_ID"] = client_id
    column_chart_json_dict["User_ID"] = user_id
    column_chart_json_dict["Session_ID"] = session_id

    if len(y_values) == 1:
        card_chart_json_dict: dict = generate_card_chart_d3(
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            column_chart_json_dict["Chart_Type"],
            logging_url,
            code_level_logger,
        )
        return card_chart_json_dict

    return column_chart_json_dict


def generate_group_column_chart_d3(
    llama70b_client: Any,
    user_query: str,
    chart_id: str,
    sql_query: str,
    chart_title: str,
    chart_axis: dict,
    chart_data: pd.DataFrame,
    database_properties: dict,
    ups_idx: int,
    chart_position: int,
    overall_title: str,
    client_id: str,
    user_id: str,
    session_id: str,
    sql_library: str,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    grouped_column_chart_json_dict: dict = GROUPED_COLUMN_CHART_TEMPLATE_D3.copy()
    grouped_column_chart_json_dict["User_Query"] = user_query
    grouped_column_chart_json_dict["Chart_Query"] = sql_query
    grouped_column_chart_json_dict["Chart_SQL_Library"] = sql_library
    grouped_column_chart_json_dict["Chart_Name"] = f"Visual {ups_idx}"
    grouped_column_chart_json_dict["Chart_Axis"] = chart_axis
    grouped_column_chart_json_dict["Visual_Title"] = overall_title
    grouped_column_chart_json_dict["Chart_ID"] = chart_id
    grouped_column_chart_json_dict["Chart_Type"] = "grouped_column_chart"
    grouped_column_chart_json_dict["Chart_Position"] = str(chart_position)
    grouped_column_chart_json_dict["Chart_Title"] = chart_title

    grouped_column_chart_json_dict["xAxis"] = chart_axis["xAxis_title"].replace(
        "_",
        " ",
    )
    grouped_column_chart_json_dict["Aggregated_Table_JSON"] = (
        generate_aggregated_table_chart_d3(
            user_query,
            sql_query,
            chart_id,
            chart_title,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            chart_axis,
            grouped_column_chart_json_dict["Chart_Type"],
            code_level_logger,
        )
    )
    grouped_column_chart_json_dict["Aggregated_Table_Column"] = get_aggregated_columns(
        chart_axis,
    )

    yAxis_title = ""

    for chart_axis_key in chart_axis:
        if (
            chart_axis_key.lower()[0] != "y"
            or "title" not in chart_axis_key.lower()
            or chart_axis[chart_axis_key] == ""
        ):
            continue
        if yAxis_title == "":
            yAxis_title += chart_axis[chart_axis_key]
        else:
            # yAxis_title += f"/{chart_axis[chart_axis_key]}"
            yAxis_title = "Amount"
            break

    if (
        check_aggregation_phrases(yAxis_title.replace("_", " "))
        or yAxis_title == "Amount"
    ):
        grouped_column_chart_json_dict["yAxis"] = yAxis_title.replace("_", " ")
    elif "yAxis_aggregation" in chart_axis:
        if chart_axis["yAxis_aggregation"] in ["SUM"]:
            grouped_column_chart_json_dict["yAxis"] = "Total " + yAxis_title.replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
            grouped_column_chart_json_dict["yAxis"] = "Average " + yAxis_title.replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
            grouped_column_chart_json_dict["yAxis"] = "Median " + yAxis_title.replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["MIN"]:
            grouped_column_chart_json_dict["yAxis"] = "Minimum " + yAxis_title.replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["MAX"]:
            grouped_column_chart_json_dict["yAxis"] = "Maximum " + yAxis_title.replace(
                "_",
                " ",
            )
        else:
            grouped_column_chart_json_dict["yAxis"] = "Total " + yAxis_title.replace(
                "_",
                " ",
            )
    else:
        grouped_column_chart_json_dict["yAxis"] = "Total " + yAxis_title.replace(
            "_",
            " ",
        )

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
        code_level_logger.error(
            "grouped_column_chart: X-Axis is not found in extraction!"
        )
        raise RuntimeError("grouped_column_chart: X-Axis is not found in extraction!")

    if "series" in chart_data_columns:
        series_column_name = "series"
    elif (
        "series_column" in chart_axis
        and isinstance(chart_axis["series_column"], str)
        and chart_axis["series_column"] in chart_data_columns
    ):
        series_column_name = chart_axis["series_column"]
    else:
        series_column_name = ""

    object_columns = chart_data.select_dtypes(include=[object])

    yAxis_column_names = list(chart_data.columns)
    yAxis_column_names.remove(xAxis_column_name)
    if series_column_name in yAxis_column_names:
        yAxis_column_names.remove(series_column_name)

    for yAxis_column_name in yAxis_column_names:
        if yAxis_column_name in object_columns:
            try:
                if not isinstance(
                    chart_data[yAxis_column_name].values.tolist()[0],
                    datetime.date,
                ) and not isinstance(
                    chart_data[yAxis_column_name].values.tolist()[0],
                    datetime.datetime,
                ):
                    if isinstance(
                        chart_data[yAxis_column_name].values.tolist()[0],
                        str,
                    ):
                        chart_data[yAxis_column_name] = chart_data[
                            yAxis_column_name
                        ].replace("%", "", regex=True)
                    chart_data[yAxis_column_name] = pd.to_numeric(
                        chart_data[yAxis_column_name],
                    )
            except Exception:
                code_level_logger.error(
                    f"grouped_column_chart: {yAxis_column_name} is not numerical!",
                )
                raise RuntimeError(
                    f"grouped_column_chart: {yAxis_column_name} is not numerical!",
                )

    if (
        series_column_name != ""
        and series_column_name in chart_data.columns
        and chart_data[series_column_name].nunique() > 1
    ):
        new_chart_data = pd.DataFrame()

        pivot_data = chart_data.pivot_table(
            index="xAxis",
            columns="series",
            values=yAxis_column_names,
        )
        pivot_data = pivot_data.reset_index()
        new_chart_data["xAxis"] = pivot_data["xAxis"].values.tolist()

        for yAxis_column_name in yAxis_column_names:
            yAxis_pivot_table = pivot_data[yAxis_column_name]
            for yAxis_pivot_column in list(yAxis_pivot_table.columns):
                new_columns = {
                    f"{yAxis_column_name}_{yAxis_pivot_column}": [
                        float(val) if isinstance(val, decimal.Decimal) else val
                        for val in yAxis_pivot_table[yAxis_pivot_column].values.tolist()
                    ],
                }
                added_chart_data = pd.DataFrame(new_columns)
                new_chart_data = pd.concat([new_chart_data, added_chart_data], axis=1)

        chart_data = new_chart_data.fillna(
            {
                col: (
                    0 if new_chart_data[col].dtype in [np.float64, np.int64] else "null"
                )
                for col in new_chart_data.columns
            },
        )

    if (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{4}-\d{2}-\d{2}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%Y-%m-%d",
        )
    elif (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{2}/\d{2}/\d{4}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%d/%m/%Y",
        )

    if all(
        isinstance(val, (datetime.date, datetime.datetime))
        for val in chart_data[xAxis_column_name]
    ):
        chart_data, new_chart_axis, new_chart_title = adjust_axis_title_and_data(
            llama70b_client,
            chart_id,
            chart_data,
            chart_axis,
            chart_title,
            logging_url,
        )
        grouped_column_chart_json_dict["xAxis"] = new_chart_axis["xAxis_title"].replace(
            "_",
            " ",
        )
        grouped_column_chart_json_dict["Chart_Title"] = new_chart_title

    try:
        if len(chart_data[xAxis_column_name][0].split("-")) == 1:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                ),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (
                        int(date.split("-")[0]),
                        int(date.split("-")[1]),
                        int(date.split("-")[2]),
                    ),
                ),
            )
        else:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)
    except Exception:
        chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

    if isinstance(xAxis_column_name, str):
        chart_data = sort_pandas_date(chart_data, xAxis_column_name)

    grouped_column_chart_json_dict["X"] = [
        str(x_data) for x_data in chart_data[xAxis_column_name].values.tolist()
    ]

    yAxis_idx = 1

    for column_name in list(chart_data.columns):
        if not re.search(r"yAxis([23456789])?", column_name, re.IGNORECASE):
            continue

        if yAxis_idx <= 1:
            grouped_column_chart_json_dict["Y"] = [
                float(val) if isinstance(val, decimal.Decimal) else val
                for val in chart_data[column_name].values.tolist()
            ]

            underscore_index = column_name.find("_")

            # No Series
            if underscore_index == -1:
                if check_aggregation_phrases(
                    chart_axis[f"{column_name}_title"].replace("_", " "),
                ):
                    grouped_column_chart_json_dict["yName"] = chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")
                elif f"{column_name}_aggregation" in chart_axis:
                    if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                        grouped_column_chart_json_dict["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["AVG", "MEAN"]:
                        grouped_column_chart_json_dict["yName"] = (
                            "Average "
                            + chart_axis[f"{column_name}_title"].replace("_", " ")
                        )
                    elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                        grouped_column_chart_json_dict["yName"] = (
                            "Median "
                            + chart_axis[f"{column_name}_title"].replace("_", " ")
                        )
                    elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                        grouped_column_chart_json_dict["yName"] = (
                            "Minimum "
                            + chart_axis[f"{column_name}_title"].replace("_", " ")
                        )
                    elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                        grouped_column_chart_json_dict["yName"] = (
                            "Maximum "
                            + chart_axis[f"{column_name}_title"].replace("_", " ")
                        )
                    else:
                        grouped_column_chart_json_dict["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                else:
                    grouped_column_chart_json_dict["yName"] = "Total " + chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")
            # Has Series
            else:
                original_column_name = column_name[:underscore_index]
                series_name = column_name[underscore_index + 1 :]

                # Add Series Title to Series Name
                if "series_title" in chart_axis and chart_axis["series_title"] != "":
                    series_name = f"""{chart_axis["series_title"]}: {series_name}"""

                if (
                    f"{original_column_name}_title" in chart_axis
                    and check_aggregation_phrases(
                        f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        ),
                    )
                ):
                    grouped_column_chart_json_dict["yName"] = (
                        f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        )
                    )
                elif f"{original_column_name}_aggregation" in chart_axis:
                    if chart_axis[f"{original_column_name}_aggregation"] in ["SUM"]:
                        grouped_column_chart_json_dict["yName"] = (
                            "Total "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in [
                        "AVG",
                        "MEAN",
                    ]:
                        grouped_column_chart_json_dict["yName"] = (
                            "Average "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in [
                        "MEDIAN",
                    ]:
                        grouped_column_chart_json_dict["yName"] = (
                            "Median "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in ["MIN"]:
                        grouped_column_chart_json_dict["yName"] = (
                            "Minimum "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in ["MAX"]:
                        grouped_column_chart_json_dict["yName"] = (
                            "Maximum "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    else:
                        grouped_column_chart_json_dict["yName"] = (
                            "Total "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                else:
                    grouped_column_chart_json_dict["yName"] = (
                        "Total "
                        + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        )
                    )

            if not (
                isinstance(grouped_column_chart_json_dict["Y"][0], int)
                or isinstance(grouped_column_chart_json_dict["Y"][0], float)
            ):
                code_level_logger.error(
                    "grouped_column_chart: Y-axis is not integer or float!",
                )
                raise RuntimeError(
                    "grouped_column_chart: Y-axis is not integer or float!",
                )
        else:
            grouped_column_chart_json_dict[f"Y{yAxis_idx}"] = [
                float(val) if isinstance(val, decimal.Decimal) else val
                for val in chart_data[column_name].values.tolist()
            ]

            underscore_index = column_name.find("_")

            # No Series
            if underscore_index == -1:
                grouped_column_chart_json_dict[f"y{yAxis_idx}Name"] = chart_axis[
                    f"{column_name}_title"
                ].replace("_", " ")
                if grouped_column_chart_json_dict[f"y{yAxis_idx}Name"] == "":
                    grouped_column_chart_json_dict[f"y{yAxis_idx}Name"] = (
                        grouped_column_chart_json_dict["yName"]
                    )

                if not check_aggregation_phrases(
                    grouped_column_chart_json_dict[f"y{yAxis_idx}Name"],
                ):
                    if f"{column_name}_aggregation" in chart_axis:
                        if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                            grouped_column_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Total "
                                + grouped_column_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            grouped_column_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Average "
                                + grouped_column_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                            grouped_column_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Median "
                                + grouped_column_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                            grouped_column_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Minimum "
                                + grouped_column_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                            grouped_column_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Maximum "
                                + grouped_column_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        else:
                            grouped_column_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Total "
                                + grouped_column_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                    else:
                        grouped_column_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Total "
                            + grouped_column_chart_json_dict[f"y{yAxis_idx}Name"]
                        )
            # Has Series
            else:
                original_column_name = column_name[:underscore_index]
                series_name = column_name[underscore_index + 1 :]

                # Add Series Title to Series Name
                if "series_title" in chart_axis and chart_axis["series_title"] != "":
                    series_name = f"""{chart_axis["series_title"]}: {series_name}"""

                grouped_column_chart_json_dict[f"y{yAxis_idx}Name"] = (
                    f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                        "_",
                        " ",
                    )
                )
                if grouped_column_chart_json_dict[f"y{yAxis_idx}Name"] == "":
                    grouped_column_chart_json_dict[f"y{yAxis_idx}Name"] = (
                        grouped_column_chart_json_dict["yName"]
                    )

                if not check_aggregation_phrases(
                    grouped_column_chart_json_dict[f"y{yAxis_idx}Name"],
                ):
                    if f"{original_column_name}_aggregation" in chart_axis:
                        if chart_axis[f"{original_column_name}_aggregation"] in ["SUM"]:
                            grouped_column_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Total "
                                + grouped_column_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            grouped_column_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Average "
                                + grouped_column_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MEDIAN",
                        ]:
                            grouped_column_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Median "
                                + grouped_column_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MIN",
                        ]:
                            grouped_column_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Minimum "
                                + grouped_column_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MAX",
                        ]:
                            grouped_column_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Maximum "
                                + grouped_column_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        else:
                            grouped_column_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Total "
                                + grouped_column_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                    else:
                        grouped_column_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Total "
                            + grouped_column_chart_json_dict[f"y{yAxis_idx}Name"]
                        )

            if not (
                isinstance(grouped_column_chart_json_dict[f"Y{yAxis_idx}"][0], int)
                or isinstance(grouped_column_chart_json_dict[f"Y{yAxis_idx}"][0], float)
            ):
                code_level_logger.error(
                    f"grouped_column_chart: Y{yAxis_idx}-axis is not integer or float!",
                )
                raise RuntimeError(
                    f"grouped_column_chart: Y{yAxis_idx}-axis is not integer or float!",
                )

        yAxis_idx += 1

    if grouped_column_chart_json_dict["Y"] == []:
        code_level_logger.error(
            "grouped_column_chart: Y-Axis is not found in extraction!"
        )
        raise RuntimeError("grouped_column_chart: Y-Axis is not found in extraction!")

    if any(
        grouped_column_chart_json_dict[key] == []
        or grouped_column_chart_json_dict[key] == [""]
        for key in grouped_column_chart_json_dict
        if re.match(r"^X\d*$", key)
    ):
        code_level_logger.error(
            "grouped_column_chart: One or more X-axis values are empty!"
        )
        raise RuntimeError("grouped_column_chart: One or more X-axis values are empty!")

    grouped_column_chart_json_dict["Database_Identifier"] = database_properties[
        "db_tag"
    ]

    # Convert chart type to 'column_chart'
    if grouped_column_chart_json_dict["Y2"] == []:
        # grouped_column_chart_json_dict["Chart_Type"] = "column_chart"
        grouped_column_chart_json_dict["Chart_Type"] = "grouped_column_chart"

        if len(grouped_column_chart_json_dict["Y"]) == 1:
            card_chart_json_dict: dict = generate_card_chart_d3(
                llama70b_client,
                user_query,
                chart_id,
                sql_query,
                chart_title,
                chart_axis,
                chart_data,
                database_properties,
                ups_idx,
                chart_position,
                overall_title,
                client_id,
                user_id,
                session_id,
                sql_library,
                grouped_column_chart_json_dict["Chart_Type"],
                logging_url,
                code_level_logger,
            )
            return card_chart_json_dict

    grouped_column_chart_json_dict["Client_ID"] = client_id
    grouped_column_chart_json_dict["User_ID"] = user_id
    grouped_column_chart_json_dict["Session_ID"] = session_id

    return grouped_column_chart_json_dict


def generate_group_bar_chart_d3(
    llama70b_client: Any,
    user_query: str,
    chart_id: str,
    sql_query: str,
    chart_title: str,
    chart_axis: dict,
    chart_data: pd.DataFrame,
    database_properties: dict,
    ups_idx: int,
    chart_position: int,
    overall_title: str,
    client_id: str,
    user_id: str,
    session_id: str,
    sql_library: str,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    grouped_bar_chart_json_dict: dict = GROUPED_BAR_CHART_TEMPLATE_D3.copy()
    grouped_bar_chart_json_dict["User_Query"] = user_query
    grouped_bar_chart_json_dict["Chart_Query"] = sql_query
    grouped_bar_chart_json_dict["Chart_SQL_Library"] = sql_library
    grouped_bar_chart_json_dict["Chart_Name"] = f"Visual {ups_idx}"
    grouped_bar_chart_json_dict["Chart_Axis"] = chart_axis
    grouped_bar_chart_json_dict["Visual_Title"] = overall_title
    grouped_bar_chart_json_dict["Chart_ID"] = chart_id
    grouped_bar_chart_json_dict["Chart_Type"] = "grouped_bar_chart"
    grouped_bar_chart_json_dict["Chart_Position"] = str(chart_position)
    grouped_bar_chart_json_dict["Chart_Title"] = chart_title

    grouped_bar_chart_json_dict["xAxis"] = chart_axis["xAxis_title"].replace("_", " ")

    grouped_bar_chart_json_dict["Aggregated_Table_JSON"] = (
        generate_aggregated_table_chart_d3(
            user_query,
            sql_query,
            chart_id,
            chart_title,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            chart_axis,
            grouped_bar_chart_json_dict["Chart_Type"],
            code_level_logger,
        )
    )
    grouped_bar_chart_json_dict["Aggregated_Table_Column"] = get_aggregated_columns(
        chart_axis,
    )

    yAxis_title = ""

    for chart_axis_key in chart_axis:
        if (
            chart_axis_key.lower()[0] != "y"
            or "title" not in chart_axis_key.lower()
            or chart_axis[chart_axis_key] == ""
        ):
            continue
        if yAxis_title == "":
            yAxis_title += chart_axis[chart_axis_key]
        else:
            # yAxis_title += f"/{chart_axis[chart_axis_key]}"
            yAxis_title = "Amount"
            break

    if (
        check_aggregation_phrases(yAxis_title.replace("_", " "))
        or yAxis_title == "Amount"
    ):
        grouped_bar_chart_json_dict["yAxis"] = yAxis_title.replace("_", " ")
    elif "yAxis_aggregation" in chart_axis:
        if chart_axis["yAxis_aggregation"] in ["SUM"]:
            grouped_bar_chart_json_dict["yAxis"] = "Total " + yAxis_title.replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
            grouped_bar_chart_json_dict["yAxis"] = "Average " + yAxis_title.replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
            grouped_bar_chart_json_dict["yAxis"] = "Median " + yAxis_title.replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["MIN"]:
            grouped_bar_chart_json_dict["yAxis"] = "Minimum " + yAxis_title.replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["MAX"]:
            grouped_bar_chart_json_dict["yAxis"] = "Maximum " + yAxis_title.replace(
                "_",
                " ",
            )
        else:
            grouped_bar_chart_json_dict["yAxis"] = "Total " + yAxis_title.replace(
                "_",
                " ",
            )
    else:
        grouped_bar_chart_json_dict["yAxis"] = "Total " + yAxis_title.replace(
            "_",
            " ",
        )
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
        code_level_logger.error("grouped_bar_chart: X-Axis is not found in extraction!")
        raise RuntimeError("grouped_bar_chart: X-Axis is not found in extraction!")

    if "series" in chart_data_columns:
        series_column_name = "series"
    elif (
        "series_column" in chart_axis
        and isinstance(chart_axis["series_column"], str)
        and chart_axis["series_column"] in chart_data_columns
    ):
        series_column_name = chart_axis["series_column"]
    else:
        series_column_name = ""

    object_columns = chart_data.select_dtypes(include=[object])

    yAxis_column_names = list(chart_data.columns)
    yAxis_column_names.remove(xAxis_column_name)
    if series_column_name in yAxis_column_names:
        yAxis_column_names.remove(series_column_name)

    for yAxis_column_name in yAxis_column_names:
        if yAxis_column_name in object_columns:
            try:
                if not isinstance(
                    chart_data[yAxis_column_name].values.tolist()[0],
                    datetime.date,
                ) and not isinstance(
                    chart_data[yAxis_column_name].values.tolist()[0],
                    datetime.datetime,
                ):
                    if isinstance(
                        chart_data[yAxis_column_name].values.tolist()[0],
                        str,
                    ):
                        chart_data[yAxis_column_name] = chart_data[
                            yAxis_column_name
                        ].replace("%", "", regex=True)
                    chart_data[yAxis_column_name] = pd.to_numeric(
                        chart_data[yAxis_column_name],
                    )
            except Exception:
                code_level_logger.error(
                    f"grouped_bar_chart: {yAxis_column_name} is not numerical!",
                )
                raise RuntimeError(
                    f"grouped_bar_chart: {yAxis_column_name} is not numerical!",
                )

    if (
        series_column_name != ""
        and series_column_name in chart_data.columns
        and chart_data[series_column_name].nunique() > 1
    ):
        new_chart_data = pd.DataFrame()

        pivot_data = chart_data.pivot_table(
            index=xAxis_column_name,
            columns=series_column_name,
            values=yAxis_column_names,
        )
        pivot_data = pivot_data.reset_index()
        new_chart_data[xAxis_column_name] = pivot_data[
            xAxis_column_name
        ].values.tolist()

        for yAxis_column_name in yAxis_column_names:
            yAxis_pivot_table = pivot_data[yAxis_column_name]
            for yAxis_pivot_column in list(yAxis_pivot_table.columns):
                new_columns = {
                    f"{yAxis_column_name}_{yAxis_pivot_column}": yAxis_pivot_table[
                        yAxis_pivot_column
                    ].values.tolist(),
                }
                added_chart_data = pd.DataFrame(new_columns)
                new_chart_data = pd.concat([new_chart_data, added_chart_data], axis=1)

        chart_data = new_chart_data.fillna(
            {
                col: (
                    0 if new_chart_data[col].dtype in [np.float64, np.int64] else "null"
                )
                for col in new_chart_data.columns
            },
        )

    if (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{4}-\d{2}-\d{2}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%Y-%m-%d",
        )
    elif (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{2}/\d{2}/\d{4}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%d/%m/%Y",
        )

    if all(
        isinstance(val, (datetime.date, datetime.datetime))
        for val in chart_data[xAxis_column_name]
    ):
        chart_data, new_chart_axis, new_chart_title = adjust_axis_title_and_data(
            llama70b_client,
            chart_id,
            chart_data,
            chart_axis,
            chart_title,
            logging_url,
        )
        grouped_bar_chart_json_dict["xAxis"] = new_chart_axis["xAxis_title"].replace(
            "_",
            " ",
        )
        grouped_bar_chart_json_dict["Chart_Title"] = new_chart_title

    try:
        if len(chart_data[xAxis_column_name][0].split("-")) == 1:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                ),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (
                        int(date.split("-")[0]),
                        int(date.split("-")[1]),
                        int(date.split("-")[2]),
                    ),
                ),
            )
        else:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)
    except Exception:
        chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

    if isinstance(xAxis_column_name, str):
        chart_data, is_date = detect_and_sort_pandas_date(chart_data, xAxis_column_name)

        # If date, convert to line chart
        if is_date:
            grouped_bar_chart_json_dict["Chart_Type"] = "line_chart"

    grouped_bar_chart_json_dict["X"] = [
        str(x_data) for x_data in chart_data[xAxis_column_name].values.tolist()
    ]
    yAxis_idx = 1

    for column_name in list(chart_data.columns):
        if not re.search(r"yAxis([23456789])?", column_name, re.IGNORECASE):
            continue

        if yAxis_idx <= 1:
            grouped_bar_chart_json_dict["Y"] = [
                float(val) if isinstance(val, decimal.Decimal) else val
                for val in chart_data[column_name].values.tolist()
            ]

            underscore_index = column_name.find("_")

            # No Series
            if underscore_index == -1:
                if check_aggregation_phrases(
                    chart_axis[f"{column_name}_title"].replace("_", " "),
                ):
                    grouped_bar_chart_json_dict["yName"] = chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")
                elif f"{column_name}_aggregation" in chart_axis:
                    if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                        grouped_bar_chart_json_dict["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["AVG", "MEAN"]:
                        grouped_bar_chart_json_dict["yName"] = "Average " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                        grouped_bar_chart_json_dict["yName"] = "Median " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                        grouped_bar_chart_json_dict["yName"] = "Minimum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                        grouped_bar_chart_json_dict["yName"] = "Maximum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    else:
                        grouped_bar_chart_json_dict["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                else:
                    grouped_bar_chart_json_dict["yName"] = "Total " + chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")
            # Has Series
            else:
                original_column_name = column_name[:underscore_index]
                series_name = column_name[underscore_index + 1 :]

                # Add Series Title to Series Name
                if "series_title" in chart_axis and chart_axis["series_title"] != "":
                    series_name = f"""{chart_axis["series_title"]}: {series_name}"""

                if (
                    f"{original_column_name}_title" in chart_axis
                    and check_aggregation_phrases(
                        f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        ),
                    )
                ):
                    grouped_bar_chart_json_dict["yName"] = (
                        f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        )
                    )
                elif f"{original_column_name}_aggregation" in chart_axis:
                    if chart_axis[f"{original_column_name}_aggregation"] in ["SUM"]:
                        grouped_bar_chart_json_dict["yName"] = (
                            "Total "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in [
                        "AVG",
                        "MEAN",
                    ]:
                        grouped_bar_chart_json_dict["yName"] = (
                            "Average "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in [
                        "MEDIAN",
                    ]:
                        grouped_bar_chart_json_dict["yName"] = (
                            "Median "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in ["MIN"]:
                        grouped_bar_chart_json_dict["yName"] = (
                            "Minimum "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in ["MAX"]:
                        grouped_bar_chart_json_dict["yName"] = (
                            "Maximum "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    else:
                        grouped_bar_chart_json_dict["yName"] = (
                            "Total "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                else:
                    grouped_bar_chart_json_dict["yName"] = (
                        "Total "
                        + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        )
                    )

            if not (
                isinstance(grouped_bar_chart_json_dict["Y"][0], int)
                or isinstance(grouped_bar_chart_json_dict["Y"][0], float)
            ):
                code_level_logger.error(
                    "grouped_bar_chart: Y-axis is not integer or float!"
                )
                raise RuntimeError("grouped_bar_chart: Y-axis is not integer or float!")

            # if check_negative_value(grouped_bar_chart_json_dict["Y"]):
            #     # grouped_bar_chart_json_dict["Chart_Type"] = "column_chart"
            #     grouped_bar_chart_json_dict["Chart_Type"] = "grouped_column_chart"
        else:
            grouped_bar_chart_json_dict[f"Y{yAxis_idx}"] = [
                float(val) if isinstance(val, decimal.Decimal) else val
                for val in chart_data[column_name].values.tolist()
            ]

            underscore_index = column_name.find("_")

            # No Series
            if underscore_index == -1:
                grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"] = chart_axis[
                    f"{column_name}_title"
                ].replace("_", " ")
                if grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"] == "":
                    grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                        grouped_bar_chart_json_dict["yName"]
                    )

                if not check_aggregation_phrases(
                    grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"],
                ):
                    if f"{column_name}_aggregation" in chart_axis:
                        if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                            grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Total "
                                + grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Average "
                                + grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                            grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Median "
                                + grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                            grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Minimum "
                                + grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                            grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Maximum "
                                + grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        else:
                            grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                    else:
                        grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Total " + grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"]
                        )
            # Has Series
            else:
                original_column_name = column_name[:underscore_index]
                series_name = column_name[underscore_index + 1 :]

                # Add Series Title to Series Name
                if "series_title" in chart_axis and chart_axis["series_title"] != "":
                    series_name = f"""{chart_axis["series_title"]}: {series_name}"""

                grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                    f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                        "_",
                        " ",
                    )
                )
                if grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"] == "":
                    grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                        grouped_bar_chart_json_dict["yName"]
                    )

                if not check_aggregation_phrases(
                    grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"],
                ):
                    if f"{original_column_name}_aggregation" in chart_axis:
                        if chart_axis[f"{original_column_name}_aggregation"] in ["SUM"]:
                            grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Total "
                                + grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Average "
                                + grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MEDIAN",
                        ]:
                            grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Median "
                                + grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MIN",
                        ]:
                            grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Minimum "
                                + grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MAX",
                        ]:
                            grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Maximum "
                                + grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        else:
                            grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Total "
                                + grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                    else:
                        grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Total " + grouped_bar_chart_json_dict[f"y{yAxis_idx}Name"]
                        )

            if not (
                isinstance(grouped_bar_chart_json_dict[f"Y{yAxis_idx}"][0], int)
                or isinstance(grouped_bar_chart_json_dict[f"Y{yAxis_idx}"][0], float)
            ):
                code_level_logger.error(
                    f"grouped_bar_chart: Y{yAxis_idx}-axis is not integer or float!",
                )
                raise RuntimeError(
                    f"grouped_bar_chart: Y{yAxis_idx}-axis is not integer or float!",
                )

            # if (
            #     check_negative_value(grouped_bar_chart_json_dict[f"Y{yAxis_idx}"])
            #     or grouped_bar_chart_json_dict["Chart_Type"] == "column_chart"
            # ):
            #     grouped_bar_chart_json_dict["Chart_Type"] = "grouped_column_chart"

        yAxis_idx += 1

    if grouped_bar_chart_json_dict["Y"] == []:
        code_level_logger.error("grouped_bar_chart: Y-Axis is not found in extraction!")
        raise RuntimeError("grouped_bar_chart: Y-Axis is not found in extraction!")

    if any(
        grouped_bar_chart_json_dict[key] == []
        or grouped_bar_chart_json_dict[key] == [""]
        for key in grouped_bar_chart_json_dict
        if re.match(r"^X\d*$", key)
    ):
        code_level_logger.error(
            "grouped_bar_chart: One or more X-axis values are empty!"
        )
        raise RuntimeError("grouped_bar_chart: One or more X-axis values are empty!")

    chart_data_lists = []

    x_values = grouped_bar_chart_json_dict["X"]

    if "Y" in grouped_bar_chart_json_dict:
        main_y_data = []
        for i in range(len(x_values)):
            x_value = x_values[i]
            main_y_value = grouped_bar_chart_json_dict["Y"][i]
            main_group_name = grouped_bar_chart_json_dict.get("yName", "Series 1")
            main_y_data.append(
                {
                    "X_Value": x_value,
                    "Y_Value": main_y_value,
                    "Group_Name": main_group_name,
                },
            )
        chart_data_lists.append(main_y_data)

    j = 2
    while f"Y{j}" in grouped_bar_chart_json_dict:
        additional_y_data = []

        for i in range(len(x_values)):
            x_value = x_values[i]

            y_key = f"Y{j}"
            if y_key in grouped_bar_chart_json_dict:
                additional_y_value = grouped_bar_chart_json_dict[y_key][i]
                group_name_key = f"y{j}Name"
                group_name = grouped_bar_chart_json_dict.get(
                    group_name_key,
                    f"Series {j}",
                )
                additional_y_data.append(
                    {
                        "X_Value": x_value,
                        "Y_Value": additional_y_value,
                        "Group_Name": group_name,
                    },
                )

        if additional_y_data:
            chart_data_lists.append(additional_y_data)

        j += 1

    def is_within_max_length(chart_data: list, maximum_length: int) -> bool:
        for data in chart_data:
            if len(data) > maximum_length:
                return False

        return True

    def map_original_list_with_sorted_x(original_x: list, sorted_x: list):
        sorted_list = []

        for sublist in original_x:
            sorted_sublist = sorted(sublist, key=lambda x: sorted_x.index(x["X_Value"]))
            sorted_list.append(sorted_sublist)

        return sorted_list

    def llm_semantic_sort(x_values: list, logging_url: str) -> list:
        list_to_be_sort = x_values
        system_prompt = "Sort the given list in chronological order and return only the sorted list as a Python list, without any explanations."
        user_prompt = f"Please sort this {list_to_be_sort}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        start_narrative = perf_counter()

        response: list = (
            llama70b_client.chat.completions.create(
                messages=messages,
                model=os.getenv("LLAMA70B_MODEL"),
                max_tokens=2000,
                temperature=0.5,
            )
            .choices[0]
            .message.content
        )

        input_tokens = 0
        output_tokens = 0

        input_tokens = calculate_token_usage(system_prompt) + calculate_token_usage(
            user_prompt
        )
        output_tokens = calculate_token_usage(response)

        llm_semantic_sort_inference_time = perf_counter() - start_narrative

        MODULEID_LLM_SEMANTIC_SORT = os.getenv("MODULEID_LLM_SEMANTIC_SORT", "")

        if MODULEID_LLM_SEMANTIC_SORT == "":
            code_level_logger.error("MODULEID_LLM_SEMANTIC_SORT is invalid!")
            raise ValueError("MODULEID_LLM_SEMANTIC_SORT is invalid!")

        formatted_data = {
            "chart_id": chart_id,
            "module_id": int(MODULEID_LLM_SEMANTIC_SORT),
            "messages": messages,
            "output": response,
            "inference_time": llm_semantic_sort_inference_time,
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

        return response

    if is_within_max_length(chart_data_lists, 12):
        grouped_bar_chart_json_dict["Chart_Data"] = map_original_list_with_sorted_x(
            chart_data_lists, llm_semantic_sort(x_values, logging_url)
        )

    grouped_bar_chart_json_dict["Database_Identifier"] = database_properties["db_tag"]

    # Convert chart type to 'bar_chart'
    # if grouped_bar_chart_json_dict["Y2"] == []:
    #     grouped_bar_chart_json_dict["Chart_Type"] = "bar_chart"

    if (
        len(grouped_bar_chart_json_dict["Chart_Data"]) == 1
        and len(grouped_bar_chart_json_dict["Chart_Data"][0]) == 1
    ):
        card_chart_json_dict: dict = generate_card_chart_d3(
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            grouped_bar_chart_json_dict["Chart_Type"],
            logging_url,
            code_level_logger,
        )
        return card_chart_json_dict

    keys_to_remove = ["X", "Y", "yName"]

    i = 2
    while f"y{i}Name" in grouped_bar_chart_json_dict:
        keys_to_remove.append(f"y{i}Name")
        i += 1

    j = 2
    while f"Y{j}" in grouped_bar_chart_json_dict:
        keys_to_remove.append(f"Y{j}")
        j += 1

    # Remove all specified keys ['X', 'Y', 'yName'] and etc. from the dictionary
    for key in keys_to_remove:
        if key in grouped_bar_chart_json_dict:
            del grouped_bar_chart_json_dict[key]

    grouped_bar_chart_json_dict["Client_ID"] = client_id
    grouped_bar_chart_json_dict["User_ID"] = user_id
    grouped_bar_chart_json_dict["Session_ID"] = session_id

    return grouped_bar_chart_json_dict


def generate_radar_chart_d3(
    llama70b_client: Any,
    user_query: str,
    chart_id: str,
    sql_query: str,
    chart_title: str,
    chart_axis: dict,
    chart_data: pd.DataFrame,
    database_properties: dict,
    ups_idx: int,
    chart_position: int,
    overall_title: str,
    client_id: str,
    user_id: str,
    session_id: str,
    sql_library: str,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    if len(chart_data) > 6:
        return generate_group_bar_chart_d3(
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            logging_url,
            code_level_logger,
        )

    radar_chart_json_dict: dict = RADAR_CHART_TEMPLATE_D3.copy()
    radar_chart_json_dict["User_Query"] = user_query
    radar_chart_json_dict["Chart_Query"] = sql_query
    radar_chart_json_dict["Chart_SQL_Library"] = sql_library
    radar_chart_json_dict["Chart_Name"] = f"Visual {ups_idx}"
    radar_chart_json_dict["Chart_Axis"] = chart_axis
    radar_chart_json_dict["Visual_Title"] = overall_title
    radar_chart_json_dict["Chart_ID"] = chart_id
    radar_chart_json_dict["Chart_Type"] = "radar_chart"
    radar_chart_json_dict["Chart_Position"] = str(chart_position)
    radar_chart_json_dict["Chart_Title"] = chart_title

    radar_chart_json_dict["xAxis"] = chart_axis["xAxis_title"].replace("_", " ")

    radar_chart_json_dict["Aggregated_Table_JSON"] = generate_aggregated_table_chart_d3(
        user_query,
        sql_query,
        chart_id,
        chart_title,
        chart_data,
        database_properties,
        ups_idx,
        chart_position,
        overall_title,
        client_id,
        user_id,
        session_id,
        sql_library,
        chart_axis,
        radar_chart_json_dict["Chart_Type"],
        code_level_logger,
    )
    radar_chart_json_dict["Aggregated_Table_Column"] = get_aggregated_columns(
        chart_axis,
    )

    yAxis_title = ""

    for chart_axis_key in chart_axis:
        if (
            chart_axis_key.lower()[0] != "y"
            or "title" not in chart_axis_key.lower()
            or chart_axis[chart_axis_key] == ""
        ):
            continue
        if yAxis_title == "":
            yAxis_title += chart_axis[chart_axis_key]
        else:
            # yAxis_title += f"/{chart_axis[chart_axis_key]}"
            yAxis_title = "Amount"
            break

    if (
        check_aggregation_phrases(yAxis_title.replace("_", " "))
        or yAxis_title == "Amount"
    ):
        radar_chart_json_dict["yAxis"] = yAxis_title.replace("_", " ")
    elif "yAxis_aggregation" in chart_axis:
        if chart_axis["yAxis_aggregation"] in ["SUM"]:
            radar_chart_json_dict["yAxis"] = "Total " + yAxis_title.replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
            radar_chart_json_dict["yAxis"] = "Average " + yAxis_title.replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
            radar_chart_json_dict["yAxis"] = "Median " + yAxis_title.replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["MIN"]:
            radar_chart_json_dict["yAxis"] = "Minimum " + yAxis_title.replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["MAX"]:
            radar_chart_json_dict["yAxis"] = "Maximum " + yAxis_title.replace(
                "_",
                " ",
            )
        else:
            radar_chart_json_dict["yAxis"] = "Total " + yAxis_title.replace(
                "_",
                " ",
            )
    else:
        radar_chart_json_dict["yAxis"] = "Total " + yAxis_title.replace("_", " ")

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
        code_level_logger.error("radar_chart: X-Axis is not found in extraction!")
        raise RuntimeError("radar_chart: X-Axis is not found in extraction!")

    if "series" in chart_data_columns:
        series_column_name = "series"
    elif (
        "series_column" in chart_axis
        and isinstance(chart_axis["series_column"], str)
        and chart_axis["series_column"] in chart_data_columns
    ):
        series_column_name = chart_axis["series_column"]
    else:
        series_column_name = ""

    object_columns = chart_data.select_dtypes(include=[object])

    yAxis_column_names = list(chart_data.columns)
    yAxis_column_names.remove(xAxis_column_name)
    if series_column_name in yAxis_column_names:
        yAxis_column_names.remove(series_column_name)

    for yAxis_column_name in yAxis_column_names:
        if yAxis_column_name in object_columns:
            try:
                if not isinstance(
                    chart_data[yAxis_column_name].values.tolist()[0],
                    datetime.date,
                ) and not isinstance(
                    chart_data[yAxis_column_name].values.tolist()[0],
                    datetime.datetime,
                ):
                    if isinstance(
                        chart_data[yAxis_column_name].values.tolist()[0],
                        str,
                    ):
                        chart_data[yAxis_column_name] = chart_data[
                            yAxis_column_name
                        ].replace("%", "", regex=True)
                    chart_data[yAxis_column_name] = pd.to_numeric(
                        chart_data[yAxis_column_name],
                    )
            except Exception:
                code_level_logger.error(
                    f"radar_chart: {yAxis_column_name} is not numerical!",
                )
                raise RuntimeError(
                    f"radar_chart: {yAxis_column_name} is not numerical!",
                )

    if (
        series_column_name != ""
        and series_column_name in chart_data.columns
        and chart_data[series_column_name].nunique() > 1
    ):
        new_chart_data = pd.DataFrame()

        pivot_data = chart_data.pivot_table(
            index=xAxis_column_name,
            columns=series_column_name,
            values=yAxis_column_names,
        )
        pivot_data = pivot_data.reset_index()
        new_chart_data[xAxis_column_name] = pivot_data[
            xAxis_column_name
        ].values.tolist()

        for yAxis_column_name in yAxis_column_names:
            yAxis_pivot_table = pivot_data[yAxis_column_name]
            for yAxis_pivot_column in list(yAxis_pivot_table.columns):
                new_columns = {
                    f"{yAxis_column_name}_{yAxis_pivot_column}": [
                        float(val) if isinstance(val, decimal.Decimal) else val
                        for val in yAxis_pivot_table[yAxis_pivot_column].values.tolist()
                    ],
                }
                added_chart_data = pd.DataFrame(new_columns)
                new_chart_data = pd.concat([new_chart_data, added_chart_data], axis=1)

        chart_data = new_chart_data.fillna(
            {
                col: (
                    0 if new_chart_data[col].dtype in [np.float64, np.int64] else "null"
                )
                for col in new_chart_data.columns
            },
        )

    if (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{4}-\d{2}-\d{2}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%Y-%m-%d",
        )
    elif (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{2}/\d{2}/\d{4}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%d/%m/%Y",
        )

    if all(
        isinstance(val, (datetime.date, datetime.datetime))
        for val in chart_data[xAxis_column_name]
    ):
        chart_data, new_chart_axis, new_chart_title = adjust_axis_title_and_data(
            llama70b_client,
            chart_id,
            chart_data,
            chart_axis,
            chart_title,
            logging_url,
        )
        radar_chart_json_dict["xAxis"] = new_chart_axis["xAxis_title"].replace("_", " ")
        radar_chart_json_dict["Chart_Title"] = new_chart_title

    try:
        if len(chart_data[xAxis_column_name][0].split("-")) == 1:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                ),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (
                        int(date.split("-")[0]),
                        int(date.split("-")[1]),
                        int(date.split("-")[2]),
                    ),
                ),
            )
        else:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)
    except Exception:
        chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

    if isinstance(xAxis_column_name, str):
        chart_data = sort_pandas_date(chart_data, xAxis_column_name)

    radar_chart_json_dict["X"] = [
        str(x_data) for x_data in chart_data[xAxis_column_name].values.tolist()
    ]

    if (
        len(radar_chart_json_dict["X"]) >= 1 and len(radar_chart_json_dict["X"]) <= 2
    ) or len(radar_chart_json_dict["X"]) > 12:
        return generate_group_bar_chart_d3(
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            logging_url,
            code_level_logger,
        )

    yAxis_idx = 1

    for column_name in list(chart_data.columns):
        if not re.search(r"yAxis([23456789])?", column_name, re.IGNORECASE):
            continue

        if yAxis_idx <= 1:
            radar_chart_json_dict["Y"] = [
                float(val) if isinstance(val, decimal.Decimal) else val
                for val in chart_data[column_name].values.tolist()
            ]

            underscore_index = column_name.find("_")

            # No Series
            if underscore_index == -1:
                if check_aggregation_phrases(
                    chart_axis[f"{column_name}_title"].replace("_", " "),
                ):
                    radar_chart_json_dict["yName"] = chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")
                elif f"{column_name}_aggregation" in chart_axis:
                    if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                        radar_chart_json_dict["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["AVG", "MEAN"]:
                        radar_chart_json_dict["yName"] = "Average " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                        radar_chart_json_dict["yName"] = "Median " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                        radar_chart_json_dict["yName"] = "Minimum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                        radar_chart_json_dict["yName"] = "Maximum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    else:
                        radar_chart_json_dict["yName"] = chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                else:
                    radar_chart_json_dict["yName"] = "Total " + chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")
            # Has Series
            else:
                original_column_name = column_name[:underscore_index]
                series_name = column_name[underscore_index + 1 :]

                # Add Series Title to Series Name
                if "series_title" in chart_axis and chart_axis["series_title"] != "":
                    series_name = f"""{chart_axis["series_title"]}: {series_name}"""

                if (
                    f"{original_column_name}_title" in chart_axis
                    and check_aggregation_phrases(
                        f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        ),
                    )
                ):
                    radar_chart_json_dict["yName"] = (
                        f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        )
                    )
                elif f"{original_column_name}_aggregation" in chart_axis:
                    if chart_axis[f"{original_column_name}_aggregation"] in ["SUM"]:
                        radar_chart_json_dict["yName"] = (
                            "Total "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in [
                        "AVG",
                        "MEAN",
                    ]:
                        radar_chart_json_dict["yName"] = (
                            "Average "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in [
                        "MEDIAN",
                    ]:
                        radar_chart_json_dict["yName"] = (
                            "Median "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in ["MIN"]:
                        radar_chart_json_dict["yName"] = (
                            "Minimum "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in ["MAX"]:
                        radar_chart_json_dict["yName"] = (
                            "Maximum "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    else:
                        radar_chart_json_dict["yName"] = (
                            "Total "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                else:
                    radar_chart_json_dict["yName"] = (
                        "Total "
                        + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        )
                    )

            if not (
                isinstance(radar_chart_json_dict["Y"][0], int)
                or isinstance(radar_chart_json_dict["Y"][0], float)
            ):
                code_level_logger.error("radar_chart: Y-axis is not integer or float!")
                raise RuntimeError("radar_chart: Y-axis is not integer or float!")

            # if check_negative_value(radar_chart_json_dict["Y"]):
            #     # radar_chart_json_dict["Chart_Type"] = "column_chart"
            #     radar_chart_json_dict["Chart_Type"] = "grouped_column_chart"
        else:
            radar_chart_json_dict[f"Y{yAxis_idx}"] = [
                float(val) if isinstance(val, decimal.Decimal) else val
                for val in chart_data[column_name].values.tolist()
            ]

            underscore_index = column_name.find("_")

            # No Series
            if underscore_index == -1:
                radar_chart_json_dict[f"y{yAxis_idx}Name"] = chart_axis[
                    f"{column_name}_title"
                ].replace("_", " ")
                if radar_chart_json_dict[f"y{yAxis_idx}Name"] == "":
                    radar_chart_json_dict[f"y{yAxis_idx}Name"] = radar_chart_json_dict[
                        "yName"
                    ]

                if not check_aggregation_phrases(
                    radar_chart_json_dict[f"y{yAxis_idx}Name"],
                ):
                    if f"{column_name}_aggregation" in chart_axis:
                        if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                            radar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Total " + radar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            radar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Average " + radar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                            radar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Median " + radar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                            radar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Minimum " + radar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                            radar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Maximum " + radar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        else:
                            radar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                radar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                    else:
                        radar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Total " + radar_chart_json_dict[f"y{yAxis_idx}Name"]
                        )
            # Has Series
            else:
                original_column_name = column_name[:underscore_index]
                series_name = column_name[underscore_index + 1 :]

                # Add Series Title to Series Name
                if "series_title" in chart_axis and chart_axis["series_title"] != "":
                    series_name = f"""{chart_axis["series_title"]}: {series_name}"""

                radar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                    f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                        "_",
                        " ",
                    )
                )
                if radar_chart_json_dict[f"y{yAxis_idx}Name"] == "":
                    radar_chart_json_dict[f"y{yAxis_idx}Name"] = radar_chart_json_dict[
                        "yName"
                    ]

                if not check_aggregation_phrases(
                    radar_chart_json_dict[f"y{yAxis_idx}Name"],
                ):
                    if f"{original_column_name}_aggregation" in chart_axis:
                        if chart_axis[f"{original_column_name}_aggregation"] in ["SUM"]:
                            radar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Total " + radar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            radar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Average " + radar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MEDIAN",
                        ]:
                            radar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Median " + radar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MIN",
                        ]:
                            radar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Minimum " + radar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MAX",
                        ]:
                            radar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Maximum " + radar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        else:
                            radar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Total " + radar_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                    else:
                        radar_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Total " + radar_chart_json_dict[f"y{yAxis_idx}Name"]
                        )

            if not (
                isinstance(radar_chart_json_dict[f"Y{yAxis_idx}"][0], int)
                or isinstance(radar_chart_json_dict[f"Y{yAxis_idx}"][0], float)
            ):
                code_level_logger.error(
                    f"radar_chart: Y{yAxis_idx}-axis is not integer or float!",
                )
                raise RuntimeError(
                    f"radar_chart: Y{yAxis_idx}-axis is not integer or float!",
                )

            # if (
            #     check_negative_value(radar_chart_json_dict[f"Y{yAxis_idx}"])
            #     or radar_chart_json_dict["Chart_Type"] == "column_chart"
            # ):
            #     radar_chart_json_dict["Chart_Type"] = "grouped_column_chart"

        yAxis_idx += 1

    if radar_chart_json_dict["Y"] == []:
        code_level_logger.error("radar_chart: Y-Axis is not found in extraction!")
        raise RuntimeError("radar_chart: Y-Axis is not found in extraction!")

    if any(
        radar_chart_json_dict[key] == [] or radar_chart_json_dict[key] == [""]
        for key in radar_chart_json_dict
        if re.match(r"^X\d*$", key)
    ):
        code_level_logger.error("radar_chart: One or more X-axis values are empty!")
        raise RuntimeError("radar_chart: One or more X-axis values are empty!")

    radar_chart_json_dict["Database_Identifier"] = database_properties["db_tag"]

    radar_chart_json_dict["Client_ID"] = client_id
    radar_chart_json_dict["User_ID"] = user_id
    radar_chart_json_dict["Session_ID"] = session_id

    if len(radar_chart_json_dict["Y"]) == 1 and radar_chart_json_dict["Y2"] == []:
        card_chart_json_dict: dict = generate_card_chart_d3(
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            radar_chart_json_dict["Chart_Type"],
            logging_url,
            code_level_logger,
        )
        return card_chart_json_dict

    return radar_chart_json_dict


def generate_area_chart_d3(
    llama70b_client: Any,
    user_query: str,
    chart_id: str,
    sql_query: str,
    chart_title: str,
    chart_axis: dict,
    chart_data: pd.DataFrame,
    database_properties: dict,
    ups_idx: int,
    chart_position: int,
    overall_title: str,
    client_id: str,
    user_id: str,
    session_id: str,
    sql_library: str,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    area_chart_json_dict: dict = AREA_CHART_TEMPLATE_D3.copy()
    area_chart_json_dict["User_Query"] = user_query
    area_chart_json_dict["Chart_Query"] = sql_query
    area_chart_json_dict["Chart_SQL_Library"] = sql_library
    area_chart_json_dict["Chart_Name"] = f"Visual {ups_idx}"
    area_chart_json_dict["Chart_Axis"] = chart_axis
    area_chart_json_dict["Visual_Title"] = overall_title
    area_chart_json_dict["Chart_ID"] = chart_id
    area_chart_json_dict["Chart_Type"] = "area_chart"
    area_chart_json_dict["Chart_Position"] = str(chart_position)
    area_chart_json_dict["Chart_Title"] = chart_title

    area_chart_json_dict["xAxis"] = chart_axis["xAxis_title"].replace("_", " ")

    area_chart_json_dict["Aggregated_Table_JSON"] = generate_aggregated_table_chart_d3(
        user_query,
        sql_query,
        chart_id,
        chart_title,
        chart_data,
        database_properties,
        ups_idx,
        chart_position,
        overall_title,
        client_id,
        user_id,
        session_id,
        sql_library,
        chart_axis,
        area_chart_json_dict["Chart_Type"],
        code_level_logger,
    )
    area_chart_json_dict["Aggregated_Table_Column"] = get_aggregated_columns(chart_axis)

    yAxis_title = ""

    for chart_axis_key in chart_axis:
        if (
            chart_axis_key.lower()[0] != "y"
            or "title" not in chart_axis_key.lower()
            or chart_axis[chart_axis_key] == ""
        ):
            continue
        if yAxis_title == "":
            yAxis_title += chart_axis[chart_axis_key]
        else:
            # yAxis_title += f"/{chart_axis[chart_axis_key]}"
            yAxis_title = "Amount"
            break

    if (
        check_aggregation_phrases(yAxis_title.replace("_", " "))
        or yAxis_title == "Amount"
    ):
        area_chart_json_dict["yAxis"] = yAxis_title.replace("_", " ")
    elif "yAxis_aggregation" in chart_axis:
        if chart_axis["yAxis_aggregation"] in ["SUM"]:
            area_chart_json_dict["yAxis"] = "Total " + yAxis_title.replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
            area_chart_json_dict["yAxis"] = "Average " + yAxis_title.replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
            area_chart_json_dict["yAxis"] = "Median " + yAxis_title.replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["MIN"]:
            area_chart_json_dict["yAxis"] = "Minimum " + yAxis_title.replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["MAX"]:
            area_chart_json_dict["yAxis"] = "Maximum " + yAxis_title.replace(
                "_",
                " ",
            )
        else:
            area_chart_json_dict["yAxis"] = "Total " + yAxis_title.replace("_", " ")
    else:
        area_chart_json_dict["yAxis"] = "Total " + yAxis_title.replace("_", " ")

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
        code_level_logger.error("area_chart: X-Axis is not found in extraction!")
        raise RuntimeError("area_chart: X-Axis is not found in extraction!")

    if "series" in chart_data_columns:
        series_column_name = "series"
    elif (
        "series_column" in chart_axis
        and isinstance(chart_axis["series_column"], str)
        and chart_axis["series_column"] in chart_data_columns
    ):
        series_column_name = chart_axis["series_column"]
    else:
        series_column_name = ""

    object_columns = chart_data.select_dtypes(include=[object])

    yAxis_column_names = list(chart_data.columns)
    yAxis_column_names.remove(xAxis_column_name)
    if series_column_name in yAxis_column_names:
        yAxis_column_names.remove(series_column_name)

    for yAxis_column_name in yAxis_column_names:
        if yAxis_column_name in object_columns:
            try:
                if not isinstance(
                    chart_data[yAxis_column_name].values.tolist(),
                    datetime.date,
                ) and not isinstance(
                    chart_data[yAxis_column_name].values.tolist(),
                    datetime.datetime,
                ):
                    if isinstance(chart_data[yAxis_column_name].values.tolist(), str):
                        chart_data[yAxis_column_name] = chart_data[
                            yAxis_column_name
                        ].replace("%", "", regex=True)
                    chart_data[yAxis_column_name] = pd.to_numeric(
                        chart_data[yAxis_column_name],
                    )
            except Exception:
                code_level_logger.error(
                    f"area_chart: {yAxis_column_name} is not numerical!"
                )
                raise RuntimeError(f"area_chart: {yAxis_column_name} is not numerical!")

    if (
        series_column_name != ""
        and series_column_name in chart_data.columns
        and chart_data[series_column_name].nunique() > 1
    ):
        new_chart_data = pd.DataFrame()

        pivot_data = chart_data.pivot_table(
            index=xAxis_column_name,
            columns=series_column_name,
            values=yAxis_column_names,
        )
        pivot_data = pivot_data.reset_index()
        new_chart_data[xAxis_column_name] = pivot_data[
            xAxis_column_name
        ].values.tolist()

        for yAxis_column_name in yAxis_column_names:
            yAxis_pivot_table = pivot_data[yAxis_column_name]
            for yAxis_pivot_column in list(yAxis_pivot_table.columns):
                new_columns = {
                    f"{yAxis_column_name}_{yAxis_pivot_column}": yAxis_pivot_table[
                        yAxis_pivot_column
                    ].values.tolist(),
                }
                added_chart_data = pd.DataFrame(new_columns)
                new_chart_data = pd.concat([new_chart_data, added_chart_data], axis=1)

        chart_data = new_chart_data.fillna(
            {
                col: (
                    0 if new_chart_data[col].dtype in [np.float64, np.int64] else "null"
                )
                for col in new_chart_data.columns
            },
        )

    if (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{4}-\d{2}-\d{2}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%Y-%m-%d",
        )
    elif (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{2}/\d{2}/\d{4}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%d/%m/%Y",
        )

    if all(
        isinstance(val, (datetime.date, datetime.datetime))
        for val in chart_data[xAxis_column_name]
    ):
        chart_data, new_chart_axis, new_chart_title = adjust_axis_title_and_data(
            llama70b_client,
            chart_id,
            chart_data,
            chart_axis,
            chart_title,
            logging_url,
        )
        area_chart_json_dict["xAxis"] = new_chart_axis["xAxis_title"].replace("_", " ")
        area_chart_json_dict["Chart_Title"] = new_chart_title

    try:
        if len(chart_data[xAxis_column_name][0].split("-")) == 1:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                ),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (
                        int(date.split("-")[0]),
                        int(date.split("-")[1]),
                        int(date.split("-")[2]),
                    ),
                ),
            )
        else:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)
    except Exception:
        chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

    if isinstance(xAxis_column_name, str):
        chart_data = sort_pandas_date(chart_data, xAxis_column_name)

    area_chart_json_dict["X"] = [
        str(x_data) for x_data in chart_data[xAxis_column_name].values.tolist()
    ]

    if len(area_chart_json_dict["X"]) >= 1 and len(area_chart_json_dict["X"]) <= 2:
        return generate_group_bar_chart_d3(
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            logging_url,
            code_level_logger,
        )

    yAxis_idx = 1

    for column_name in list(chart_data.columns):
        if not re.search(r"yAxis([23456789])?", column_name, re.IGNORECASE):
            continue

        if yAxis_idx <= 1:
            area_chart_json_dict["Y"] = [
                float(val) if isinstance(val, decimal.Decimal) else val
                for val in chart_data[column_name].values.tolist()
            ]

            underscore_index = column_name.find("_")

            # No Series
            if underscore_index == -1:
                if check_aggregation_phrases(
                    chart_axis[f"{column_name}_title"].replace("_", " "),
                ):
                    area_chart_json_dict["yName"] = chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")
                elif f"{column_name}_aggregation" in chart_axis:
                    if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                        area_chart_json_dict["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["AVG", "MEAN"]:
                        area_chart_json_dict["yName"] = "Average " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                        area_chart_json_dict["yName"] = "Median " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                        area_chart_json_dict["yName"] = "Minimum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                        area_chart_json_dict["yName"] = "Maximum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    else:
                        area_chart_json_dict["yName"] = chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                else:
                    area_chart_json_dict["yName"] = "Total " + chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")
            # Has Series
            else:
                original_column_name = column_name[:underscore_index]
                series_name = column_name[underscore_index + 1 :]

                # Add Series Title to Series Name
                if "series_title" in chart_axis and chart_axis["series_title"] != "":
                    series_name = f"""{chart_axis["series_title"]}: {series_name}"""

                if (
                    f"{original_column_name}_title" in chart_axis
                    and check_aggregation_phrases(
                        f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        ),
                    )
                ):
                    area_chart_json_dict["yName"] = (
                        f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        )
                    )
                elif f"{original_column_name}_aggregation" in chart_axis:
                    if chart_axis[f"{original_column_name}_aggregation"] in ["SUM"]:
                        area_chart_json_dict["yName"] = (
                            "Total "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in [
                        "AVG",
                        "MEAN",
                    ]:
                        area_chart_json_dict["yName"] = (
                            "Average "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in [
                        "MEDIAN",
                    ]:
                        area_chart_json_dict["yName"] = (
                            "Median "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in ["MIN"]:
                        area_chart_json_dict["yName"] = (
                            "Minimum "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in ["MAX"]:
                        area_chart_json_dict["yName"] = (
                            "Maximum "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    else:
                        area_chart_json_dict["yName"] = (
                            "Total "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                else:
                    area_chart_json_dict["yName"] = (
                        "Total "
                        + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        )
                    )

            if not (
                isinstance(area_chart_json_dict["Y"][0], int)
                or isinstance(area_chart_json_dict["Y"][0], float)
            ):
                code_level_logger.error("area_chart: Y-axis is not integer or float!")
                raise RuntimeError("area_chart: Y-axis is not integer or float!")

            # if check_negative_value(area_chart_json_dict["Y"]):
            #     # area_chart_json_dict["Chart_Type"] = "column_chart"
            #     area_chart_json_dict["Chart_Type"] = "grouped_column_chart"
        else:
            area_chart_json_dict[f"Y{yAxis_idx}"] = [
                float(val) if isinstance(val, decimal.Decimal) else val
                for val in chart_data[column_name].values.tolist()
            ]

            underscore_index = column_name.find("_")

            # No Series
            if underscore_index == -1:
                area_chart_json_dict[f"y{yAxis_idx}Name"] = chart_axis[
                    f"{column_name}_title"
                ].replace("_", " ")
                if area_chart_json_dict[f"y{yAxis_idx}Name"] == "":
                    area_chart_json_dict[f"y{yAxis_idx}Name"] = area_chart_json_dict[
                        "yName"
                    ]

                if not check_aggregation_phrases(
                    area_chart_json_dict[f"y{yAxis_idx}Name"],
                ):
                    if f"{column_name}_aggregation" in chart_axis:
                        if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                            area_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Total " + area_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            area_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Average " + area_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                            area_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Median " + area_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                            area_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Minimum " + area_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                            area_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Maximum " + area_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        else:
                            area_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                area_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                    else:
                        area_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Total " + area_chart_json_dict[f"y{yAxis_idx}Name"]
                        )
            # Has Series
            else:
                original_column_name = column_name[:underscore_index]
                series_name = column_name[underscore_index + 1 :]

                # Add Series Title to Series Name
                if "series_title" in chart_axis and chart_axis["series_title"] != "":
                    series_name = f"""{chart_axis["series_title"]}: {series_name}"""

                area_chart_json_dict[f"y{yAxis_idx}Name"] = (
                    f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                        "_",
                        " ",
                    )
                )
                if area_chart_json_dict[f"y{yAxis_idx}Name"] == "":
                    area_chart_json_dict[f"y{yAxis_idx}Name"] = area_chart_json_dict[
                        "yName"
                    ]

                if not check_aggregation_phrases(
                    area_chart_json_dict[f"y{yAxis_idx}Name"],
                ):
                    if f"{original_column_name}_aggregation" in chart_axis:
                        if chart_axis[f"{original_column_name}_aggregation"] in ["SUM"]:
                            area_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Total " + area_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            area_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Average " + area_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MEDIAN",
                        ]:
                            area_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Median " + area_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MIN",
                        ]:
                            area_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Minimum " + area_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MAX",
                        ]:
                            area_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Maximum " + area_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                        else:
                            area_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                "Total " + area_chart_json_dict[f"y{yAxis_idx}Name"]
                            )
                    else:
                        area_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Total " + area_chart_json_dict[f"y{yAxis_idx}Name"]
                        )

            if not (
                isinstance(area_chart_json_dict[f"Y{yAxis_idx}"][0], int)
                or isinstance(area_chart_json_dict[f"Y{yAxis_idx}"][0], float)
            ):
                code_level_logger.error(
                    f"area_chart: Y{yAxis_idx}-axis is not integer or float!",
                )
                raise RuntimeError(
                    f"area_chart: Y{yAxis_idx}-axis is not integer or float!",
                )

            # if (
            #     check_negative_value(area_chart_json_dict[f"Y{yAxis_idx}"])
            #     or area_chart_json_dict["Chart_Type"] == "column_chart"
            # ):
            #     area_chart_json_dict["Chart_Type"] = "grouped_column_chart"

        yAxis_idx += 1

    if area_chart_json_dict["Y"] == []:
        code_level_logger.error("area_chart: Y-Axis is not found in extraction!")
        raise RuntimeError("area_chart: Y-Axis is not found in extraction!")

    if any(
        area_chart_json_dict[key] == [] or area_chart_json_dict[key] == [""]
        for key in area_chart_json_dict
        if re.match(r"^X\d*$", key)
    ):
        code_level_logger.error("area_chart: One or more X-axis values are empty!")
        raise RuntimeError("area_chart: One or more X-axis values are empty!")

    area_chart_json_dict["Database_Identifier"] = database_properties["db_tag"]

    area_chart_json_dict["Client_ID"] = client_id
    area_chart_json_dict["User_ID"] = user_id
    area_chart_json_dict["Session_ID"] = session_id

    if len(area_chart_json_dict["Y"]) == 1 and area_chart_json_dict["Y2"] == []:
        card_chart_json_dict: dict = generate_card_chart_d3(
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            area_chart_json_dict["Chart_Type"],
            logging_url,
            code_level_logger,
        )
        return card_chart_json_dict

    return area_chart_json_dict


def generate_histogram_chart_d3(
    llama70b_client: Any,
    user_query: str,
    chart_id: str,
    sql_query: str,
    chart_title: str,
    chart_axis: dict,
    chart_data: pd.DataFrame,
    database_properties: dict,
    ups_idx: int,
    chart_position: int,
    overall_title: str,
    client_id: str,
    user_id: str,
    session_id: str,
    sql_library: str,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    histogram_chart_json_dict: dict = HISTOGRAM_CHART_TEMPLATE_D3.copy()
    histogram_chart_json_dict["User_Query"] = user_query
    histogram_chart_json_dict["Chart_Query"] = sql_query
    histogram_chart_json_dict["Chart_SQL_Library"] = sql_library
    histogram_chart_json_dict["Chart_Name"] = f"Visual {ups_idx}"
    histogram_chart_json_dict["Chart_Axis"] = chart_axis
    histogram_chart_json_dict["Visual_Title"] = overall_title
    histogram_chart_json_dict["Chart_ID"] = chart_id
    histogram_chart_json_dict["Chart_Type"] = "histogram_chart"
    histogram_chart_json_dict["Number_of_Bins"] = calculate_bins(chart_data)
    histogram_chart_json_dict["Chart_Position"] = str(chart_position)
    histogram_chart_json_dict["Chart_Title"] = chart_title
    histogram_chart_json_dict["xAxis"] = chart_axis["xAxis_title"].replace("_", " ")
    if histogram_chart_json_dict["xAxis"] == "":
        histogram_chart_json_dict["xAxis"] = "Distribution"

    histogram_chart_json_dict["yAxis"] = "Frequency"
    histogram_chart_json_dict["Chart_Data"] = []
    histogram_chart_json_dict["Aggregated_Table_JSON"] = (
        generate_aggregated_table_chart_d3(
            user_query,
            sql_query,
            chart_id,
            chart_title,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            chart_axis,
            histogram_chart_json_dict["Chart_Type"],
            code_level_logger,
        )
    )
    histogram_chart_json_dict["Aggregated_Table_Column"] = get_aggregated_columns(
        chart_axis,
    )
    histogram_chart_json_dict["Database_Identifier"] = database_properties["db_tag"]

    chart_data_columns = list(chart_data.columns)

    if "xAxis" in chart_data_columns:
        xAxis_column_name = "xAxis"
        if (
            isinstance(
                chart_data[xAxis_column_name].values.tolist()[0],
                (str, datetime.datetime, datetime.date),
            )
        ) and len(chart_data_columns) > 1:
            chart_data_columns.remove(xAxis_column_name)
    elif "yAxis" in chart_data_columns:
        xAxis_column_name = "yAxis"
    elif (
        "xAxis_column" in chart_axis
        and isinstance(chart_axis["xAxis_column"], str)
        and chart_axis["xAxis_column"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_column"]
        if (
            isinstance(
                chart_data[xAxis_column_name].values.tolist()[0],
                (str, datetime.datetime, datetime.date),
            )
        ) and len(chart_data_columns) > 1:
            chart_data_columns.remove(xAxis_column_name)
    elif (
        "xAxis_column" in chart_axis
        and isinstance(chart_axis["xAxis_column"], list)
        and all(elem in chart_data_columns for elem in chart_axis["xAxis_column"])
    ):
        xAxis_column_names = chart_axis["xAxis_column"]
        for xAxis_column_name in xAxis_column_names:
            if (
                isinstance(
                    chart_data[xAxis_column_name].values.tolist()[0],
                    (str, datetime.datetime, datetime.date),
                )
            ) and len(chart_data_columns) > 1:
                chart_data_columns.remove(xAxis_column_name)
    elif (
        "xAxis_title" in chart_axis and chart_axis["xAxis_title"] in chart_data.columns
    ) or (
        "xAxis_title" in chart_axis and chart_axis["xAxis_title"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_title"]
        if (
            isinstance(
                chart_data[xAxis_column_name].values.tolist()[0],
                (str, datetime.datetime, datetime.date),
            )
        ) and len(chart_data_columns) > 1:
            chart_data_columns.remove(xAxis_column_name)
    else:
        code_level_logger.error("histogram_chart: X-Axis is not found in extraction!")
        raise RuntimeError("histogram_chart: X-Axis is not found in extraction!")

    for chart_column_name in chart_data_columns:
        try:
            if not isinstance(
                chart_data[chart_column_name].values.tolist()[0],
                datetime.date,
            ) and not isinstance(
                chart_data[chart_column_name].values.tolist()[0],
                datetime.datetime,
            ):
                if isinstance(chart_data[chart_column_name].values.tolist()[0], str):
                    chart_data[chart_column_name] = chart_data[
                        chart_column_name
                    ].replace("%", "", regex=True)
                chart_data[chart_column_name] = pd.to_numeric(
                    chart_data[chart_column_name],
                )
                chart_column_data = chart_data[chart_column_name].values.tolist()

                histogram_chart_json_dict["Chart_Data"] = [
                    {"X_Value": x} for x in chart_column_data
                ]
                break

        except Exception:
            print(traceback.format_exc())

    # if "xAxis_title" in chart_axis.keys() and chart_axis["xAxis_title"] != "":
    #     histogram_chart_json_dict["yName"] = (
    #         f"Frequency of {chart_axis['xAxis_title']}".replace("_", " ")
    #     )
    # else:
    #     histogram_chart_json_dict["yName"] = f"Frequency"

    if histogram_chart_json_dict["Chart_Data"] == []:
        code_level_logger.error("histogram_chart: Chart data is empty!")
        raise RuntimeError("histogram_chart: Chart data is empty!")

    if isinstance(histogram_chart_json_dict["xAxis"], list):
        histogram_chart_json_dict["xAxis"] = " ".join(
            histogram_chart_json_dict["xAxis"],
        )

    if isinstance(histogram_chart_json_dict["yAxis"], list):
        histogram_chart_json_dict["yAxis"] = " ".join(
            histogram_chart_json_dict["yAxis"],
        )

    if any(
        histogram_chart_json_dict[key] == [] or histogram_chart_json_dict[key] == [""]
        for key in histogram_chart_json_dict
        if re.match(r"^X\d*$", key)
    ):
        code_level_logger.error("histogram_chart: One or more X-axis values are empty!")
        raise RuntimeError("histogram_chart: One or more X-axis values are empty!")

    histogram_chart_json_dict["Client_ID"] = client_id
    histogram_chart_json_dict["User_ID"] = user_id
    histogram_chart_json_dict["Session_ID"] = session_id

    return histogram_chart_json_dict


def generate_table_chart_d3(
    llama70b_client: Any,
    user_query: str,
    chart_id: str,
    sql_query: str,
    chart_title: str,
    chart_axis: dict,
    chart_data: pd.DataFrame,
    database_properties: dict,
    ups_idx: int,
    chart_position: int,
    overall_title: str,
    client_id: str,
    user_id: str,
    session_id: str,
    sql_library: str,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    table_chart_json_dict: dict = TABLE_CHART_TEMPLATE_D3.copy()
    table_chart_json_dict["User_Query"] = user_query
    table_chart_json_dict["Chart_Name"] = f"Visual {ups_idx}"
    table_chart_json_dict["Chart_SQL_Library"] = sql_library
    table_chart_json_dict["Visual_Title"] = overall_title
    table_chart_json_dict["Chart_ID"] = chart_id
    table_chart_json_dict["Chart_Axis"] = chart_axis
    table_chart_json_dict["Chart_Query"] = sql_query
    table_chart_json_dict["Chart_Position"] = str(chart_position)
    table_chart_json_dict["Chart_Type"] = "table_chart"
    table_chart_json_dict["Chart_Title"] = chart_title
    table_chart_json_dict["data"] = []

    column_names = list(chart_data.columns)

    for column in column_names:
        if chart_data[column].dtype == object or (
            np.issubdtype(chart_data[column].dtype, np.number)
            and chart_data[column].nunique() < 12
        ):
            chart_data = chart_data.dropna(subset=[column])
            break

    chart_data = chart_data.fillna("NaN")

    if "xAxis" in column_names:
        xAxis_column_name = "xAxis"
    elif (
        "xAxis_column" in chart_axis
        and isinstance(chart_axis["xAxis_column"], str)
        and chart_axis["xAxis_column"] in column_names
    ):
        xAxis_column_name = chart_axis["xAxis_column"]
    elif (
        "xAxis_title" in chart_axis and chart_axis["xAxis_title"] in chart_data.columns
    ):
        xAxis_column_name = chart_axis["xAxis_title"]
    else:
        xAxis_column_name = column_names[0]

    try:
        if len(chart_data[xAxis_column_name][0].split("-")) == 1:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                ),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (
                        int(date.split("-")[0]),
                        int(date.split("-")[1]),
                        int(date.split("-")[2]),
                    ),
                ),
            )
        else:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)
    except Exception:
        chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

    if isinstance(xAxis_column_name, str):
        chart_data = sort_pandas_date(chart_data, xAxis_column_name)

    chart_data_values = chart_data.values.tolist()

    for row in chart_data_values:
        row_data = {}
        for column_idx, column_name in enumerate(column_names):
            try:
                if column_name == "xAxis" or (
                    "xAxis_column" in chart_axis
                    and column_name in chart_axis["xAxis_column"]
                ):
                    new_column_name = chart_axis["xAxis_title"]
                elif column_name == "yAxis" or (
                    "yAxis_column" in chart_axis
                    and column_name in chart_axis["yAxis_column"]
                ):
                    new_column_name = chart_axis["yAxis_title"]
                else:
                    new_column_name = column_name
            except Exception:
                new_column_name = column_name

            new_column_name = new_column_name.replace("_", " ")

            try:
                if isinstance(row[column_idx], int):
                    # row_data[new_column_name] = '{:,}'.format(row[column_idx])
                    row_data[new_column_name] = row[column_idx]
                elif isinstance(row[column_idx], float):
                    # row_data[new_column_name] = '{:,}'.format(row[column_idx])
                    # Round off to 6 decimal points
                    row_data[new_column_name] = round(row[column_idx], 6)
                elif isinstance(row[column_idx], decimal.Decimal):
                    # row_data[new_column_name] = '{:,}'.format(float(row[column_idx]))
                    # Round off to 6 decimal points
                    row_data[new_column_name] = round(float(row[column_idx]), 6)
                # elif pd.api.types.is_datetime64_any_dtype(row[column_idx]):
                #     row_data[new_column_name] = row[column_idx].astype(str)
                elif (
                    isinstance(row[column_idx], datetime.date)
                    or isinstance(row[column_idx], datetime.datetime)
                ) and not pd.isnull(row[column_idx]):
                    row_data[new_column_name] = row[column_idx].strftime("%m/%d/%Y")
                else:
                    row_data[new_column_name] = str(row[column_idx])
            except Exception:
                row_data[new_column_name] = str(row[column_idx])
        table_chart_json_dict["data"].append(row_data)

    table_chart_json_dict["Chart_Size"] = sys.getsizeof(table_chart_json_dict["data"])

    table_chart_json_dict["Database_Identifier"] = database_properties["db_tag"]

    table_chart_json_dict["Client_ID"] = client_id
    table_chart_json_dict["User_ID"] = user_id
    table_chart_json_dict["Session_ID"] = session_id

    return table_chart_json_dict


def generate_pie_chart_d3(
    llama70b_client: Any,
    user_query: str,
    chart_id: str,
    sql_query: str,
    chart_title: str,
    chart_axis: dict,
    chart_data: pd.DataFrame,
    database_properties: dict,
    ups_idx: int,
    chart_position: int,
    overall_title: str,
    client_id: str,
    user_id: str,
    session_id: str,
    sql_library: str,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    pie_chart_json_dict: dict = PIE_CHART_TEMPLATE_D3.copy()
    pie_chart_json_dict["User_Query"] = user_query
    pie_chart_json_dict["Chart_Query"] = sql_query
    pie_chart_json_dict["Chart_SQL_Library"] = sql_library
    pie_chart_json_dict["Chart_Name"] = f"Visual {ups_idx}"
    pie_chart_json_dict["Visual_Title"] = overall_title
    pie_chart_json_dict["Chart_ID"] = chart_id
    pie_chart_json_dict["Chart_Axis"] = chart_axis
    pie_chart_json_dict["Chart_Type"] = "pie_chart"
    pie_chart_json_dict["Chart_Position"] = str(chart_position)
    pie_chart_json_dict["Chart_Title"] = chart_title
    pie_chart_json_dict["xAxis"] = chart_axis["xAxis_title"].replace("_", " ")
    if check_aggregation_phrases(chart_axis["yAxis_title"].replace("_", " ")):
        pie_chart_json_dict["yAxis"] = chart_axis["yAxis_title"].replace("_", " ")
        pie_chart_json_dict["yName"] = chart_axis["yAxis_title"].replace("_", " ")
    elif "yAxis_aggregation" in chart_axis:
        if chart_axis["yAxis_aggregation"] in ["SUM"]:
            pie_chart_json_dict["yAxis"] = "Total " + chart_axis["yAxis_title"].replace(
                "_",
                " ",
            )
            pie_chart_json_dict["yName"] = "Total " + chart_axis["yAxis_title"].replace(
                "_",
                " ",
            )
        elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
            pie_chart_json_dict["yAxis"] = "Average " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            pie_chart_json_dict["yName"] = "Average " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
            pie_chart_json_dict["yAxis"] = "Median " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            pie_chart_json_dict["yName"] = "Median " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["MIN"]:
            pie_chart_json_dict["yAxis"] = "Minimum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            pie_chart_json_dict["yName"] = "Minimum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["MAX"]:
            pie_chart_json_dict["yAxis"] = "Maximum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            pie_chart_json_dict["yName"] = "Maximum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        else:
            pie_chart_json_dict["yAxis"] = "Total " + chart_axis["yAxis_title"].replace(
                "_",
                " ",
            )
            pie_chart_json_dict["yName"] = "Total " + chart_axis["yAxis_title"].replace(
                "_",
                " ",
            )
    else:
        pie_chart_json_dict["yAxis"] = "Total " + chart_axis["yAxis_title"].replace(
            "_",
            " ",
        )
        pie_chart_json_dict["yName"] = "Total " + chart_axis["yAxis_title"].replace(
            "_",
            " ",
        )

    pie_chart_json_dict["Aggregated_Table_JSON"] = generate_aggregated_table_chart_d3(
        user_query,
        sql_query,
        chart_id,
        chart_title,
        chart_data,
        database_properties,
        ups_idx,
        chart_position,
        overall_title,
        client_id,
        user_id,
        session_id,
        sql_library,
        chart_axis,
        pie_chart_json_dict["Chart_Type"],
        code_level_logger,
    )
    pie_chart_json_dict["Aggregated_Table_Column"] = get_aggregated_columns(chart_axis)
    pie_chart_json_dict["Database_Identifier"] = database_properties["db_tag"]

    sorted_chart_data = chart_data.copy()
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
        code_level_logger.error("pie_chart: X-Axis is not found in extraction!")
        raise RuntimeError("pie_chart: X-Axis is not found in extraction!")

    if "yAxis" in chart_data_columns:
        yAxis_column_name = "yAxis"
    elif (
        "yAxis_column" in chart_axis
        and isinstance(chart_axis["yAxis_column"], str)
        and chart_axis["yAxis_column"] in chart_data_columns
    ):
        yAxis_column_name = chart_axis["yAxis_column"]
    else:
        code_level_logger.error("pie_chart: Y-Axis is not found in extraction!")
        raise RuntimeError("pie_chart: Y-Axis is not found in extraction!")

    object_columns = chart_data.select_dtypes(include=[object])

    if yAxis_column_name in object_columns:
        try:
            if not isinstance(
                chart_data[yAxis_column_name].values.tolist(),
                datetime.date,
            ) and not isinstance(
                chart_data[yAxis_column_name].values.tolist(),
                datetime.datetime,
            ):
                if isinstance(chart_data[yAxis_column_name].values.tolist(), str):
                    chart_data[yAxis_column_name] = chart_data[
                        yAxis_column_name
                    ].replace("%", "", regex=True)
                chart_data[yAxis_column_name] = pd.to_numeric(
                    chart_data[yAxis_column_name],
                )
        except Exception:
            code_level_logger.error(f"pie_chart: {yAxis_column_name} is not numerical!")
            raise RuntimeError(f"pie_chart: {yAxis_column_name} is not numerical!")

    try:
        if len(chart_data[xAxis_column_name][0].split("-")) == 1:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                ),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (
                        int(date.split("-")[0]),
                        int(date.split("-")[1]),
                        int(date.split("-")[2]),
                    ),
                ),
            )
        else:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)
    except Exception:
        chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

    if len(pie_chart_json_dict["Chart_Data"]) > 12:
        bar_chart_json_dict: dict = generate_group_bar_chart_d3(
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            logging_url,
            code_level_logger,
        )
        return bar_chart_json_dict

    y_values = chart_data[yAxis_column_name].values.tolist()

    if 0 in y_values or 0.0 in y_values:
        return generate_group_bar_chart_d3(
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            logging_url,
            code_level_logger,
        )

    sorted_chart_data = sorted_chart_data.sort_values(
        by=yAxis_column_name,
        ascending=False,
    )

    if (
        not isinstance(
            sorted_chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            sorted_chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{4}-\d{2}-\d{2}$",
            str(sorted_chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        sorted_chart_data[xAxis_column_name] = pd.to_datetime(
            sorted_chart_data[xAxis_column_name],
            format="%Y-%m-%d",
        )
    elif (
        not isinstance(
            sorted_chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            sorted_chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{2}/\d{2}/\d{4}$",
            str(sorted_chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        sorted_chart_data[xAxis_column_name] = pd.to_datetime(
            sorted_chart_data[xAxis_column_name],
            format="%d/%m/%Y",
        )

    if all(
        isinstance(val, (datetime.date, datetime.datetime))
        for val in sorted_chart_data[xAxis_column_name]
    ):
        sorted_chart_data, new_chart_axis, new_chart_title = adjust_axis_title_and_data(
            llama70b_client,
            chart_id,
            chart_data,
            chart_axis,
            chart_title,
            logging_url,
        )
        pie_chart_json_dict["xAxis"] = new_chart_axis["xAxis_title"].replace("_", " ")
        pie_chart_json_dict["Chart_Title"] = new_chart_title

    try:
        if len(chart_data[xAxis_column_name][0].split("-")) == 1:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                ),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (
                        int(date.split("-")[0]),
                        int(date.split("-")[1]),
                        int(date.split("-")[2]),
                    ),
                ),
            )
        else:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)
    except Exception:
        chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

    if isinstance(xAxis_column_name, str):
        chart_data = sort_pandas_date(chart_data, xAxis_column_name)

    pie_chart_json_dict["Chart_Data"] = []
    for group_name, y_value in zip(
        sorted_chart_data[xAxis_column_name].values.tolist(),
        sorted_chart_data[yAxis_column_name].values.tolist(),
    ):
        pie_chart_json_dict["Chart_Data"].append(
            {
                "Group_Name": str(group_name),
                "Y_Value": (
                    float(y_value) if isinstance(y_value, decimal.Decimal) else y_value
                ),
            },
        )

    # if not (
    #     isinstance(pie_chart_json_dict["Y"][0], int)
    #     or isinstance(pie_chart_json_dict["Y"][0], float)
    # ):
    #     code_level_logger.error("pie_chart: Y-axis is not integer or float!")
    #     raise RuntimeError("pie_chart: Y-axis is not integer or float!")

    # if check_negative_value(pie_chart_json_dict["Y"]):
    #     # pie_chart_json_dict["Chart_Type"] = "column_chart"
    #     pie_chart_json_dict["Chart_Type"] = "grouped_column_chart"

    if isinstance(pie_chart_json_dict["xAxis"], list):
        pie_chart_json_dict["xAxis"] = " ".join(pie_chart_json_dict["xAxis"])

    if isinstance(pie_chart_json_dict["yAxis"], list):
        pie_chart_json_dict["yAxis"] = " ".join(pie_chart_json_dict["yAxis"])

    if any(
        pie_chart_json_dict[key] == [] or pie_chart_json_dict[key] == [""]
        for key in pie_chart_json_dict
        if re.match(r"^X\d*$", key)
    ):
        code_level_logger.error("pie_chart: One or more X-axis values are empty!")
        raise RuntimeError("pie_chart: One or more X-axis values are empty!")

    pie_chart_json_dict["Client_ID"] = client_id
    pie_chart_json_dict["User_ID"] = user_id
    pie_chart_json_dict["Session_ID"] = session_id

    if len(y_values) == 1:
        card_chart_json_dict: dict = generate_card_chart_d3(
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            pie_chart_json_dict["Chart_Type"],
            logging_url,
            code_level_logger,
        )
        return card_chart_json_dict

    return pie_chart_json_dict


def generate_pyramid_chart_d3(
    llama70b_client: Any,
    user_query: str,
    chart_id: str,
    sql_query: str,
    chart_title: str,
    chart_axis: dict,
    chart_data: pd.DataFrame,
    database_properties: dict,
    ups_idx: int,
    chart_position: int,
    overall_title: str,
    client_id: str,
    user_id: str,
    session_id: str,
    sql_library: str,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    pyramid_chart_json_dict: dict = PYRAMIDFUNNEL_CHART_TEMPLATE_D3.copy()
    pyramid_chart_json_dict["User_Query"] = user_query
    pyramid_chart_json_dict["Chart_Query"] = sql_query
    pyramid_chart_json_dict["Chart_SQL_Library"] = sql_library
    pyramid_chart_json_dict["Chart_Name"] = f"Visual {ups_idx}"
    pyramid_chart_json_dict["Visual_Title"] = overall_title
    pyramid_chart_json_dict["Chart_ID"] = chart_id
    pyramid_chart_json_dict["Chart_Axis"] = chart_axis
    pyramid_chart_json_dict["Chart_Type"] = "pyramidfunnel_chart"
    pyramid_chart_json_dict["Chart_Position"] = str(chart_position)
    pyramid_chart_json_dict["Chart_Title"] = chart_title
    pyramid_chart_json_dict["xAxis"] = chart_axis["xAxis_title"].replace("_", " ")
    if check_aggregation_phrases(chart_axis["yAxis_title"].replace("_", " ")):
        pyramid_chart_json_dict["yAxis"] = chart_axis["yAxis_title"].replace("_", " ")
        pyramid_chart_json_dict["yName"] = chart_axis["yAxis_title"].replace("_", " ")
    elif "yAxis_aggregation" in chart_axis:
        if chart_axis["yAxis_aggregation"] in ["SUM"]:
            pyramid_chart_json_dict["yAxis"] = "Total " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            pyramid_chart_json_dict["yName"] = "Total " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
            pyramid_chart_json_dict["yAxis"] = "Average " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            pyramid_chart_json_dict["yName"] = "Average " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
            pyramid_chart_json_dict["yAxis"] = "Median " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            pyramid_chart_json_dict["yName"] = "Median " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["MIN"]:
            pyramid_chart_json_dict["yAxis"] = "Minimum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            pyramid_chart_json_dict["yName"] = "Minimum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["MAX"]:
            pyramid_chart_json_dict["yAxis"] = "Maximum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            pyramid_chart_json_dict["yName"] = "Maximum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        else:
            pyramid_chart_json_dict["yAxis"] = "Total " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            pyramid_chart_json_dict["yName"] = "Total " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
    else:
        pyramid_chart_json_dict["yAxis"] = "Total " + chart_axis["yAxis_title"].replace(
            "_",
            " ",
        )
        pyramid_chart_json_dict["yName"] = "Total " + chart_axis["yAxis_title"].replace(
            "_",
            " ",
        )

    pyramid_chart_json_dict["Aggregated_Table_JSON"] = (
        generate_aggregated_table_chart_d3(
            user_query,
            sql_query,
            chart_id,
            chart_title,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            chart_axis,
            pyramid_chart_json_dict["Chart_Type"],
            code_level_logger,
        )
    )
    pyramid_chart_json_dict["Aggregated_Table_Column"] = get_aggregated_columns(
        chart_axis,
    )
    pyramid_chart_json_dict["Database_Identifier"] = database_properties["db_tag"]
    sorted_chart_data = chart_data.copy()

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
        code_level_logger.error(
            "pyramidfunnel_chart: X-Axis is not found in extraction!"
        )
        raise RuntimeError("pyramidfunnel_chart: X-Axis is not found in extraction!")

    if "yAxis" in chart_data_columns:
        yAxis_column_name = "yAxis"
    elif (
        "yAxis_column" in chart_axis
        and isinstance(chart_axis["yAxis_column"], str)
        and chart_axis["yAxis_column"] in chart_data_columns
    ):
        yAxis_column_name = chart_axis["yAxis_column"]
    else:
        code_level_logger.error(
            "pyramidfunnel_chart: Y-Axis is not found in extraction!"
        )
        raise RuntimeError("pyramidfunnel_chart: Y-Axis is not found in extraction!")

    object_columns = chart_data.select_dtypes(include=[object])

    if yAxis_column_name in object_columns:
        try:
            if not isinstance(
                chart_data[yAxis_column_name].values.tolist()[0],
                datetime.date,
            ) and not isinstance(
                chart_data[yAxis_column_name].values.tolist()[0],
                datetime.datetime,
            ):
                if isinstance(chart_data[yAxis_column_name].values.tolist()[0], str):
                    chart_data[yAxis_column_name] = chart_data[
                        yAxis_column_name
                    ].replace("%", "", regex=True)
                chart_data[yAxis_column_name] = pd.to_numeric(
                    chart_data[yAxis_column_name],
                )
        except Exception:
            code_level_logger.error(
                f"pyramidfunnel_chart: {yAxis_column_name} is not numerical!",
            )
            raise RuntimeError(
                f"pyramidfunnel_chart: {yAxis_column_name} is not numerical!",
            )

    y_values = chart_data[yAxis_column_name].values.tolist()
    if len(y_values) == 1:
        card_chart_json_dict: dict = generate_card_chart_d3(
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            "pyramidfunnel_chart",
            logging_url,
            code_level_logger,
        )
        return card_chart_json_dict

    sorted_chart_data = sorted_chart_data.sort_values(
        by=yAxis_column_name,
        ascending=False,
    )

    if (
        not isinstance(
            sorted_chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            sorted_chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{4}-\d{2}-\d{2}$",
            str(sorted_chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        sorted_chart_data[xAxis_column_name] = pd.to_datetime(
            sorted_chart_data[xAxis_column_name],
            format="%Y-%m-%d",
        )
    elif (
        not isinstance(
            sorted_chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            sorted_chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{2}/\d{2}/\d{4}$",
            str(sorted_chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        sorted_chart_data[xAxis_column_name] = pd.to_datetime(
            sorted_chart_data[xAxis_column_name],
            format="%d/%m/%Y",
        )

    if all(
        isinstance(val, (datetime.date, datetime.datetime))
        for val in sorted_chart_data[xAxis_column_name]
    ):
        sorted_chart_data, new_chart_axis, new_chart_title = adjust_axis_title_and_data(
            llama70b_client,
            chart_id,
            chart_data,
            chart_axis,
            chart_title,
            logging_url,
        )
        pyramid_chart_json_dict["xAxis"] = new_chart_axis["xAxis_title"].replace(
            "_",
            " ",
        )
        pyramid_chart_json_dict["Chart_Title"] = new_chart_title

    try:
        if len(chart_data[xAxis_column_name][0].split("-")) == 1:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                ),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (
                        int(date.split("-")[0]),
                        int(date.split("-")[1]),
                        int(date.split("-")[2]),
                    ),
                ),
            )
        else:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)
    except Exception:
        chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

    if isinstance(xAxis_column_name, str):
        chart_data = sort_pandas_date(chart_data, xAxis_column_name)

    pyramid_chart_json_dict["X"] = [
        str(x_data) for x_data in sorted_chart_data[xAxis_column_name].values.tolist()
    ]
    pyramid_chart_json_dict["Y"] = [
        float(val) if isinstance(val, decimal.Decimal) else val
        for val in sorted_chart_data[yAxis_column_name].values.tolist()
    ]

    if not (
        isinstance(pyramid_chart_json_dict["Y"][0], int)
        or isinstance(pyramid_chart_json_dict["Y"][0], float)
    ):
        code_level_logger.error("pyramid-chart: Y-axis is not integer or float!")
        raise RuntimeError("pyramid-chart: Y-axis is not integer or float!")

    if len(pyramid_chart_json_dict["X"]) > 8:
        # pyramid_chart_json_dict["Chart_Type"] = "bar_chart"
        pyramid_chart_json_dict["Chart_Type"] = "grouped_bar_chart"

    # if check_negative_value(pyramid_chart_json_dict["Y"]):
    #     # pyramid_chart_json_dict["Chart_Type"] = "column_chart"
    #     pyramid_chart_json_dict["Chart_Type"] = "grouped_column_chart"

    if isinstance(pyramid_chart_json_dict["xAxis"], list):
        pyramid_chart_json_dict["xAxis"] = " ".join(pyramid_chart_json_dict["xAxis"])

    if isinstance(pyramid_chart_json_dict["yAxis"], list):
        pyramid_chart_json_dict["yAxis"] = " ".join(pyramid_chart_json_dict["yAxis"])

    if any(
        pyramid_chart_json_dict[key] == [] or pyramid_chart_json_dict[key] == [""]
        for key in pyramid_chart_json_dict
        if re.match(r"^X\d*$", key)
    ):
        code_level_logger.error("pyramid_chart: One or more X-axis values are empty!")
        raise RuntimeError("pyramid_chart: One or more X-axis values are empty!")

    pyramid_chart_json_dict["Client_ID"] = client_id
    pyramid_chart_json_dict["User_ID"] = user_id
    pyramid_chart_json_dict["Session_ID"] = session_id

    if len(y_values) == 1:
        card_chart_json_dict = generate_card_chart_d3(
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            pyramid_chart_json_dict["Chart_Type"],
            logging_url,
            code_level_logger,
        )
        return card_chart_json_dict

    return pyramid_chart_json_dict


def generate_treemap_chart_d3(
    llama70b_client: Any,
    user_query: str,
    chart_id: str,
    sql_query: str,
    chart_title: str,
    chart_axis: dict,
    chart_data: pd.DataFrame,
    database_properties: dict,
    ups_idx: int,
    chart_position: int,
    overall_title: str,
    client_id: str,
    user_id: str,
    session_id: str,
    sql_library: str,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    treemap_chart_json_dict: dict = TREEMAPMULTI_CHART_TEMPLATE_D3.copy()
    treemap_chart_json_dict["User_Query"] = user_query
    treemap_chart_json_dict["Chart_Query"] = sql_query
    treemap_chart_json_dict["Chart_SQL_Library"] = sql_library
    treemap_chart_json_dict["Chart_Name"] = f"Visual {ups_idx}"
    treemap_chart_json_dict["Visual_Title"] = overall_title
    treemap_chart_json_dict["Chart_ID"] = chart_id
    treemap_chart_json_dict["Chart_Axis"] = chart_axis
    treemap_chart_json_dict["Chart_Type"] = "TreemapMulti_chart"
    treemap_chart_json_dict["Chart_Position"] = str(chart_position)
    treemap_chart_json_dict["Chart_Title"] = chart_title

    treemap_chart_json_dict["xAxis"] = chart_axis["xAxis_title"].replace("_", " ")

    treemap_chart_json_dict["Aggregated_Table_JSON"] = (
        generate_aggregated_table_chart_d3(
            user_query,
            sql_query,
            chart_id,
            chart_title,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            chart_axis,
            treemap_chart_json_dict["Chart_Type"],
            code_level_logger,
        )
    )
    treemap_chart_json_dict["Aggregated_Table_Column"] = get_aggregated_columns(
        chart_axis,
    )

    yAxis_title = ""

    for chart_axis_key in chart_axis:
        if (
            chart_axis_key.lower()[0] != "y"
            or "title" not in chart_axis_key.lower()
            or chart_axis[chart_axis_key] == ""
        ):
            continue
        if yAxis_title == "":
            yAxis_title += chart_axis[chart_axis_key]
        else:
            # yAxis_title += f"/{chart_axis[chart_axis_key]}"
            yAxis_title = "Amount"
            break

    if (
        check_aggregation_phrases(yAxis_title.replace("_", " "))
        or yAxis_title == "Amount"
    ):
        treemap_chart_json_dict["yAxis"] = yAxis_title.replace("_", " ")
    elif "yAxis_aggregation" in chart_axis:
        if chart_axis["yAxis_aggregation"] in ["SUM"]:
            treemap_chart_json_dict["yAxis"] = "Total " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            treemap_chart_json_dict["yName"] = "Total " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
            treemap_chart_json_dict["yAxis"] = "Average " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            treemap_chart_json_dict["yName"] = "Average " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
            treemap_chart_json_dict["yAxis"] = "Median " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            treemap_chart_json_dict["yName"] = "Median " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["MIN"]:
            treemap_chart_json_dict["yAxis"] = "Minimum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            treemap_chart_json_dict["yName"] = "Minimum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        elif chart_axis["yAxis_aggregation"] in ["MAX"]:
            treemap_chart_json_dict["yAxis"] = "Maximum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            treemap_chart_json_dict["yName"] = "Maximum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
        else:
            treemap_chart_json_dict["yAxis"] = "Total " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            treemap_chart_json_dict["yName"] = "Total " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
    else:
        treemap_chart_json_dict["yAxis"] = "Total " + chart_axis["yAxis_title"].replace(
            "_",
            " ",
        )
        treemap_chart_json_dict["yName"] = "Total " + chart_axis["yAxis_title"].replace(
            "_",
            " ",
        )

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
        code_level_logger.error("treemap_chart: X-Axis is not found in extraction!")
        raise RuntimeError("treemap_chart: X-Axis is not found in extraction!")

    if "yAxis" in chart_data_columns:
        yAxis_column_name = "yAxis"
    elif (
        "yAxis_column" in chart_axis
        and isinstance(chart_axis["yAxis_column"], str)
        and chart_axis["yAxis_column"] in chart_data_columns
    ):
        yAxis_column_name = chart_axis["yAxis_column"]
    else:
        code_level_logger.error("treemap_chart: Y-Axis is not found in extraction!")
        raise RuntimeError("treemap_chart: Y-Axis is not found in extraction!")

    object_columns = chart_data.select_dtypes(include=[object])

    if yAxis_column_name in object_columns:
        try:
            if not isinstance(
                chart_data[yAxis_column_name].values.tolist()[0],
                datetime.date,
            ) and not isinstance(
                chart_data[yAxis_column_name].values.tolist()[0],
                datetime.datetime,
            ):
                if isinstance(chart_data[yAxis_column_name].values.tolist()[0], str):
                    chart_data[yAxis_column_name] = chart_data[
                        yAxis_column_name
                    ].replace("%", "", regex=True)
                chart_data[yAxis_column_name] = pd.to_numeric(
                    chart_data[yAxis_column_name],
                )
        except Exception:
            code_level_logger.error(
                f"treemap_chart: {yAxis_column_name} is not numerical!"
            )
            raise RuntimeError(f"treemap_chart: {yAxis_column_name} is not numerical!")

    if "series" in chart_data_columns:
        series_column_name = "series"
    elif (
        "series_column" in chart_axis
        and isinstance(chart_axis["series_column"], str)
        and chart_axis["series_column"] in chart_data_columns
    ):
        series_column_name = chart_axis["series_column"]
    else:
        series_column_name = ""

    chart_data = chart_data.fillna(
        {
            col: 0 if chart_data[col].dtype in [np.float64, np.int64] else "null"
            for col in chart_data.columns
        },
    )
    chart_data = chart_data.sort_values(by=yAxis_column_name, ascending=False)

    if (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{4}-\d{2}-\d{2}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%Y-%m-%d",
        )
    elif (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{2}/\d{2}/\d{4}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%d/%m/%Y",
        )

    if all(
        isinstance(val, (datetime.date, datetime.datetime))
        for val in chart_data[xAxis_column_name]
    ):
        chart_data, new_chart_axis, new_chart_title = adjust_axis_title_and_data(
            llama70b_client,
            chart_id,
            chart_data,
            chart_axis,
            chart_title,
            logging_url,
        )
        treemap_chart_json_dict["xAxis"] = new_chart_axis["xAxis_title"].replace(
            "_",
            " ",
        )
        treemap_chart_json_dict["Chart_Title"] = new_chart_title

    try:
        if len(chart_data[xAxis_column_name][0].split("-")) == 1:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                ),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (
                        int(date.split("-")[0]),
                        int(date.split("-")[1]),
                        int(date.split("-")[2]),
                    ),
                ),
            )
        else:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)
    except Exception:
        chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

    if isinstance(xAxis_column_name, str):
        chart_data = sort_pandas_date(chart_data, xAxis_column_name)

    if (
        series_column_name != ""
        and series_column_name in chart_data.columns
        and chart_data[series_column_name].nunique() > 1
    ):
        unique_series = chart_data[series_column_name].unique().tolist()

        yAxis_idx = 1

        for series_value in unique_series:
            series_chart_data: pd.DataFrame = chart_data[
                chart_data[series_column_name] == series_value
            ]

            if (
                not isinstance(
                    series_chart_data[xAxis_column_name].reset_index().iloc[0],
                    datetime.date,
                )
                and not isinstance(
                    series_chart_data[xAxis_column_name].reset_index().iloc[0],
                    datetime.datetime,
                )
            ) and (
                re.search(
                    r"^\d{4}-\d{2}-\d{2}$",
                    str(series_chart_data[xAxis_column_name].values.tolist()[0]),
                    re.IGNORECASE,
                )
            ):
                series_chart_data[xAxis_column_name] = pd.to_datetime(
                    series_chart_data[xAxis_column_name],
                    format="%Y-%m-%d",
                )
            elif (
                not isinstance(
                    series_chart_data[xAxis_column_name].reset_index().iloc[0],
                    datetime.date,
                )
                and not isinstance(
                    series_chart_data[xAxis_column_name].reset_index().iloc[0],
                    datetime.datetime,
                )
            ) and (
                re.search(
                    r"^\d{2}/\d{2}/\d{4}$",
                    str(series_chart_data[xAxis_column_name].values.tolist()[0]),
                    re.IGNORECASE,
                )
            ):
                series_chart_data[xAxis_column_name] = pd.to_datetime(
                    series_chart_data[xAxis_column_name],
                    format="%d/%m/%Y",
                )

            if all(
                isinstance(val, (datetime.date, datetime.datetime))
                for val in series_chart_data[xAxis_column_name]
            ):
                series_chart_data, new_chart_axis, new_chart_title = (
                    adjust_axis_title_and_data(
                        llama70b_client,
                        chart_id,
                        chart_data,
                        chart_axis,
                        chart_title,
                        logging_url,
                    )
                )
                treemap_chart_json_dict["xAxis"] = new_chart_axis[
                    "xAxis_title"
                ].replace("_", " ")
                treemap_chart_json_dict["Chart_Title"] = new_chart_title

            try:
                if len(series_chart_data[xAxis_column_name][0].split("-")) == 1:
                    series_chart_data = series_chart_data.sort_values(
                        by=xAxis_column_name,
                        key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
                    )
                elif len(series_chart_data[xAxis_column_name][0].split("-")) == 2:
                    series_chart_data = series_chart_data.sort_values(
                        by=xAxis_column_name,
                        key=lambda x: x.apply(
                            lambda date: (
                                int(date.split("-")[0]),
                                int(date.split("-")[1]),
                            ),
                        ),
                    )
                elif len(series_chart_data[xAxis_column_name][0].split("-")) == 3:
                    series_chart_data = series_chart_data.sort_values(
                        by=xAxis_column_name,
                        key=lambda x: x.apply(
                            lambda date: (
                                int(date.split("-")[0]),
                                int(date.split("-")[1]),
                                int(date.split("-")[2]),
                            ),
                        ),
                    )
                else:
                    series_chart_data = series_chart_data.sort_values(
                        by=xAxis_column_name,
                        ascending=True,
                    )
            except Exception:
                series_chart_data = series_chart_data.sort_values(
                    by=xAxis_column_name,
                    ascending=True,
                )

            if isinstance(xAxis_column_name, str):
                series_chart_data = sort_pandas_date(
                    series_chart_data,
                    xAxis_column_name,
                )

            for series_chart_column in list(series_chart_data.columns):
                if not re.search(
                    r"yAxis([23456789])?",
                    series_chart_column,
                    re.IGNORECASE,
                ):
                    continue

                if yAxis_idx <= 1:
                    treemap_chart_json_dict["X"] = [
                        str(x_data)
                        for x_data in series_chart_data[
                            xAxis_column_name
                        ].values.tolist()
                    ]

                    treemap_chart_json_dict["Y"] = [
                        float(val) if isinstance(val, decimal.Decimal) else val
                        for val in series_chart_data[
                            series_chart_column
                        ].values.tolist()
                    ]

                    # Add Series Title to Series Value
                    if (
                        "series_title" in chart_axis
                        and chart_axis["series_title"] != ""
                    ):
                        series_value = (
                            f"""{chart_axis["series_title"]}: {series_value}"""
                        )

                    if (
                        f"{series_chart_column}_title" in chart_axis
                        and check_aggregation_phrases(
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})",
                        )
                    ):
                        treemap_chart_json_dict["yName"] = (
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif f"{series_chart_column}_aggregation" in chart_axis:
                        if chart_axis[f"{series_chart_column}_aggregation"] in ["SUM"]:
                            treemap_chart_json_dict["yName"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            treemap_chart_json_dict["yName"] = (
                                f"Average {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "MEDIAN",
                        ]:
                            treemap_chart_json_dict["yName"] = (
                                f"Median {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "MIN",
                        ]:
                            treemap_chart_json_dict["yName"] = (
                                f"Minimum {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "MAX",
                        ]:
                            treemap_chart_json_dict["yName"] = (
                                f"Maximum {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        else:
                            treemap_chart_json_dict["yName"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                    else:
                        treemap_chart_json_dict["yName"] = (
                            f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                "_",
                                " ",
                            )
                        )

                    if not (
                        isinstance(treemap_chart_json_dict["Y"][0], int)
                        or isinstance(treemap_chart_json_dict["Y"][0], float)
                    ):
                        code_level_logger.error(
                            "treemap_chart: Y-axis is not integer or float!",
                        )
                        raise RuntimeError(
                            "treemap_chart: Y-axis is not integer or float!",
                        )

                    # if check_negative_value(treemap_chart_json_dict["Y"]):
                    #     # treemap_chart_json_dict["Chart_Type"] = "column_chart"
                    #     treemap_chart_json_dict["Chart_Type"] = "grouped_column_chart"
                else:
                    treemap_chart_json_dict[f"X{yAxis_idx}"] = [
                        str(x_data)
                        for x_data in series_chart_data[
                            xAxis_column_name
                        ].values.tolist()
                    ]

                    treemap_chart_json_dict[f"Y{yAxis_idx}"] = [
                        float(val) if isinstance(val, decimal.Decimal) else val
                        for val in series_chart_data[
                            series_chart_column
                        ].values.tolist()
                    ]

                    # Add Series Title to Series Value
                    if (
                        "series_title" in chart_axis
                        and chart_axis["series_title"] != ""
                    ):
                        series_value = (
                            f"""{chart_axis["series_title"]}: {series_value}"""
                        )

                    if (
                        f"{series_chart_column}_title" in chart_axis
                        and check_aggregation_phrases(
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})",
                        )
                    ):
                        treemap_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif "yAxis_aggregation" in chart_axis:
                        if chart_axis["yAxis_aggregation"] in ["SUM"]:
                            treemap_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
                            treemap_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                f"Average {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
                            treemap_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                f"Median {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis["yAxis_aggregation"] in ["MIN"]:
                            treemap_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                f"Minimum {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis["yAxis_aggregation"] in ["MAX"]:
                            treemap_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                f"Maximum {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        else:
                            treemap_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                    else:
                        treemap_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                "_",
                                " ",
                            )
                        )

                    if not (
                        isinstance(treemap_chart_json_dict[f"Y{yAxis_idx}"][0], int)
                        or isinstance(
                            treemap_chart_json_dict[f"Y{yAxis_idx}"][0],
                            float,
                        )
                    ):
                        code_level_logger.error(
                            f"treemap_chart: Y{yAxis_idx}-axis is not integer or float!",
                        )
                        raise RuntimeError(
                            f"treemap_chart: Y{yAxis_idx}-axis is not integer or float!",
                        )

                    # if (
                    #     check_negative_value(treemap_chart_json_dict[f"Y{yAxis_idx}"])
                    #     or treemap_chart_json_dict["Chart_Type"] == "column_chart"
                    # ):
                    #     return generate_group_column_chart_d3(
                    #         llama70b_client,
                    #         user_query,
                    #         chart_id,
                    #         sql_query,
                    #         chart_title,
                    #         chart_axis,
                    #         chart_data,
                    #         database_properties,
                    #         ups_idx,
                    #         chart_position,
                    #         overall_title,
                    #         client_id,
                    #         user_id,
                    #         sql_library,
                    #         logging_url,
                    #     )

                yAxis_idx += 1
    else:
        yAxis_idx = 1

        try:
            if len(chart_data[xAxis_column_name][0].split("-")) == 1:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
                )
            elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(
                        lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                    ),
                )
            elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(
                        lambda date: (
                            int(date.split("-")[0]),
                            int(date.split("-")[1]),
                            int(date.split("-")[2]),
                        ),
                    ),
                )
            else:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    ascending=True,
                )
        except Exception:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

        if isinstance(xAxis_column_name, str):
            chart_data = sort_pandas_date(chart_data, xAxis_column_name)

        for column_name in list(chart_data.columns):
            if not re.search(r"yAxis([23456789])?", column_name, re.IGNORECASE):
                continue

            if yAxis_idx <= 1:
                treemap_chart_json_dict["X"] = [
                    str(x_data)
                    for x_data in chart_data[xAxis_column_name].values.tolist()
                ]

                treemap_chart_json_dict["Y"] = [
                    float(val) if isinstance(val, decimal.Decimal) else val
                    for val in chart_data[column_name].values.tolist()
                ]

                if check_aggregation_phrases(chart_axis[f"{column_name}_title"]):
                    treemap_chart_json_dict["yName"] = chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")
                elif "yAxis_aggregation" in chart_axis:
                    if chart_axis["yAxis_aggregation"] in ["SUM"]:
                        treemap_chart_json_dict["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
                        treemap_chart_json_dict["yName"] = "Average " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
                        treemap_chart_json_dict["yName"] = "Median " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["MIN"]:
                        treemap_chart_json_dict["yName"] = "Minimum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["MAX"]:
                        treemap_chart_json_dict["yName"] = "Maximum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    else:
                        treemap_chart_json_dict["yName"] = chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                else:
                    treemap_chart_json_dict["yName"] = "Total " + chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")

                if not (
                    isinstance(treemap_chart_json_dict["Y"][0], int)
                    or isinstance(treemap_chart_json_dict["Y"][0], float)
                ):
                    code_level_logger.error(
                        "treemap_chart: Y-axis is not integer or float!"
                    )
                    raise RuntimeError("treemap_chart: Y-axis is not integer or float!")

                # if check_negative_value(treemap_chart_json_dict["Y"]):
                #     # treemap_chart_json_dict["Chart_Type"] = "column_chart"
                #     treemap_chart_json_dict["Chart_Type"] = "grouped_column_chart"
            else:
                treemap_chart_json_dict[f"X{yAxis_idx}"] = [
                    str(x_data)
                    for x_data in chart_data[xAxis_column_name].values.tolist()
                ]

                treemap_chart_json_dict[f"Y{yAxis_idx}"] = [
                    float(val) if isinstance(val, decimal.Decimal) else val
                    for val in chart_data[column_name].values.tolist()
                ]

                if check_aggregation_phrases(chart_axis[f"{column_name}_title"]):
                    treemap_chart_json_dict[f"y{yAxis_idx}Name"] = chart_axis[
                        f"{column_name}_title"
                    ]
                elif f"{column_name}_aggregation" in chart_axis:
                    if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                        treemap_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Total "
                            + chart_axis[f"{column_name}_title"].replace("_", " ")
                        )
                    elif chart_axis[f"{column_name}_aggregation"] in ["AVG", "MEAN"]:
                        treemap_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Average "
                            + chart_axis[f"{column_name}_title"].replace("_", " ")
                        )
                    elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                        treemap_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Median "
                            + chart_axis[f"{column_name}_title"].replace("_", " ")
                        )
                    elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                        treemap_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Minimum "
                            + chart_axis[f"{column_name}_title"].replace("_", " ")
                        )
                    elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                        treemap_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Maximum "
                            + chart_axis[f"{column_name}_title"].replace("_", " ")
                        )
                    else:
                        treemap_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Total "
                            + chart_axis[f"{column_name}_title"].replace("_", " ")
                        )
                else:
                    treemap_chart_json_dict[f"y{yAxis_idx}Name"] = (
                        "Total " + chart_axis[f"{column_name}_title"].replace("_", " ")
                    )

                if not (
                    isinstance(treemap_chart_json_dict[f"Y{yAxis_idx}"][0], int)
                    or isinstance(treemap_chart_json_dict[f"Y{yAxis_idx}"][0], float)
                ):
                    code_level_logger.error(
                        f"treemap_chart: Y{yAxis_idx}-axis is not integer or float!",
                    )
                    raise RuntimeError(
                        f"treemap_chart: Y{yAxis_idx}-axis is not integer or float!",
                    )

                # if (
                #     check_negative_value(treemap_chart_json_dict[f"Y{yAxis_idx}"])
                #     or treemap_chart_json_dict["Chart_Type"] == "column_chart"
                # ):
                #     return generate_group_column_chart_d3(
                #         llama70b_client,
                #         user_query,
                #         chart_id,
                #         sql_query,
                #         chart_title,
                #         chart_axis,
                #         chart_data,
                #         database_properties,
                #         ups_idx,
                #         chart_position,
                #         overall_title,
                #         client_id,
                #         user_id,
                #         sql_library,
                #         logging_url,
                #     )

            yAxis_idx += 1

    if treemap_chart_json_dict["Y"] == []:
        code_level_logger.error("treemap_chart: Y-Axis is not found in extraction!")
        raise RuntimeError("treemap_chart: Y-Axis is not found in extraction!")

    if any(
        treemap_chart_json_dict[key] == [] or treemap_chart_json_dict[key] == [""]
        for key in treemap_chart_json_dict
        if re.match(r"^X\d*$", key)
    ):
        code_level_logger.error("treemap_chart: One or more X-axis values are empty!")
        raise RuntimeError("treemap_chart: One or more X-axis values are empty!")

    treemap_chart_json_dict["Database_Identifier"] = database_properties["db_tag"]

    treemap_chart_json_dict["Client_ID"] = client_id
    treemap_chart_json_dict["User_ID"] = user_id
    treemap_chart_json_dict["Session_ID"] = session_id

    if len(treemap_chart_json_dict["Y"]) == 1 and treemap_chart_json_dict["Y2"] == []:
        card_chart_json_dict: dict = generate_card_chart_d3(
            llama70b_client,
            user_query,
            chart_id,
            sql_query,
            chart_title,
            chart_axis,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            treemap_chart_json_dict["Chart_Type"],
            logging_url,
            code_level_logger,
        )
        return card_chart_json_dict

    return treemap_chart_json_dict


def generate_bubbleplot_chart_d3(
    llama70b_client: Any,
    user_query: str,
    chart_id: str,
    sql_query: str,
    chart_title: str,
    chart_axis: dict,
    chart_data: pd.DataFrame,
    database_properties: dict,
    ups_idx: int,
    chart_position: int,
    overall_title: str,
    client_id: str,
    user_id: str,
    session_id: str,
    sql_library: str,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    bubble_chart_json_dict: dict = BUBBLE_CHART_TEMPLATE_D3.copy()
    bubble_chart_json_dict["User_Query"] = user_query
    bubble_chart_json_dict["Chart_Query"] = sql_query
    bubble_chart_json_dict["Chart_SQL_Library"] = sql_library
    bubble_chart_json_dict["Chart_Name"] = f"Visual {ups_idx}"
    bubble_chart_json_dict["Visual_Title"] = overall_title
    bubble_chart_json_dict["Chart_ID"] = chart_id
    bubble_chart_json_dict["Chart_Axis"] = chart_axis
    bubble_chart_json_dict["Chart_Type"] = "bubbleplot_chart"
    bubble_chart_json_dict["Chart_Position"] = str(chart_position)
    bubble_chart_json_dict["Chart_Title"] = chart_title

    bubble_chart_json_dict["xAxis"] = chart_axis["xAxis_title"].replace("_", " ")

    bubble_chart_json_dict["zAxis"] = chart_axis["zAxis_title"].replace("_", " ")

    bubble_chart_json_dict["Aggregated_Table_JSON"] = (
        generate_aggregated_table_chart_d3(
            user_query,
            sql_query,
            chart_id,
            chart_title,
            chart_data,
            database_properties,
            ups_idx,
            chart_position,
            overall_title,
            client_id,
            user_id,
            session_id,
            sql_library,
            chart_axis,
            bubble_chart_json_dict["Chart_Type"],
            code_level_logger,
        )
    )
    bubble_chart_json_dict["Aggregated_Table_Column"] = get_aggregated_columns(
        chart_axis,
    )

    yAxis_title = ""
    for chart_axis_key in chart_axis:
        if (
            chart_axis_key.lower()[0] != "y"
            or "title" not in chart_axis_key.lower()
            or chart_axis[chart_axis_key] == ""
        ):
            continue
        if yAxis_title == "":
            yAxis_title += chart_axis[chart_axis_key]
        else:
            # yAxis_title += f"/{chart_axis[chart_axis_key]}"
            yAxis_title = "Amount"
            break

    if (
        check_aggregation_phrases(yAxis_title.replace("_", " "))
        or yAxis_title == "Amount"
    ):
        bubble_chart_json_dict["yAxis"] = yAxis_title.replace("_", " ")
    elif "yAxis_aggregation" in chart_axis:
        if chart_axis["yAxis_aggregation"] in ["SUM"]:
            bubble_chart_json_dict["yAxis"] = "Total " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            bubble_chart_json_dict["yName"] = "Total " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")

        elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
            bubble_chart_json_dict["yAxis"] = "Average " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            bubble_chart_json_dict["yName"] = "Average " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")

        elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
            bubble_chart_json_dict["yAxis"] = "Median " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            bubble_chart_json_dict["yName"] = "Median " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")

        elif chart_axis["yAxis_aggregation"] in ["MIN"]:
            bubble_chart_json_dict["yAxis"] = "Minimum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            bubble_chart_json_dict["yName"] = "Minimum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")

        elif chart_axis["yAxis_aggregation"] in ["MAX"]:
            bubble_chart_json_dict["yAxis"] = "Maximum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            bubble_chart_json_dict["yName"] = "Maximum " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")

        else:
            bubble_chart_json_dict["yAxis"] = "Total " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")
            bubble_chart_json_dict["yName"] = "Total " + chart_axis[
                "yAxis_title"
            ].replace("_", " ")

    else:
        bubble_chart_json_dict["yAxis"] = "Total " + chart_axis["yAxis_title"].replace(
            "_",
            " ",
        )
        bubble_chart_json_dict["yName"] = "Total " + chart_axis["yAxis_title"].replace(
            "_",
            " ",
        )

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
        code_level_logger.error("bubbleplot_: X-Axis is not found in extraction!")
        raise RuntimeError("bubbleplot_: X-Axis is not found in extraction!")

    if "yAxis" in chart_data_columns:
        yAxis_column_name = "yAxis"
    elif (
        "yAxis_column" in chart_axis
        and isinstance(chart_axis["yAxis_column"], str)
        and chart_axis["yAxis_column"] in chart_data_columns
    ):
        yAxis_column_name = chart_axis["yAxis_column"]
    else:
        code_level_logger.error("bubbleplot_chart: Y-Axis is not found in extraction!")
        raise RuntimeError("bubbleplot_chart: Y-Axis is not found in extraction!")

    if "zAxis" in chart_data_columns:
        zAxis_column_name = "zAxis"
    elif (
        "zAxis_column" in chart_axis
        and isinstance(chart_axis["zAxis_column"], str)
        and chart_axis["zAxis_column"] in chart_data_columns
    ):
        zAxis_column_name = chart_axis["zAxis_column"]
    else:
        code_level_logger.error("bubbleplot_chart: Z-Axis is not found in extraction!")
        raise RuntimeError("bubbleplot_chart: Z-Axis is not found in extraction!")

    if "series" in chart_data_columns:
        series_column_name = "series"
    elif (
        "series_column" in chart_axis
        and isinstance(chart_axis["series_column"], str)
        and chart_axis["series_column"] in chart_data_columns
    ):
        series_column_name = chart_axis["series_column"]
    else:
        series_column_name = ""

    object_columns = chart_data.select_dtypes(include=[object])

    numerical_column_names = list(chart_data.columns)
    if series_column_name in numerical_column_names:
        numerical_column_names.remove(series_column_name)

    for numerical_column_name in numerical_column_names:
        if numerical_column_name in object_columns:
            try:
                if not isinstance(
                    chart_data[numerical_column_name].values.tolist()[0],
                    datetime.date,
                ) and not isinstance(
                    chart_data[numerical_column_name].values.tolist()[0],
                    datetime.datetime,
                ):
                    if isinstance(
                        chart_data[numerical_column_name].values.tolist()[0],
                        str,
                    ):
                        chart_data[numerical_column_name] = chart_data[
                            numerical_column_name
                        ].replace("%", "", regex=True)
                    chart_data[numerical_column_name] = pd.to_numeric(
                        chart_data[numerical_column_name],
                    )
            except Exception:
                code_level_logger.error(
                    f"bubbleplot_chart: {numerical_column_name} is not numerical!",
                )
                raise RuntimeError(
                    f"bubbleplot_chart: {numerical_column_name} is not numerical!",
                )

    chart_data = chart_data.fillna(
        {
            col: 0 if chart_data[col].dtype in [np.float64, np.int64] else "null"
            for col in chart_data.columns
        },
    )
    chart_data = chart_data.sort_values(by=yAxis_column_name, ascending=False)

    if (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{4}-\d{2}-\d{2}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%Y-%m-%d",
        )
    elif (
        not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.date,
        )
        and not isinstance(
            chart_data[xAxis_column_name].reset_index().iloc[0],
            datetime.datetime,
        )
    ) and (
        re.search(
            r"^\d{2}/\d{2}/\d{4}$",
            str(chart_data[xAxis_column_name].values.tolist()[0]),
            re.IGNORECASE,
        )
    ):
        chart_data[xAxis_column_name] = pd.to_datetime(
            chart_data[xAxis_column_name],
            format="%d/%m/%Y",
        )

    if all(
        isinstance(val, (datetime.date, datetime.datetime))
        for val in chart_data[xAxis_column_name]
    ):
        chart_data, new_chart_axis, new_chart_title = adjust_axis_title_and_data(
            llama70b_client,
            chart_id,
            chart_data,
            chart_axis,
            chart_title,
            logging_url,
        )
        bubble_chart_json_dict["xAxis"] = new_chart_axis["xAxis_title"].replace(
            "_",
            " ",
        )
        bubble_chart_json_dict["Chart_Title"] = new_chart_title

    try:
        if len(chart_data[xAxis_column_name][0].split("-")) == 1:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                ),
            )
        elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
            chart_data = chart_data.sort_values(
                by=xAxis_column_name,
                key=lambda x: x.apply(
                    lambda date: (
                        int(date.split("-")[0]),
                        int(date.split("-")[1]),
                        int(date.split("-")[2]),
                    ),
                ),
            )
        else:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)
    except Exception:
        chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

    if isinstance(xAxis_column_name, str):
        chart_data = sort_pandas_date(chart_data, xAxis_column_name)

    if (
        series_column_name != ""
        and series_column_name in chart_data.columns
        and chart_data[series_column_name].nunique() > 1
    ):
        unique_series = chart_data[series_column_name].unique().tolist()

        yAxis_idx = 1

        for series_value in unique_series:
            series_chart_data: pd.DataFrame = chart_data[
                chart_data[series_column_name] == series_value
            ]

            if (
                not isinstance(
                    series_chart_data[xAxis_column_name].reset_index().iloc[0],
                    datetime.date,
                )
                and not isinstance(
                    series_chart_data[xAxis_column_name].reset_index().iloc[0],
                    datetime.datetime,
                )
            ) and (
                re.search(
                    r"^\d{4}-\d{2}-\d{2}$",
                    str(series_chart_data[xAxis_column_name].values.tolist()[0]),
                    re.IGNORECASE,
                )
            ):
                series_chart_data[xAxis_column_name] = pd.to_datetime(
                    series_chart_data[xAxis_column_name],
                    format="%Y-%m-%d",
                )
            elif (
                not isinstance(
                    series_chart_data[xAxis_column_name].reset_index().iloc[0],
                    datetime.date,
                )
                and not isinstance(
                    series_chart_data[xAxis_column_name].reset_index().iloc[0],
                    datetime.datetime,
                )
            ) and (
                re.search(
                    r"^\d{2}/\d{2}/\d{4}$",
                    str(series_chart_data[xAxis_column_name].values.tolist()[0]),
                    re.IGNORECASE,
                )
            ):
                series_chart_data[xAxis_column_name] = pd.to_datetime(
                    series_chart_data[xAxis_column_name],
                    format="%d/%m/%Y",
                )

            if all(
                isinstance(val, (datetime.date, datetime.datetime))
                for val in series_chart_data[xAxis_column_name]
            ):
                series_chart_data, new_chart_axis, new_chart_title = (
                    adjust_axis_title_and_data(
                        llama70b_client,
                        chart_id,
                        chart_data,
                        chart_axis,
                        chart_title,
                        logging_url,
                    )
                )
                bubble_chart_json_dict["xAxis"] = new_chart_axis["xAxis_title"].replace(
                    "_",
                    " ",
                )
                bubble_chart_json_dict["Chart_Title"] = new_chart_title

            try:
                if len(series_chart_data[xAxis_column_name][0].split("-")) == 1:
                    series_chart_data = series_chart_data.sort_values(
                        by=xAxis_column_name,
                        key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
                    )
                elif len(series_chart_data[xAxis_column_name][0].split("-")) == 2:
                    series_chart_data = series_chart_data.sort_values(
                        by=xAxis_column_name,
                        key=lambda x: x.apply(
                            lambda date: (
                                int(date.split("-")[0]),
                                int(date.split("-")[1]),
                            ),
                        ),
                    )
                elif len(series_chart_data[xAxis_column_name][0].split("-")) == 3:
                    series_chart_data = series_chart_data.sort_values(
                        by=xAxis_column_name,
                        key=lambda x: x.apply(
                            lambda date: (
                                int(date.split("-")[0]),
                                int(date.split("-")[1]),
                                int(date.split("-")[2]),
                            ),
                        ),
                    )
                else:
                    series_chart_data = series_chart_data.sort_values(
                        by=xAxis_column_name,
                        ascending=True,
                    )
            except Exception:
                series_chart_data = series_chart_data.sort_values(
                    by=xAxis_column_name,
                    ascending=True,
                )

            if isinstance(xAxis_column_name, str):
                series_chart_data = sort_pandas_date(
                    series_chart_data,
                    xAxis_column_name,
                )

            for series_chart_column in list(series_chart_data.columns):
                if not re.search(
                    r"yAxis([23456789])?",
                    series_chart_column,
                    re.IGNORECASE,
                ):
                    continue

                if yAxis_idx <= 1:
                    bubble_chart_json_dict["X"] = [
                        float(x_data) if isinstance(x_data, decimal.Decimal) else x_data
                        for x_data in series_chart_data[
                            xAxis_column_name
                        ].values.tolist()
                    ]

                    bubble_chart_json_dict["Y"] = [
                        float(val) if isinstance(val, decimal.Decimal) else val
                        for val in series_chart_data[yAxis_column_name].values.tolist()
                    ]

                    bubble_chart_json_dict["Z"] = [
                        float(val) if isinstance(val, decimal.Decimal) else val
                        for val in series_chart_data[zAxis_column_name].values.tolist()
                    ]

                    # Add Series Title to Series Value
                    if (
                        "series_title" in chart_axis
                        and chart_axis["series_title"] != ""
                    ):
                        series_value = (
                            f"""{chart_axis["series_title"]}: {series_value}"""
                        )

                    if (
                        f"{series_chart_column}_title" in chart_axis
                        and check_aggregation_phrases(
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})",
                        )
                    ):
                        bubble_chart_json_dict["yName"] = (
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif f"{series_chart_column}_aggregation" in chart_axis:
                        if chart_axis[f"{series_chart_column}_aggregation"] in ["SUM"]:
                            bubble_chart_json_dict["yName"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            bubble_chart_json_dict["yName"] = (
                                f"Average {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "MEDIAN",
                        ]:
                            bubble_chart_json_dict["yName"] = (
                                f"Median {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "MIN",
                        ]:
                            bubble_chart_json_dict["yName"] = (
                                f"Minimum {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "MAX",
                        ]:
                            bubble_chart_json_dict["yName"] = (
                                f"Maximum {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        else:
                            bubble_chart_json_dict["yName"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                    else:
                        bubble_chart_json_dict["yName"] = (
                            f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                "_",
                                " ",
                            )
                        )

                    if not (
                        isinstance(bubble_chart_json_dict["Y"][0], int)
                        or isinstance(bubble_chart_json_dict["Y"][0], float)
                    ):
                        code_level_logger.error(
                            "bubbleplot_chart: Y-axis is not integer or float!",
                        )
                        raise RuntimeError(
                            "bubbleplot_chart: Y-axis is not integer or float!",
                        )

                    # if check_negative_value(scatterplot_chart_json_dict["Y"]):
                    #     # scatterplot_chart_json_dict["Chart_Type"] = "column_chart"
                    #     scatterplot_chart_json_dict["Chart_Type"] = "grouped_column_chart"
                else:
                    X_data = list(
                        [
                            float(val) if isinstance(val, decimal.Decimal) else val
                            for val in series_chart_data[
                                xAxis_column_name
                            ].values.tolist()
                        ],
                    )

                    bubble_chart_json_dict[f"X{yAxis_idx}"] = X_data

                    Y_data = list(
                        [
                            float(val) if isinstance(val, decimal.Decimal) else val
                            for val in series_chart_data[
                                yAxis_column_name
                            ].values.tolist()
                        ],
                    )

                    bubble_chart_json_dict[f"Y{yAxis_idx}"] = Y_data

                    bubble_chart_json_dict[f"Y{yAxis_idx}"] = Y_data

                    bubble_chart_json_dict[f"Z{yAxis_idx}"] = [
                        float(val) if isinstance(val, decimal.Decimal) else val
                        for val in series_chart_data[zAxis_column_name].values.tolist()
                    ]

                    # Add Series Title to Series Value
                    if (
                        "series_title" in chart_axis
                        and chart_axis["series_title"] != ""
                    ):
                        series_value = (
                            f"""{chart_axis["series_title"]}: {series_value}"""
                        )

                    if (
                        f"{series_chart_column}_title" in chart_axis
                        and check_aggregation_phrases(
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})",
                        )
                    ):
                        bubble_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif "yAxis_aggregation" in chart_axis:
                        if chart_axis["yAxis_aggregation"] in ["SUM"]:
                            bubble_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
                            bubble_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                f"Average {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
                            bubble_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                f"Median {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis["yAxis_aggregation"] in ["MIN"]:
                            bubble_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                f"Minimum {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis["yAxis_aggregation"] in ["MAX"]:
                            bubble_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                f"Maximum {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        else:
                            bubble_chart_json_dict[f"y{yAxis_idx}Name"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                    else:
                        bubble_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                "_",
                                " ",
                            )
                        )

                    if not (
                        isinstance(bubble_chart_json_dict[f"Y{yAxis_idx}"][0], int)
                        or isinstance(bubble_chart_json_dict[f"Y{yAxis_idx}"][0], float)
                    ):
                        code_level_logger.error(
                            f"bubbleplot_chart: Y{yAxis_idx}-axis is not integer or float!",
                        )
                        raise RuntimeError(
                            f"bubbleplot_chart: Y{yAxis_idx}-axis is not integer or float!",
                        )

                    # if (
                    #     check_negative_value(scatterplot_chart_json_dict[f"Y{yAxis_idx}"])
                    #     or scatterplot_chart_json_dict["Chart_Type"] == "column_chart"
                    # ):
                    #     return generate_group_column_chart_d3(
                    #         llama70b_client,
                    #         user_query,
                    #         chart_id,
                    #         sql_query,
                    #         chart_title,
                    #         chart_axis,
                    #         chart_data,
                    #         database_properties,
                    #         ups_idx,
                    #         chart_position,
                    #         overall_title,
                    #         client_id,
                    #         user_id,
                    #         sql_library,
                    #         logging_url,
                    #     )

                yAxis_idx += 1
    else:
        yAxis_idx = 1

        try:
            if len(chart_data[xAxis_column_name][0].split("-")) == 1:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(lambda date: (int(date.split("-")[0]))),
                )
            elif len(chart_data[xAxis_column_name][0].split("-")) == 2:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(
                        lambda date: (int(date.split("-")[0]), int(date.split("-")[1])),
                    ),
                )
            elif len(chart_data[xAxis_column_name][0].split("-")) == 3:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    key=lambda x: x.apply(
                        lambda date: (
                            int(date.split("-")[0]),
                            int(date.split("-")[1]),
                            int(date.split("-")[2]),
                        ),
                    ),
                )
            else:
                chart_data = chart_data.sort_values(
                    by=xAxis_column_name,
                    ascending=True,
                )
        except Exception:
            chart_data = chart_data.sort_values(by=xAxis_column_name, ascending=True)

        if isinstance(xAxis_column_name, str):
            chart_data = sort_pandas_date(chart_data, xAxis_column_name)

        for column_name in list(chart_data.columns):
            if not re.search(r"yAxis([23456789])?", column_name, re.IGNORECASE):
                continue

            if yAxis_idx <= 1:
                bubble_chart_json_dict["X"] = (
                    [
                        float(val) if isinstance(val, decimal.Decimal) else val
                        for val in chart_data[xAxis_column_name].values.tolist()
                    ],
                )

                bubble_chart_json_dict["Y"] = [
                    float(val) if isinstance(val, decimal.Decimal) else val
                    for val in chart_data[yAxis_column_name].values.tolist()
                ]

                bubble_chart_json_dict["Z"] = [
                    float(val) if isinstance(val, decimal.Decimal) else val
                    for val in chart_data[zAxis_column_name].values.tolist()
                ]

                if check_aggregation_phrases(chart_axis[f"{column_name}_title"]):
                    bubble_chart_json_dict["yName"] = chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")
                elif "yAxis_aggregation" in chart_axis:
                    if chart_axis["yAxis_aggregation"] in ["SUM"]:
                        bubble_chart_json_dict["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
                        bubble_chart_json_dict["yName"] = "Average " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
                        bubble_chart_json_dict["yName"] = "Median " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["MIN"]:
                        bubble_chart_json_dict["yName"] = "Minimum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["MAX"]:
                        bubble_chart_json_dict["yName"] = "Maximum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    else:
                        bubble_chart_json_dict["yName"] = chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                else:
                    bubble_chart_json_dict["yName"] = "Total " + chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")

                if not (
                    isinstance(bubble_chart_json_dict["Y"][0], int)
                    or isinstance(bubble_chart_json_dict["Y"][0], float)
                ):
                    code_level_logger.error(
                        "bubbleplot_chart: Y-axis is not integer or float!",
                    )
                    raise RuntimeError(
                        "bubbleplot_chart: Y-axis is not integer or float!",
                    )

                # if check_negative_value(scatterplot_chart_json_dict["Y"]):
                #     # scatterplot_chart_json_dict["Chart_Type"] = "column_chart"
                #     scatterplot_chart_json_dict["Chart_Type"] = "grouped_column_chart"
            else:
                bubble_chart_json_dict[f"X{yAxis_idx}"] = [
                    float(val) if isinstance(val, decimal.Decimal) else val
                    for val in chart_data[xAxis_column_name].values.tolist()
                ]

                bubble_chart_json_dict[f"Y{yAxis_idx}"] = [
                    float(val) if isinstance(val, decimal.Decimal) else val
                    for val in chart_data[yAxis_column_name].values.tolist()
                ]

                bubble_chart_json_dict[f"Z{yAxis_idx}"] = [
                    float(val) if isinstance(val, decimal.Decimal) else val
                    for val in chart_data[zAxis_column_name].values.tolist()
                ]

                if check_aggregation_phrases(chart_axis[f"{column_name}_title"]):
                    bubble_chart_json_dict[f"y{yAxis_idx}Name"] = chart_axis[
                        f"{column_name}_title"
                    ]
                elif f"{column_name}_aggregation" in chart_axis:
                    if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                        bubble_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Total "
                            + chart_axis[f"{column_name}_title"].replace("_", " ")
                        )
                    elif chart_axis[f"{column_name}_aggregation"] in ["AVG", "MEAN"]:
                        bubble_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Average "
                            + chart_axis[f"{column_name}_title"].replace("_", " ")
                        )
                    elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                        bubble_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Median "
                            + chart_axis[f"{column_name}_title"].replace("_", " ")
                        )
                    elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                        bubble_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Minimum "
                            + chart_axis[f"{column_name}_title"].replace("_", " ")
                        )
                    elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                        bubble_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Maximum "
                            + chart_axis[f"{column_name}_title"].replace("_", " ")
                        )
                    else:
                        bubble_chart_json_dict[f"y{yAxis_idx}Name"] = (
                            "Total "
                            + chart_axis[f"{column_name}_title"].replace("_", " ")
                        )
                else:
                    bubble_chart_json_dict[f"y{yAxis_idx}Name"] = "Total " + chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")

                if not (
                    isinstance(bubble_chart_json_dict[f"Y{yAxis_idx}"][0], int)
                    or isinstance(bubble_chart_json_dict[f"Y{yAxis_idx}"][0], float)
                ):
                    code_level_logger.error(
                        f"bubbleplot_chart: Y{yAxis_idx}-axis is not integer or float!",
                    )
                    raise RuntimeError(
                        f"bubbleplot_chart: Y{yAxis_idx}-axis is not integer or float!",
                    )

                # if (
                #     check_negative_value(scatterplot_chart_json_dict[f"Y{yAxis_idx}"])
                #     or scatterplot_chart_json_dict["Chart_Type"] == "column_chart"
                # ):
                #     return generate_group_column_chart_d3(
                #         llama70b_client,
                #         user_query,
                #         chart_id,
                #         sql_query,
                #         chart_title,
                #         chart_axis,
                #         chart_data,
                #         database_properties,
                #         ups_idx,
                #         chart_position,
                #         overall_title,
                #         client_id,
                #         user_id,
                #         sql_library,
                #         logging_url,
                #     )

            yAxis_idx += 1

    if bubble_chart_json_dict["Y"] == []:
        code_level_logger.error("bubbleplot_chart: Y-Axis is not found in extraction!")
        raise RuntimeError("bubbleplot_chart: Y-Axis is not found in extraction!")

    if any(
        bubble_chart_json_dict[key] == [] or bubble_chart_json_dict[key] == [""]
        for key in bubble_chart_json_dict
        if re.match(r"^X\d*$", key)
    ):
        code_level_logger.error(
            "bubbleplot_chart: One or more X-axis values are empty!"
        )
        raise RuntimeError("bubbleplot_chart: One or more X-axis values are empty!")

    chart_data_lists: list = []

    # Check for the main Y and its corresponding X
    if (
        "X" not in bubble_chart_json_dict
        or "Y" not in bubble_chart_json_dict
        or "Z" not in bubble_chart_json_dict
    ):
        code_level_logger.error("Bubbleplot chart doesn't contain 'X' / 'Y' / 'Z' !")
        raise RuntimeError("Bubbleplot chart doesn't contain 'X' / 'Y' / 'Z' !")

    x_values: list = list(bubble_chart_json_dict["X"])
    main_group_name = bubble_chart_json_dict.get("yName", "Series 1")

    for i in range(len(x_values)):
        x_value = float(x_values[i])
        main_y_value = bubble_chart_json_dict["Y"][i]
        main_z_value = bubble_chart_json_dict["Z"][i]
        chart_data_lists.append(
            {
                "X_Value": x_value,
                "Y_Value": main_y_value,
                "Z_Value": main_z_value,
                "Group_Name": main_group_name,
            },
        )

    # Check for additional Y values (Y2, Y3, ...)
    j = 2
    while f"Y{j}" in bubble_chart_json_dict.keys():
        # Corresponding X values for Y2, Y3, etc.
        x_key = f"X{j}"
        if x_key in bubble_chart_json_dict.keys():
            x_values = bubble_chart_json_dict[x_key]
            group_name_key = f"y{j}Name"
            group_name = bubble_chart_json_dict.get(group_name_key, f"Series {j}")

            for i in range(len(x_values)):
                x_value = float(x_values[i])
                y_key = f"Y{j}"
                z_key = f"Z{j}"
                if y_key in bubble_chart_json_dict.keys():
                    additional_y_value = bubble_chart_json_dict[y_key][i]
                    additional_z_value = bubble_chart_json_dict[z_key][i]
                    chart_data_lists.append(
                        {
                            "X_Value": x_value,
                            "Y_Value": additional_y_value,
                            "Z_Value": additional_z_value,
                            "Group_Name": group_name,
                        },
                    )

        j += 1

    # Store chart data in the original dict
    bubble_chart_json_dict["Chart_Data"] = chart_data_lists

    bubble_chart_json_dict["Database_Identifier"] = database_properties["db_tag"]

    bubble_chart_json_dict["Client_ID"] = client_id
    bubble_chart_json_dict["User_ID"] = user_id
    bubble_chart_json_dict["Session_ID"] = session_id

    keys_to_remove = ["X", "Y", "Z", "yName"]

    i = 2
    while f"y{i}Name" in bubble_chart_json_dict:
        keys_to_remove.append(f"y{i}Name")
        i += 1

    j = 2
    while (
        f"X{j}" in bubble_chart_json_dict
        and f"Y{j}" in bubble_chart_json_dict
        and f"Z{j}" in bubble_chart_json_dict
    ):
        keys_to_remove.append(f"X{j}")
        keys_to_remove.append(f"Y{j}")
        keys_to_remove.append(f"Z{j}")
        j += 1

    # Remove all specified keys ['X', 'Y', 'Z', 'yName'] and etc. from the dictionary
    for key in keys_to_remove:
        if key in bubble_chart_json_dict:
            del bubble_chart_json_dict[key]

    return bubble_chart_json_dict


CHART_TYPE_FUNCTIONS_D3: dict = {
    "bar_chart": generate_bar_chart_d3,
    "column_chart": generate_column_chart_d3,
    "barlinecombo_chart": generate_combo_chart_d3,
    "line_chart": generate_line_chart_d3,
    "spline_chart": generate_spline_chart_d3,
    "scatterplot_chart": generate_scatterplot_chart_d3,
    "grouped_column_chart": generate_group_column_chart_d3,
    "grouped_bar_chart": generate_group_bar_chart_d3,
    "radar_chart": generate_radar_chart_d3,
    "histogram_chart": generate_histogram_chart_d3,
    "area_chart": generate_area_chart_d3,
    "pie_chart": generate_pie_chart_d3,
    "bubbleplot_chart": generate_bubbleplot_chart_d3,
    "pyramidfunnel_chart": generate_pyramid_chart_d3,
    "TreemapMulti_chart": generate_treemap_chart_d3,
    "table_chart": generate_table_chart_d3,
    "full_table_chart": generate_table_chart_d3,
    "aggregated_table_chart": generate_table_chart_d3,
}


def arrange_json(chart_jsons: list) -> list:
    new_chart_jsons = []

    new_chart_position = 1
    for chart_json in chart_jsons:
        # continue when empty
        if chart_json == {}:
            continue

        chart_json["Chart_Position"] = str(new_chart_position)
        if "Aggregated_Table_JSON" in chart_json.keys():
            chart_json["Aggregated_Table_JSON"]["Chart_Position"] = str(
                new_chart_position,
            )

        new_chart_jsons.append(chart_json)
        new_chart_position += 1

    return new_chart_jsons


def get_yAxis_columns_from_chart_axis(
    chart_axis: dict,
):
    yAxis_columns = []
    for key in chart_axis:
        if "yaxis" in key.lower() and "column" in key.lower():
            if isinstance(chart_axis[key], str) and chart_axis[key] != "":
                yAxis_columns.append(chart_axis[key])
            elif isinstance(chart_axis[key], list) and chart_axis[key] != []:
                yAxis_columns.extend(chart_axis[key])

    yAxis_columns = list(set(yAxis_columns))
    return yAxis_columns


def extract_chart_data_d3(
    llama70b_client: Any,
    user_query: str,
    data_summary: DataSummary,
    chart_data: dict,
    sql_library: str,
    database_properties: dict,
    ups_idx: int,
    client_id: str,
    user_id: str,
    database_name: str,
    logging_url: str,
    session_id: str,
    code_level_logger: logging.Logger,
):
    with PerformanceLogger(session_id):
        chart_jsons = []

        chart_position = 1
        main_chart_type = chart_data["main_chart_type"]
        sub_question_datas = chart_data["sub_questions"]

        main_chart_title = chart_data["main_title"]
        main_chart_axis = chart_data["main_chart_axis"]
        main_chart_sql = chart_data["main_chart_sql"]
        main_chart_data = chart_data["chart_data"]
        overall_title = chart_data["overall_title"]
        main_chart_id = chart_data["chart_id"]

        # Validate date xAxis_title (e.g., 'Month', 'Year', 'Week')
        if "xAxis_title" in main_chart_axis.keys():
            if "xAxis" in main_chart_data.columns:
                main_chart_axis["xAxis_title"] = validate_and_fix_xAxis_title(
                    main_chart_axis["xAxis_title"],
                    main_chart_data["xAxis"],
                )
            elif (
                isinstance(main_chart_axis["xAxis_column"], str)
                and main_chart_axis["xAxis_column"] in main_chart_data.columns
            ):
                main_chart_axis["xAxis_title"] = validate_and_fix_xAxis_title(
                    main_chart_axis["xAxis_title"],
                    main_chart_data[main_chart_axis["xAxis_column"]],
                )

        if main_chart_type in ["area_chart", "line_chart"]:
            if (
                isinstance(main_chart_axis["xAxis_column"], str)
                and main_chart_axis["xAxis_column"]
                in data_summary.column_data_tribes.keys()
                and data_summary.column_data_tribes[main_chart_axis["xAxis_column"]]
                in ["categorical", "id"]
            ):
                chart_data["main_chart_type"] = main_chart_type = "grouped_bar_chart"

        # Empty Data Frame
        if (not isinstance(main_chart_data, pd.DataFrame)) or (
            main_chart_data.empty or main_chart_data.iloc[:, 0].isna().all()
        ):
            print(f"Error Main Chart Type: {main_chart_type}")
            print(f"Error Chart title: {main_chart_title}")
            print(f"Error Chart Axis: {main_chart_axis}")
            print(f"Error Chart SQL: {main_chart_sql}")
            print(f"Error Chart Data: {main_chart_data}")
            print(f"Error Chart overall title: {overall_title}")
            print("Error: Empty Pandas Dataframe")
            print()
            code_level_logger.error(
                f"Error: Empty Pandas Dataframe.\nError Main Chart Type: {main_chart_type}\nError Chart title: {main_chart_title}\nError Chart Axis: {main_chart_axis}\nError Chart SQL: {main_chart_sql}\nError Chart Data: {main_chart_data}\nError Chart overall title: {overall_title}"
            )
            # return chart_jsons
        else:
            yAxis_columns = get_yAxis_columns_from_chart_axis(main_chart_axis)
            yAxis_zero = []

            for column_name in data_summary.column_name_list.copy():
                if column_name not in main_chart_data.columns:
                    continue

                if "yAxis" not in column_name and column_name not in yAxis_columns:
                    continue

                if (main_chart_data[column_name] == 0).all() or main_chart_data[
                    column_name
                ].isna().all():
                    yAxis_zero.append(True)
                else:
                    yAxis_zero.append(False)

            # if main_chart_type != "histogram_chart":
            #     try:
            #         new_main_chart_axis = _fix_axis_titles(
            #             llama70b_client,
            #             database_summary,
            #             main_chart_sql,
            #             main_chart_axis,
            #         )
            #     except Exception:
            #         print(traceback.format_exc())

            if not all(yAxis_zero) or yAxis_zero == []:
                try:
                    chart_json = CHART_TYPE_FUNCTIONS_D3[main_chart_type](
                        llama70b_client,
                        user_query,
                        main_chart_id,
                        main_chart_sql,
                        main_chart_title,
                        main_chart_axis,  # new_main_chart_axis
                        main_chart_data,
                        database_properties,
                        ups_idx,
                        chart_position,
                        overall_title,
                        client_id,
                        user_id,
                        session_id,
                        sql_library,
                        logging_url,
                        code_level_logger,
                    )

                    chart_position += 1
                    chart_jsons.append(chart_json)
                except Exception:
                    print(f"Error Main Chart Type: {main_chart_type}")
                    print(f"Error Chart title: {main_chart_title}")
                    print(f"Error Chart Axis: {main_chart_axis}")
                    print(f"Error Chart SQL: {main_chart_sql}")
                    print(f"Error Chart Data: {main_chart_data}")
                    print(f"Error Chart overall title: {overall_title}")
                    print(traceback.format_exc())
                    print()
                    code_level_logger.error(
                        f"{traceback.format_exc()}\nError Main Chart Type: {main_chart_type}\nError Chart title: {main_chart_title}\nError Chart Axis: {main_chart_axis}\nError Chart SQL: {main_chart_sql}\nError Chart Data: {main_chart_data}\nError Chart overall title: {overall_title}"
                    )

        for sub_question_data_idx, sub_question_data in enumerate(sub_question_datas):
            sub_chart_type = sub_question_data["chart_type"]
            sub_chart_title = sub_question_data["chart_title"]
            sub_chart_axis = sub_question_data["chart_axis"]
            sub_chart_sql = sub_question_data["chart_sql"]
            sub_chart_data = sub_question_data["chart_data"]
            sub_chart_id = sub_question_data["chart_id"]

            # Validate date xAxis_title (e.g., 'Month', 'Year', 'Week')
            if "xAxis_title" in sub_chart_axis.keys():
                if "xAxis" in sub_chart_data.columns:
                    sub_chart_axis["xAxis_title"] = validate_and_fix_xAxis_title(
                        sub_chart_axis["xAxis_title"],
                        sub_chart_data["xAxis"],
                    )
                elif (
                    isinstance(sub_chart_axis["xAxis_column"], str)
                    and sub_chart_axis["xAxis_column"] in sub_chart_data.columns
                ):
                    sub_chart_axis["xAxis_title"] = validate_and_fix_xAxis_title(
                        sub_chart_axis["xAxis_title"],
                        sub_chart_data[sub_chart_axis["xAxis_column"]],
                    )

            if sub_chart_type in ["area_chart", "line_chart"]:
                if (
                    isinstance(sub_chart_axis["xAxis_column"], str)
                    and sub_chart_axis["xAxis_column"]
                    in data_summary.column_data_tribes.keys()
                    and data_summary.column_data_tribes[sub_chart_axis["xAxis_column"]]
                    in ["categorical", "id"]
                ):
                    sub_question_data["chart_type"] = sub_question_datas[
                        sub_question_data_idx
                    ]["chart_type"] = sub_chart_type = "grouped_bar_chart"

            # Empty Data Frame
            if (not isinstance(sub_chart_data, pd.DataFrame)) or (
                sub_chart_data.empty or sub_chart_data.iloc[:, 0].isna().all()
            ):
                print(f"Error Sub Chart Type: {sub_chart_type}")
                print(f"Error Chart title: {sub_chart_title}")
                print(f"Error Chart Axis: {sub_chart_axis}")
                print(f"Error Chart SQL: {sub_chart_sql}")
                print(f"Error Chart Data: {sub_chart_data}")
                print(f"Error Chart overall title: {overall_title}")
                print(traceback.format_exc())
                print()
                code_level_logger.error(
                    f"{traceback.format_exc()}\nError Main Chart Type: {main_chart_type}\nError Chart title: {main_chart_title}\nError Chart Axis: {main_chart_axis}\nError Chart SQL: {main_chart_sql}\nError Chart Data: {main_chart_data}\nError Chart overall title: {overall_title}"
                )
                continue
            yAxis_columns = get_yAxis_columns_from_chart_axis(sub_chart_axis)
            yAxis_zero = []

            for column_name in data_summary.column_name_list.copy():
                if column_name not in sub_chart_data.columns:
                    continue

                if "yAxis" not in column_name and column_name not in yAxis_columns:
                    continue

                if (sub_chart_data[column_name] == 0).all() or sub_chart_data[
                    column_name
                ].isna().all():
                    yAxis_zero.append(True)
                else:
                    yAxis_zero.append(False)

            # if sub_chart_type != "histogram_chart":
            #     try:
            #         new_sub_chart_axis = _fix_axis_titles(
            #             llama70b_client,
            #             database_summary,
            #             sub_chart_sql,
            #             sub_chart_axis,
            #         )
            #     except Exception:
            #         print(traceback.format_exc())
            if not all(yAxis_zero) or yAxis_zero == []:
                try:
                    chart_json = CHART_TYPE_FUNCTIONS_D3[sub_chart_type](
                        llama70b_client,
                        user_query,
                        sub_chart_id,
                        sub_chart_sql,
                        sub_chart_title,
                        sub_chart_axis,  # new_sub_chart_axis
                        sub_chart_data,
                        database_properties,
                        ups_idx,
                        chart_position,
                        overall_title,
                        client_id,
                        user_id,
                        sql_library,
                        logging_url,
                        code_level_logger,
                    )

                    chart_jsons.append(chart_json)
                    chart_position += 1
                except Exception:
                    print(f"Error Sub Chart Type: {sub_chart_type}")
                    print(f"Error Chart title: {sub_chart_title}")
                    print(f"Error Chart Axis: {sub_chart_axis}")
                    print(f"Error Chart SQL: {sub_chart_sql}")
                    print(f"Error Chart Data: {sub_chart_data}")
                    print(f"Error Chart overall title: {overall_title}")
                    print(traceback.format_exc())
                    code_level_logger.error(
                        f"{traceback.format_exc()}\nError Main Chart Type: {main_chart_type}\nError Chart title: {main_chart_title}\nError Chart Axis: {main_chart_axis}\nError Chart SQL: {main_chart_sql}\nError Chart Data: {main_chart_data}\nError Chart overall title: {overall_title}"
                    )
                    print()
                    continue

        if chart_jsons == []:
            return []

        chart_jsons = arrange_json(chart_jsons)
        chart_jsons_copy = chart_jsons[0].copy()

        keys_to_drop = [
            "Client_ID",
            "User_ID",
            "User_Query",
            "Visual_Title",
            "Chart_Data",
            "Chart_Query",
            "Chart_Type",
            "Chart_Title",
        ]

        keys_to_drop_aggregated = [
            "Subscription_ID",
            "Subscription_Name",
            "Client_ID",
            "User_ID",
            "User_Query",
            "Chart_Name",
            "Chart_Query",
            "Chart_SQL_Library",
            "Chart_Position",
            "Visual_Title",
            "Chart_ID",
            "Chart_Title",
            "data",
        ]

        for key in keys_to_drop:
            chart_jsons_copy.pop(key, None)

        # Handle the nested 'Aggregated_Table_JSON' key if it exists
        if "Aggregated_Table_JSON" in chart_jsons_copy:
            aggregated_table = chart_jsons_copy["Aggregated_Table_JSON"]

            # Ensure it is a dictionary
            if isinstance(aggregated_table, dict):
                for key in keys_to_drop_aggregated:
                    aggregated_table.pop(key, None)
            else:
                code_level_logger.error("Aggregated_Table_JSON is not a dictionary!")
                raise RuntimeError("Aggregated_Table_JSON is not a dictionary!")

        log_chart_data = {
            "chart_id": chart_jsons_copy["Chart_ID"],
            "chart_name": chart_jsons_copy["Chart_Name"],
            "chart_position": chart_jsons_copy["Chart_Position"],
            "chart_json": str(chart_jsons_copy),
        }

        logging_url_chart = logging_url + "chart"
        requests.post(logging_url_chart, json=log_chart_data, verify=False)

        return chart_jsons


def extract_chart_data_testcase(
    llama70b_client: Any,
    user_query: str,
    data_summary: DataSummary,
    chart_data: dict,
    sql_library: str,
    database_properties: dict,
    ups_idx: int,
    client_id: str,
    user_id: str,
    database_name: str,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    chart_jsons = []

    chart_position = 1
    main_chart_type = chart_data["main_chart_type"]
    sub_question_datas = chart_data["sub_questions"]

    main_chart_title = chart_data["main_title"]
    main_chart_axis = chart_data["main_chart_axis"]
    main_chart_sql = chart_data["main_chart_sql"]
    main_chart_data = chart_data["chart_data"]
    main_chart_id = chart_data["chart_id"]
    overall_title = chart_data["overall_title"]

    # Validate date xAxis_title (e.g., 'Month', 'Year', 'Week')
    if "xAxis_title" in main_chart_axis.keys():
        if "xAxis" in main_chart_data.columns:
            main_chart_axis["xAxis_title"] = validate_and_fix_xAxis_title(
                main_chart_axis["xAxis_title"],
                main_chart_data["xAxis"],
            )
        elif (
            isinstance(main_chart_axis["xAxis_column"], str)
            and main_chart_axis["xAxis_column"] in main_chart_data.columns
        ):
            main_chart_axis["xAxis_title"] = validate_and_fix_xAxis_title(
                main_chart_axis["xAxis_title"],
                main_chart_data[main_chart_axis["xAxis_column"]],
            )

    if main_chart_type in ["area_chart", "line_chart"]:
        if (
            isinstance(main_chart_axis["xAxis_column"], str)
            and main_chart_axis["xAxis_column"]
            in data_summary.column_data_tribes.keys()
            and data_summary.column_data_tribes[main_chart_axis["xAxis_column"]]
            in ["categorical", "id"]
        ):
            chart_data["main_chart_type"] = main_chart_type = "grouped_bar_chart"

    # Empty Data Frame
    if (not isinstance(main_chart_data, pd.DataFrame)) or (
        main_chart_data.empty or main_chart_data.iloc[:, 0].isna().all()
    ):
        print(f"Error Main Chart Type: {main_chart_type}")
        print(f"Error Chart title: {main_chart_title}")
        print(f"Error Chart Axis: {main_chart_axis}")
        print(f"Error Chart SQL: {main_chart_sql}")
        print(f"Error Chart Data: {main_chart_data}")
        print(f"Error Chart overall title: {overall_title}")
        print("Error: Empty Pandas Dataframe")
        print()
        # return chart_jsons
    else:
        yAxis_columns = get_yAxis_columns_from_chart_axis(main_chart_axis)
        yAxis_zero = []

        for column_name in data_summary.column_name_list.copy():
            if column_name not in main_chart_data.columns:
                continue

            if "yAxis" not in column_name and column_name not in yAxis_columns:
                continue

            if (main_chart_data[column_name] == 0).all() or main_chart_data[
                column_name
            ].isna().all():
                yAxis_zero.append(True)
            else:
                yAxis_zero.append(False)

        if not all(yAxis_zero) or yAxis_zero == []:
            try:
                chart_json = CHART_TYPE_FUNCTIONS_D3[main_chart_type](
                    llama70b_client,
                    user_query,
                    main_chart_id,
                    main_chart_sql,
                    main_chart_title,
                    main_chart_axis,
                    main_chart_data,
                    database_properties,
                    ups_idx,
                    chart_position,
                    overall_title,
                    client_id,
                    user_id,
                    sql_library,
                    logging_url,
                    code_level_logger,
                )

                chart_position += 1
                chart_jsons.append(chart_json)
                chart_data["main_chart_json"] = chart_json
            except Exception:
                print(f"Error Main Chart Type: {main_chart_type}")
                print(f"Error Chart title: {main_chart_title}")
                print(f"Error Chart Axis: {main_chart_axis}")
                print(f"Error Chart SQL: {main_chart_sql}")
                print(f"Error Chart Data: {main_chart_data}")
                print(f"Error Chart overall title: {overall_title}")
                print(traceback.format_exc())
                print()
                # return chart_jsons

    for sub_question_data_idx, sub_question_data in enumerate(sub_question_datas):
        sub_chart_type = sub_question_data["chart_type"]
        sub_chart_title = sub_question_data["chart_title"]
        sub_chart_axis = sub_question_data["chart_axis"]
        sub_chart_sql = sub_question_data["chart_sql"]
        sub_chart_data = sub_question_data["chart_data"]
        sub_chart_id = sub_chart_data["chart_id"]

        # Validate date xAxis_title (e.g., 'Month', 'Year', 'Week')
        if "xAxis_title" in sub_chart_axis.keys():
            if "xAxis" in sub_chart_data.columns:
                sub_chart_axis["xAxis_title"] = validate_and_fix_xAxis_title(
                    sub_chart_axis["xAxis_title"],
                    sub_chart_data["xAxis"],
                )
            elif (
                isinstance(sub_chart_axis["xAxis_column"], str)
                and sub_chart_axis["xAxis_column"] in sub_chart_data.columns
            ):
                sub_chart_axis["xAxis_title"] = validate_and_fix_xAxis_title(
                    sub_chart_axis["xAxis_title"],
                    sub_chart_data[sub_chart_axis["xAxis_column"]],
                )

        if sub_chart_type in ["area_chart", "line_chart"]:
            if (
                isinstance(sub_chart_axis["xAxis_column"], str)
                and sub_chart_axis["xAxis_column"]
                in data_summary.column_data_tribes.keys()
                and data_summary.column_data_tribes[sub_chart_axis["xAxis_column"]]
                in ["categorical", "id"]
            ):
                sub_question_data["chart_type"] = sub_question_datas[
                    sub_question_data_idx
                ]["chart_type"] = sub_chart_type = "grouped_bar_chart"

        # Empty Data Frame
        if (not isinstance(sub_chart_data, pd.DataFrame)) or (
            sub_chart_data.empty or sub_chart_data.iloc[:, 0].isna().all()
        ):
            print(f"Error Sub Chart Type: {sub_chart_type}")
            print(f"Error Chart title: {sub_chart_title}")
            print(f"Error Chart Axis: {sub_chart_axis}")
            print(f"Error Chart SQL: {sub_chart_sql}")
            print(f"Error Chart Data: {sub_chart_data}")
            print(f"Error Chart overall title: {overall_title}")
            print(traceback.format_exc())
            print()
            continue
        yAxis_columns = get_yAxis_columns_from_chart_axis(sub_chart_axis)
        yAxis_zero = []

        for column_name in data_summary.column_name_list.copy():
            if column_name not in sub_chart_data.columns:
                continue

            if "yAxis" not in column_name and column_name not in yAxis_columns:
                continue

            if (sub_chart_data[column_name] == 0).all() or sub_chart_data[
                column_name
            ].isna().all():
                yAxis_zero.append(True)
            else:
                yAxis_zero.append(False)

        if not all(yAxis_zero) or yAxis_zero == []:
            try:
                chart_json = CHART_TYPE_FUNCTIONS_D3[sub_chart_type](
                    llama70b_client,
                    user_query,
                    sub_chart_id,
                    sub_chart_sql,
                    sub_chart_title,
                    sub_chart_axis,
                    sub_chart_data,
                    database_properties,
                    ups_idx,
                    chart_position,
                    overall_title,
                    client_id,
                    user_id,
                    sql_library,
                    code_level_logger,
                )

                chart_jsons.append(chart_json)
                chart_position += 1
                sub_question_datas[sub_question_data_idx]["chart_json"] = chart_json
            except Exception:
                print(f"Error Sub Chart Type: {sub_chart_type}")
                print(f"Error Chart title: {sub_chart_title}")
                print(f"Error Chart Axis: {sub_chart_axis}")
                print(f"Error Chart SQL: {sub_chart_sql}")
                print(f"Error Chart Data: {sub_chart_data}")
                print(f"Error Chart overall title: {overall_title}")
                print(traceback.format_exc())
                # logger.error(traceback.format_exc())
                print()
                continue

    chart_data["sub_questions"] = sub_question_datas
    chart_jsons = arrange_json(chart_jsons)

    return chart_jsons


def extract_beautiful_table_data(
    llama70b_client: Any,
    user_query: str,
    chart_id: str,
    chart_sql: str,
    chart_title: str,
    chart_axis: dict,
    chart_data: pd.DataFrame,
    database_properties: dict,
    ups_idx: int,
    chart_position: int,
    overall_title: str,
    client_id: str,
    user_id: str,
    session_id: str,
    sql_library: str,
    database_name: str,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    chart_json = CHART_TYPE_FUNCTIONS_D3["table_chart"](
        llama70b_client,
        user_query,
        chart_id,
        chart_sql,
        chart_title,
        chart_axis,
        chart_data,
        database_properties,
        ups_idx,
        chart_position,
        overall_title,
        client_id,
        user_id,
        session_id,
        sql_library,
        logging_url,
        code_level_logger,
    )
    chart_json["Chart_Name"] = "Table"
    chart_json["Chart_Type"] = "full_table_chart"

    return chart_json


def determine_date_frequency(
    date_series: pd.Series,
) -> Union[Tuple[str, pd.Series], Tuple[None, None]]:
    date_series = pd.to_datetime(date_series, errors="coerce")

    if date_series.isna().all():
        return None, None

    date_diffs = date_series.diff().dropna()

    if (date_diffs == pd.Timedelta(days=1)).all():
        return "daily", date_series.dt.strftime("%Y-%m-%d")
    if (date_diffs >= pd.Timedelta(days=28)).all() and (
        date_diffs <= pd.Timedelta(days=31)
    ).all():
        return "monthly", date_series.dt.strftime("%Y-%m")
    if (date_diffs >= pd.Timedelta(days=365)).all() and (
        date_diffs <= pd.Timedelta(days=366)
    ).all():
        return "yearly", date_series.dt.to_period("Y").astype(str)

    return "irregular", date_series.dt.strftime("%Y-%m-%d")
