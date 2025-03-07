import logging
import os
import re
import requests

from typing import Any, Union
from rapidfuzz import fuzz
from time import perf_counter
from components.cmysql import native
from components.sql_query import (
    classify_time_duration,
    classify_instruction_time_duration,
)

from ..datamodel import DataSummary
from ..utils import (
    generate_column_information_prompt,
    normalize_chart_type,
    calculate_token_usage,
)

logger = logging.getLogger(__name__)


def fix_sql_query(
    llama70b_client: Any,
    sql_query: str,
    data_summary: DataSummary,
    chart_id: str,
    chart_type: str,
    chart_axis: dict,
    filters: dict,
    aggregations: list,
    database_name: str,
    table_name: str,
    error_message: str,
    logging_url: str,
    question: Union[str, None] = None,
    chart_title: Union[str, None] = None,
    instruction: Union[str, None] = None,
):
    normalized_chart_type = normalize_chart_type(chart_type)

    chart_axis_edited = chart_axis.copy()
    chart_axis_edited_keys = list(chart_axis_edited.keys())

    chart_axis_title_edited = chart_axis.copy()
    chart_axis_title_edited_keys = list(chart_axis_title_edited.keys())

    AXIS_KEY_LIST = []

    for chart_axis_edited_key in chart_axis_edited_keys:
        if "title" in str(chart_axis_edited_key).lower():
            del chart_axis_edited[chart_axis_edited_key]
        elif "aggregation" in str(chart_axis_edited_key).lower():
            if chart_axis_edited[chart_axis_edited_key] == "MEDIAN":
                chart_axis_edited[chart_axis_edited_key] = ""
            elif chart_axis_edited[chart_axis_edited_key] == "MEAN":
                chart_axis_edited[chart_axis_edited_key] = "AVG"
        elif (
            chart_axis_edited[chart_axis_edited_key] == ""
            or chart_axis_edited[chart_axis_edited_key] == []
        ):
            del chart_axis_edited[chart_axis_edited_key]

    for chart_axis_title_edited_key in chart_axis_title_edited_keys:
        if "column" in str(chart_axis_title_edited_key).lower():
            del chart_axis_title_edited[chart_axis_title_edited_key]
        elif "aggregation" in str(chart_axis_title_edited_key).lower():
            if chart_axis_title_edited[chart_axis_title_edited_key] == "MEDIAN":
                chart_axis_title_edited[chart_axis_title_edited_key] = ""
            elif chart_axis_title_edited[chart_axis_title_edited_key] == "MEAN":
                chart_axis_title_edited[chart_axis_title_edited_key] = "AVG"
        elif (
            chart_axis_title_edited[chart_axis_title_edited_key] == ""
            or chart_axis_title_edited[chart_axis_title_edited_key] == []
        ):
            del chart_axis_title_edited[chart_axis_title_edited_key]
        elif isinstance(
            chart_axis_title_edited_key.replace("_title", "").replace(
                "_column",
                "",
            ),
            str,
        ):
            AXIS_KEY_LIST.append(
                chart_axis_title_edited_key.replace("_title", "").replace(
                    "_column",
                    "",
                ),
            )
        else:
            AXIS_KEY_LIST.extend(
                chart_axis_title_edited_key.replace("_title", "").replace(
                    "_column",
                    "",
                ),
            )

    AXIS_KEY_LIST = list(set(AXIS_KEY_LIST))

    if filters == {}:
        FILTER_INSTRUCTIONS = ""
    else:
        FILTER_COLUMNS = []

        for filter_key in filters:
            if filters[filter_key] == [] or filters[filter_key] == [""]:
                pass
            else:
                FILTER_COLUMNS.append(filter_key)

        if FILTER_COLUMNS == []:
            FILTER_INSTRUCTIONS = ""
        else:
            FILTER_INSTRUCTIONS = "Filter the data in the generated SQL query.\n"

            for filter_column in FILTER_COLUMNS:
                FILTER_INSTRUCTIONS += f"'{filter_column}' = {filters[filter_column]}\n"

    if aggregations == []:
        AGGREGATION_INSTRUCTIONS = ""
    else:
        AGGREGATION_INSTRUCTIONS = f"Group or aggregate the data by at least the following columns: {', '.join(aggregations)} in the generated SQL query.\n"

    if chart_type in ["bar_chart", "column_chart", "pyramidfunnel_chart", "pie_chart"]:
        AXIS_INSTRUCTIONS = "SELECT given xAxis column and RENAME it into 'xAxis'. SELECT given yAxis column and RENAME it into 'yAxis'. NEVER SPLIT the yAxis column into several columns."
    elif chart_type in ["histogram_chart"]:
        AXIS_INSTRUCTIONS = "SELECT given xAxis column and RENAME it into 'xAxis'. ENSURE ONLY ONE column selected named 'xAxis' in the generated sql query. The generated SQL query MUST ONLY SELECT ONE COLUMN with NUMERICAL data type for the 'xAxis'. NEVER SELECT ANY COLUMN with STRING / TEXT / DATE data type in the generated SQL query."
    elif chart_type in [
        "area_chart",
        "line_chart",
        "spline_chart",
        "grouped_column_chart",
        "grouped_bar_chart",
        "radar_chart",
        "scatterplot_chart",
        "TreemapMulti_chart",
    ]:
        AXIS_INSTRUCTIONS = "SELECT given xAxis column and RENAME it into 'xAxis'. SELECT given yAxis column and RENAME it into 'yAxis'."

        if (
            "yAxis2_column" in chart_axis
            and chart_axis["yAxis2_column"] != ""
            and chart_axis["yAxis2_column"] != []
        ):
            AXIS_INSTRUCTIONS += (
                " SELECT given yAxis2 column and RENAME it into 'yAxis2'."
            )
        if (
            "yAxis3_column" in chart_axis
            and chart_axis["yAxis3_column"] != ""
            and chart_axis["yAxis3_column"] != []
        ):
            AXIS_INSTRUCTIONS += (
                " SELECT given yAxis3 column and RENAME it into 'yAxis3'."
            )
        if (
            "series_column" in chart_axis
            and chart_axis["series_column"] != ""
            and chart_axis["series_column"] != []
        ):
            AXIS_INSTRUCTIONS += (
                " SELECT given series column and RENAME it into 'series'."
            )
    elif chart_type in ["barlinecombo_chart"]:
        AXIS_INSTRUCTIONS = "SELECT given xAxis column and RENAME it into 'xAxis'. SELECT given yAxisBar column and RENAME it into 'yAxisBar'. ENSURE ALSO SELECT given yAxisLine column and RENAME it into 'yAxisLine'."
    elif chart_type in ["table_chart"]:
        AXIS_INSTRUCTIONS = "SELECT columns related to the question from the database SQL schema given. NEVER RENAME every selected columns."
    else:
        raise RuntimeError(
            f"'{chart_type}' Chart Type is not supported in SQL Query Generator!",
        )

    if (
        "postgresql" in data_summary.sql_library.lower()
        or "oracle" in data_summary.sql_library.lower()
    ):
        TABLE_INSTRUCTION = (
            f"""USE {table_name.replace('"', '')} as the source table."""
        )
        BACKTICK_INSTRUCTION = """ENSURE TO ALWAYS ENCLOSE column names and column aliases in double quotes in the generated SQL query."""
    else:
        TABLE_INSTRUCTION = f"""USE {database_name}.{table_name} as the source table."""
        BACKTICK_INSTRUCTION = "ENSURE TO ALWAYS REMOVE backticks, quotes, and double quotes from table name in the sql query."

    # DATE_INSTRUCTION -- general instructions
    # DATE_INSTRUCTION2 -- Instructions for Date Selection in SELECT statement
    # DATE_INSTRUCTION2 -- Instructions for Date Selection for filtering
    # DATE_INSTRUCTION -- general instructions
    # DATE_INSTRUCTION2 -- Instructions for Date Selection in SELECT statement
    # DATE_INSTRUCTION2 -- Instructions for Date Selection for filtering
    if (
        "mysql" in data_summary.sql_library.lower()
        or "mariadb" in data_summary.sql_library.lower()
    ):
        NATIVE_LANG = native.NATIVE_FUNC_MYSQL_MARIA
        if (
            isinstance(chart_axis["xAxis_column"], str)
            and chart_axis["xAxis_column"] in data_summary.column_data_tribes.keys()
            and data_summary.column_data_tribes[chart_axis["xAxis_column"]]
            in ["date_related"]
        ):
            if (
                isinstance(chart_axis["xAxis_column"], str)
                and chart_axis["xAxis_column"]
                in data_summary.column_sql_data_types.keys()
                and data_summary.column_sql_data_types[chart_axis["xAxis_column"]]
                in ["text"]
            ):
                DATE_INSTRUCTION = """Ensure to convert any date related columns with TEXT / STRING data types to DATE data types. This conversion should be applied in all parts of the SQL query, including the 'WHERE' clause, subqueries, 'CONCAT' function, and any other functions, methods, clauses, or statements, using the 'STR_TO_DATE' function."""
            else:
                DATE_INSTRUCTION = """"""

            DATE_INSTRUCTION += """ Ensuring the correct syntax for date conversion and formatting in all parts of the SQL query is essential to avoid errors and achieve accurate results. When calculating a date interval and formatting it as a string, use the following approach: DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL time_period), '%Y-%m-%d'). ENSURE the sql query follows the given time frame in the question and chart title, or the default time frame which is "past 1 year" if time frame not exist."""

            if (
                (
                    chart_title is not None
                    and fuzz.partial_ratio(chart_title.lower(), "yearly") > 80
                )
                or (
                    question is not None
                    and fuzz.partial_ratio(question.lower(), "yearly") > 80
                )
                or (
                    instruction is not None
                    and fuzz.partial_ratio(instruction.lower(), "yearly") > 80
                )
            ):
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                    and data_summary.column_sql_data_types[chart_axis["xAxis_column"]]
                    in ["text"]
                ):
                    DATE_INSTRUCTION2 = """Use the SQL query snippet "YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y'))" as a reference or sample of proper date selection."""
                else:
                    DATE_INSTRUCTION2 = """Use the SQL query snippet "YEAR(`Date`)" as a reference or sample of proper date selection."""

            elif (
                (
                    chart_title is not None
                    and fuzz.partial_ratio(chart_title.lower(), "quarterly") > 80
                )
                or (
                    question is not None
                    and fuzz.partial_ratio(question.lower(), "quarterly") > 80
                )
                or (
                    instruction is not None
                    and fuzz.partial_ratio(instruction.lower(), "quarterly") > 80
                )
            ):
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                    and data_summary.column_sql_data_types[chart_axis["xAxis_column"]]
                    in ["text"]
                ):
                    DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-Q', QUARTER(STR_TO_DATE(`Date`, '%d/%m/%Y')))" as a reference or sample of proper date selection."""
                else:
                    DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR(`Date`), '-Q', QUARTER(`Date`))" as a reference or sample of proper date selection."""

                DATE_INSTRUCTION2 += """ Never use 'YYYY-Qq', '%Y-Q%q' and '%Y-%q' for formatting quarter dates in your generated SQL queries. Instead, format the quarter dates by correctly combining the year and quarter using the `QUARTER` and `YEAR` functions within the `CONCAT` statement, without using any `SUBSTRING` function where the date column is formatted as 'YYYY-Q1', 'YYYY-Q2', 'YYYY-Q3', and 'YYYY-Q4'."""

            elif (
                (
                    chart_title is not None
                    and fuzz.partial_ratio(chart_title.lower(), "weekly") > 80
                )
                or (
                    question is not None
                    and fuzz.partial_ratio(question.lower(), "weekly") > 80
                )
                or (
                    instruction is not None
                    and fuzz.partial_ratio(instruction.lower(), "weekly") > 80
                )
            ):
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                    and data_summary.column_sql_data_types[chart_axis["xAxis_column"]]
                    in ["text"]
                ):
                    DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-W', WEEK(STR_TO_DATE(`Date`, '%d/%m/%Y')))" as a reference or sample of proper date selection."""
                else:
                    DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR(`Date`), '-W', WEEK(`Date`))" as a reference or sample of proper date selection."""

            elif (
                (
                    chart_title is not None
                    and fuzz.partial_ratio(chart_title.lower(), "daily") > 80
                )
                or (
                    question is not None
                    and fuzz.partial_ratio(question.lower(), "daily") > 80
                )
                or (
                    instruction is not None
                    and fuzz.partial_ratio(instruction.lower(), "daily") > 80
                )
            ):
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                    and data_summary.column_sql_data_types[chart_axis["xAxis_column"]]
                    in ["text"]
                ):
                    DATE_INSTRUCTION2 = """Use the SQL query snippet "DATE(STR_TO_DATE(`Date`, '%d/%m/%Y'))" as a reference or sample of proper date selection."""
                else:
                    DATE_INSTRUCTION2 = """Use the SQL query snippet "DATE(`Date`)" as a reference or sample of proper date selection."""

                DATE_INSTRUCTION2 += """ Avoid using day names in the SQL query."""

            elif (
                (
                    chart_title is not None
                    and fuzz.partial_ratio(chart_title.lower(), "half-yearly") > 80
                )
                or (
                    question is not None
                    and fuzz.partial_ratio(question.lower(), "half-yearly") > 80
                )
                or (
                    instruction is not None
                    and fuzz.partial_ratio(instruction.lower(), "half-yearly") > 80
                )
            ):
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                    and data_summary.column_sql_data_types[chart_axis["xAxis_column"]]
                    in ["text"]
                ):
                    DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-H', IF(MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y')) <= 6, 1, 2))" as a reference or sample of proper date selection."""
                else:
                    DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR(`Date`), '-H', IF(MONTH(`Date`) <= 6, 1, 2))" as a reference or sample of proper date selection."""

            elif (
                (
                    chart_title is not None
                    and fuzz.partial_ratio(chart_title.lower(), "monthly") > 80
                )
                or (
                    question is not None
                    and fuzz.partial_ratio(question.lower(), "monthly") > 80
                )
                or (
                    instruction is not None
                    and fuzz.partial_ratio(instruction.lower(), "monthly") > 80
                )
            ):
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                    and data_summary.column_sql_data_types[chart_axis["xAxis_column"]]
                    in ["text"]
                ):
                    DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-', MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y')))" as a reference or sample of proper date selection."""
                else:
                    DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR(`Date`), '-', MONTH(`Date`))" as a reference or sample of proper date selection."""

                DATE_INSTRUCTION2 += """ Avoid using month names in the SQL query."""
            else:
                DATE_INSTRUCTION2 = """"""
        else:
            DATE_INSTRUCTION = """When calculating a date interval for filtering and formatting it as a string, use the following approach: DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL time_period), '%Y-%m-%d'). ENSURE the sql query follows the given time frame in the question and chart title, or the default time frame which is "past 1 year" if time frame not exist."""
            DATE_INSTRUCTION2 = """"""

        if instruction is None:
            if question is None or chart_title is None:
                raise ValueError(
                    "Both 'question' and 'chart_title' must be provided if 'instruction' is None."
                )
            time_duration = classify_time_duration(question, chart_title)
        else:
            time_duration = classify_instruction_time_duration(instruction)

        if time_duration == "Week":
            DATE_INSTRUCTION3 = """If date filtering is required for weekly data, ensure to specify the date range using INTERVAL for weeks, and apply DATE_SUB, DATE_ADD, or WHERE BETWEEN functions appropriately. Use the SQL query snippet "WHERE date_column BETWEEN DATE_SUB(CURDATE(), INTERVAL N WEEK) AND CURDATE()" as a reference or sample of proper date selection."""
        elif time_duration == "Month":
            DATE_INSTRUCTION3 = """If date filtering is required for monthly data, ensure to specify the date range using INTERVAL for months, and apply DATE_SUB, DATE_ADD, or WHERE BETWEEN functions as needed. Use the SQL query snippet "WHERE date_column BETWEEN DATE_SUB(CURDATE(), INTERVAL N MONTH) AND CURDATE()" as a reference or sample of proper date selection."""
        elif time_duration == "Quarter":
            DATE_INSTRUCTION3 = """If date filtering is required for quarterly data, ensure to specify the date range using INTERVAL for quarters, and utilize DATE_SUB, DATE_ADD, or WHERE BETWEEN functions accordingly. Use the SQL query snippet "WHERE date_column BETWEEN DATE_SUB(CURDATE(), INTERVAL N QUARTER) AND CURDATE()" as a reference or sample of proper date selection."""
        elif time_duration == "Year":
            DATE_INSTRUCTION3 = """If date filtering is required for yearly data, ensure to specify the date range using INTERVAL for years, and use DATE_SUB, DATE_ADD, or WHERE BETWEEN functions as applicable. Use the SQL query snippet "WHERE date_column BETWEEN DATE_SUB(CURDATE(), INTERVAL N YEAR) AND CURDATE()" as a reference or sample of proper date selection."""
        else:
            DATE_INSTRUCTION3 = """"""

    elif "sqlserver" in data_summary.sql_library.lower():
        NATIVE_LANG = """"""
        DATE_INSTRUCTION = """Always check for any date related columns involved including its data type before generating the sql query. Ensure to convert any date related columns with TEXT or STRING data types to DATE data types. This conversion should be applied in all parts of the SQL query, including the 'WHERE' clause, subqueries, 'CONCAT' function, and any other functions, methods, clauses, or statements, using the 'STR_TO_DATE' function. Never use 'YYYY-Qq', '%Y-Q%q' and '%Y-%q' for formatting quarter dates in your generated SQL queries. Instead, format the quarter dates by correctly combining the year and quarter using the `QUARTER` and `YEAR` functions within the `CONCAT` statement, without using any `SUBSTRING` function where the x-axis is formatted as 'YYYY-Q1', 'YYYY-Q2', 'YYYY-Q3', and 'YYYY-Q4'. Ensuring the correct syntax for date conversion and formatting in all parts of the SQL query is essential to avoid errors and achieve accurate results."""

        DATE_INSTRUCTION2 = """Avoid using month names or day names in the SQL query."""

        DATE_INSTRUCTION3 = """If the x-axis is related to quarterly date and the x-axis column data type is 'DATE', use the SQL query snippet "CONCAT(YEAR([Date]), '-Q', DATEPART(QUARTER, [Date]))" as a reference or sample of proper x-axis selection. If the x-axis is related to quarterly date and the x-axis column data type is 'TEXT'/'STRING', use the SQL query snippet "CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, [Date], 103)))" as a reference or sample of proper x-axis selection.
If the x-axis is related to daily date and the x-axis column data type is 'DATE', use the SQL query snippet "[Date]" as a reference or sample of proper x-axis selection. If the x-axis is related to daily date and the x-axis column data type is 'TEXT'/'STRING', use the SQL query snippet CONVERT(DATE, [Date], 103)" as a reference or sample of proper x-axis selection.
If the x-axis is related to weekly date and the x-axis column data type is 'DATE', use the SQL query snippet "YEAR([Date]), DATEPART(WEEK, [Date])" as a reference or sample of proper x-axis selection. If the x-axis is related to weekly date and the x-axis column data type is 'TEXT'/'STRING', use the SQL query snippet "CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-W', DATEPART(WEEK, CONVERT(DATE, [Date], 103)))" as a reference or sample of proper x-axis selection.
If the x-axis is related to monthly date and the x-axis column data type is 'DATE', use the SQL query snippet "CONCAT(YEAR([Date]), '-', MONTH([Date]))" as a reference or sample of proper x-axis selection. If the x-axis is related to monthly date and the x-axis column data type is 'TEXT'/'STRING', use the SQL query snippet "CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-', MONTH(CONVERT(DATE, [Date], 103)))" as a reference or sample of proper x-axis selection.
If the x-axis is related to yearly date and the x-axis column data type is 'DATE', use the SQL query snippet "YEAR([Date])" as a reference or sample of proper x-axis selection. If the x-axis is related to yearly date and the x-axis column data type is 'TEXT'/'STRING', use the SQL query snippet "YEAR(CONVERT(DATE, [Date], 103))" as a reference or sample of proper x-axis selection.
If the x-axis is related to half-yearly date and the x-axis column data type is 'DATE', use the SQL query snippet "CONCAT(YEAR([Date]), '-H', CASE WHEN MONTH([Date]) <= 6 THEN 1 ELSE 2 END)" as a reference or sample of proper x-axis selection. If the x-axis is related to half-yearly date and the x-axis column data type is 'TEXT'/'STRING', use the SQL query snippet "CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-H', CASE WHEN MONTH(CONVERT(DATE, [Date], 103)) <= 6 THEN 1 ELSE 2 END)" as a reference or sample of proper x-axis selection.
IF the x-axis is related to date, ENSURE the x-axis in the sql query follows the given time frame in the question and chart title, or the default time frame if time frame not exist.
If the x-axis is NOT related to date (e.g., 'Product', 'Region', 'User Type', etc.) or the x-axis is NOT related to quarterly date, AVOID USING any of the SQL snippet references above."""
    elif "postgresql" in data_summary.sql_library.lower():
        NATIVE_LANG = native.NATIVE_FUNC_POSTGRESQL
        if (
            isinstance(chart_axis["xAxis_column"], str)
            and chart_axis["xAxis_column"] in data_summary.column_data_tribes.keys()
            and data_summary.column_data_tribes[chart_axis["xAxis_column"]]
            in ["date_related"]
        ):
            if (
                isinstance(chart_axis["xAxis_column"], str)
                and chart_axis["xAxis_column"]
                in data_summary.column_sql_data_types.keys()
                and data_summary.column_sql_data_types[chart_axis["xAxis_column"]]
                in ["text"]
            ):
                DATE_INSTRUCTION = """Ensure to convert any date related columns with TEXT / STRING data types to DATE data types and implemented consistently throughout the SQL query. This conversion should be applied in all parts of the SQL query, including the 'WHERE' clause, subqueries, 'CONCAT' function, and any other functions, methods, clauses, or statements, using the 'TO_DATE' function. Ensure that all date-related operations are compatible and correctly implemented when using different date-related functions (e.g., DATE_TRUNC, EXTRACT) in conjunction with TO_DATE."""
            else:
                DATE_INSTRUCTION = """"""

            DATE_INSTRUCTION += """ Ensuring the correct syntax for date conversion and formatting in all parts of the SQL query is essential to avoid errors and achieve accurate results. When calculating date intervals and formatting them as strings, particularly when subtracting a specified time period from the current date, adhere rigorously to this format: TO_CHAR(CURRENT_DATE - INTERVAL 'time period', 'YYYY-MM-DD'). This approach guarantees reliable date calculations and mitigates any potential inaccuracies in your query outcomes. ENSURE the sql query follows the given time frame in the question and chart title, or the default time frame which is "past 1 year" if time frame not exist."""

            if (
                (
                    chart_title is not None
                    and fuzz.partial_ratio(chart_title.lower(), "yearly") > 80
                )
                or (
                    question is not None
                    and fuzz.partial_ratio(question.lower(), "yearly") > 80
                )
                or (
                    instruction is not None
                    and fuzz.partial_ratio(instruction.lower(), "yearly") > 80
                )
            ):
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                    and data_summary.column_sql_data_types[chart_axis["xAxis_column"]]
                    in ["text"]
                ):
                    DATE_INSTRUCTION2 = """Use the SQL query snippet `EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY'))` as a reference or sample of proper date selection."""
                else:
                    DATE_INSTRUCTION2 = """Use the SQL query snippet `EXTRACT(YEAR FROM "Date")` as a reference or sample of proper date selection."""
            elif (
                (
                    chart_title is not None
                    and fuzz.partial_ratio(chart_title.lower(), "quarterly") > 80
                )
                or (
                    question is not None
                    and fuzz.partial_ratio(question.lower(), "quarterly") > 80
                )
                or (
                    instruction is not None
                    and fuzz.partial_ratio(instruction.lower(), "quarterly") > 80
                )
            ):
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                    and data_summary.column_sql_data_types[chart_axis["xAxis_column"]]
                    in ["text"]
                ):
                    DATE_INSTRUCTION2 = """Use the SQL query snippet `CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-Q', EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY')))` as a reference or sample of proper date selection."""
                else:
                    DATE_INSTRUCTION2 = """Use the SQL query snippet `CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date"))` as a reference or sample of proper date selection."""

                DATE_INSTRUCTION2 += """ Format the quarter dates by correctly combining the year and quarter using the `QUARTER` and `YEAR` functions within the `CONCAT` statement, without using any `SUBSTRING` function where the x-axis is formatted as 'YYYY-Q1', 'YYYY-Q2', 'YYYY-Q3', and 'YYYY-Q4'. Use 'EXTRACT' for extracting specific parts of the date. """

            elif (
                (
                    chart_title is not None
                    and fuzz.partial_ratio(chart_title.lower(), "weekly") > 80
                )
                or (
                    question is not None
                    and fuzz.partial_ratio(question.lower(), "weekly") > 80
                )
                or (
                    instruction is not None
                    and fuzz.partial_ratio(instruction.lower(), "weekly") > 80
                )
            ):
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                    and data_summary.column_sql_data_types[chart_axis["xAxis_column"]]
                    in ["text"]
                ):
                    DATE_INSTRUCTION2 = """Use the SQL query snippet `CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY')))` as a reference or sample of proper date selection."""
                else:
                    DATE_INSTRUCTION2 = """Use the SQL query snippet `CONCAT(EXTRACT(YEAR FROM "Date"), '-W', EXTRACT(WEEK FROM "Date"))` as a reference or sample of proper date selection."""

            elif (
                (
                    chart_title is not None
                    and fuzz.partial_ratio(chart_title.lower(), "daily") > 80
                )
                or (
                    question is not None
                    and fuzz.partial_ratio(question.lower(), "daily") > 80
                )
                or (
                    instruction is not None
                    and fuzz.partial_ratio(instruction.lower(), "daily") > 80
                )
            ):
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                    and data_summary.column_sql_data_types[chart_axis["xAxis_column"]]
                    in ["text"]
                ):
                    DATE_INSTRUCTION2 = """Use the SQL query snippet "TO_DATE("Date", 'DD/MM/YYYY')" as a reference or sample of proper date selection."""
                else:
                    DATE_INSTRUCTION2 = """Use the SQL query snippet "Date" as a reference or sample of proper date selection."""

                DATE_INSTRUCTION2 += """ Avoid using day names in the SQL query."""

            elif (
                (
                    chart_title is not None
                    and fuzz.partial_ratio(chart_title.lower(), "half-yearly") > 80
                )
                or (
                    question is not None
                    and fuzz.partial_ratio(question.lower(), "half-yearly") > 80
                )
                or (
                    instruction is not None
                    and fuzz.partial_ratio(instruction.lower(), "half-yearly") > 80
                )
            ):
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                    and data_summary.column_sql_data_types[chart_axis["xAxis_column"]]
                    in ["text"]
                ):
                    DATE_INSTRUCTION2 = """Use the SQL query snippet `CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-H', CASE WHEN EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) <= 6 THEN 1 ELSE 2 END)` as a reference or sample of proper date selection."""
                else:
                    DATE_INSTRUCTION2 = """Use the SQL query snippet `CONCAT(EXTRACT(YEAR FROM "Date"), '-H', CASE WHEN EXTRACT(MONTH FROM "Date") <= 6 THEN 1 ELSE 2 END)` as a reference or sample of proper date selection."""

            elif (
                (
                    chart_title is not None
                    and fuzz.partial_ratio(chart_title.lower(), "monthly") > 80
                )
                or (
                    question is not None
                    and fuzz.partial_ratio(question.lower(), "monthly") > 80
                )
                or (
                    instruction is not None
                    and fuzz.partial_ratio(instruction.lower(), "monthly") > 80
                )
            ):
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                    and data_summary.column_sql_data_types[chart_axis["xAxis_column"]]
                    in ["text"]
                ):
                    DATE_INSTRUCTION2 = """Use the SQL query snippet `CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-', EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')))` as a reference or sample of proper date selection."""
                else:
                    DATE_INSTRUCTION2 = """Use the SQL query snippet `CONCAT(EXTRACT(YEAR FROM "Date"), '-', EXTRACT(MONTH FROM "Date"))` as a reference or sample of proper date selection."""

                DATE_INSTRUCTION2 += """ Avoid using month names in the SQL query."""
            else:
                DATE_INSTRUCTION2 = """"""
        else:
            DATE_INSTRUCTION = """When calculating a date interval for filtering and formatting it as a string, use the following approach: TO_CHAR(CURRENT_DATE - INTERVAL 'time_period', 'YYYY-MM-DD'). ENSURE the SQL query follows the given time frame in the question and chart title, or the default time frame, which is "past 1 year" if the time frame does not exist."""
            DATE_INSTRUCTION2 = """"""

        if instruction is None:
            if question is None or chart_title is None:
                raise ValueError(
                    "Both 'question' and 'chart_title' must be provided if 'instruction' is None."
                )
            time_duration = classify_time_duration(question, chart_title)
        else:
            time_duration = classify_instruction_time_duration(instruction)

        if time_duration == "Week":
            DATE_INSTRUCTION3 = """If date filtering is required for weekly data, ensure to specify the date range using INTERVAL for weeks, and apply DATE_TRUNC or WHERE BETWEEN functions appropriately. Use the SQL query snippet "WHERE \"Date\" BETWEEN DATE_TRUNC('week', CURRENT_DATE - INTERVAL 'N week') AND DATE_TRUNC('week', CURRENT_DATE)" as a reference or sample of proper date selection."""
        elif time_duration == "Month":
            DATE_INSTRUCTION3 = """If date filtering is required for monthly data, ensure to specify the date range using INTERVAL for months, and apply DATE_TRUNC or WHERE BETWEEN functions as needed. Use the SQL query snippet "WHERE \"Date\" BETWEEN DATE_TRUNC('month', CURRENT_DATE - INTERVAL 'N month') AND DATE_TRUNC('month', CURRENT_DATE)" as a reference or sample of proper date selection."""
        elif time_duration == "Quarter":
            DATE_INSTRUCTION3 = """If date filtering is required for quarterly data, ensure to specify the date range using INTERVAL for quarters, and utilize DATE_TRUNC or WHERE BETWEEN functions accordingly. Use the SQL query snippet "WHERE \"Date\" BETWEEN DATE_TRUNC('quarter', CURRENT_DATE - INTERVAL 'N quarter') AND DATE_TRUNC('quarter', CURRENT_DATE)" as a reference or sample of proper date selection."""
        elif time_duration == "Year":
            DATE_INSTRUCTION3 = """If date filtering is required for yearly data, ensure to specify the date range using INTERVAL for years, and use DATE_TRUNC or WHERE BETWEEN functions as applicable. Use the SQL query snippet "WHERE \"Date\" BETWEEN DATE_TRUNC('year', CURRENT_DATE - INTERVAL 'N year') AND DATE_TRUNC('year', CURRENT_DATE)" as a reference or sample of proper date selection."""
        else:
            DATE_INSTRUCTION3 = """"""

    elif "oracle" in data_summary.sql_library.lower():
        NATIVE_LANG = """"""
        DATE_INSTRUCTION = """Always check for any date related columns involved including its data type before generating the sql query. Ensure to convert any date related columns with TEXT / STRING data types to DATE data types. This conversion should be applied in all parts of the SQL query, including the 'WHERE' clause, subqueries, 'CONCAT' function, and any other functions, methods, clauses, or statements, using the 'STR_TO_DATE' function. Format the quarter dates by correctly combining the year and quarter using the `QUARTER` and `YEAR` functions within the `CONCAT` statement, without using any `SUBSTRING` function where the x-axis is formatted as 'YYYY-Q1', 'YYYY-Q2', 'YYYY-Q3', and 'YYYY-Q4'. Ensuring the correct syntax for date conversion and formatting in all parts of the SQL query is essential to avoid errors and achieve accurate results."""
        DATE_INSTRUCTION2 = """Avoid using month names or day names in the SQL query."""
        DATE_INSTRUCTION3 = """If the x-axis is related to quarterly date and the x-axis column data type is 'DATE', use the SQL query snippet `CONCAT(TO_CHAR("Date", 'YYYY'), '-Q', TO_CHAR("Date", 'Q'))` as a reference or sample of proper x-axis selection. If the x-axis is related to quarterly date and the x-axis column data type is 'TEXT'/'STRING', use the SQL query snippet `CONCAT(TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY'), '-Q', TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'Q'))` as a reference or sample of proper x-axis selection.
If the x-axis is related to daily date and the x-axis column data type is 'DATE', use the SQL query snippet `TO_DATE("Date", 'YYYY-MM-DD')` as a reference or sample of proper x-axis selection. If the x-axis is related to daily date and the x-axis column data type is 'TEXT'/'STRING', use the SQL query snippet `TO_DATE("Date", 'DD/MM/YYYY')` as a reference or sample of proper x-axis selection.
If the x-axis is related to weekly date and the x-axis column data type is 'DATE', use the SQL query snippet `TO_CHAR("Date", 'IYYY-IW')` as a reference or sample of proper x-axis selection. If the x-axis is related to weekly date and the x-axis column data type is 'TEXT'/'STRING', use the SQL query snippet `TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'IYYY-IW')` as a reference or sample of proper x-axis selection.
If the x-axis is related to monthly date and the x-axis column data type is 'DATE', use the SQL query snippet `TO_CHAR("Date", 'YYYY-MM')` as a reference or sample of proper x-axis selection. If the x-axis is related to monthly date and the x-axis column data type is 'TEXT'/'STRING', use the SQL query snippet `TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM')` as a reference or sample of proper x-axis selection.
If the x-axis is related to yearly date and the x-axis column data type is 'DATE', use the SQL query snippet TO_CHAR("Date", 'YYYY') as a reference or sample of proper x-axis selection. If the x-axis is related to yearly date and the x-axis column data type is 'TEXT'/'STRING', use the SQL query snippet `TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY')` as a reference or sample of proper x-axis selection.
If the x-axis is related to half-yearly date and the x-axis column data type is 'DATE', use the SQL query snippet `TO_CHAR("Date", 'YYYY-"H"') || CASE WHEN TO_NUMBER(TO_CHAR("Date", 'MM')) <= 6 THEN '1' ELSE '2'` END as a reference or sample of proper x-axis selection. If the x-axis is related to half-yearly date and the x-axis column data type is 'TEXT'/'STRING', use the SQL query snippet `TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-"H"') || CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'MM')) <= 6 THEN '1' ELSE '2' END` as a reference or sample of proper x-axis selection.
IF the x-axis is related to date, ENSURE the x-axis in the sql query follows the given time frame in the question and chart title, or the default time frame if time frame not exist.
If the x-axis is NOT related to date (e.g., 'Product', 'Region', 'User Type', etc.) or the x-axis is NOT related to quarterly date, AVOID USING any of the SQL snippet references above."""
    else:
        raise RuntimeError(
            f"{data_summary.sql_library} DB is not supported in SQL query generator!",
        )

    if "mysql" in data_summary.sql_library.lower():
        MEDIAN_INSTRUCTION = "AVOID using 'MEDIAN' function or 'PERCENTILE_CONT' function on your generated SQL query. Instead, use 'AVG' and sub query to calculate the median value."
    elif (
        "mariadb" in data_summary.sql_library.lower()
        or "sqlserver" in data_summary.sql_library.lower()
        or "postgresql" in data_summary.sql_library.lower()
        or "oracle" in data_summary.sql_library.lower()
    ):
        MEDIAN_INSTRUCTION = "AVOID using 'MEDIAN' function or 'PERCENTILE_CONT' function on your generated SQL query. Instead, use 'PERCENTILE_DISC' to calculate the median value."
    else:
        raise RuntimeError(
            f"{data_summary.sql_library} DB is not supported in SQL query generator!",
        )

    GROUPBY_INSTRUCTION = """MUST INCLUDE all non-aggregated columns from the SELECT clause in the GROUP BY clause to comply 'only_full_group_by' mode!"""

    if "oracle" in data_summary.sql_library.lower():
        column_sql_data_type = data_summary.column_sql_data_types.copy()

        for column_sql_data_type_key in list(column_sql_data_type.keys()):
            if column_sql_data_type[column_sql_data_type_key].upper() != "CLOB":
                del column_sql_data_type[column_sql_data_type_key]

        DATATYPE_INSTRUCTION = f"""- Use the query snippet that uses 'DBMS_LOB.SUBSTR("KEY", 4000, 1)' as a reference, and replace "KEY" in the query snippet with the actual column name for {list(column_sql_data_type.keys())} columns."""
    else:
        DATATYPE_INSTRUCTION = """"""

    system_prompt = f"""You are a skilled SQL query assistant specializing in {data_summary.sql_library} SQL queries. Your task is to fix a given {data_summary.sql_library} SQL query which intended to answer the given question visually using specified data visualizations, particularly a {normalized_chart_type}. Your query must adhere to industry standards, avoid common pitfalls, and comply with the provided instructions.

Instructions:
- Your SQL query must be error-free.
- GENERATE only the SQL query and NEVER INCLUDE explanations before or after the SQL query.
- NEVER INCLUDE '```sql' in the generated SQL query.
- ALWAYS CONSIDER column data types before adding any operations.
- ENSURE TO APPLY the required transformations or aggregation operators (such as 'SUM', 'COUNT', 'MEDIAN', 'AVG', 'MAX', MIN, etc) especially for all yAxis columns according to the question.
- ENSURE TO USE correct operators and data encoding, and apply the correct WHERE conditions.
- AVOID 'KeyError' and ENSURE the SQL result includes data for every column.
- GROUP BY all non-aggregated columns from the SELECT clause.
- Ensure the 'group by' clauses are fully specified.
- NEVER USE 'FOR' operator in the SQL query.
- NEVER USE 'CASE' function if not required for the question.
- FOLLOW the time frame in the 'xAxis_title' or time frame in the chart title if 'xAxis_column' is related to date.
- AVOID unnecessary clauses like 'HAVING' when grouping has already been performed.
- ENSURE NO DUPLICATE selected column name or alias.
- {DATE_INSTRUCTION}
- AVOID ANY UNNECESSARY FILTER that doesn't fit the user's intent.
- USE 'CASE' operator instead of 'FILTER' operator.
- ONLY use selected column(s) in GROUP BY clause.
- NEVER ADD OR CONCAT ANY SYMBOLS such as '%' and '$' with any numerical columns.
- Optimize the SQL query by utilizing subqueries instead of 'PARTITION BY' clause where applicable.
- {GROUPBY_INSTRUCTION}
- ENSURE to use aggregation on numerical columns when using GROUP BY clause.
- ENSURE NOT to use y-axis in GROUP BY clause.
- ENSURE the SQL query is COMPLETE and NEVER ENDS abruptly.
- ENSURE to RENAME all selected columns to the appropriate axis name given.
- ENSURE to END the generated SQL query with a semicolon.
- ENSURE all columns in Chart Column Used given are used in the generated SQL query.
- {DATE_INSTRUCTION2}
- IF a time frame exists in the question, ALWAYS REFER to the question's time frame when specifying the time frame in the SQL query.
- STRICTLY REFRAIN from generating columns for specific series only.
- USE numeric representations for dates to maintain consistency.
- STRICTLY AVOID concatenating any symbol with the numerical columns (e.g., `CONCAT(ROUND(SUM(CostVariance_Actual_vs_Budget) / SUM(SUM(CostVariance_Actual_vs_Budget)) OVER () * 100, 1), '%')`).
- ENSURE all column aliases are clear, correct, and consistently assigned throughout the SQL query.
- ENSURE to convert any date related columns with TEXT / STRING data types to DATE data types in every part of your generated SQL query.
- STRICTLY AVOID selecting columns other than those provided in the Database SQL Schema.
- STRICTLY AVOID using column aliases in 'groupby' and 'orderby' clauses.
- ENSURE to have the same data type between the column and the filter value.
- Avoid using 'LIMIT' unless the title or question pertains to 'top', 'lowest', 'highest', or similar topics.
- ENSURE y-axis related columns (e.g., 'yAxisBar', 'yAxis', 'yAxis2', 'yAxis3', 'yAxisLine', etc.) are numerical columns.
- ENSURE to follow the time duration and time frame if exist in the chart title or question.
- ENSURE that the date formats are consistently applied across all parts of the set operators (UNION, INTERSECT, MINUS, etc.) query and apply consistent date filters across both parts of the set operators (UNION, INTERSECT, MINUS, etc.) query if used.
- If the question and chart title indicates a time duration such as "past 12 months," ensure that the data range is from the current date minus 1 year. If the question and chart title specifies "past year" or "last year," use data exclusively from the previous calendar year. Similarly, if the title specifies "next year" or "upcoming year," use data exclusively for the next calendar year.
- {AXIS_INSTRUCTIONS}
- {TABLE_INSTRUCTION}
- {BACKTICK_INSTRUCTION}
- {MEDIAN_INSTRUCTION}
{DATATYPE_INSTRUCTION}

For more context, you are provided a database SQL schema, database table description, and database column description to support the sql query fix.

Database SQL Schema:
{data_summary.database_schema_sql}

Database Table Description:
{data_summary.table_description}

{generate_column_information_prompt(data_summary.column_description_dict,data_summary.column_sample_dict,data_summary.column_display_name_dict,data_summary.column_n_unique_value_dict,data_summary.column_data_tribes)}

{FILTER_INSTRUCTIONS}

{AGGREGATION_INSTRUCTIONS}

{DATE_INSTRUCTION3}

Your complete adherence to each instruction is non-negotiable and critical to the success of the task. No instruction can be missed, and every aspect of the SQL query must align precisely with all the instructions provided. Please review each instruction carefully and ensure full compliance before finalizing your SQL query. NEVER INCLUDE explanations or notes.
Axis instructions: {AXIS_INSTRUCTIONS}

ENSURE that all column aliases in the fixed SQL query generated EXCLUSIVELY utilize the names from the Axis Key List below.

Axis Key List: {AXIS_KEY_LIST}

DO NOT INCLUDE ANY additional columns aliases in the fixed SQL query generated that are NOT PART of the Axis Key List. This is ABSOLUTELY CRITICAL for the query's correctness!

FUNCTIONS AND OPERATOR REFERENCE
---
{NATIVE_LANG}

"""
    if question is not None and chart_title is not None:
        user_prompt = f"""Generate the fixed {data_summary.sql_library} sql query based on the sql query, error message, question, required chart column used, and chart title below.

    SQL query: {sql_query}

    Error Message: {error_message}

    Question: {question}

    Required Chart Column Used: {chart_axis_edited}

    Chart Title: {chart_title}

    """
    elif instruction is not None:
        user_prompt = f"""Generate the fixed {data_summary.sql_library} sql query based on the sql query, error message, instruction and required chart column used below.

    SQL query: {sql_query}

    Error Message: {error_message}

    Instruction: {question}

    Required Chart Column Used: {chart_axis_edited}

    """

    start_narrative = perf_counter()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response = (
        llama70b_client.chat.completions.create(
            messages=messages,
            model=os.getenv("LLAMA70B_MODEL"),
            max_tokens=1000,
            temperature=0.0,
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

    chart_sql_inference_time = perf_counter() - start_narrative

    MODULEID_FIX_SQL_QUERY = os.getenv("MODULEID_FIX_SQL_QUERY", "")

    if MODULEID_FIX_SQL_QUERY == "":
        raise ValueError("MODULEID_FIX_SQL_QUERY is invalid!")

    formatted_data = {
        "chart_id": chart_id,
        "module_id": int(MODULEID_FIX_SQL_QUERY),
        "messages": messages,
        "output": response,
        "inference_time": chart_sql_inference_time,
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

    log_chart_data = {
        "chart_id": chart_id,
        "sql_query": response,
    }

    logging_url_chart = logging_url + "chart"
    requests.post(logging_url_chart, json=log_chart_data, verify=False)

    if ";" in response:
        sql_string = response.split(";")[0] + ";"
    else:
        sql_string = response

    sql_string = sql_string.replace(r"\_", "_")
    sql_string = sql_string.replace("\n", " ")
    sql_string = sql_string.replace("\\", " ")
    sql_string = sql_string.replace("\t", " ")
    sql_string = sql_string.replace("%%", "%")
    sql_string = sql_string.replace(
        f"`{database_name}.{table_name}`",
        f"{database_name}.{table_name}",
    )
    sql_string = sql_string.replace(
        f"`{database_name}`.`{table_name}`",
        f"{database_name}.{table_name}",
    )
    sql_string = sql_string.replace("%Y-%b", "%Y-%m")
    sql_string = sql_string.replace("%Y-%B", "%Y-%m")
    sql_string = sql_string.replace("```sql", "")
    sql_string = sql_string.replace("```", "")
    sql_string = sql_string.replace("yAxis1", "yAxis")
    sql_string = sql_string.strip()

    if "%Y-Q%q" in sql_string or "%Y-%q" in sql_string:
        print("SQL query generator response:")
        print(sql_string)
        raise RuntimeError("SQL query generated contains '%Y-Q%q' or '%Y-%q'!")

    if "MM-MM" in sql_string:
        sql_string = sql_string.replace("MM-MM", "MM")

    if (
        "CONCAT_WS ('-', SUBSTRING(" in sql_string
        or "CONCAT_WS('-', SUBSTRING(" in sql_string
    ):
        print("SQL query generator response:")
        print(sql_string)
        raise RuntimeError("SQL query generated contains 'CONCAT_WS ('-', SUBSTRING('!")

    for sql_function_datename in ["monthname", "dayname"]:
        if sql_function_datename in sql_string.lower():
            raise RuntimeError("SQL query generated contains 'monthname'!")

    if data_summary.sql_library.lower() in ["mysql", "mariadb"]:
        sql_string = sql_string.replace(
            f" {table_name} ",
            f" {database_name}.{table_name} ",
        )

    if data_summary.sql_library.lower() in ["postgresql"]:
        # Add double quotes to column `names`
        columns = data_summary.column_name_list.copy()
        for column in columns:
            if column != "":
                pattern = rf'(?<!")\b{column}\b(?!")'
                sql_string = re.sub(pattern, f'"{column}"', sql_string)

        # Add double quotes to column aliases
        aliases = AXIS_KEY_LIST
        for alias in aliases:
            pattern = rf'(?<!")\b{alias}\b(?!")'
            sql_string = re.sub(pattern, f'"{alias}"', sql_string)

        sql_string = sql_string.replace("YYYY-QQ", "YYYY-Q")
        sql_string = sql_string.replace("YYYY-IQ", "YYYY-WW")

    if data_summary.sql_library.lower() in ["oracle"]:
        sql_string = sql_string.replace(";", "")

    sql_string_raw = sql_string

    if data_summary.table_join_sql_query != "":
        table_join_sql_query = data_summary.table_join_sql_query.strip().rstrip(";")
        sql_string = sql_string.replace(
            f"`{database_name}`.`{table_name}`",
            f"({table_join_sql_query}) AS joined_table",
        )
        sql_string = sql_string.replace(
            f"'{database_name}'.'{table_name}'",
            f"({table_join_sql_query}) AS joined_table",
        )
        sql_string = sql_string.replace(
            f'"{database_name}"."{table_name}"',
            f"({table_join_sql_query}) AS joined_table",
        )
        sql_string = sql_string.replace(
            f"{database_name}.{table_name}",
            f"({table_join_sql_query}) AS joined_table",
        )
        sql_string = sql_string.replace(
            f"`{table_name}`",
            f"({table_join_sql_query}) AS joined_table",
        )
        sql_string = sql_string.replace(
            f"'{table_name}'",
            f"({table_join_sql_query}) AS joined_table",
        )
        sql_string = sql_string.replace(
            f'"{table_name}"',
            f"({table_join_sql_query}) AS joined_table",
        )
        sql_string = sql_string.replace(
            f"{table_name}",
            f"({table_join_sql_query}) AS joined_table",
        )

    if data_summary.sql_library.lower() in ["mysql", "mariadb"]:
        pattern = r"\b(INSERT\s+INTO|UPDATE\s+\w+|DELETE\s+FROM|REPLACE\s+INTO|CREATE\s+(TABLE|INDEX|DATABASE|VIEW)|ALTER\s+TABLE|DROP\s+(TABLE|DATABASE|INDEX|VIEW)|TRUNCATE\s+TABLE|LOAD\s+DATA\s+INFILE|GRANT\s+.*\s+ON|REVOKE\s+.*\s+ON|START\s+TRANSACTION|COMMIT|ROLLBACK|SAVEPOINT|RELEASE\s+SAVEPOINT|SET\s+TRANSACTION)\b"
    if data_summary.sql_library.lower() in ["postgresql"]:
        pattern = r"\b(INSERT\s+INTO|UPDATE\s+\w+|DELETE\s+FROM|REPLACE\s+INTO|CREATE\s+(TABLE|INDEX|DATABASE|VIEW)|ALTER\s+TABLE|DROP\s+(TABLE|DATABASE|INDEX|VIEW)|TRUNCATE\s+TABLE|COPY\s+(TABLE)|GRANT\s+.*\s+ON|REVOKE\s+.*\s+ON|START\s+TRANSACTION|COMMIT|ROLLBACK|SAVEPOINT|RELEASE\s+SAVEPOINT|SET\s+TRANSACTION)\b"
    if data_summary.sql_library.lower() in ["oracle"]:
        pattern = r"\b(INSERT\s+INTO|UPDATE\s+\w+|DELETE\s+FROM|REPLACE\s+INTO|CREATE\s+(TABLE|INDEX|DATABASE|VIEW)|ALTER\s+TABLE|DROP\s+(TABLE|DATABASE|INDEX|VIEW)|TRUNCATE\s+TABLE|COPY\s+(TABLE)|GRANT\s+.*\s+ON|REVOKE\s+.*\s+ON|START\s+TRANSACTION|COMMIT|ROLLBACK|SAVEPOINT|RELEASE\s+SAVEPOINT|SET\s+TRANSACTION)\b"
    if data_summary.sql_library.lower() in ["sqlserver"]:
        pattern = r"\b(INSERT\s+INTO|UPDATE\s+\w+|DELETE\s+FROM|MERGE\s+INTO|CREATE\s+(TABLE|INDEX|DATABASE|VIEW)|ALTER\s+TABLE|DROP\s+(TABLE|DATABASE|INDEX|VIEW)|TRUNCATE\s+TABLE|GRANT\s+.*\s+ON|REVOKE\s+.*\s+ON|START\s+TRANSACTION|COMMIT|ROLLBACK|SAVEPOINT|RELEASE\s+SAVEPOINT|SET\s+TRANSACTION)\b"

    if re.search(pattern, sql_string, re.IGNORECASE):
        print(f"Unauthorized SQL Query (sql_string): {sql_string}")

    return sql_string, sql_string_raw
