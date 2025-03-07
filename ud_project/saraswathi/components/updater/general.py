import datetime
import decimal
import os
import requests
import re
import sys
import traceback
import logging
import numpy as np
import pandas as pd

from time import perf_counter
from typing import Any
from ..executor import execute_sql_query_updater
from ..extractor import check_aggregation_phrases
from ..insights import (
    generate_business_recommendation_chart,
    generate_visual_description_chart,
)
from ..postprocess import postprocess_updater_chart_json
from ..utils import (
    is_within_max_length,
    map_original_list_with_sorted_x,
    sort_pandas_date,
    calculate_token_usage,
)


def check_negative_value(value_list: list):
    is_negative = False
    for value in value_list:
        if isinstance(value, int) or isinstance(value, float):
            if value < 0:
                is_negative = True
                break

    return is_negative


def update_aggregated_table_chart_d3(
    chart_json: dict,
    chart_data: pd.DataFrame,
    chart_axis: dict,
    base_chart_type: str,
):
    new_data = []

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

            new_data.append(row_data)
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

                    for x in chart_column_data:
                        row_data = {
                            chart_axis["xAxis_title"].replace("_", " "): x,
                        }
                        new_data.append(row_data)
                    break
            except Exception:
                print(traceback.format_exc())
    elif base_chart_type in [
        "bubbleplot_chart",
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
            new_data.append(row_data)
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
            new_data.append(row_data)

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
            new_data.append(row_data)

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
            new_data.append(row_data)
    else:
        raise RuntimeError(
            f"{base_chart_type} Chart Type is not supported in generate aggregated table chart!",
        )

    chart_json["data"] = new_data
    chart_json["Chart_Size"] = sys.getsizeof(chart_json["data"])

    return chart_json


def update_card_chart_from_histogram_chart_d3(
    llama70b_client: Any,
    chart_json: dict,
    chart_data: pd.DataFrame,
    logging_url: str,
):
    # Reassign chart type to card_chart
    chart_json["Chart_Type"] = "card_chart"

    chart_json["Aggregated_Table_JSON"] = update_aggregated_table_chart_d3(
        chart_json["Aggregated_Table_JSON"],
        chart_data,
        chart_json["Chart_Axis"],
        chart_json["Original_Chart_Type"],
    )
    chart_axis = chart_json["Chart_Axis"]

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
        "xAxis_column" in chart_axis.keys()
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
        "xAxis_column" in chart_axis.keys()
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
        "xAxis_title" in chart_axis.keys()
        and chart_axis["xAxis_title"] in chart_data.columns
    ) or (
        "xAxis_title" in chart_axis.keys()
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
                    chart_json_dict = CHART_TYPE_UPDATER_FUNCTIONS_D3[
                        chart_json["Original_Chart_Type"]
                    ](
                        llama70b_client,
                        chart_json,
                        chart_data,
                        logging_url,
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
        chart_json["Y"] = (
            f"{round(chart_data[chart_column_name_found].values.tolist()[0], 2)}"
        )
    else:
        chart_json["Y"] = f"{chart_data[chart_column_name_found].values.tolist()[0]}"

    return chart_json


def update_card_chart_d3(
    llama70b_client: Any,
    chart_json: dict,
    chart_data: pd.DataFrame,
    logging_url: str,
):
    # Reassign chart type to card_chart
    chart_json["Chart_Type"] = "card_chart"

    if chart_json["Original_Chart_Type"] == "histogram_chart":
        return update_card_chart_from_histogram_chart_d3(
            llama70b_client,
            chart_json,
            chart_data,
            logging_url,
        )

    chart_json["Aggregated_Table_JSON"] = update_aggregated_table_chart_d3(
        chart_json["Aggregated_Table_JSON"],
        chart_data,
        chart_json["Chart_Axis"],
        chart_json["Original_Chart_Type"],
    )
    chart_axis = chart_json["Chart_Axis"]

    chart_data_columns = list(chart_data.columns)

    if "xAxis" in chart_data_columns:
        xAxis_column_name = "xAxis"
    elif (
        "xAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["xAxis_column"], str)
        and chart_axis["xAxis_column"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_column"]
    elif (
        "xAxis_title" in chart_axis.keys()
        and chart_axis["xAxis_title"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_title"]
    else:
        raise RuntimeError("card_chart: X-Axis is not found in extraction!")

    if "yAxis" in chart_data_columns:
        yAxis_column_name = "yAxis"
    elif (
        "yAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["yAxis_column"], str)
        and chart_axis["yAxis_column"] in chart_data_columns
    ):
        yAxis_column_name = chart_axis["yAxis_column"]
    else:
        raise RuntimeError("card_chart: Y-Axis is not found in extraction!")

    y_values = chart_data[yAxis_column_name].values.tolist()

    if len(y_values) > 1:
        return CHART_TYPE_UPDATER_FUNCTIONS_D3[chart_json["Original_Chart_Type"]](
            llama70b_client,
            chart_json,
            chart_data,
            logging_url,
        )
    if len(y_values) <= 0:
        return chart_json
    single_value = y_values[0]

    if isinstance(single_value, int):
        chart_json["Y"] = f"{int(single_value):,}"
    elif isinstance(single_value, (float, decimal.Decimal)):
        chart_json["Y"] = f"{round(float(single_value), 2):,.2f}"
    else:
        chart_json["Y"] = str(single_value)

    if not (
        str(chart_data[xAxis_column_name].values.tolist()[0]) == "0"
        or str(chart_data[xAxis_column_name].values.tolist()[0]) == "nan"
    ):
        description = str(chart_data[xAxis_column_name].values.tolist()[0]).strip()
        chart_json["Y"] = f"{chart_json['Y']!s}\n({description})"

    return chart_json


def convert_to_card_chart_from_histogram_chart_d3(
    llama70b_client: Any,
    chart_json: dict,
    chart_data: pd.DataFrame,
    logging_url: str,
):
    chart_json["Original_Chart_Type"] = chart_json["Chart_Type"]
    chart_json["Chart_Type"] = "card_chart"
    chart_json["Aggregated_Table_JSON"] = update_aggregated_table_chart_d3(
        chart_json["Aggregated_Table_JSON"],
        chart_data,
        chart_json["Chart_Axis"],
        chart_json["Original_Chart_Type"],
    )
    chart_axis = chart_json["Chart_Axis"]

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
        "xAxis_column" in chart_axis.keys()
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
        "xAxis_column" in chart_axis.keys()
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
        "xAxis_title" in chart_axis.keys()
        and chart_axis["xAxis_title"] in chart_data.columns
    ) or (
        "xAxis_title" in chart_axis.keys()
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
                    chart_json_dict = CHART_TYPE_UPDATER_FUNCTIONS_D3[
                        chart_json["Original_Chart_Type"]
                    ](
                        llama70b_client,
                        chart_json,
                        chart_data,
                        logging_url,
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
        chart_json["Y"] = (
            f"{round(chart_data[chart_column_name_found].values.tolist()[0], 2)}"
        )
    else:
        chart_json["Y"] = f"{chart_data[chart_column_name_found].values.tolist()[0]}"

    chart_json["yAxis"] = chart_json["yAxis"].replace("_", " ")
    chart_json["yAxis_Description"] = chart_json["yAxis_Description"].replace("_", " ")

    if not check_aggregation_phrases(chart_json["yAxis"]):
        if "yAxis_aggregation" in chart_axis.keys():
            if chart_axis["yAxis_aggregation"] in ["SUM"]:
                chart_json["yAxis"] = "Total " + chart_json["yAxis"]
                chart_json["yAxis_Description"] = (
                    "Total " + chart_json["yAxis_Description"]
                )
            elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
                chart_json["yAxis"] = "Average " + chart_json["yAxis"]
                chart_json["yAxis_Description"] = (
                    "Average " + chart_json["yAxis_Description"]
                )
            elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
                chart_json["yAxis"] = "Median " + chart_json["yAxis"]
                chart_json["yAxis_Description"] = (
                    "Median " + chart_json["yAxis_Description"]
                )
            elif chart_axis["yAxis_aggregation"] in ["MIN"]:
                chart_json["yAxis"] = "Minimum " + chart_json["yAxis"]
                chart_json["yAxis_Description"] = (
                    "Minimum " + chart_json["yAxis_Description"]
                )
            elif chart_axis["yAxis_aggregation"] in ["MAX"]:
                chart_json["yAxis"] = "Maximum " + chart_json["yAxis"]
                chart_json["yAxis_Description"] = (
                    "Maximum " + chart_json["yAxis_Description"]
                )
            else:
                chart_json["yAxis"] = "Total " + chart_json["yAxis"]
                chart_json["yAxis_Description"] = (
                    "Total " + chart_json["yAxis_Description"]
                )
        else:
            chart_json["yAxis"] = "Total " + chart_json["yAxis"]
            chart_json["yAxis_Description"] = "Total " + chart_json["yAxis_Description"]

    return chart_json


def convert_to_card_chart_d3(
    llama70b_client: Any,
    chart_json: dict,
    chart_data: pd.DataFrame,
    logging_url: str,
):
    if chart_json["Chart_Type"] == "histogram_chart":
        return convert_to_card_chart_from_histogram_chart_d3(
            llama70b_client,
            chart_json,
            chart_data,
            logging_url,
        )

    chart_json["Original_Chart_Type"] = chart_json["Chart_Type"]
    chart_json["Chart_Type"] = "card_chart"
    chart_json["Aggregated_Table_JSON"] = update_aggregated_table_chart_d3(
        chart_json["Aggregated_Table_JSON"],
        chart_data,
        chart_json["Chart_Axis"],
        chart_json["Original_Chart_Type"],
    )
    chart_axis = chart_json["Chart_Axis"]

    chart_data_columns = list(chart_data.columns)

    if "xAxis" in chart_data_columns:
        xAxis_column_name = "xAxis"
    elif (
        "xAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["xAxis_column"], str)
        and chart_axis["xAxis_column"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_column"]
    elif (
        "xAxis_title" in chart_axis.keys()
        and chart_axis["xAxis_title"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_title"]
    else:
        raise RuntimeError("card_chart: X-Axis is not found in extraction!")

    if "yAxis" in chart_data_columns:
        yAxis_column_name = "yAxis"
    elif (
        "yAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["yAxis_column"], str)
        and chart_axis["yAxis_column"] in chart_data_columns
    ):
        yAxis_column_name = chart_axis["yAxis_column"]
    else:
        raise RuntimeError("card_chart: Y-Axis is not found in extraction!")

    y_values = chart_data[yAxis_column_name].values.tolist()

    if len(y_values) > 1:
        return CHART_TYPE_UPDATER_FUNCTIONS_D3[chart_json["Original_Chart_Type"]](
            llama70b_client,
            chart_json,
            chart_data,
            logging_url,
        )
    if len(y_values) <= 0:
        return chart_json
    single_value = y_values[0]

    if isinstance(single_value, int):
        chart_json["Y"] = f"{int(single_value):,}"
    elif isinstance(single_value, (float, decimal.Decimal)):
        chart_json["Y"] = f"{round(float(single_value), 2):,.2f}"
    else:
        chart_json["Y"] = str(single_value)

    if not (
        str(chart_data[xAxis_column_name].values.tolist()[0]) == "0"
        or str(chart_data[xAxis_column_name].values.tolist()[0]) == "nan"
    ):
        description = str(chart_data[xAxis_column_name].values.tolist()[0]).strip()
        chart_json["Y"] = f"{chart_json['Y']!s} ({description})"

    return chart_json


def update_combo_chart_d3(
    llama70b_client: Any,
    chart_json: dict,
    chart_data: pd.DataFrame,
    logging_url: str,
):
    # Reassign chart type to barlinecombo_chart
    chart_json["Chart_Type"] = "barlinecombo_chart"

    chart_json["Aggregated_Table_JSON"] = update_aggregated_table_chart_d3(
        chart_json["Aggregated_Table_JSON"],
        chart_data,
        chart_json["Chart_Axis"],
        chart_json["Chart_Type"],
    )
    chart_axis = chart_json["Chart_Axis"]

    chart_data_columns = list(chart_data.columns)

    if "xAxis" in chart_data_columns:
        xAxis_column_name = "xAxis"
    elif (
        "xAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["xAxis_column"], str)
        and chart_axis["xAxis_column"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_column"]
    elif (
        "xAxis_title" in chart_axis.keys()
        and chart_axis["xAxis_title"] in chart_data.columns
    ):
        xAxis_column_name = chart_axis["xAxis_title"]
    else:
        raise RuntimeError("barlinecombo_chart: X-Axis is not found in extraction!")

    if "yAxisBar" in chart_data_columns:
        yAxisBar_column_name = "yAxisBar"
    elif (
        "yAxisBar_column" in chart_axis.keys()
        and isinstance(chart_axis["yAxisBar_column"], str)
        and chart_axis["yAxisBar_column"] in chart_data_columns
    ):
        yAxisBar_column_name = chart_axis["yAxisBar_column"]
    elif "yAxis" in chart_data_columns:
        yAxisBar_column_name = "yAxis"
    elif (
        "yAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["yAxis_column"], str)
        and chart_axis["yAxis_column"] in chart_data_columns
    ):
        yAxisBar_column_name = chart_axis["yAxis_column"]
    else:
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
            raise RuntimeError("barlinecombo_chart: yAxisBar is not numerical!")

    if "yAxisLine" in chart_data_columns:
        yAxisLine_column_name = "yAxisLine"
    elif (
        "yAxisLine_column" in chart_axis.keys()
        and isinstance(chart_axis["yAxisLine_column"], str)
        and chart_axis["yAxisLine_column"] in chart_data_columns
    ):
        yAxisLine_column_name = chart_axis["yAxisLine_column"]
    elif "y2Axis" in chart_data_columns:
        yAxisLine_column_name = "y2Axis"
    elif (
        "y2Axis_column" in chart_axis.keys()
        and isinstance(chart_axis["y2Axis_column"], str)
        and chart_axis["y2Axis_column"] in chart_data_columns
    ):
        yAxisLine_column_name = chart_axis["y2Axis_column"]
    else:
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
        chart_data = update_axis_title_and_data(chart_data, chart_axis)

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

    chart_json["X"] = [
        str(x_data) for x_data in chart_data[xAxis_column_name].values.tolist()
    ]

    if len(chart_json["X"]) >= 1 and len(chart_json["X"]) <= 2:
        return update_group_bar_chart_d3(
            llama70b_client, chart_json, chart_data, logging_url
        )

    chart_json["Y"] = [
        float(val) if isinstance(val, decimal.Decimal) else val
        for val in chart_data[yAxisBar_column_name].values.tolist()
    ]
    chart_json["Y2"] = [
        float(val) if isinstance(val, decimal.Decimal) else val
        for val in chart_data[yAxisLine_column_name].values.tolist()
    ]

    if "Y2" not in chart_json or chart_json["Y2"] == []:
        chart_json["Chart_Type"] = "bar_chart"
        # if check_negative_value(chart_json["Y"]):
        #     chart_json["Chart_Type"] = "column_chart"

        if len(chart_json["Y"]) == 1 and int(chart_json["Chart_Position"]) > 1:
            return convert_to_card_chart_d3(
                llama70b_client,
                chart_json,
                chart_data,
                logging_url,
            )
    else:
        # if check_negative_value(chart_json["Y"]) or check_negative_value(
        #     chart_json["Y2"]
        # ):
        #     chart_json["Chart_Type"] = "grouped_column_chart"
        pass

    if not (
        isinstance(chart_json["Y2"][0], int) or isinstance(chart_json["Y2"][0], float)
    ):
        raise RuntimeError("combo_chart: Y2-axis is not integer or float!")

    if any(
        chart_json[key] == [] or chart_json[key] == [""]
        for key in chart_json
        if re.match(r"^X\d*$", key)
    ):
        raise RuntimeError("combo_chart: One or more X-axis values are empty!")

    return chart_json


def update_line_chart_d3(
    llama70b_client: Any,
    chart_json: dict,
    chart_data: pd.DataFrame,
    logging_url: str,
):
    # Reassign chart type to line_chart
    chart_json["Chart_Type"] = "line_chart"

    chart_json["Aggregated_Table_JSON"] = update_aggregated_table_chart_d3(
        chart_json["Aggregated_Table_JSON"],
        chart_data,
        chart_json["Chart_Axis"],
        chart_json["Chart_Type"],
    )
    chart_axis = chart_json["Chart_Axis"]

    chart_data_columns = list(chart_data.columns)

    if "xAxis" in chart_data_columns:
        xAxis_column_name = "xAxis"
    elif (
        "xAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["xAxis_column"], str)
        and chart_axis["xAxis_column"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_column"]
    elif (
        "xAxis_title" in chart_axis.keys()
        and chart_axis["xAxis_title"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_title"]
    else:
        raise RuntimeError("line_chart: X-Axis is not found in extraction!")

    if "series" in chart_data_columns:
        series_column_name = "series"
    elif (
        "series_column" in chart_axis.keys()
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
        chart_data = update_axis_title_and_data(chart_data, chart_axis)

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

    chart_json["X"] = [
        str(x_data) for x_data in chart_data[xAxis_column_name].values.tolist()
    ]

    if len(chart_json["X"]) >= 1 and len(chart_json["X"]) <= 2:
        return update_group_bar_chart_d3(
            llama70b_client, chart_json, chart_data, logging_url
        )

    yAxis_idx = 1

    for column_name in list(chart_data.columns):
        if not re.search(r"yAxis([23456789])?", column_name, re.IGNORECASE):
            continue

        if yAxis_idx <= 1:
            chart_json["Y"] = [
                float(val) if isinstance(val, decimal.Decimal) else val
                for val in chart_data[column_name].values.tolist()
            ]

            underscore_index = column_name.find("_")

            # No Series
            if underscore_index == -1:
                if check_aggregation_phrases(
                    chart_axis[f"{column_name}_title"].replace("_", " "),
                ):
                    chart_json["yName"] = chart_axis[f"{column_name}_title"].replace(
                        "_",
                        " ",
                    )
                elif f"{column_name}_aggregation" in chart_axis.keys():
                    if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                        chart_json["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["AVG", "MEAN"]:
                        chart_json["yName"] = "Average " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                        chart_json["yName"] = "Median " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                        chart_json["yName"] = "Minimum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                        chart_json["yName"] = "Maximum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    else:
                        chart_json["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                else:
                    chart_json["yName"] = "Total " + chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")
            # Has Series
            else:
                original_column_name = column_name[:underscore_index]
                series_name = column_name[underscore_index + 1 :]

                # Add Series Title to Series Name
                if (
                    "series_title" in chart_axis.keys()
                    and chart_axis["series_title"] != ""
                ):
                    series_name = f"""{chart_axis["series_title"]}: {series_name}"""

                if (
                    f"{original_column_name}_title" in chart_axis.keys()
                    and check_aggregation_phrases(
                        f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        ),
                    )
                ):
                    chart_json["yName"] = (
                        f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        )
                    )
                elif f"{original_column_name}_aggregation" in chart_axis.keys():
                    if chart_axis[f"{original_column_name}_aggregation"] in ["SUM"]:
                        chart_json["yName"] = (
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
                        chart_json["yName"] = (
                            "Average "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in [
                        "MEDIAN",
                    ]:
                        chart_json["yName"] = (
                            "Median "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in ["MIN"]:
                        chart_json["yName"] = (
                            "Minimum "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in ["MAX"]:
                        chart_json["yName"] = (
                            "Maximum "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    else:
                        chart_json["yName"] = (
                            "Total "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                else:
                    chart_json["yName"] = (
                        "Total "
                        + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        )
                    )

            if not (
                isinstance(chart_json["Y"][0], int)
                or isinstance(chart_json["Y"][0], float)
            ):
                raise RuntimeError("line_chart: Y-axis is not integer or float!")

            # if check_negative_value(chart_json["Y"]):
            #     chart_json["Chart_Type"] = "column_chart"
        else:
            chart_json[f"Y{yAxis_idx}"] = [
                float(val) if isinstance(val, decimal.Decimal) else val
                for val in chart_data[column_name].values.tolist()
            ]

            underscore_index = column_name.find("_")

            # No Series
            if underscore_index == -1:
                chart_json[f"y{yAxis_idx}Name"] = chart_axis[
                    f"{column_name}_title"
                ].replace("_", " ")
                if chart_json[f"y{yAxis_idx}Name"] == "":
                    chart_json[f"y{yAxis_idx}Name"] = chart_json["yName"]

                if not check_aggregation_phrases(chart_json[f"y{yAxis_idx}Name"]):
                    if f"{column_name}_aggregation" in chart_axis.keys():
                        if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                            chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{column_name}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = "Average " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                            chart_json[f"y{yAxis_idx}Name"] = "Median " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                            chart_json[f"y{yAxis_idx}Name"] = "Minimum " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                            chart_json[f"y{yAxis_idx}Name"] = "Maximum " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        else:
                            chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                    else:
                        chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                            f"y{yAxis_idx}Name"
                        ].replace("_", " ")
            # Has Series
            else:
                original_column_name = column_name[:underscore_index]
                series_name = column_name[underscore_index + 1 :]
                chart_json[f"y{yAxis_idx}Name"] = (
                    f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                        "_",
                        " ",
                    )
                )
                if chart_json[f"y{yAxis_idx}Name"] == "":
                    chart_json[f"y{yAxis_idx}Name"] = chart_json["yName"]

                if not check_aggregation_phrases(chart_json[f"y{yAxis_idx}Name"]):
                    if f"{original_column_name}_aggregation" in chart_axis.keys():
                        if chart_axis[f"{original_column_name}_aggregation"] in ["SUM"]:
                            chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = "Average " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MEDIAN",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = "Median " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MIN",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = "Minimum " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MAX",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = "Maximum " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        else:
                            chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                    else:
                        chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                            f"y{yAxis_idx}Name"
                        ].replace("_", " ")

            # if chart_json["Chart_Type"] == "line_chart":
            #     chart_json["Chart_Type"] = "stackedline_chart"

            if not (
                isinstance(chart_json[f"Y{yAxis_idx}"][0], int)
                or isinstance(chart_json[f"Y{yAxis_idx}"][0], float)
            ):
                raise RuntimeError(
                    f"line_chart: Y{yAxis_idx}-axis is not integer or float!",
                )

            # if (
            #     check_negative_value(chart_json[f"Y{yAxis_idx}"])
            #     or chart_json["Chart_Type"] == "column_chart"
            # ):
            #     chart_json["Chart_Type"] = "grouped_column_chart"

        yAxis_idx += 1

    if any(
        chart_json[key] == [] or chart_json[key] == [""]
        for key in chart_json
        if re.match(r"^X\d*$", key)
    ):
        raise RuntimeError("line_chart: One or more X-axis values are empty!")

    if (
        len(chart_json["Y"]) == 1
        and ("Y2" not in chart_json or chart_json["Y2"] == [])
        and int(chart_json["Chart_Position"]) > 1
    ):
        return convert_to_card_chart_d3(
            llama70b_client,
            chart_json,
            chart_data,
            logging_url,
        )

    new_chart_data_lists = []

    x_values = chart_json["X"]

    if "Y" in chart_json:
        main_y_data = []
        for i in range(len(x_values)):
            x_value = x_values[i]
            main_y_value = chart_json["Y"][i]
            main_group_name = chart_json.get("yName", "Series 1")
            main_y_data.append(
                {
                    "X_Value": x_value,
                    "Y_Value": main_y_value,
                    "Group_Name": main_group_name,
                },
            )
        new_chart_data_lists.append(main_y_data)

    j = 2
    while f"Y{j}" in chart_json:
        additional_y_data = []

        for i in range(len(x_values)):
            x_value = x_values[i]

            y_key = f"Y{j}"
            if y_key in chart_json:
                additional_y_value = chart_json[y_key][i]
                group_name_key = f"y{j}Name"
                group_name = chart_json.get(group_name_key, f"Series {j}")
                additional_y_data.append(
                    {
                        "X_Value": x_value,
                        "Y_Value": additional_y_value,
                        "Group_Name": group_name,
                    },
                )

        if additional_y_data:
            new_chart_data_lists.append(additional_y_data)

        j += 1

    chart_json["Chart_Data"] = new_chart_data_lists

    keys_to_remove = ["X", "Y", "yName"]

    i = 2
    while f"y{i}Name" in chart_json:
        keys_to_remove.append(f"y{i}Name")
        i += 1

    j = 2
    while f"Y{j}" in chart_json:
        keys_to_remove.append(f"Y{j}")
        j += 1

    # Remove all specified keys ['X', 'Y', 'yName'] and etc. from the dictionary
    for key in keys_to_remove:
        if key in chart_json:
            del chart_json[key]

    return chart_json


def update_scatterplot_chart_d3(
    llama70b_client: Any,
    chart_json: dict,
    chart_data: pd.DataFrame,
    logging_url: str,
):
    # Reassign chart type to scatterplot_chart
    chart_json["Chart_Type"] = "scatterplot_chart"

    chart_json["Aggregated_Table_JSON"] = update_aggregated_table_chart_d3(
        chart_json["Aggregated_Table_JSON"],
        chart_data,
        chart_json["Chart_Axis"],
        chart_json["Chart_Type"],
    )
    chart_axis = chart_json["Chart_Axis"]

    chart_data_columns = list(chart_data.columns)

    if "xAxis" in chart_data_columns:
        xAxis_column_name = "xAxis"
    elif (
        "xAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["xAxis_column"], str)
        and chart_axis["xAxis_column"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_column"]
    elif (
        "xAxis_title" in chart_axis.keys()
        and chart_axis["xAxis_title"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_title"]
    else:
        raise RuntimeError("X-Axis is not found in extraction!")

    if "yAxis" in chart_data_columns:
        yAxis_column_name = "yAxis"
    elif (
        "yAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["yAxis_column"], str)
        and chart_axis["yAxis_column"] in chart_data_columns
    ):
        yAxis_column_name = chart_axis["yAxis_column"]
    else:
        raise RuntimeError("scatterplot_chart: Y-Axis is not found in extraction!")

    if "series" in chart_data_columns:
        series_column_name = "series"
    elif (
        "series_column" in chart_axis.keys()
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
                    chart_data[yAxis_column_name].values.tolist()[0],
                    datetime.date,
                ) and not isinstance(
                    chart_data[yAxis_column_name].values.tolist()[0],
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
        chart_data = update_axis_title_and_data(chart_data, chart_axis)

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
                for val in chart_data[xAxis_column_name]
            ):
                chart_data = update_axis_title_and_data(chart_data, chart_axis)

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
                    chart_json["X"] = [
                        str(x_data)
                        for x_data in series_chart_data[
                            xAxis_column_name
                        ].values.tolist()
                    ]

                    chart_json["Y"] = [
                        float(val) if isinstance(val, decimal.Decimal) else val
                        for val in series_chart_data[
                            series_chart_column
                        ].values.tolist()
                    ]

                    # Add Series Title to Series Value
                    if (
                        "series_title" in chart_axis.keys()
                        and chart_axis["series_title"] != ""
                    ):
                        series_value = (
                            f"""{chart_axis["series_title"]}: {series_value}"""
                        )

                    if (
                        f"{series_chart_column}_title" in chart_axis.keys()
                        and check_aggregation_phrases(
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})",
                        )
                    ):
                        chart_json["yName"] = (
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif f"{series_chart_column}_aggregation" in chart_axis.keys():
                        if chart_axis[f"{series_chart_column}_aggregation"] in ["SUM"]:
                            chart_json["yName"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            chart_json["yName"] = (
                                f"Average {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "MEDIAN",
                        ]:
                            chart_json["yName"] = (
                                f"Median {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "MIN",
                        ]:
                            chart_json["yName"] = (
                                f"Minimum {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "MAX",
                        ]:
                            chart_json["yName"] = (
                                f"Maximum {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        else:
                            chart_json["yName"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                    else:
                        chart_json["yName"] = (
                            f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                "_",
                                " ",
                            )
                        )

                    if not (
                        isinstance(chart_json["Y"][0], int)
                        or isinstance(chart_json["Y"][0], float)
                    ):
                        raise RuntimeError(
                            "scatterplot_chart: Y-axis is not integer or float!",
                        )

                    # if check_negative_value(chart_json["Y"]):
                    #     chart_json["Chart_Type"] = "column_chart"
                else:
                    chart_json[f"X{yAxis_idx}"] = [
                        float(val) if isinstance(val, decimal.Decimal) else val
                        for val in series_chart_data[xAxis_column_name].values.tolist()
                    ]

                    chart_json[f"Y{yAxis_idx}"] = [
                        float(val) if isinstance(val, decimal.Decimal) else val
                        for val in series_chart_data[
                            series_chart_column
                        ].values.tolist()
                    ]

                    # Add Series Title to Series Value
                    if (
                        "series_title" in chart_axis.keys()
                        and chart_axis["series_title"] != ""
                    ):
                        series_value = (
                            f"""{chart_axis["series_title"]}: {series_value}"""
                        )

                    if (
                        f"{series_chart_column}_title" in chart_axis.keys()
                        and check_aggregation_phrases(
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})",
                        )
                    ):
                        chart_json[f"y{yAxis_idx}Name"] = (
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif "yAxis_aggregation" in chart_axis.keys():
                        if chart_axis["yAxis_aggregation"] in ["SUM"]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                f"Average {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                f"Median {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis["yAxis_aggregation"] in ["MIN"]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                f"Minimum {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        elif chart_axis["yAxis_aggregation"] in ["MAX"]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                f"Maximum {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                        else:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                    "_",
                                    " ",
                                )
                            )
                    else:
                        chart_json[f"y{yAxis_idx}Name"] = (
                            f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})".replace(
                                "_",
                                " ",
                            )
                        )

                    if not (
                        isinstance(chart_json[f"Y{yAxis_idx}"][0], int)
                        or isinstance(chart_json[f"Y{yAxis_idx}"][0], float)
                    ):
                        raise RuntimeError(
                            f"scatterplot_chart: Y{yAxis_idx}-axis is not integer or float!",
                        )

                    # if (
                    #     check_negative_value(chart_json[f"Y{yAxis_idx}"])
                    #     or chart_json["Chart_Type"] == "column_chart"
                    # ):
                    #     return update_group_column_chart(
                    #         chart_json,
                    #         chart_data,
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
                chart_json["X"] = [
                    str(x_data)
                    for x_data in chart_data[xAxis_column_name].values.tolist()
                ]

                chart_json["Y"] = [
                    float(val) if isinstance(val, decimal.Decimal) else val
                    for val in chart_data[column_name].values.tolist()
                ]

                if check_aggregation_phrases(chart_axis[f"{column_name}_title"]):
                    chart_json["yName"] = chart_axis[f"{column_name}_title"]
                elif "yAxis_aggregation" in chart_axis.keys():
                    if chart_axis["yAxis_aggregation"] in ["SUM"]:
                        chart_json["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
                        chart_json["yName"] = "Average " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
                        chart_json["yName"] = "Median " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["MIN"]:
                        chart_json["yName"] = "Minimum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["MAX"]:
                        chart_json["yName"] = "Maximum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    else:
                        chart_json["yName"] = chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                else:
                    chart_json["yName"] = "Total " + chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")

                if not (
                    isinstance(chart_json["Y"][0], int)
                    or isinstance(chart_json["Y"][0], float)
                ):
                    raise RuntimeError("treemap_chart: Y-axis is not integer or float!")

                # if check_negative_value(chart_json["Y"]):
                #     chart_json["Chart_Type"] = "column_chart"
            else:
                chart_json[f"X{yAxis_idx}"] = [
                    str(x_data)
                    for x_data in chart_data[xAxis_column_name].values.tolist()
                ]

                chart_json[f"Y{yAxis_idx}"] = [
                    float(val) if isinstance(val, decimal.Decimal) else val
                    for val in chart_data[column_name].values.tolist()
                ]

                if check_aggregation_phrases(chart_axis[f"{column_name}_title"]):
                    chart_json[f"y{yAxis_idx}Name"] = chart_axis[f"{column_name}_title"]
                elif f"{column_name}_aggregation" in chart_axis.keys():
                    if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                        chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["AVG", "MEAN"]:
                        chart_json[f"y{yAxis_idx}Name"] = "Average " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                        chart_json[f"y{yAxis_idx}Name"] = "Median " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                        chart_json[f"y{yAxis_idx}Name"] = "Minimum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                        chart_json[f"y{yAxis_idx}Name"] = "Maximum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    else:
                        chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                else:
                    chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")

                if not (
                    isinstance(chart_json[f"Y{yAxis_idx}"][0], int)
                    or isinstance(chart_json[f"Y{yAxis_idx}"][0], float)
                ):
                    raise RuntimeError(
                        f"scatterplot_chart: Y{yAxis_idx}-axis is not integer or float!",
                    )

                # if (
                #     check_negative_value(chart_json[f"Y{yAxis_idx}"])
                #     or chart_json["Chart_Type"] == "column_chart"
                # ):
                #     return update_group_column_chart(
                #         chart_json,
                #         chart_data,
                #     )

            yAxis_idx += 1

    if chart_json["Y"] == []:
        raise RuntimeError("scatterplot_chart: Y-Axis is not found in extraction!")

    if any(
        chart_json[key] == [] or chart_json[key] == [""]
        for key in chart_json
        if re.match(r"^X\d*$", key)
    ):
        raise RuntimeError("scatterplot_chart: One or more X-axis values are empty!")

    if (
        len(chart_json["Y"]) == 1
        and ("Y2" not in chart_json or chart_json["Y2"] == [])
        and int(chart_json["Chart_Position"]) > 1
    ):
        return convert_to_card_chart_d3(
            llama70b_client,
            chart_json,
            chart_data,
            logging_url,
        )

    new_chart_data_lists = []

    # Check for the main Y and its corresponding X
    if "Y" in chart_json:
        x_values = chart_json["X"]
        main_group_name = chart_json.get("yName", "Series 1")

        for i in range(len(x_values)):
            x_value = float(x_values[i])
            main_y_value = chart_json["Y"][i]
            new_chart_data_lists.append(
                {
                    "X_Value": x_value,
                    "Y_Value": main_y_value,
                    "Group_Name": main_group_name,
                },
            )

    # Check for additional Y values (Y2, Y3, ...)
    j = 2
    while f"Y{j}" in chart_json:
        # Corresponding X values for Y2, Y3, etc.
        x_key = f"X{j}"
        if x_key in chart_json:
            x_values = chart_json[x_key]
            group_name_key = f"y{j}Name"
            group_name = chart_json.get(group_name_key, f"Series {j}")

            for i in range(len(x_values)):
                x_value = float(x_values[i])
                y_key = f"Y{j}"
                if y_key in chart_json:
                    additional_y_value = chart_json[y_key][i]
                    new_chart_data_lists.append(
                        {
                            "X_Value": x_value,
                            "Y_Value": additional_y_value,
                            "Group_Name": group_name,
                        },
                    )

        j += 1

    # Store chart data in the original dict
    chart_json["Chart_Data"] = new_chart_data_lists

    keys_to_remove = ["X", "Y", "yName"]

    i = 2
    while f"y{i}Name" in chart_json:
        keys_to_remove.append(f"y{i}Name")
        i += 1

    j = 2
    while f"X{j}" and f"Y{j}" in chart_json:
        keys_to_remove.append(f"X{j}")
        keys_to_remove.append(f"Y{j}")
        j += 1

    # Remove all specified keys ['X', 'Y', 'yName'] and etc. from the dictionary
    for key in keys_to_remove:
        if key in chart_json:
            del chart_json[key]

    return chart_json


def update_spline_chart_d3(
    llama70b_client: Any,
    chart_json: dict,
    chart_data: pd.DataFrame,
    logging_url: str,
):
    # Reassign chart type to line_chart
    chart_json["Chart_Type"] = "line_chart"

    chart_json["Aggregated_Table_JSON"] = update_aggregated_table_chart_d3(
        chart_json["Aggregated_Table_JSON"],
        chart_data,
        chart_json["Chart_Axis"],
        chart_json["Chart_Type"],
    )
    chart_axis = chart_json["Chart_Axis"]

    chart_data_columns = list(chart_data.columns)

    if "xAxis" in chart_data_columns:
        xAxis_column_name = "xAxis"
    elif (
        "xAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["xAxis_column"], str)
        and chart_axis["xAxis_column"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_column"]
    elif (
        "xAxis_title" in chart_axis.keys()
        and chart_axis["xAxis_title"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_title"]
    else:
        raise RuntimeError("spline_chart: X-Axis is not found in extraction!")

    if "series" in chart_data_columns:
        series_column_name = "series"
    elif (
        "series_column" in chart_axis.keys()
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
                raise RuntimeError(
                    f"spline_chart: {yAxis_column_name} is not numerical!",
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
        new_chart_data[xAxis_column_name] = [
            float(val) if isinstance(val, decimal.Decimal) else val
            for val in pivot_data[xAxis_column_name].values.tolist()
        ]

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
        chart_data = update_axis_title_and_data(chart_data, chart_axis)

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

    chart_json["X"] = [
        str(x_data) for x_data in chart_data[xAxis_column_name].values.tolist()
    ]

    if len(chart_json["X"]) >= 1 and len(chart_json["X"]) <= 2:
        return update_group_bar_chart_d3(
            llama70b_client, chart_json, chart_data, logging_url
        )

    yAxis_idx = 1

    for column_name in list(chart_data.columns):
        if not re.search(r"yAxis([23456789])?", column_name, re.IGNORECASE):
            continue

        if yAxis_idx <= 1:
            chart_json["Y"] = [
                float(val) if isinstance(val, decimal.Decimal) else val
                for val in chart_data[column_name].values.tolist()
            ]

            underscore_index = column_name.find("_")

            # No Series
            if underscore_index == -1:
                if check_aggregation_phrases(
                    chart_axis[f"{column_name}_title"].replace("_", " "),
                ):
                    chart_json["yName"] = chart_axis[f"{column_name}_title"].replace(
                        "_",
                        " ",
                    )
                elif f"{column_name}_aggregation" in chart_axis.keys():
                    if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                        chart_json["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["AVG", "MEAN"]:
                        chart_json["yName"] = "Average " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                        chart_json["yName"] = "Median " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                        chart_json["yName"] = "Minimum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                        chart_json["yName"] = "Maximum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    else:
                        chart_json["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                else:
                    chart_json["yName"] = "Total " + chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")
            # Has Series
            else:
                original_column_name = column_name[:underscore_index]
                series_name = column_name[underscore_index + 1 :]

                # Add Series Title to Series Name
                if (
                    "series_title" in chart_axis.keys()
                    and chart_axis["series_title"] != ""
                ):
                    series_name = f"""{chart_axis["series_title"]}: {series_name}"""

                if (
                    f"{original_column_name}_title" in chart_axis.keys()
                    and check_aggregation_phrases(
                        f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        ),
                    )
                ):
                    chart_json["yName"] = (
                        f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        )
                    )
                elif f"{original_column_name}_aggregation" in chart_axis.keys():
                    if chart_axis[f"{original_column_name}_aggregation"] in ["SUM"]:
                        chart_json["yName"] = (
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
                        chart_json["yName"] = (
                            "Average "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in [
                        "MEDIAN",
                    ]:
                        chart_json["yName"] = (
                            "Median "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in ["MIN"]:
                        chart_json["yName"] = (
                            "Minimum "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in ["MAX"]:
                        chart_json["yName"] = (
                            "Maximum "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    else:
                        chart_json["yName"] = (
                            "Total "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                else:
                    chart_json["yName"] = (
                        "Total "
                        + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        )
                    )

            if not (
                isinstance(chart_json["Y"][0], int)
                or isinstance(chart_json["Y"][0], float)
            ):
                raise RuntimeError("spline_chart: Y-axis is not integer or float!")

            # if check_negative_value(chart_axis["Y"]):
            #     chart_axis["Chart_Type"] = "column_chart"
        else:
            chart_json[f"Y{yAxis_idx}"] = [
                float(val) if isinstance(val, decimal.Decimal) else val
                for val in chart_data[column_name].values.tolist()
            ]

            underscore_index = column_name.find("_")

            # No Series
            if underscore_index == -1:
                chart_json[f"y{yAxis_idx}Name"] = chart_axis[
                    f"{column_name}_title"
                ].replace("_", " ")
                if chart_json[f"y{yAxis_idx}Name"] == "":
                    chart_json[f"y{yAxis_idx}Name"] = chart_json["yName"]

                if not check_aggregation_phrases(chart_json[f"y{yAxis_idx}Name"]):
                    if f"{column_name}_aggregation" in chart_axis.keys():
                        if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                            chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{column_name}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = "Average " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                            chart_json[f"y{yAxis_idx}Name"] = "Median " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                            chart_json[f"y{yAxis_idx}Name"] = "Minimum " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                            chart_json[f"y{yAxis_idx}Name"] = "Maximum " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        else:
                            chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                    else:
                        chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                            f"y{yAxis_idx}Name"
                        ].replace("_", " ")
            # Has Series
            else:
                original_column_name = column_name[:underscore_index]
                series_name = column_name[underscore_index + 1 :]
                chart_json[f"y{yAxis_idx}Name"] = (
                    f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                        "_",
                        " ",
                    )
                )
                if chart_json[f"y{yAxis_idx}Name"] == "":
                    chart_json[f"y{yAxis_idx}Name"] = chart_json["yName"]

                if not check_aggregation_phrases(chart_json[f"y{yAxis_idx}Name"]):
                    if f"{original_column_name}_aggregation" in chart_axis.keys():
                        if chart_axis[f"{original_column_name}_aggregation"] in ["SUM"]:
                            chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = "Average " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MEDIAN",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = "Median " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MIN",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = "Minimum " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MAX",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = "Maximum " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        else:
                            chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                    else:
                        chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                            f"y{yAxis_idx}Name"
                        ].replace("_", " ")

            if not (
                isinstance(chart_json[f"Y{yAxis_idx}"][0], int)
                or isinstance(chart_json[f"Y{yAxis_idx}"][0], float)
            ):
                raise RuntimeError(
                    f"spline_chart: Y{yAxis_idx}-axis is not integer or float!",
                )

            # if (
            #     check_negative_value(chart_axis[f"Y{yAxis_idx}"])
            #     or chart_axis["Chart_Type"] == "column_chart"
            # ):
            #     chart_axis["Chart_Type"] = "grouped_column_chart"

        yAxis_idx += 1

    if any(
        chart_json[key] == [] or chart_json[key] == [""]
        for key in chart_json
        if re.match(r"^X\d*$", key)
    ):
        raise RuntimeError("spline_chart: One or more X-axis values are empty!")

    if (
        len(chart_json["Y"]) == 1
        and ("Y2" not in chart_json or chart_json["Y2"] == [])
        and int(chart_json["Chart_Position"]) > 1
    ):
        return convert_to_card_chart_d3(
            llama70b_client,
            chart_json,
            chart_data,
            logging_url,
        )

    new_chart_data_lists = []

    x_values = chart_json["X"]

    if "Y" in chart_json:
        main_y_data = []
        for i in range(len(x_values)):
            x_value = x_values[i]
            main_y_value = chart_json["Y"][i]
            main_group_name = chart_json.get("yName", "Series 1")
            main_y_data.append(
                {
                    "X_Value": x_value,
                    "Y_Value": main_y_value,
                    "Group_Name": main_group_name,
                },
            )
        new_chart_data_lists.append(main_y_data)

    j = 2
    while f"Y{j}" in chart_json:
        additional_y_data = []

        for i in range(len(x_values)):
            x_value = x_values[i]

            y_key = f"Y{j}"
            if y_key in chart_json:
                additional_y_value = chart_json[y_key][i]
                group_name_key = f"y{j}Name"
                group_name = chart_json.get(group_name_key, f"Series {j}")
                additional_y_data.append(
                    {
                        "X_Value": x_value,
                        "Y_Value": additional_y_value,
                        "Group_Name": group_name,
                    },
                )

        if additional_y_data:
            new_chart_data_lists.append(additional_y_data)

        j += 1

    chart_json["Chart_Data"] = new_chart_data_lists

    keys_to_remove = ["X", "Y", "yName"]

    i = 2
    while f"y{i}Name" in chart_json:
        keys_to_remove.append(f"y{i}Name")
        i += 1

    j = 2
    while f"Y{j}" in chart_json:
        keys_to_remove.append(f"Y{j}")
        j += 1

    # Remove all specified keys ['X', 'Y', 'yName'] and etc. from the dictionary
    for key in keys_to_remove:
        if key in chart_json:
            del chart_json[key]

    return chart_json


def update_group_bar_chart_d3(
    llama70b_client: Any,
    chart_json: dict,
    chart_data: pd.DataFrame,
    logging_url: str,
):
    # Reassign chart type to grouped_bar_chart
    chart_json["Chart_Type"] = "grouped_bar_chart"

    chart_json["Aggregated_Table_JSON"] = update_aggregated_table_chart_d3(
        chart_json["Aggregated_Table_JSON"],
        chart_data,
        chart_json["Chart_Axis"],
        chart_json["Chart_Type"],
    )
    chart_axis = chart_json["Chart_Axis"]

    chart_data_columns = list(chart_data.columns)

    if "xAxis" in chart_data_columns:
        xAxis_column_name = "xAxis"
    elif (
        "xAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["xAxis_column"], str)
        and chart_axis["xAxis_column"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_column"]
    elif (
        "xAxis_title" in chart_axis.keys()
        and chart_axis["xAxis_title"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_title"]
    else:
        raise RuntimeError("X-Axis is not found in extraction!")

    if "series" in chart_data_columns:
        series_column_name = "series"
    elif (
        "series_column" in chart_axis.keys()
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
        chart_data = update_axis_title_and_data(chart_data, chart_axis)

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

    chart_json["X"] = [
        str(x_data) for x_data in chart_data[xAxis_column_name].values.tolist()
    ]

    if any(
        chart_json[key] == [] or chart_json[key] == [""]
        for key in chart_json
        if re.match(r"^X\d*$", key)
    ):
        raise RuntimeError("grouped_bar_chart: One or more X-axis values are empty!")

    yAxis_idx = 1

    for column_name in list(chart_data.columns):
        if not re.search(r"yAxis([23456789])?", column_name, re.IGNORECASE):
            continue

        if yAxis_idx <= 1:
            chart_json["Y"] = [
                float(val) if isinstance(val, decimal.Decimal) else val
                for val in chart_data[column_name].values.tolist()
            ]

            underscore_index = column_name.find("_")

            # No Series
            if underscore_index == -1:
                if check_aggregation_phrases(
                    chart_axis[f"{column_name}_title"].replace("_", " "),
                ):
                    chart_json["yName"] = chart_axis[f"{column_name}_title"].replace(
                        "_",
                        " ",
                    )
                elif f"{column_name}_aggregation" in chart_axis.keys():
                    if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                        chart_json["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["AVG", "MEAN"]:
                        chart_json["yName"] = "Average " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                        chart_json["yName"] = "Median " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                        chart_json["yName"] = "Minimum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                        chart_json["yName"] = "Maximum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    else:
                        chart_json["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                else:
                    chart_json["yName"] = "Total " + chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")
            # Has Series
            else:
                original_column_name = column_name[:underscore_index]
                series_name = column_name[underscore_index + 1 :]

                if (
                    "series_title" in chart_axis.keys()
                    and chart_axis["series_title"] != ""
                ):
                    series_name = f"""{chart_axis["series_title"]}: {series_name}"""

                if (
                    f"{original_column_name}_title" in chart_axis.keys()
                    and check_aggregation_phrases(
                        f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        ),
                    )
                ):
                    chart_json["yName"] = (
                        f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        )
                    )
                elif f"{original_column_name}_aggregation" in chart_axis.keys():
                    if chart_axis[f"{original_column_name}_aggregation"] in ["SUM"]:
                        chart_json["yName"] = (
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
                        chart_json["yName"] = (
                            "Average "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in [
                        "MEDIAN",
                    ]:
                        chart_json["yName"] = (
                            "Median "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in ["MIN"]:
                        chart_json["yName"] = (
                            "Minimum "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in ["MAX"]:
                        chart_json["yName"] = (
                            "Maximum "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    else:
                        chart_json["yName"] = (
                            "Total "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                else:
                    chart_json["yName"] = (
                        "Total "
                        + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        )
                    )

            if not (
                isinstance(chart_json["Y"][0], int)
                or isinstance(chart_json["Y"][0], float)
            ):
                raise RuntimeError("grouped_bar_chart: Y-axis is not integer or float!")

            # if check_negative_value(chart_json["Y"]):
            #     chart_json["Chart_Type"] = "column_chart"
        else:
            chart_json[f"Y{yAxis_idx}"] = [
                float(val) if isinstance(val, decimal.Decimal) else val
                for val in chart_data[column_name].values.tolist()
            ]

            underscore_index = column_name.find("_")

            # No Series
            if underscore_index == -1:
                chart_json[f"y{yAxis_idx}Name"] = chart_axis[
                    f"{column_name}_title"
                ].replace("_", " ")
                if chart_json[f"y{yAxis_idx}Name"] == "":
                    chart_json[f"y{yAxis_idx}Name"] = chart_json["yName"]

                if not check_aggregation_phrases(chart_json[f"y{yAxis_idx}Name"]):
                    if f"{column_name}_aggregation" in chart_axis.keys():
                        if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                            chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{column_name}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = "Average " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                            chart_json[f"y{yAxis_idx}Name"] = "Median " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                            chart_json[f"y{yAxis_idx}Name"] = "Minimum " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                            chart_json[f"y{yAxis_idx}Name"] = "Maximum " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        else:
                            chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                    else:
                        chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                            f"y{yAxis_idx}Name"
                        ].replace("_", " ")
            # Has Series
            else:
                original_column_name = column_name[:underscore_index]
                series_name = column_name[underscore_index + 1 :]
                chart_json[f"y{yAxis_idx}Name"] = (
                    f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                        "_",
                        " ",
                    )
                )
                if chart_json[f"y{yAxis_idx}Name"] == "":
                    chart_json[f"y{yAxis_idx}Name"] = chart_json["yName"]

                if not check_aggregation_phrases(chart_json[f"y{yAxis_idx}Name"]):
                    if f"{original_column_name}_aggregation" in chart_axis.keys():
                        if chart_axis[f"{original_column_name}_aggregation"] in ["SUM"]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                "Total " + chart_json[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                "Average " + chart_json[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MEDIAN",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                "Median " + chart_json[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MIN",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                "Minimum " + chart_json[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MAX",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                "Maximum " + chart_json[f"y{yAxis_idx}Name"]
                            )
                        else:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                "Total " + chart_json[f"y{yAxis_idx}Name"]
                            )
                    else:
                        chart_json[f"y{yAxis_idx}Name"] = (
                            "Total " + chart_json[f"y{yAxis_idx}Name"]
                        )

            if not (
                isinstance(chart_json[f"Y{yAxis_idx}"][0], int)
                or isinstance(chart_json[f"Y{yAxis_idx}"][0], float)
            ):
                raise RuntimeError(
                    f"grouped_bar_chart: Y{yAxis_idx}-axis is not integer or float!",
                )

            # if (
            #     check_negative_value(chart_json[f"Y{yAxis_idx}"])
            #     or chart_json["Chart_Type"] == "column_chart"
            # ):
            #     chart_json["Chart_Type"] = "grouped_column_chart"

        yAxis_idx += 1

    if chart_json["Y"] == []:
        raise RuntimeError("grouped_bar_chart: Y-Axis is not found in extraction!")

    if any(
        chart_json[key] == [] or chart_json[key] == [""]
        for key in chart_json
        if re.match(r"^X\d*$", key)
    ):
        raise RuntimeError("grouped_bar_chart: One or more X-axis values are empty!")

    if (
        len(chart_json["Y"]) == 1
        and ("Y2" not in chart_json or chart_json["Y2"] == [])
        and int(chart_json["Chart_Position"]) > 1
    ):
        card_chart_json_dict = convert_to_card_chart_d3(
            llama70b_client,
            chart_json,
            chart_data,
            logging_url,
        )
        return card_chart_json_dict

    new_chart_data_lists = []

    x_values = chart_json["X"]

    if "Y" in chart_json:
        main_y_data = []
        for i in range(len(x_values)):
            x_value = x_values[i]
            main_y_value = chart_json["Y"][i]
            main_group_name = chart_json.get("yName", "Series 1")
            main_y_data.append(
                {
                    "X_Value": x_value,
                    "Y_Value": main_y_value,
                    "Group_Name": main_group_name,
                },
            )
        new_chart_data_lists.append(main_y_data)

    j = 2
    while f"Y{j}" in chart_json:
        additional_y_data = []

        for i in range(len(x_values)):
            x_value = x_values[i]

            y_key = f"Y{j}"
            if y_key in chart_json:
                additional_y_value = chart_json[y_key][i]
                group_name_key = f"y{j}Name"
                group_name = chart_json.get(group_name_key, f"Series {j}")
                additional_y_data.append(
                    {
                        "X_Value": x_value,
                        "Y_Value": additional_y_value,
                        "Group_Name": group_name,
                    },
                )

        if additional_y_data:
            new_chart_data_lists.append(additional_y_data)

        j += 1

    chart_json["Chart_Data"] = new_chart_data_lists
    chart_id = chart_json["Chart_ID"]

    if is_within_max_length(chart_json["Chart_Data"], 12):
        system_prompt = "Sort the given list in chronological order and return only the sorted list as a Python list, without any explanations."
        list_to_be_sort = x_values
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

        MODULEID_UPDATE_GROUP_BAR_CHART_D3 = os.getenv(
            "MODULEID_UPDATE_GROUP_BAR_CHART_D3", ""
        )

        if MODULEID_UPDATE_GROUP_BAR_CHART_D3 == "":
            raise ValueError("MODULEID_UPDATE_GROUP_BAR_CHART_D3 is invalid!")

        formatted_data = {
            "chart_id": chart_id,
            "module_id": int(MODULEID_UPDATE_GROUP_BAR_CHART_D3),
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

        sorted_Chart_Data = map_original_list_with_sorted_x(
            chart_json["Chart_Data"],
            response,
        )
        chart_json["Chart_Data"] = sorted_Chart_Data

    keys_to_remove = ["X", "Y", "yName"]

    i = 2
    while f"y{i}Name" in chart_json:
        keys_to_remove.append(f"y{i}Name")
        i += 1

    j = 2
    while f"Y{j}" in chart_json:
        keys_to_remove.append(f"Y{j}")
        j += 1

    # Remove all specified keys ['X', 'Y', 'yName'] and etc. from the dictionary
    for key in keys_to_remove:
        if key in chart_json:
            del chart_json[key]

    return chart_json


def update_radar_chart_d3(
    llama70b_client: Any,
    chart_json: dict,
    chart_data: pd.DataFrame,
    logging_url: str,
):
    if len(chart_data) > 6:
        return update_group_bar_chart_d3(
            llama70b_client,
            chart_json,
            chart_data,
            logging_url,
        )

    # Reassign chart type to radar_chart
    chart_json["Chart_Type"] = "radar_chart"

    chart_json["Aggregated_Table_JSON"] = update_aggregated_table_chart_d3(
        chart_json["Aggregated_Table_JSON"],
        chart_data,
        chart_json["Chart_Axis"],
        chart_json["Chart_Type"],
    )
    chart_axis = chart_json["Chart_Axis"]

    chart_data_columns = list(chart_data.columns)

    if "xAxis" in chart_data_columns:
        xAxis_column_name = "xAxis"
    elif (
        "xAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["xAxis_column"], str)
        and chart_axis["xAxis_column"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_column"]
    elif (
        "xAxis_title" in chart_axis.keys()
        and chart_axis["xAxis_title"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_title"]
    else:
        raise RuntimeError("radar_chart: X-Axis is not found in extraction!")

    if "series" in chart_data_columns:
        series_column_name = "series"
    elif (
        "series_column" in chart_axis.keys()
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
        chart_data = update_axis_title_and_data(chart_data, chart_axis)

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

    chart_json["X"] = [
        str(x_data) for x_data in chart_data[xAxis_column_name].values.tolist()
    ]

    if (len(chart_json["X"]) >= 1 and len(chart_json["X"]) <= 2) or len(
        chart_json["X"],
    ) > 12:
        return update_group_bar_chart_d3(
            llama70b_client, chart_json, chart_data, logging_url
        )

    yAxis_idx = 1

    for column_name in list(chart_data.columns):
        if not re.search(r"yAxis([23456789])?", column_name, re.IGNORECASE):
            continue

        if yAxis_idx <= 1:
            chart_json["Y"] = [
                float(val) if isinstance(val, decimal.Decimal) else val
                for val in chart_data[column_name].values.tolist()
            ]

            underscore_index = column_name.find("_")

            # No Series
            if underscore_index == -1:
                if check_aggregation_phrases(
                    chart_axis[f"{column_name}_title"].replace("_", " "),
                ):
                    chart_json["yName"] = chart_axis[f"{column_name}_title"].replace(
                        "_",
                        " ",
                    )
                elif f"{column_name}_aggregation" in chart_axis.keys():
                    if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                        chart_json["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["AVG", "MEAN"]:
                        chart_json["yName"] = "Average " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                        chart_json["yName"] = "Median " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                        chart_json["yName"] = "Minimum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                        chart_json["yName"] = "Maximum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    else:
                        chart_json["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                else:
                    chart_json["yName"] = "Total " + chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")
            # Has Series
            else:
                original_column_name = column_name[:underscore_index]
                series_name = column_name[underscore_index + 1 :]
                if (
                    f"{original_column_name}_title" in chart_axis.keys()
                    and check_aggregation_phrases(
                        f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        ),
                    )
                ):
                    chart_json["yName"] = (
                        f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        )
                    )
                elif f"{original_column_name}_aggregation" in chart_axis.keys():
                    if chart_axis[f"{original_column_name}_aggregation"] in ["SUM"]:
                        chart_json["yName"] = (
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
                        chart_json["yName"] = (
                            "Average "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in [
                        "MEDIAN",
                    ]:
                        chart_json["yName"] = (
                            "Median "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in ["MIN"]:
                        chart_json["yName"] = (
                            "Minimum "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in ["MAX"]:
                        chart_json["yName"] = (
                            "Maximum "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    else:
                        chart_json["yName"] = (
                            "Total "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                else:
                    chart_json["yName"] = (
                        "Total "
                        + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        )
                    )

            if not (
                isinstance(chart_json["Y"][0], int)
                or isinstance(chart_json["Y"][0], float)
            ):
                raise RuntimeError("radar_chart: Y-axis is not integer or float!")

            # if check_negative_value(chart_json["Y"]):
            #     chart_json["Chart_Type"] = "column_chart"
        else:
            chart_json[f"Y{yAxis_idx}"] = [
                float(val) if isinstance(val, decimal.Decimal) else val
                for val in chart_data[column_name].values.tolist()
            ]

            underscore_index = column_name.find("_")

            # No Series
            if underscore_index == -1:
                chart_json[f"y{yAxis_idx}Name"] = chart_axis[
                    f"{column_name}_title"
                ].replace("_", " ")
                if chart_json[f"y{yAxis_idx}Name"] == "":
                    chart_json[f"y{yAxis_idx}Name"] = chart_json["yName"]

                if not check_aggregation_phrases(chart_json[f"y{yAxis_idx}Name"]):
                    if f"{column_name}_aggregation" in chart_axis.keys():
                        if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                            chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{column_name}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = "Average " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                            chart_json[f"y{yAxis_idx}Name"] = "Median " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                            chart_json[f"y{yAxis_idx}Name"] = "Minimum " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                            chart_json[f"y{yAxis_idx}Name"] = "Maximum " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        else:
                            chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                    else:
                        chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                            f"y{yAxis_idx}Name"
                        ].replace("_", " ")
            # Has Series
            else:
                original_column_name = column_name[:underscore_index]
                series_name = column_name[underscore_index + 1 :]
                chart_json[f"y{yAxis_idx}Name"] = (
                    f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                        "_",
                        " ",
                    )
                )
                if chart_json[f"y{yAxis_idx}Name"] == "":
                    chart_json[f"y{yAxis_idx}Name"] = chart_json["yName"]

                if not check_aggregation_phrases(chart_json[f"y{yAxis_idx}Name"]):
                    if f"{original_column_name}_aggregation" in chart_axis.keys():
                        if chart_axis[f"{original_column_name}_aggregation"] in ["SUM"]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                "Total " + chart_json[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                "Average " + chart_json[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MEDIAN",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                "Median " + chart_json[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MIN",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                "Minimum " + chart_json[f"y{yAxis_idx}Name"]
                            )
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MAX",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                "Maximum " + chart_json[f"y{yAxis_idx}Name"]
                            )
                        else:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                "Total " + chart_json[f"y{yAxis_idx}Name"]
                            )
                    else:
                        chart_json[f"y{yAxis_idx}Name"] = (
                            "Total " + chart_json[f"y{yAxis_idx}Name"]
                        )

            if not (
                isinstance(chart_json[f"Y{yAxis_idx}"][0], int)
                or isinstance(chart_json[f"Y{yAxis_idx}"][0], float)
            ):
                raise RuntimeError(
                    f"radar_chart: Y{yAxis_idx}-axis is not integer or float!",
                )

            # if (
            #     check_negative_value(chart_json[f"Y{yAxis_idx}"])
            #     or chart_json["Chart_Type"] == "column_chart"
            # ):
            #     chart_json["Chart_Type"] = "grouped_column_chart"

        yAxis_idx += 1

    if chart_json["Y"] == []:
        raise RuntimeError("radar_chart: Y-Axis is not found in extraction!")

    if any(
        chart_json[key] == [] or chart_json[key] == [""]
        for key in chart_json
        if re.match(r"^X\d*$", key)
    ):
        raise RuntimeError("radar_chart: One or more X-axis values are empty!")

    # Convert chart type to 'column_chart'
    if (
        len(chart_json["Y"]) == 1
        and ("Y2" not in chart_json or chart_json["Y2"] == [])
        and int(chart_json["Chart_Position"]) > 1
    ):
        card_chart_json_dict = convert_to_card_chart_d3(
            llama70b_client,
            chart_json,
            chart_data,
            logging_url,
        )
        return card_chart_json_dict

    return chart_json


def update_area_chart_d3(
    llama70b_client: Any,
    chart_json: dict,
    chart_data: pd.DataFrame,
    logging_url: str,
):
    # Reassign chart type to area_chart
    chart_json["Chart_Type"] = "area_chart"

    chart_json["Aggregated_Table_JSON"] = update_aggregated_table_chart_d3(
        chart_json["Aggregated_Table_JSON"],
        chart_data,
        chart_json["Chart_Axis"],
        chart_json["Chart_Type"],
    )
    chart_axis = chart_json["Chart_Axis"]

    chart_data_columns = list(chart_data.columns)

    if "xAxis" in chart_data_columns:
        xAxis_column_name = "xAxis"
    elif (
        "xAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["xAxis_column"], str)
        and chart_axis["xAxis_column"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_column"]
    elif (
        "xAxis_title" in chart_axis.keys()
        and chart_axis["xAxis_title"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_title"]
    else:
        raise RuntimeError("area_chart: X-Axis is not found in extraction!")

    if "series" in chart_data_columns:
        series_column_name = "series"
    elif (
        "series_column" in chart_axis.keys()
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
        chart_data = update_axis_title_and_data(chart_data, chart_axis)

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

    chart_json["X"] = [
        str(x_data) for x_data in chart_data[xAxis_column_name].values.tolist()
    ]

    if len(chart_json["X"]) >= 1 and len(chart_json["X"]) <= 2:
        return update_group_bar_chart_d3(
            llama70b_client,
            chart_json,
            chart_data,
            logging_url,
        )

    yAxis_idx = 1

    for column_name in list(chart_data.columns):
        if not re.search(r"yAxis([23456789])?", column_name, re.IGNORECASE):
            continue

        if yAxis_idx <= 1:
            chart_json["Y"] = [
                float(val) if isinstance(val, decimal.Decimal) else val
                for val in chart_data[column_name].values.tolist()
            ]

            underscore_index = column_name.find("_")

            # No Series
            if underscore_index == -1:
                if check_aggregation_phrases(
                    chart_axis[f"{column_name}_title"].replace("_", " "),
                ):
                    chart_json["yName"] = chart_axis[f"{column_name}_title"].replace(
                        "_",
                        " ",
                    )
                elif f"{column_name}_aggregation" in chart_axis.keys():
                    if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                        chart_json["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["AVG", "MEAN"]:
                        chart_json["yName"] = "Average " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                        chart_json["yName"] = "Median " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                        chart_json["yName"] = "Minimum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                        chart_json["yName"] = "Maximum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    else:
                        chart_json["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                else:
                    chart_json["yName"] = "Total " + chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")
            # Has Series
            else:
                original_column_name = column_name[:underscore_index]
                series_name = column_name[underscore_index + 1 :]
                if (
                    f"{original_column_name}_title" in chart_axis.keys()
                    and check_aggregation_phrases(
                        f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        ),
                    )
                ):
                    chart_json["yName"] = (
                        f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        )
                    )
                elif f"{original_column_name}_aggregation" in chart_axis.keys():
                    if chart_axis[f"{original_column_name}_aggregation"] in ["SUM"]:
                        chart_json["yName"] = (
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
                        chart_json["yName"] = (
                            "Average "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in [
                        "MEDIAN",
                    ]:
                        chart_json["yName"] = (
                            "Median "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in ["MIN"]:
                        chart_json["yName"] = (
                            "Minimum "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    elif chart_axis[f"{original_column_name}_aggregation"] in ["MAX"]:
                        chart_json["yName"] = (
                            "Maximum "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                    else:
                        chart_json["yName"] = (
                            "Total "
                            + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                                "_",
                                " ",
                            )
                        )
                else:
                    chart_json["yName"] = (
                        "Total "
                        + f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                            "_",
                            " ",
                        )
                    )

            if not (
                isinstance(chart_json["Y"][0], int)
                or isinstance(chart_json["Y"][0], float)
            ):
                raise RuntimeError("area_chart: Y-axis is not integer or float!")

            # if check_negative_value(chart_json["Y"]):
            #     chart_json["Chart_Type"] = "column_chart"
        else:
            chart_json[f"Y{yAxis_idx}"] = [
                float(val) if isinstance(val, decimal.Decimal) else val
                for val in chart_data[column_name].values.tolist()
            ]

            underscore_index = column_name.find("_")

            # No Series
            if underscore_index == -1:
                chart_json[f"y{yAxis_idx}Name"] = chart_axis[
                    f"{column_name}_title"
                ].replace("_", " ")
                if chart_json[f"y{yAxis_idx}Name"] == "":
                    chart_json[f"y{yAxis_idx}Name"] = chart_json["yName"]

                if not check_aggregation_phrases(chart_json[f"y{yAxis_idx}Name"]):
                    if f"{column_name}_aggregation" in chart_axis.keys():
                        if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                            chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{column_name}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = "Average " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                            chart_json[f"y{yAxis_idx}Name"] = "Median " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                            chart_json[f"y{yAxis_idx}Name"] = "Minimum " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                            chart_json[f"y{yAxis_idx}Name"] = "Maximum " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        else:
                            chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                    else:
                        chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                            f"y{yAxis_idx}Name"
                        ].replace("_", " ")
            # Has Series
            else:
                original_column_name = column_name[:underscore_index]
                series_name = column_name[underscore_index + 1 :]

                # Add Series Title to Series Name
                if (
                    "series_title" in chart_axis.keys()
                    and chart_axis["series_title"] != ""
                ):
                    series_name = f"""{chart_axis["series_title"]}: {series_name}"""

                chart_json[f"y{yAxis_idx}Name"] = (
                    f"{chart_axis[f'{original_column_name}_title']} ({series_name})".replace(
                        "_",
                        " ",
                    )
                )
                if chart_json[f"y{yAxis_idx}Name"] == "":
                    chart_json[f"y{yAxis_idx}Name"] = chart_json["yName"]

                if not check_aggregation_phrases(chart_json[f"y{yAxis_idx}Name"]):
                    if f"{original_column_name}_aggregation" in chart_axis.keys():
                        if chart_axis[f"{original_column_name}_aggregation"] in ["SUM"]:
                            chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = "Average " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MEDIAN",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = "Median " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MIN",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = "Minimum " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        elif chart_axis[f"{original_column_name}_aggregation"] in [
                            "MAX",
                        ]:
                            chart_json[f"y{yAxis_idx}Name"] = "Maximum " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                        else:
                            chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                                f"y{yAxis_idx}Name"
                            ].replace("_", " ")
                    else:
                        chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_json[
                            f"y{yAxis_idx}Name"
                        ].replace("_", " ")

            if not (
                isinstance(chart_json[f"Y{yAxis_idx}"][0], int)
                or isinstance(chart_json[f"Y{yAxis_idx}"][0], float)
            ):
                raise RuntimeError(
                    f"area_chart: Y{yAxis_idx}-axis is not integer or float!",
                )

            # if (
            #     check_negative_value(chart_json[f"Y{yAxis_idx}"])
            #     or chart_json["Chart_Type"] == "column_chart"
            # ):
            #     chart_json["Chart_Type"] = "grouped_column_chart"

        yAxis_idx += 1

    if chart_json["Y"] == []:
        raise RuntimeError("area_chart: Y-Axis is not found in extraction!")

    if any(
        chart_json[key] == [] or chart_json[key] == [""]
        for key in chart_json
        if re.match(r"^X\d*$", key)
    ):
        raise RuntimeError("area_chart: One or more X-axis values are empty!")

    if (
        len(chart_json["Y"]) == 1
        and ("Y2" not in chart_json or chart_json["Y2"] == [])
        and int(chart_json["Chart_Position"]) > 1
    ):
        card_chart_json_dict = convert_to_card_chart_d3(
            llama70b_client,
            chart_json,
            chart_data,
            logging_url,
        )
        return card_chart_json_dict

    return chart_json


def update_histogram_chart_d3(
    llama70b_client: Any,
    chart_json: dict,
    chart_data: pd.DataFrame,
    logging_url: str,
):
    # Reassign chart type to histogram_chart
    chart_json["Chart_Type"] = "histogram_chart"

    chart_json["Aggregated_Table_JSON"] = update_aggregated_table_chart_d3(
        chart_json["Aggregated_Table_JSON"],
        chart_data,
        chart_json["Chart_Axis"],
        chart_json["Chart_Type"],
    )
    chart_axis = chart_json["Chart_Axis"]

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
        "xAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["xAxis_column"], str)
        and chart_axis["xAxis_column"] in chart_data_columns
    ) or (
        "xAxis_column" in chart_axis.keys()
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
        "xAxis_column" in chart_axis.keys()
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
        "xAxis_title" in chart_axis.keys()
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

                chart_json["Chart_Data"] = [{"X_Value": x} for x in chart_column_data]
                break

        except Exception:
            print(traceback.format_exc())

    if chart_json["Chart_Data"] == []:
        raise RuntimeError("histogram_chart: Chart data is empty!")

    if any(
        chart_json[key] == [] or chart_json[key] == [""]
        for key in chart_json
        if re.match(r"^X\d*$", key)
    ):
        raise RuntimeError("histogram_chart: One or more X-axis values are empty!")

    return chart_json


def update_table_chart_d3(
    llama70b_client: Any,
    chart_json: dict,
    chart_data: pd.DataFrame,
    logging_url: str,
):
    # Reassign chart type to table_chart
    chart_json["Chart_Type"] = "table_chart"

    new_data = []

    column_names = list(chart_data.columns)
    chart_axis = chart_json["Chart_Axis"]

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
        "xAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["xAxis_column"], str)
        and chart_axis["xAxis_column"] in column_names
    ):
        xAxis_column_name = chart_axis["xAxis_column"]
    elif (
        "xAxis_title" in chart_axis.keys()
        and chart_axis["xAxis_title"] in chart_data.columns
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
                    "xAxis_column" in chart_axis.keys()
                    and column_name in chart_axis["xAxis_column"]
                ):
                    new_column_name = chart_axis["xAxis_title"]
                elif column_name == "yAxis" or (
                    "yAxis_column" in chart_axis.keys()
                    and column_name in chart_axis["yAxis_column"]
                ):
                    new_column_name = chart_axis["yAxis_title"]
                else:
                    new_column_name = column_name
            except Exception:
                new_column_name = column_name

            new_column_name = new_column_name.replace("_", " ")

            try:
                if isinstance(row[column_idx], int) or isinstance(
                    row[column_idx],
                    float,
                ):
                    # row_data[new_column_name] = '{:,}'.format(row[column_idx])
                    row_data[new_column_name] = row[column_idx]
                elif isinstance(row[column_idx], decimal.Decimal):
                    # row_data[new_column_name] = '{:,}'.format(float(row[column_idx]))
                    row_data[new_column_name] = float(row[column_idx])
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
        new_data.append(row_data)

    chart_json["data"] = new_data
    chart_json["Chart_Size"] = sys.getsizeof(new_data)

    return chart_json


def update_pie_chart_d3(
    llama70b_client: Any,
    chart_json: dict,
    chart_data: pd.DataFrame,
    logging_url: str,
):
    # Reassign chart type to pie_chart
    chart_json["Chart_Type"] = "pie_chart"

    chart_json["Aggregated_Table_JSON"] = update_aggregated_table_chart_d3(
        chart_json["Aggregated_Table_JSON"],
        chart_data,
        chart_json["Chart_Axis"],
        chart_json["Chart_Type"],
    )
    chart_axis = chart_json["Chart_Axis"]

    sorted_chart_data = chart_data.copy()
    chart_data_columns = list(chart_data.columns)

    if "xAxis" in chart_data_columns:
        xAxis_column_name = "xAxis"
    elif (
        "xAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["xAxis_column"], str)
        and chart_axis["xAxis_column"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_column"]
    elif (
        "xAxis_title" in chart_axis.keys()
        and chart_axis["xAxis_title"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_title"]
    else:
        raise RuntimeError("pie_chart: X-Axis is not found in extraction!")

    if "yAxis" in chart_data_columns:
        yAxis_column_name = "yAxis"
    elif (
        "yAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["yAxis_column"], str)
        and chart_axis["yAxis_column"] in chart_data_columns
    ):
        yAxis_column_name = chart_axis["yAxis_column"]
    else:
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

    if len(chart_json["Chart_Data"]) > 12:
        return update_group_bar_chart_d3(
            chart_json, chart_data, chart_data, logging_url
        )

    y_values = chart_data[yAxis_column_name].values.tolist()

    if 0 in y_values or 0.0 in y_values:
        return update_group_bar_chart_d3(
            llama70b_client, chart_json, chart_data, logging_url
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
        sorted_chart_data = update_axis_title_and_data(sorted_chart_data, chart_axis)

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

    chart_json["Chart_Data"] = []
    for group_name, y_value in zip(
        sorted_chart_data[xAxis_column_name].values.tolist(),
        sorted_chart_data[yAxis_column_name].values.tolist(),
    ):
        chart_json["Chart_Data"].append(
            {
                "Group_Name": str(group_name),
                "Y_Value": (
                    float(y_value) if isinstance(y_value, decimal.Decimal) else y_value
                ),
            },
        )

    if any(
        chart_json[key] == [] or chart_json[key] == [""]
        for key in chart_json
        if re.match(r"^X\d*$", key)
    ):
        raise RuntimeError("pie_chart: One or more X-axis values are empty!")

    # if check_negative_value(chart_json["Y"]):
    #     chart_json["Chart_Type"] = "column_chart"

    if len(y_values) == 1 and int(chart_json["Chart_Position"]) > 1:
        card_chart_json_dict = convert_to_card_chart_d3(
            llama70b_client,
            chart_json,
            chart_data,
            logging_url,
        )
        return card_chart_json_dict

    return chart_json


def update_pyramid_chart_d3(
    llama70b_client: Any,
    chart_json: dict,
    chart_data: pd.DataFrame,
    logging_url: str,
):
    # Reassign chart type to pyramid_chart
    chart_json["Chart_Type"] = "pyramidfunnel_chart"

    chart_json["Aggregated_Table_JSON"] = update_aggregated_table_chart_d3(
        chart_json["Aggregated_Table_JSON"],
        chart_data,
        chart_json["Chart_Axis"],
        chart_json["Chart_Type"],
    )
    chart_axis = chart_json["Chart_Axis"]

    sorted_chart_data = chart_data.copy()

    chart_data_columns = list(chart_data.columns)

    if "xAxis" in chart_data_columns:
        xAxis_column_name = "xAxis"
    elif (
        "xAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["xAxis_column"], str)
        and chart_axis["xAxis_column"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_column"]
    elif (
        "xAxis_title" in chart_axis.keys()
        and chart_axis["xAxis_title"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_title"]
    else:
        raise RuntimeError("pyramidfunnel_chart: X-Axis is not found in extraction!")

    if "yAxis" in chart_data_columns:
        yAxis_column_name = "yAxis"
    elif (
        "yAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["yAxis_column"], str)
        and chart_axis["yAxis_column"] in chart_data_columns
    ):
        yAxis_column_name = chart_axis["yAxis_column"]
    else:
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
            raise RuntimeError(
                f"pyramidfunnel_chart: {yAxis_column_name} is not numerical!",
            )

    y_values = chart_data[yAxis_column_name].values.tolist()
    if len(y_values) == 1:
        card_chart_json_dict = convert_to_card_chart_d3(
            llama70b_client,
            chart_json,
            chart_data,
            logging_url,
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
        sorted_chart_data = update_axis_title_and_data(sorted_chart_data, chart_axis)
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

    chart_json["X"] = [
        str(x_data) for x_data in sorted_chart_data[xAxis_column_name].values.tolist()
    ]

    chart_json["Y"] = [
        float(val) if isinstance(val, decimal.Decimal) else val
        for val in sorted_chart_data[yAxis_column_name].values.tolist()
    ]

    if not (
        isinstance(chart_json["Y"][0], int) or isinstance(chart_json["Y"][0], float)
    ):
        raise RuntimeError("pyramid-chart: Y-axis is not integer or float!")

    if len(chart_json["X"]) > 8:
        # pyramid_chart_json_dict["Chart_Type"] = "bar_chart"
        chart_json["Chart_Type"] = "grouped_bar_chart"

    if any(
        chart_json[key] == [] or chart_json[key] == [""]
        for key in chart_json
        if re.match(r"^X\d*$", key)
    ):
        raise RuntimeError("pyramid_chart: One or more X-axis values are empty!")

    # if check_negative_value(chart_json["Y"]):
    #     chart_json["Chart_Type"] = "column_chart"

    if len(chart_json["Y"]) == 1 and int(chart_json["Chart_Position"]) > 1:
        card_chart_json_dict = convert_to_card_chart_d3(
            llama70b_client,
            chart_json,
            chart_data,
            logging_url,
        )
        return card_chart_json_dict

    return chart_json


def update_treemap_chart_d3(
    llama70b_client: Any,
    chart_json: dict,
    chart_data: pd.DataFrame,
    logging_url: str,
):
    # Reassign chart type to TreemapMulti_chart
    chart_json["Chart_Type"] = "TreemapMulti_chart"

    chart_json["Aggregated_Table_JSON"] = update_aggregated_table_chart_d3(
        chart_json["Aggregated_Table_JSON"],
        chart_data,
        chart_json["Chart_Axis"],
        chart_json["Chart_Type"],
    )
    chart_axis = chart_json["Chart_Axis"]

    chart_data_columns = list(chart_data.columns)

    if "xAxis" in chart_data_columns:
        xAxis_column_name = "xAxis"
    elif (
        "xAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["xAxis_column"], str)
        and chart_axis["xAxis_column"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_column"]
    elif (
        "xAxis_title" in chart_axis.keys()
        and chart_axis["xAxis_title"] in chart_data.columns
    ):
        xAxis_column_name = chart_axis["xAxis_title"]
    else:
        raise RuntimeError("treemap_chart: X-Axis is not found in extraction!")

    if "yAxis" in chart_data_columns:
        yAxis_column_name = "yAxis"
    elif (
        "yAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["yAxis_column"], str)
        and chart_axis["yAxis_column"] in chart_data_columns
    ):
        yAxis_column_name = chart_axis["yAxis_column"]
    else:
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
            raise RuntimeError(f"treemap_chart: {yAxis_column_name} is not numerical!")

    if "series" in chart_data_columns:
        series_column_name = "series"
    elif (
        "series_column" in chart_axis.keys()
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
        chart_data = update_axis_title_and_data(chart_data, chart_axis)

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
                series_chart_data = update_axis_title_and_data(
                    series_chart_data,
                    chart_axis,
                )

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
                    chart_json["X"] = [
                        str(x_data)
                        for x_data in series_chart_data[
                            xAxis_column_name
                        ].values.tolist()
                    ]

                    chart_json["Y"] = [
                        float(val) if isinstance(val, decimal.Decimal) else val
                        for val in series_chart_data[
                            series_chart_column
                        ].values.tolist()
                    ]

                    # Add Series Title to Series Value
                    if (
                        "series_title" in chart_axis.keys()
                        and chart_axis["series_title"] != ""
                    ):
                        series_value = (
                            f"""{chart_axis["series_title"]}: {series_value}"""
                        )

                    if (
                        f"{series_chart_column}_title" in chart_axis.keys()
                        and check_aggregation_phrases(
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})",
                        )
                    ):
                        chart_json["yName"] = (
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})"
                        )
                    elif f"{series_chart_column}_aggregation" in chart_axis.keys():
                        if chart_axis[f"{series_chart_column}_aggregation"] in ["SUM"]:
                            chart_json["yName"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            chart_json["yName"] = (
                                f"Average {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "MEDIAN",
                        ]:
                            chart_json["yName"] = (
                                f"Median {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "MIN",
                        ]:
                            chart_json["yName"] = (
                                f"Minimum {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "MAX",
                        ]:
                            chart_json["yName"] = (
                                f"Maximum {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                        else:
                            chart_json["yName"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                    else:
                        chart_json["yName"] = (
                            f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                        )

                    if not (
                        isinstance(chart_json["Y"][0], int)
                        or isinstance(chart_json["Y"][0], float)
                    ):
                        raise RuntimeError(
                            "treemap_chart: Y-axis is not integer or float!",
                        )

                    # if check_negative_value(chart_json["Y"]):
                    #     chart_json["Chart_Type"] = "column_chart"
                else:
                    chart_json[f"X{yAxis_idx}"] = [
                        str(x_data)
                        for x_data in series_chart_data[
                            xAxis_column_name
                        ].values.tolist()
                    ]

                    chart_json[f"Y{yAxis_idx}"] = [
                        float(val) if isinstance(val, decimal.Decimal) else val
                        for val in series_chart_data[
                            series_chart_column
                        ].values.tolist()
                    ]

                    # Add Series Title to Series Value
                    if (
                        "series_title" in chart_axis.keys()
                        and chart_axis["series_title"] != ""
                    ):
                        series_value = (
                            f"""{chart_axis["series_title"]}: {series_value}"""
                        )

                    if (
                        f"{series_chart_column}_title" in chart_axis.keys()
                        and check_aggregation_phrases(
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})",
                        )
                    ):
                        chart_json[f"y{yAxis_idx}Name"] = (
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})"
                        )
                    elif "yAxis_aggregation" in chart_axis.keys():
                        if chart_axis["yAxis_aggregation"] in ["SUM"]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                        elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                f"Average {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                        elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                f"Median {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                        elif chart_axis["yAxis_aggregation"] in ["MIN"]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                f"Minimum {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                        elif chart_axis["yAxis_aggregation"] in ["MAX"]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                f"Maximum {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                        else:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                    else:
                        chart_json[f"y{yAxis_idx}Name"] = (
                            f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                        )

                    if not (
                        isinstance(chart_json[f"Y{yAxis_idx}"][0], int)
                        or isinstance(chart_json[f"Y{yAxis_idx}"][0], float)
                    ):
                        raise RuntimeError(
                            f"treemap_chart: Y{yAxis_idx}-axis is not integer or float!",
                        )

                    # if (
                    #     check_negative_value(chart_json[f"Y{yAxis_idx}"])
                    #     or chart_json["Chart_Type"] == "column_chart"
                    # ):
                    #     return update_group_column_chart(
                    #         chart_json,
                    #         chart_data,
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
                chart_json["X"] = [
                    str(x_data)
                    for x_data in chart_data[xAxis_column_name].values.tolist()
                ]

                chart_json["Y"] = [
                    float(val) if isinstance(val, decimal.Decimal) else val
                    for val in chart_data[column_name].values.tolist()
                ]

                if check_aggregation_phrases(chart_axis[f"{column_name}_title"]):
                    chart_json["yName"] = chart_axis[f"{column_name}_title"]
                elif "yAxis_aggregation" in chart_axis.keys():
                    if chart_axis["yAxis_aggregation"] in ["SUM"]:
                        chart_json["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
                        chart_json["yName"] = "Average " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
                        chart_json["yName"] = "Median " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["MIN"]:
                        chart_json["yName"] = "Minimum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["MAX"]:
                        chart_json["yName"] = "Maximum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    else:
                        chart_json["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                else:
                    chart_json["yName"] = "Total " + chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")

                if not (
                    isinstance(chart_json["Y"][0], int)
                    or isinstance(chart_json["Y"][0], float)
                ):
                    raise RuntimeError("treemap_chart: Y-axis is not integer or float!")

                # if check_negative_value(chart_json["Y"]):
                #     chart_json["Chart_Type"] = "column_chart"
            else:
                chart_json[f"X{yAxis_idx}"] = [
                    str(x_data)
                    for x_data in chart_data[xAxis_column_name].values.tolist()
                ]
                chart_json[f"Y{yAxis_idx}"] = [
                    float(val) if isinstance(val, decimal.Decimal) else val
                    for val in chart_data[column_name].values.tolist()
                ]

                if check_aggregation_phrases(chart_axis[f"{column_name}_title"]):
                    chart_json[f"y{yAxis_idx}Name"] = chart_axis[f"{column_name}_title"]
                elif f"{column_name}_aggregation" in chart_axis.keys():
                    if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                        chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["AVG", "MEAN"]:
                        chart_json[f"y{yAxis_idx}Name"] = "Average " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                        chart_json[f"y{yAxis_idx}Name"] = "Median " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                        chart_json[f"y{yAxis_idx}Name"] = "Minimum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                        chart_json[f"y{yAxis_idx}Name"] = "Maximum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    else:
                        chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                else:
                    chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")

                if not (
                    isinstance(chart_json[f"Y{yAxis_idx}"][0], int)
                    or isinstance(chart_json[f"Y{yAxis_idx}"][0], float)
                ):
                    raise RuntimeError(
                        f"treemap_chart: Y{yAxis_idx}-axis is not integer or float!",
                    )

                # if (
                #     check_negative_value(chart_json[f"Y{yAxis_idx}"])
                #     or chart_json["Chart_Type"] == "column_chart"
                # ):
                #     return update_group_column_chart(
                #         chart_json,
                #         chart_data,
                #     )

            yAxis_idx += 1

    if any(
        chart_json[key] == [] or chart_json[key] == [""]
        for key in chart_json
        if re.match(r"^X\d*$", key)
    ):
        raise RuntimeError("treemap_chart: One or more X-axis values are empty!")

    if (
        len(chart_json["Y"]) == 1
        and ("Y2" not in chart_json or chart_json["Y2"] == [])
        and int(chart_json["Chart_Position"]) > 1
    ):
        card_chart_json_dict = convert_to_card_chart_d3(
            llama70b_client,
            chart_json,
            chart_data,
            logging_url,
        )
        return card_chart_json_dict

    return chart_json


def update_bubbleplot_chart_d3(
    llama70b_client: Any,
    chart_json: dict,
    chart_data: pd.DataFrame,
    logging_url: str,
):
    # Reassign chart type to bubble_chart
    chart_json["Chart_Type"] = "bubbleplot_chart"

    chart_json["Aggregated_Table_JSON"] = update_aggregated_table_chart_d3(
        chart_json["Aggregated_Table_JSON"],
        chart_data,
        chart_json["Chart_Axis"],
        chart_json["Chart_Type"],
    )
    chart_axis = chart_json["Chart_Axis"]

    chart_data_columns = list(chart_data.columns)

    if "xAxis" in chart_data_columns:
        xAxis_column_name = "xAxis"
    elif (
        "xAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["xAxis_column"], str)
        and chart_axis["xAxis_column"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_column"]
    elif (
        "xAxis_title" in chart_axis.keys()
        and chart_axis["xAxis_title"] in chart_data.columns
    ):
        xAxis_column_name = chart_axis["xAxis_title"]
    else:
        raise RuntimeError("bubbleplot_: X-Axis is not found in extraction!")

    if "yAxis" in chart_data_columns:
        yAxis_column_name = "yAxis"
    elif (
        "yAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["yAxis_column"], str)
        and chart_axis["yAxis_column"] in chart_data_columns
    ):
        yAxis_column_name = chart_axis["yAxis_column"]
    else:
        raise RuntimeError("bubbleplot_chart: Y-Axis is not found in extraction!")

    if "zAxis" in chart_data_columns:
        zAxis_column_name = "zAxis"
    elif (
        "zAxis_column" in chart_axis.keys()
        and isinstance(chart_axis["zAxis_column"], str)
        and chart_axis["zAxis_column"] in chart_data_columns
    ):
        zAxis_column_name = chart_axis["zAxis_column"]
    else:
        raise RuntimeError("bubbleplot_chart: Z-Axis is not found in extraction!")

    if "series" in chart_data_columns:
        series_column_name = "series"
    elif (
        "series_column" in chart_axis.keys()
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
        chart_data = update_axis_title_and_data(chart_data, chart_axis)

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
                series_chart_data = update_axis_title_and_data(
                    series_chart_data,
                    chart_axis,
                )

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
                    chart_json["X"] = [
                        str(x_data)
                        for x_data in series_chart_data[
                            xAxis_column_name
                        ].values.tolist()
                    ]

                    chart_json["Y"] = [
                        float(val) if isinstance(val, decimal.Decimal) else val
                        for val in series_chart_data[
                            series_chart_column
                        ].values.tolist()
                    ]

                    chart_json["Z"] = [
                        float(val) if isinstance(val, decimal.Decimal) else val
                        for val in series_chart_data[zAxis_column_name].values.tolist()
                    ]

                    # Add Series Title to Series Value
                    if (
                        "series_title" in chart_axis.keys()
                        and chart_axis["series_title"] != ""
                    ):
                        series_value = (
                            f"""{chart_axis["series_title"]}: {series_value}"""
                        )

                    if (
                        f"{series_chart_column}_title" in chart_axis.keys()
                        and check_aggregation_phrases(
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})",
                        )
                    ):
                        chart_json["yName"] = (
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})"
                        )
                    elif f"{series_chart_column}_aggregation" in chart_axis.keys():
                        if chart_axis[f"{series_chart_column}_aggregation"] in ["SUM"]:
                            chart_json["yName"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "AVG",
                            "MEAN",
                        ]:
                            chart_json["yName"] = (
                                f"Average {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "MEDIAN",
                        ]:
                            chart_json["yName"] = (
                                f"Median {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "MIN",
                        ]:
                            chart_json["yName"] = (
                                f"Minimum {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                        elif chart_axis[f"{series_chart_column}_aggregation"] in [
                            "MAX",
                        ]:
                            chart_json["yName"] = (
                                f"Maximum {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                        else:
                            chart_json["yName"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                    else:
                        chart_json["yName"] = (
                            f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                        )

                    if not (
                        isinstance(chart_json["Y"][0], int)
                        or isinstance(chart_json["Y"][0], float)
                    ):
                        raise RuntimeError(
                            "bubbleplot_chart: Y-axis is not integer or float!",
                        )

                    # if check_negative_value(chart_json["Y"]):
                    #     chart_json["Chart_Type"] = "column_chart"
                else:
                    chart_json[f"X{yAxis_idx}"] = [
                        str(x_data)
                        for x_data in series_chart_data[
                            xAxis_column_name
                        ].values.tolist()
                    ]

                    chart_json[f"Y{yAxis_idx}"] = [
                        float(val) if isinstance(val, decimal.Decimal) else val
                        for val in series_chart_data[
                            series_chart_column
                        ].values.tolist()
                    ]

                    chart_json[f"Z{yAxis_idx}"] = [
                        float(val) if isinstance(val, decimal.Decimal) else val
                        for val in series_chart_data[zAxis_column_name].values.tolist()
                    ]

                    # Add Series Title to Series Value
                    if (
                        "series_title" in chart_axis.keys()
                        and chart_axis["series_title"] != ""
                    ):
                        series_value = (
                            f"""{chart_axis["series_title"]}: {series_value}"""
                        )

                    if (
                        f"{series_chart_column}_title" in chart_axis.keys()
                        and check_aggregation_phrases(
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})",
                        )
                    ):
                        chart_json[f"y{yAxis_idx}Name"] = (
                            f"{chart_axis[f'{series_chart_column}_title']} ({series_value})"
                        )
                    elif "yAxis_aggregation" in chart_axis.keys():
                        if chart_axis["yAxis_aggregation"] in ["SUM"]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                        elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                f"Average {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                        elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                f"Median {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                        elif chart_axis["yAxis_aggregation"] in ["MIN"]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                f"Minimum {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                        elif chart_axis["yAxis_aggregation"] in ["MAX"]:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                f"Maximum {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                        else:
                            chart_json[f"y{yAxis_idx}Name"] = (
                                f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                            )
                    else:
                        chart_json[f"y{yAxis_idx}Name"] = (
                            f"Total {chart_axis[f'{series_chart_column}_title']} ({series_value})"
                        )

                    if not (
                        isinstance(chart_json[f"Y{yAxis_idx}"][0], int)
                        or isinstance(chart_json[f"Y{yAxis_idx}"][0], float)
                    ):
                        raise RuntimeError(
                            f"bubbleplot_chart: Y{yAxis_idx}-axis is not integer or float!",
                        )

                    # if (
                    # check_negative_value(chart_json[f"Y{yAxis_idx}"])
                    # or chart_json["Chart_Type"] == "column_chart"
                    # ):
                    #     return update_group_column_chart(
                    #         chart_json,
                    #         chart_data,
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
                chart_json["X"] = [
                    str(x_data)
                    for x_data in chart_data[xAxis_column_name].values.tolist()
                ]

                chart_json["Y"] = [
                    float(val) if isinstance(val, decimal.Decimal) else val
                    for val in chart_data[column_name].values.tolist()
                ]

                chart_json["Z"] = [
                    float(val) if isinstance(val, decimal.Decimal) else val
                    for val in chart_data[zAxis_column_name].values.tolist()
                ]

                if check_aggregation_phrases(chart_axis[f"{column_name}_title"]):
                    chart_json["yName"] = chart_axis[f"{column_name}_title"]
                elif "yAxis_aggregation" in chart_axis.keys():
                    if chart_axis["yAxis_aggregation"] in ["SUM"]:
                        chart_json["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["AVG", "MEAN"]:
                        chart_json["yName"] = "Average " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["MEDIAN"]:
                        chart_json["yName"] = "Median " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["MIN"]:
                        chart_json["yName"] = "Minimum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis["yAxis_aggregation"] in ["MAX"]:
                        chart_json["yName"] = "Maximum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    else:
                        chart_json["yName"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                else:
                    chart_json["yName"] = "Total " + chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")

                if not (
                    isinstance(chart_json["Y"][0], int)
                    or isinstance(chart_json["Y"][0], float)
                ):
                    raise RuntimeError(
                        "bubbleplot_chart: Y-axis is not integer or float!",
                    )

                # if check_negative_value(chart_json["Y"]):
                #     chart_json["Chart_Type"] = "column_chart"
            else:
                chart_json[f"X{yAxis_idx}"] = [
                    str(x_data)
                    for x_data in chart_data[xAxis_column_name].values.tolist()
                ]
                chart_json[f"Y{yAxis_idx}"] = [
                    float(val) if isinstance(val, decimal.Decimal) else val
                    for val in chart_data[column_name].values.tolist()
                ]
                chart_json[f"Z{yAxis_idx}"] = [
                    float(val) if isinstance(val, decimal.Decimal) else val
                    for val in chart_data[zAxis_column_name].values.tolist()
                ]

                if check_aggregation_phrases(chart_axis[f"{column_name}_title"]):
                    chart_json[f"y{yAxis_idx}Name"] = chart_axis[f"{column_name}_title"]
                elif f"{column_name}_aggregation" in chart_axis.keys():
                    if chart_axis[f"{column_name}_aggregation"] in ["SUM"]:
                        chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["AVG", "MEAN"]:
                        chart_json[f"y{yAxis_idx}Name"] = "Average " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MEDIAN"]:
                        chart_json[f"y{yAxis_idx}Name"] = "Median " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MIN"]:
                        chart_json[f"y{yAxis_idx}Name"] = "Minimum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    elif chart_axis[f"{column_name}_aggregation"] in ["MAX"]:
                        chart_json[f"y{yAxis_idx}Name"] = "Maximum " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                    else:
                        chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_axis[
                            f"{column_name}_title"
                        ].replace("_", " ")
                else:
                    chart_json[f"y{yAxis_idx}Name"] = "Total " + chart_axis[
                        f"{column_name}_title"
                    ].replace("_", " ")

                if not (
                    isinstance(chart_json[f"Y{yAxis_idx}"][0], int)
                    or isinstance(chart_json[f"Y{yAxis_idx}"][0], float)
                ):
                    raise RuntimeError(
                        f"bubbleplot_chart: Y{yAxis_idx}-axis is not integer or float!",
                    )

                # if (
                #     check_negative_value(chart_json[f"Y{yAxis_idx}"])
                #     or chart_json["Chart_Type"] == "column_chart"
                # ):
                #     return update_group_column_chart(
                #         chart_json,
                #         chart_data,
                #     )

            yAxis_idx += 1

    if chart_json["Y"] == []:
        raise RuntimeError("bubbleplot_chart: Y-Axis is not found in extraction!")

    if any(
        chart_json[key] == [] or chart_json[key] == [""]
        for key in chart_json
        if re.match(r"^X\d*$", key)
    ):
        raise RuntimeError("bubbleplot_chart: One or more X-axis values are empty!")

    if (
        len(chart_json["Y"]) == 1
        and ("Y2" not in chart_json or chart_json["Y2"] == [])
        and int(chart_json["Chart_Position"]) > 1
    ):
        card_chart_json_dict = convert_to_card_chart_d3(
            llama70b_client,
            chart_json,
            chart_data,
            logging_url,
        )
        return card_chart_json_dict

    new_chart_data_lists = []

    # Check for the main Y and its corresponding X
    if "Z" in chart_json and "Y" in chart_json:
        x_values = chart_json["X"]
        main_group_name = chart_json.get("yName", "Series 1")

        for i in range(len(x_values)):
            x_value = float(x_values[i])
            main_y_value = chart_json["Y"][i]
            main_z_value = chart_json["Z"][i]
            new_chart_data_lists.append(
                {
                    "X_Value": x_value,
                    "Y_Value": main_y_value,
                    "Z_Value": main_z_value,
                    "Group_Name": main_group_name,
                },
            )

    # Check for additional Y values (Y2, Y3, ...)
    j = 2
    while f"Y{j}" in chart_json:
        # Corresponding X values for Y2, Y3, etc.
        x_key = f"X{j}"
        if x_key in chart_json:
            x_values = chart_json[x_key]
            group_name_key = f"y{j}Name"
            group_name = chart_json.get(group_name_key, f"Series {j}")

            for i in range(len(x_values)):
                x_value = float(x_values[i])
                y_key = f"Y{j}"
                z_key = f"Z{j}"
                if y_key in chart_json:
                    additional_y_value = chart_json[y_key][i]
                    additional_z_value = chart_json[z_key][i]
                    new_chart_data_lists.append(
                        {
                            "X_Value": x_value,
                            "Y_Value": additional_y_value,
                            "Z_Value": additional_z_value,
                            "Group_Name": group_name,
                        },
                    )

        j += 1

    # Store chart data in the original dict
    chart_json["Chart_Data"] = new_chart_data_lists

    keys_to_remove = ["X", "Y", "Z", "yName"]

    i = 2
    while f"y{i}Name" in chart_json:
        keys_to_remove.append(f"y{i}Name")
        i += 1

    j = 2
    while f"X{j}" in chart_json and f"Y{j}" in chart_json and f"Z{j}" in chart_json:
        keys_to_remove.append(f"X{j}")
        keys_to_remove.append(f"Y{j}")
        keys_to_remove.append(f"Z{j}")
        j += 1

    # Remove all specified keys ['X', 'Y', 'Z', 'yName'] and etc. from the dictionary
    for key in keys_to_remove:
        if key in chart_json:
            del chart_json[key]

    return chart_json


CHART_TYPE_UPDATER_FUNCTIONS_D3 = {
    "barlinecombo_chart": update_combo_chart_d3,
    "line_chart": update_line_chart_d3,
    "spline_chart": update_spline_chart_d3,
    "scatterplot_chart": update_scatterplot_chart_d3,
    "grouped_bar_chart": update_group_bar_chart_d3,
    "radar_chart": update_radar_chart_d3,
    "histogram_chart": update_histogram_chart_d3,
    "area_chart": update_area_chart_d3,
    "pie_chart": update_pie_chart_d3,
    "bubbleplot_chart": update_bubbleplot_chart_d3,
    "pyramidfunnel_chart": update_pyramid_chart_d3,
    "TreemapMulti_chart": update_treemap_chart_d3,
    "table_chart": update_table_chart_d3,
    "full_table_chart": update_table_chart_d3,
    "card_chart": update_card_chart_d3,
}


def update_chart_data_d3(
    llama70b_client: Any,
    separated_chart_json: dict,
    logging_url: str,
    session_id: str,
    database_logger: logging.Logger,
) -> list:
    for chart_name in separated_chart_json:
        separated_chart_json[chart_name] = sorted(
            separated_chart_json[chart_name],
            key=lambda x: int(x["Chart_Position"]),
        )

        # If Visual
        if "visual" in chart_name.lower():
            # Main Chart Update
            chart_data = execute_sql_query_updater(separated_chart_json[chart_name][0])

            if chart_data.empty:
                continue

            chart_data = postprocess_updater_chart_json(
                separated_chart_json[chart_name][0],
                chart_data,
                database_logger,
            )

            chart_type = separated_chart_json[chart_name][0]["Chart_Type"]

            try:
                new_chart_json = CHART_TYPE_UPDATER_FUNCTIONS_D3[chart_type](
                    llama70b_client,
                    separated_chart_json[chart_name][0],
                    chart_data,
                    logging_url,
                )
                separated_chart_json[chart_name][0] = new_chart_json

                if len(separated_chart_json[chart_name]) > 1:
                    # Visual Description Update
                    separated_chart_json[chart_name][1] = (
                        generate_visual_description_chart(
                            llama70b_client,
                            separated_chart_json[chart_name][0]["User_Query"],
                            separated_chart_json[chart_name][0],
                            logging_url,
                            session_id,
                            database_logger,
                            2,
                        )
                    )

                    # Business Recommendation Update
                    separated_chart_json[chart_name][2] = (
                        generate_business_recommendation_chart(
                            llama70b_client,
                            separated_chart_json[chart_name][0]["User_Query"],
                            separated_chart_json[chart_name][0],
                            logging_url,
                            session_id,
                            database_logger,
                            3,
                        )
                    )
                else:
                    # Visual Description Addition
                    separated_chart_json[chart_name].append(
                        generate_visual_description_chart(
                            llama70b_client,
                            separated_chart_json[chart_name][0]["User_Query"],
                            separated_chart_json[chart_name][0],
                            logging_url,
                            session_id,
                            database_logger,
                            2,
                        ),
                    )

                    # Business Recommendation Addition
                    separated_chart_json[chart_name].append(
                        generate_business_recommendation_chart(
                            llama70b_client,
                            separated_chart_json[chart_name][0]["User_Query"],
                            separated_chart_json[chart_name][0],
                            logging_url,
                            session_id,
                            database_logger,
                            3,
                        ),
                    )
            except Exception:
                print(traceback.format_exc())
        # If data asset
        elif "table" in chart_name.lower():
            chart_data = execute_sql_query_updater(separated_chart_json[chart_name][0])

            if chart_data.empty:
                continue

            chart_type = separated_chart_json[chart_name][0]["Chart_Type"]

            try:
                new_chart_json = CHART_TYPE_UPDATER_FUNCTIONS_D3[chart_type](
                    llama70b_client,
                    separated_chart_json[chart_name][0],
                    chart_data,
                    logging_url,
                )
                separated_chart_json[chart_name][0] = new_chart_json
            except Exception:
                print(traceback.format_exc())
        else:
            raise RuntimeError("Unknown chart name!")

    new_chart_json = []

    visual_separated_chart_json_key = [
        key for key in separated_chart_json if "visual" in key.lower()
    ]

    visual_separated_chart_json_key = sorted(
        visual_separated_chart_json_key,
        key=lambda x: int(x.split(" ")[1]),
    )

    for key in visual_separated_chart_json_key:
        new_chart_json.extend(separated_chart_json[key])

    if "Table" in separated_chart_json:
        new_chart_json.extend(separated_chart_json["Table"])

    return new_chart_json


def determine_date_frequency(date_series):
    date_series = pd.to_datetime(date_series, errors="coerce")

    if date_series.isnull().all():
        return None, None

    date_diffs = date_series.diff().dropna()

    if (date_diffs == pd.Timedelta(days=1)).all():
        return date_series.dt.strftime("%Y-%m-%d")
    if (date_diffs >= pd.Timedelta(days=28)).all() and (
        date_diffs <= pd.Timedelta(days=31)
    ).all():
        return date_series.dt.strftime("%Y-%m")
    if (date_diffs >= pd.Timedelta(days=365)).all() and (
        date_diffs <= pd.Timedelta(days=366)
    ).all():
        return date_series.dt.to_period("Y").astype(str)
    return date_series.dt.strftime("%Y-%m-%d")


def update_axis_title_and_data(chart_data: pd.DataFrame, chart_axis: dict):
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
        "xAxis_title" in chart_axis and chart_axis["xAxis_title"] in chart_data_columns
    ):
        xAxis_column_name = chart_axis["xAxis_title"]
    else:
        raise RuntimeError(
            "X-axis is not found in update_axis_title_and_data function!",
        )

    adjusted_dates = determine_date_frequency(chart_data[xAxis_column_name])
    chart_data[xAxis_column_name] = adjusted_dates

    return chart_data
