import traceback
import re
import logging
import os
import requests
from typing import Any, Tuple, Union
from time import perf_counter

from rapidfuzz import fuzz

from components.cmysql import native
from .datamodel import DataSummary
from .utils import (
    generate_column_information_prompt,
    normalize_chart_type,
    fetch_feedback,
    filter_feedback,
    filter_feedback_by_options,
    fetch_failed_sql_charts,
    calculate_token_usage,
)

from logging_library.performancelogger.performance_logger import PerformanceLogger

logger = logging.getLogger(__name__)

TARGET_TOKEN_LIMIT = int(os.getenv("SQL_TOTAL_INPUT_TOKEN_LIMIT", "0"))


def postprocess_sql(
    response: str,
    database_name: str,
    table_name: str,
    data_summary: DataSummary,
    AXIS_KEY_LIST: list,
    code_level_logger: logging.Logger,
) -> Tuple[str, str]:
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
    sql_string = sql_string.replace("MM-MM", "MM")
    sql_string = sql_string.replace("```sql", "")
    sql_string = sql_string.replace("```", "")
    sql_string = sql_string.replace("yAxis", "yAxis")
    sql_string = sql_string.strip()

    if "%Y-Q%q" in sql_string or "%Y-%q" in sql_string:
        print("SQL query generator response:")
        print(sql_string)
        code_level_logger.error(
            f"{sql_string} . SQL query generated contains '%Y-Q%q' or '%Y-%q'!"
        )
        raise RuntimeError(
            f"{sql_string} . SQL query generated contains '%Y-Q%q' or '%Y-%q'!"
        )

    if (
        "CONCAT_WS ('-M', SUBSTRING(" in sql_string
        or "CONCAT_WS('-M', SUBSTRING(" in sql_string
    ):
        print("SQL query generator response:")
        print(sql_string)
        code_level_logger.error(
            f"{sql_string} . SQL query generated contains 'CONCAT_WS ('-M', SUBSTRING('!"
        )
        raise RuntimeError(
            f"{sql_string} . SQL query generated contains 'CONCAT_WS ('-M', SUBSTRING('!",
        )

    if any(char in sql_string for char in ["'' AS", '"" AS', "`` AS"]):
        print("SQL query generator response:")
        print(sql_string)
        code_level_logger.error(
            f"{sql_string} . SQL query generated contains '' or  or ``."
        )
        raise RuntimeError(f"{sql_string} . SQL query generated contains '' or  or ``.")

    if any(char in sql_string for char in [" 0 AS"]):
        print("SQL query generator response:")
        print(sql_string)
        code_level_logger.error(f"{sql_string} . SQL query generated contains 0 AS.")
        raise RuntimeError("SQL query generated contains 0 AS.")

    for sql_function_datename in ["monthname", "dayname"]:
        if sql_function_datename in sql_string.lower():
            code_level_logger.error(
                f"{sql_string} . SQL query generated contains 'monthname'!"
            )
            raise RuntimeError(
                f"{sql_string} . SQL query generated contains 'monthname'!"
            )

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
            if alias != "":
                pattern = rf'(?<!")\b{alias}\b(?!")'
                sql_string = re.sub(pattern, f'"{alias}"', sql_string)

        sql_string = sql_string.replace("YYYY-QQ", "YYYY-Q")
        sql_string = sql_string.replace("YYYY-IQ", "YYYY-WW")

        if "CORR(" in sql_string:
            code_level_logger.error(
                f"{sql_string} . SQL query generated contains 'CORR'!"
            )
            raise RuntimeError(f"{sql_string} . SQL query generated contains 'CORR'!")

    if data_summary.sql_library.lower() in ["oracle"]:
        sql_string = sql_string.replace(";", "")

        if "CORR(" in sql_string:
            code_level_logger.error(
                f"{sql_string} . SQL query generated contains 'CORR'!"
            )
            raise RuntimeError(f"{sql_string} . SQL query generated contains 'CORR'!")

    if ";" not in sql_string:
        sql_string += ";"

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

    return sql_string, sql_string_raw


def validate_numerical_columns_for_histogram(
    sql_query: str,
    data_summary: DataSummary,
    code_level_logger: logging.Logger,
):
    non_numerical_columns = []

    for col in data_summary.column_data_tribes:
        if col in sql_query:
            if data_summary.column_data_tribes[col] != "numerical":
                non_numerical_columns.append(col)

    if non_numerical_columns:
        code_level_logger.error(
            f"Non-numerical columns found: {', '.join(non_numerical_columns)}",
        )
        raise RuntimeError(
            f"Non-numerical columns found: {', '.join(non_numerical_columns)}",
        )


def verify_sql_statement(
    data_summary: DataSummary,
    sql_string: str,
    code_level_logger: logging.Logger,
) -> None:
    if data_summary.sql_library.lower() in ["mysql", "mariadb"]:
        pattern = r"\b(INSERT\s+INTO|UPDATE\s+\w+|DELETE\s+FROM|REPLACE\s+INTO|CREATE\s+(TABLE|INDEX|DATABASE|VIEW)|ALTER\s+TABLE|DROP\s+(TABLE|DATABASE|INDEX|VIEW)|TRUNCATE\s+TABLE|LOAD\s+DATA\s+INFILE|GRANT\s+.*\s+ON|REVOKE\s+.*\s+ON|START\s+TRANSACTION|COMMIT|ROLLBACK|SAVEPOINT|RELEASE\s+SAVEPOINT|SET\s+TRANSACTION)\b"
    if data_summary.sql_library.lower() in ["postgresql"]:
        pattern = r"\b(INSERT\s+INTO|UPDATE\s+\w+|DELETE\s+FROM|REPLACE\s+INTO|CREATE\s+(TABLE|INDEX|DATABASE|VIEW)|ALTER\s+TABLE|DROP\s+(TABLE|DATABASE|INDEX|VIEW)|TRUNCATE\s+TABLE|COPY\s+(TABLE)|GRANT\s+.*\s+ON|REVOKE\s+.*\s+ON|START\s+TRANSACTION|COMMIT|ROLLBACK|SAVEPOINT|RELEASE\s+SAVEPOINT|SET\s+TRANSACTION)\b"
    if data_summary.sql_library.lower() in ["oracle"]:
        pattern = r"\b(INSERT\s+INTO|UPDATE\s+\w+|DELETE\s+FROM|REPLACE\s+INTO|CREATE\s+(TABLE|INDEX|DATABASE|VIEW)|ALTER\s+TABLE|DROP\s+(TABLE|DATABASE|INDEX|VIEW)|TRUNCATE\s+TABLE|COPY\s+(TABLE)|GRANT\s+.*\s+ON|REVOKE\s+.*\s+ON|START\s+TRANSACTION|COMMIT|ROLLBACK|SAVEPOINT|RELEASE\s+SAVEPOINT|SET\s+TRANSACTION)\b"
    if data_summary.sql_library.lower() in ["sqlserver"]:
        pattern = r"\b(INSERT\s+INTO|UPDATE\s+\w+|DELETE\s+FROM|MERGE\s+INTO|CREATE\s+(TABLE|INDEX|DATABASE|VIEW)|ALTER\s+TABLE|DROP\s+(TABLE|DATABASE|INDEX|VIEW)|TRUNCATE\s+TABLE|GRANT\s+.*\s+ON|REVOKE\s+.*\s+ON|START\s+TRANSACTION|COMMIT|ROLLBACK|SAVEPOINT|RELEASE\s+SAVEPOINT|SET\s+TRANSACTION)\b"

    if re.search(pattern, sql_string, re.IGNORECASE):
        code_level_logger.error(f"Unauthorized SQL Query (sql_string): {sql_string}")
        raise RuntimeError(f"Unauthorized SQL Query (sql_string): {sql_string}")


def classify_timeframe(chart_title: str, question: str):
    # timeframe = 'Yearly'/'Quarterly'/'Weekly'/'Daily'/'Half-Yearly'/'Monthly'/'Unclassified'
    if (
        fuzz.partial_ratio(chart_title.lower(), "yearly") > 80
        or fuzz.partial_ratio(question.lower(), "yearly") > 80
    ):
        timeframe = "Yearly"
    elif (
        fuzz.partial_ratio(chart_title.lower(), "quarterly") > 80
        or fuzz.partial_ratio(question.lower(), "quarterly") > 80
    ):
        timeframe = "Quarterly"
    elif (
        fuzz.partial_ratio(chart_title.lower(), "weekly") > 80
        or fuzz.partial_ratio(question.lower(), "weekly") > 80
    ):
        timeframe = "Weekly"
    elif (
        fuzz.partial_ratio(chart_title.lower(), "daily") > 80
        or fuzz.partial_ratio(question.lower(), "daily") > 80
    ):
        timeframe = "Daily"
    elif (
        fuzz.partial_ratio(chart_title.lower(), "half-yearly") > 80
        or fuzz.partial_ratio(question.lower(), "half-yearly") > 80
    ):
        timeframe = "Half-Yearly"
    elif (
        fuzz.partial_ratio(chart_title.lower(), "monthly") > 80
        or fuzz.partial_ratio(question.lower(), "monthly") > 80
    ):
        timeframe = "Monthly"
    else:
        timeframe = "Unclassified"

    return timeframe


def classify_time_duration(chart_title: str, question: str):
    # time_duration = 'Week'/'Month'/'Quarter'/'Year'/'Unclassified'
    question = question.lower()
    chart_title = chart_title.lower()

    # "Past 2 weeks", "Next 3 weeks", "Last week", "Week 1 - Week 4"
    week_pattern = re.compile(
        r"\b(past|last|next)?\s?\d*\s?(week|weeks)\b|\b\d+\s?week\b|\bweek\b(?:\s?[-\s]?\s?\d+)?",
        re.IGNORECASE,
    )
    # "Past 6 months", "Next January", "March", "Jan 2022 - Mar 2022"
    month_pattern = re.compile(
        r"\b(past|last|next)?\s?\d*\s?(month|months)\b|\b(january|february|march|april|may|june|july|august|september|october|november|december)\b|\b(?:\w+\s)?\d{4}\s?[-\s]?\s?(?:\w+\s)?\d{4}\b",
        re.IGNORECASE,
    )
    # "Last Q3", "Next quarter", "Past H2", "Q1 2023 - Q3 2023"
    quarter_pattern = re.compile(
        r"\b(past|last|next)?\s?\d*\s?(quarter|quarters|Q\d)\b|\b(h1|h2)\b|\bQ\d\s?\d{4}\s?[-\s]?\s?Q\d\s?\d{4}\b",
        re.IGNORECASE,
    )
    # "Past 5 years", "Next year", "2022", "Last 3 years", "2022 - 2023"
    year_pattern = re.compile(
        r"\b(past|last|next)?\s?\d*\s?(year|years)\b|\b(\d{4})\b|\b\d{4}\s?[-\s]?\s?\d{4}\b",
        re.IGNORECASE,
    )

    if week_pattern.search(question) or week_pattern.search(chart_title):
        return "Week"
    if month_pattern.search(question) or month_pattern.search(chart_title):
        return "Month"
    if quarter_pattern.search(question) or quarter_pattern.search(chart_title):
        return "Quarter"
    if year_pattern.search(question) or year_pattern.search(chart_title):
        return "Year"
    return "Unclassified"


def classify_instruction_timeframe(instruction: str):
    # timeframe = 'Yearly'/'Quarterly'/'Weekly'/'Daily'/'Half-Yearly'/'Monthly'/'Unclassified'
    if fuzz.partial_ratio(instruction.lower(), "yearly") > 80:
        timeframe = "Yearly"
    elif fuzz.partial_ratio(instruction.lower(), "quarterly") > 80:
        timeframe = "Quarterly"
    elif fuzz.partial_ratio(instruction.lower(), "weekly") > 80:
        timeframe = "Weekly"
    elif fuzz.partial_ratio(instruction.lower(), "daily") > 80:
        timeframe = "Daily"
    elif fuzz.partial_ratio(instruction.lower(), "half-yearly") > 80:
        timeframe = "Half-Yearly"
    elif fuzz.partial_ratio(instruction.lower(), "monthly") > 80:
        timeframe = "Monthly"
    else:
        timeframe = "Unclassified"

    return timeframe


def classify_instruction_time_duration(instruction: str):
    # time_duration = 'Week'/'Month'/'Quarter'/'Year'/'Unclassified'
    instruction = instruction.lower()

    # "Past 2 weeks", "Next 3 weeks", "Last week", "Week 1 - Week 4"
    week_pattern = re.compile(
        r"\b(past|last|next)?\s?\d*\s?(week|weeks)\b|\b\d+\s?week\b|\bweek\b(?:\s?[-\s]?\s?\d+)?",
        re.IGNORECASE,
    )
    # "Past 6 months", "Next January", "March", "Jan 2022 - Mar 2022"
    month_pattern = re.compile(
        r"\b(past|last|next)?\s?\d*\s?(month|months)\b|\b(january|february|march|april|may|june|july|august|september|october|november|december)\b|\b(?:\w+\s)?\d{4}\s?[-\s]?\s?(?:\w+\s)?\d{4}\b",
        re.IGNORECASE,
    )
    # "Last Q3", "Next quarter", "Past H2", "Q1 2023 - Q3 2023"
    quarter_pattern = re.compile(
        r"\b(past|last|next)?\s?\d*\s?(quarter|quarters|Q\d)\b|\b(h1|h2)\b|\bQ\d\s?\d{4}\s?[-\s]?\s?Q\d\s?\d{4}\b",
        re.IGNORECASE,
    )
    # "Past 5 years", "Next year", "2022", "Last 3 years", "2022 - 2023"
    year_pattern = re.compile(
        r"\b(past|last|next)?\s?\d*\s?(year|years)\b|\b(\d{4})\b|\b\d{4}\s?[-\s]?\s?\d{4}\b",
        re.IGNORECASE,
    )

    if week_pattern.search(instruction):
        return "Week"
    if month_pattern.search(instruction):
        return "Month"
    if quarter_pattern.search(instruction):
        return "Quarter"
    if year_pattern.search(instruction):
        return "Year"
    return "Unclassified"


def get_required_axis_columns(
    chart_axis: dict,
):
    required_axis_columns = []

    for key in chart_axis:
        if "_column" in key.lower():
            if isinstance(chart_axis[key], str):
                required_axis_columns.append(chart_axis[key])
            else:
                required_axis_columns.extend(chart_axis[key])

    return required_axis_columns


def generate_cleaned_chart_axis(chart_axis: dict) -> Tuple[dict, dict, list]:
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

    return chart_axis_edited, chart_axis_title_edited, AXIS_KEY_LIST


def generate_filter_instruction(filters: dict) -> str:
    if filters == {}:
        FILTER_INSTRUCTION = ""
    else:
        FILTER_COLUMNS = []

        for filter_key in filters:
            if filters[filter_key] == [] or filters[filter_key] == [""]:
                pass
            else:
                FILTER_COLUMNS.append(filter_key)

        if FILTER_COLUMNS == []:
            FILTER_INSTRUCTION = ""
        else:
            FILTER_INSTRUCTION = "Filter the data in the generated SQL query.\n"

            for filter_column in FILTER_COLUMNS:
                FILTER_INSTRUCTION += f"'{filter_column}' = {filters[filter_column]}\n"

    return FILTER_INSTRUCTION


def generate_aggregation_instruction(
    aggregations: list,
    chart_type: str,
    data_summary: DataSummary,
) -> str:
    for column in aggregations:
        if data_summary.column_n_unique_value_dict[column] > 12:
            aggregations.remove(column)

    if aggregations == [] or chart_type in [
        "histogram_chart",
        "scatterplot_chart",
        "bubbleplot_chart",
    ]:
        AGGREGATION_INSTRUCTION = ""
    else:
        AGGREGATION_INSTRUCTION = f"Group or aggregate the data by at least the following columns: {', '.join(aggregations)} in the generated SQL query.\n"

    return AGGREGATION_INSTRUCTION


def generate_axis_instruction(
    chart_type: str,
    chart_axis: dict,
    code_level_logger: logging.Logger,
) -> str:
    if chart_type in ["bar_chart", "column_chart", "pyramidfunnel_chart", "pie_chart"]:
        AXIS_INSTRUCTIONS = "SELECT given xAxis column and RENAME it into 'xAxis'. SELECT given yAxis column and RENAME it into 'yAxis'. NEVER SPLIT the yAxis column into several columns."
    elif chart_type in ["histogram_chart"]:
        AXIS_INSTRUCTIONS = "SELECT given xAxis column and RENAME it into 'xAxis'. ENSURE ONLY ONE column selected named 'xAxis' in the generated sql query. The generated SQL query MUST ONLY SELECT ONE COLUMN with NUMERICAL data type for the 'xAxis'. NEVER SELECT ANY COLUMN with STRING / TEXT / DATE data type in the generated SQL query. The generated SQL query MUST ONLY select a column as xAxis to determine the distribution. IT IS CRUCIAL THAT YOU DO NOT INCLUDE yAxis column OR ANY ALIASES RELATED TO yAxis, ANY AGGREGATIONS, OR GROUP BY CLAUSES. The query should simply retrieve the xAxis column. Make sure the 'xAxis' is not aggregated to improve granularity. Calculations for the xAxis column are allowed as long as the result is a numerical value. "

    elif chart_type in ["pie_chart"]:
        AXIS_INSTRUCTIONS = "SELECT given xAxis column and RENAME it into 'xAxis'. SELECT given yAxis column and RENAME it into 'yAxis'. NEVER SPLIT the yAxis column into several columns."

    elif chart_type in ["scatterplot_chart"]:
        AXIS_INSTRUCTIONS = "SELECT given xAxis column and RENAME it into 'xAxis'. SELECT given yAxis column and RENAME it into 'yAxis'. Only 'xAxis', 'yAxis', and 'series' can be selected. Strictly no additional alias such as 'yAxis2', 'yAxis3', or any other variations are allowed. Avoid using any calculations or formulas (such as sums or averages) for series column ONLY. The series column should directly represent categorical values without transformation. The xAxis and yAxis can include calculations or formulas if needed."

        if (
            "series_column" in chart_axis
            and chart_axis["series_column"] != ""
            and chart_axis["series_column"] != []
        ):
            AXIS_INSTRUCTIONS += (
                " SELECT given series column and RENAME it into 'series'."
            )

    elif chart_type in [
        "bubbleplot_chart",
    ]:
        AXIS_INSTRUCTIONS = "SELECT given xAxis column and RENAME it into 'xAxis'. SELECT given yAxis column and RENAME it into 'yAxis'. SELECT given zAxis column and RENAME it into 'zAxis'."

        if (
            "series_column" in chart_axis
            and chart_axis["series_column"] != ""
            and chart_axis["series_column"] != []
        ):
            AXIS_INSTRUCTIONS += (
                " SELECT given series column and RENAME it into 'series'."
            )

    elif chart_type in [
        "area_chart",
        "line_chart",
        "spline_chart",
        "grouped_column_chart",
        "grouped_bar_chart",
        "radar_chart",
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
        AXIS_INSTRUCTIONS = "SELECT every columns related to the question from the database SQL schema given. Ensure to rename each selected column to human-readable column name which represents the metric or category of the respective column (e.g., 'Product', 'Revenue', 'Cost-to-Revenue Ratio'). Avoid renaming any selected column to 'all', 'xAxis', 'yAxis', 'yAxis2', 'yAxis3', and 'series'."
    else:
        code_level_logger.error(
            f"'{chart_type}' Chart Type is not supported in SQL Query Generator!",
        )
        raise RuntimeError(
            f"'{chart_type}' Chart Type is not supported in SQL Query Generator!",
        )

    return AXIS_INSTRUCTIONS


def generate_table_instruction(
    data_summary: DataSummary,
    database_name: str,
    table_name: str,
) -> str:
    if (
        "postgresql" in data_summary.sql_library.lower()
        or "oracle" in data_summary.sql_library.lower()
    ):
        TABLE_INSTRUCTION = (
            f"""USE {table_name.replace('"', '')} as the source table name."""
        )
    else:
        TABLE_INSTRUCTION = (
            f"""USE {database_name}.{table_name} as the source table name."""
        )

    return TABLE_INSTRUCTION


def generate_backtick_instruction(
    data_summary: DataSummary,
) -> str:
    if (
        "postgresql" in data_summary.sql_library.lower()
        or "oracle" in data_summary.sql_library.lower()
    ):
        BACKTICK_INSTRUCTION = """ENSURE TO ALWAYS ENCLOSE column names and column aliases in double quotes in the generated SQL query."""
    else:
        BACKTICK_INSTRUCTION = "ENSURE TO ALWAYS REMOVE backticks, quotes, and double quotes from table name in the sql query."

    return BACKTICK_INSTRUCTION


def generate_alias_instruction(chart_type: str) -> str:
    if chart_type in ["table_chart"]:
        ALIAS_INSTRUCTION = """- ENSURE every column aliases are clear, correct, and consistently assigned throughout the SQL query.
- Ensure that every column aliases in the sql query are human-readable.
- ENSURE to convert any date related columns with TEXT / STRING data types to DATE data types in every part of your generated SQL query.
- STRICTLY AVOID selecting columns other than those provided in the Database SQL Schema.
- STRICTLY AVOID using column aliases in 'groupby' and 'orderby' clauses."""
    else:
        ALIAS_INSTRUCTION = """- ENSURE every column aliases are clear, correct, and consistently assigned throughout the SQL query.
- ENSURE to convert any date related columns with TEXT / STRING data types to DATE data types in every part of your generated SQL query.
- STRICTLY AVOID selecting columns other than those provided in the Database SQL Schema.
- STRICTLY AVOID using column aliases in 'groupby' and 'orderby' clauses.
- ENSURE to RENAME all selected columns to the appropriate axis name given."""

    return ALIAS_INSTRUCTION


def generate_sql_native_lang(
    data_summary: DataSummary, code_level_logger: logging.Logger
) -> str:
    if (
        "mysql" in data_summary.sql_library.lower()
        or "mariadb" in data_summary.sql_library.lower()
    ):
        NATIVE_LANG = native.NATIVE_FUNC_MYSQL_MARIA
    elif "sqlserver" in data_summary.sql_library.lower():
        NATIVE_LANG = native.NATIVE_FUNC_SQLSERVER
    elif "postgresql" in data_summary.sql_library.lower():
        NATIVE_LANG = native.NATIVE_FUNC_POSTGRESQL
    elif "oracle" in data_summary.sql_library.lower():
        NATIVE_LANG = native.NATIVE_FUNC_ORACLE
    else:
        code_level_logger.error(
            f"{data_summary.sql_library.lower()} SQL Language is unsupported!",
        )
        raise RuntimeError(
            f"{data_summary.sql_library.lower()} SQL Language is unsupported!",
        )

    return NATIVE_LANG


def generate_date_instructions(
    data_summary: DataSummary,
    chart_axis: dict,
    timeframe: str,
    time_duration: str,
    code_level_logger: logging.Logger,
) -> Tuple[str, str, str]:
    # DATE_INSTRUCTION -- general instructions
    # DATE_INSTRUCTION2 -- Instructions for Date Selection in SELECT statement
    # DATE_INSTRUCTION3 -- Instructions for Date Selection for filtering

    if (
        "mysql" in data_summary.sql_library.lower()
        or "mariadb" in data_summary.sql_library.lower()
    ):
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
            ):
                if (
                    data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower()
                    in ["text"]
                    or "varchar"
                    in data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower()
                ):
                    DATE_INSTRUCTION = """Ensure to convert any date related columns with TEXT / STRING data types to DATE data types through the entire SQL query. Ensure that this conversion is applied in all parts of the SQL query, including the 'WHERE' clause, subqueries, 'CONCAT' function, and any other functions, methods, clauses, or statements, using the 'STR_TO_DATE' function. Ensuring the correct syntax for date conversion and formatting in all parts of the SQL query is essential to avoid errors and achieve accurate results. When calculating a date interval and formatting it as a string, use the following approach: DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL time_period), '%Y-%m-%d'). ENSURE the sql query follows the given time duration in the question and chart title, or the default time duration which is "past 1 year" if time duration not exist. Make sure that any date-related axes selected are formatted as strings in the final output."""
                elif data_summary.column_sql_data_types[
                    chart_axis["xAxis_column"]
                ].lower() in [
                    "datetime",
                    "date",
                ]:
                    DATE_INSTRUCTION = """Ensure the correct syntax for date conversion and formatting in all parts of the SQL query is essential to avoid errors and achieve accurate results. When calculating a date interval and formatting it as a string, use the following approach: DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL time_period), '%Y-%m-%d'). ENSURE the sql query follows the given time duration in the question and chart title, or the default time duration which is "past 1 year" if time duration not exist. Make sure that any date-related axes selected are formatted as strings in the final output."""
                else:
                    DATE_INSTRUCTION = """Do not apply date conversion functions to date-related columns containing numerical date representations in all parts of the sql query. Ensure the SQL query does not perform invalid date comparisons. Specifically, ensure no comparison between date/datetime column with non-date types (e.g., integers or strings representing years, months, quarters, etc). Check all comparisons between dates and non-date types to ensure type consistency and prevent errors. Ensure that no date conversion functions are applied to numerical year, month, day, or similar parts of the date column. Make sure that any date-related axes selected are formatted as strings in the final output."""
            else:
                DATE_INSTRUCTION = """Do not apply date conversion functions to date-related columns containing numerical date representations in all parts of the sql query. Ensure the SQL query does not perform invalid date comparisons. Specifically, ensure no comparison between date/datetime column with non-date types (e.g., integers or strings representing years, months, quarters, etc). Check all comparisons between dates and non-date types to ensure type consistency and prevent errors. Ensure that no date conversion functions are applied to numerical year, month, day, or similar parts of the date column. Make sure that any date-related axes selected are formatted as strings in the final output."""

            if timeframe.lower() == "yearly":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CAST(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) AS CHAR)" as a reference or sample of proper date selection."""

                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CAST(YEAR(`Date`) AS CHAR)" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = """"""
                else:
                    DATE_INSTRUCTION2 = """"""
            elif timeframe.lower() == "quarterly":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-Q', QUARTER(STR_TO_DATE(`Date`, '%d/%m/%Y')))" as a reference or sample of proper date selection."""

                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR(`Date`), '-Q', QUARTER(`Date`))" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = """"""
                else:
                    DATE_INSTRUCTION2 = """"""

                if DATE_INSTRUCTION2 == """""":
                    DATE_INSTRUCTION2 = """Never use 'YYYY-Qq', '%Y-Q%q' and '%Y-%q' for formatting quarter dates in your generated SQL queries. Instead, format the quarter dates by correctly combining the year and quarter using the `QUARTER` and `YEAR` functions within the `CONCAT` statement, without using any `SUBSTRING` function where the date column is formatted as 'YYYY-Q1', 'YYYY-Q2', 'YYYY-Q3', and 'YYYY-Q4'."""
                else:
                    DATE_INSTRUCTION2 += """ Never use 'YYYY-Qq', '%Y-Q%q' and '%Y-%q' for formatting quarter dates in your generated SQL queries. Instead, format the quarter dates by correctly combining the year and quarter using the `QUARTER` and `YEAR` functions within the `CONCAT` statement, without using any `SUBSTRING` function where the date column is formatted as 'YYYY-Q1', 'YYYY-Q2', 'YYYY-Q3', and 'YYYY-Q4'."""

            elif timeframe.lower() == "weekly":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-W', WEEK(STR_TO_DATE(`Date`, '%d/%m/%Y')))" as a reference or sample of proper date selection."""
                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR(`Date`), '-W', WEEK(`Date`))" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = """"""
                else:
                    DATE_INSTRUCTION2 = """"""

            elif timeframe.lower() == "daily":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "DATE(STR_TO_DATE(`Date`, '%d/%m/%Y'))" as a reference or sample of proper date selection."""
                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "DATE(`Date`)" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = """"""
                else:
                    DATE_INSTRUCTION2 = """"""

                if DATE_INSTRUCTION2 == "":
                    DATE_INSTRUCTION2 = """Avoid using day names in the SQL query."""
                else:
                    DATE_INSTRUCTION2 += """ Avoid using day names in the SQL query."""

            elif timeframe.lower() == "half-yearly":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-H', IF(MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y')) <= 6, 1, 2))" as a reference or sample of proper date selection."""
                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR(`Date`), '-H', IF(MONTH(`Date`) <= 6, 1, 2))" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = """"""
                else:
                    DATE_INSTRUCTION2 = """"""

            elif timeframe.lower() == "monthly":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-M', MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y')))" as a reference or sample of proper date selection."""
                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR(`Date`), '-M', MONTH(`Date`))" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = ""
                else:
                    DATE_INSTRUCTION2 = """"""

                if DATE_INSTRUCTION2 == """""":
                    DATE_INSTRUCTION2 = """Avoid using month names in the SQL query."""
                else:
                    DATE_INSTRUCTION2 += (
                        """ Avoid using month names in the SQL query."""
                    )
            else:
                DATE_INSTRUCTION2 = """"""
        else:
            DATE_INSTRUCTION = """When calculating a date interval for filtering and formatting it as a string, use the following approach: DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL time_period), '%Y-%m-%d'). ENSURE the sql query follows the given time duration in the question and chart title, or the default time duration which is "past 1 year" if time duration not exist."""

            DATE_INSTRUCTION2 = """"""

        if (
            isinstance(chart_axis["xAxis_column"], str)
            and chart_axis["xAxis_column"] in data_summary.column_data_tribes.keys()
            and data_summary.column_data_tribes[chart_axis["xAxis_column"]]
            in ["date_related"]
            and chart_axis["xAxis_column"] in data_summary.column_sql_data_types.keys()
            and data_summary.column_sql_data_types[chart_axis["xAxis_column"]].lower()
            not in [
                "tinyint",
                "smallint",
                "mediumint",
                "int",
                "bigint",
                "float",
                "double",
                "decimal",
                "bit",
            ]
        ):
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
        else:
            DATE_INSTRUCTION3 = """"""
    elif "sqlserver" in data_summary.sql_library.lower():
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
            ):
                if (
                    data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower()
                    in ["text"]
                    or "varchar"
                    in data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower()
                ):
                    DATE_INSTRUCTION = """Ensure to convert any date related columns with TEXT / STRING data types to DATE data types. This conversion should be applied in all parts of the SQL query, including the 'WHERE' clause, subqueries, 'CONCAT' function, and any other functions, methods, clauses, or statements, using the 'CONVERT' function. Make sure that any date-related axes selected are formatted as strings in the final output."""
                else:
                    DATE_INSTRUCTION = """Make sure that any date-related axes selected are formatted as strings in the final output."""
            else:
                DATE_INSTRUCTION = """Make sure that any date-related axes selected are formatted as strings in the final output."""

            if DATE_INSTRUCTION == """""":
                DATE_INSTRUCTION = """Ensuring the correct syntax for date conversion and formatting in all parts of the SQL query is essential to avoid errors and achieve accurate results. When calculating a date interval and formatting it as a string, use the following approach: CONVERT(VARCHAR(10), DATEADD(DAY, -time_period, GETDATE()), 120). ENSURE the sql query follows the given time duration in the question and chart title, or the default time duration which is "past 1 year" if time duration not exist."""
            else:
                DATE_INSTRUCTION += """ Ensuring the correct syntax for date conversion and formatting in all parts of the SQL query is essential to avoid errors and achieve accurate results. When calculating a date interval and formatting it as a string, use the following approach: CONVERT(VARCHAR(10), DATEADD(DAY, -time_period, GETDATE()), 120). ENSURE the sql query follows the given time duration in the question and chart title, or the default time duration which is "past 1 year" if time duration not exist."""

            if timeframe.lower() == "yearly":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR)" as a reference or sample of proper date selection."""
                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CAST(YEAR([Date]) AS VARCHAR)" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = """"""
                else:
                    DATE_INSTRUCTION2 = """"""
            elif timeframe.lower() == "quarterly":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, [Date], 103)))" as a reference or sample of proper date selection."""
                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR([Date]), '-Q', DATEPART(QUARTER, [Date]))" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = """"""
                else:
                    DATE_INSTRUCTION2 = """"""

                if DATE_INSTRUCTION2 == """""":
                    DATE_INSTRUCTION2 = """Never use 'YYYY-Qq', 'YYYY-Q%q' and 'YYYY-%q' for formatting quarter dates in your generated SQL queries. Instead, format the quarter dates by correctly combining the year and quarter using the `DATEPART` function within the `CONCAT` statement, without using any `SUBSTRING` function where the date column is formatted as 'YYYY-Q1', 'YYYY-Q2', 'YYYY-Q3', and 'YYYY-Q4'."""
                else:
                    DATE_INSTRUCTION2 += """ Never use 'YYYY-Qq', 'YYYY-Q%q' and 'YYYY-%q' for formatting quarter dates in your generated SQL queries. Instead, format the quarter dates by correctly combining the year and quarter using the `DATEPART` function within the `CONCAT` statement, without using any `SUBSTRING` function where the date column is formatted as 'YYYY-Q1', 'YYYY-Q2', 'YYYY-Q3', and 'YYYY-Q4'."""

            elif timeframe.lower() == "weekly":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-W', DATEPART(WEEK, CONVERT(DATE, [Date], 103)))" as a reference or sample of proper date selection."""
                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR([Date]), '-W', DATEPART(WEEK, [Date]))" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = """"""
                else:
                    DATE_INSTRUCTION2 = """"""

            elif timeframe.lower() == "daily":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONVERT(DATE, [Date], 103)" as a reference or sample of proper date selection."""
                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CAST([Date] AS DATE)" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = """"""
                else:
                    DATE_INSTRUCTION2 = """"""

                if DATE_INSTRUCTION2 == """""":
                    DATE_INSTRUCTION2 = """Avoid using day names in the SQL query."""
                else:
                    DATE_INSTRUCTION2 += """ Avoid using day names in the SQL query."""

            elif timeframe.lower() == "half-yearly":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-H', CASE WHEN MONTH(CONVERT(DATE, [Date], 103)) <= 6 THEN 1 ELSE 2 END)" as a reference or sample of proper date selection."""
                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR([Date]), '-H', CASE WHEN MONTH([Date]) <= 6 THEN 1 ELSE 2 END)" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = """"""
                else:
                    DATE_INSTRUCTION2 = """"""

            elif timeframe.lower() == "monthly":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-M', MONTH(CONVERT(DATE, [Date], 103)))" as a reference or sample of proper date selection."""
                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(YEAR([Date]), '-M', MONTH([Date]))" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = """"""
                else:
                    DATE_INSTRUCTION2 = """"""

                if DATE_INSTRUCTION2 == """""":
                    DATE_INSTRUCTION2 = """Avoid using month names in the SQL query."""
                else:
                    DATE_INSTRUCTION2 += (
                        """ Avoid using month names in the SQL query."""
                    )
            else:
                DATE_INSTRUCTION2 = """"""
        else:
            DATE_INSTRUCTION = """When calculating a date interval for filtering and formatting it as a string, use the following approach: CONVERT(VARCHAR(10), DATEADD(DAY, -time_period, GETDATE()), 120). ENSURE the sql query follows the given time duration in the question and chart title, or the default time duration which is "past 1 year" if time duration not exist."""

            DATE_INSTRUCTION2 = """"""

        if (
            isinstance(chart_axis["xAxis_column"], str)
            and chart_axis["xAxis_column"] in data_summary.column_data_tribes.keys()
            and data_summary.column_data_tribes[chart_axis["xAxis_column"]]
            in ["date_related"]
            and chart_axis["xAxis_column"] in data_summary.column_sql_data_types.keys()
            and data_summary.column_sql_data_types[chart_axis["xAxis_column"]].lower()
            not in [
                "tinyint",
                "smallint",
                "mediumint",
                "int",
                "bigint",
                "float",
                "double",
                "decimal",
                "bit",
            ]
        ):
            if time_duration == "Week":
                DATE_INSTRUCTION3 = """If date filtering is required for weekly data, ensure to specify the date range using DATEADD for weeks, and apply DATEADD or WHERE BETWEEN functions appropriately. Use the SQL query snippet "WHERE date_column BETWEEN DATEADD(WEEK, -N, GETDATE()) AND GETDATE()" as a reference or sample of proper date selection."""
            elif time_duration == "Month":
                DATE_INSTRUCTION3 = """If date filtering is required for monthly data, ensure to specify the date range using DATEADD for months, and apply DATEADD or WHERE BETWEEN functions as needed. Use the SQL query snippet "WHERE date_column BETWEEN DATEADD(MONTH, -N, GETDATE()) AND GETDATE()" as a reference or sample of proper date selection."""
            elif time_duration == "Quarter":
                DATE_INSTRUCTION3 = """If date filtering is required for quarterly data, ensure to specify the date range using DATEADD for quarters, and utilize DATEADD or WHERE BETWEEN functions accordingly. Use the SQL query snippet "WHERE date_column BETWEEN DATEADD(QUARTER, -N, GETDATE()) AND GETDATE()" as a reference or sample of proper date selection."""
            elif time_duration == "Year":
                DATE_INSTRUCTION3 = """If date filtering is required for yearly data, ensure to specify the date range using DATEADD for years, and use DATEADD or WHERE BETWEEN functions as applicable. Use the SQL query snippet "WHERE date_column BETWEEN DATEADD(YEAR, -N, GETDATE()) AND GETDATE()" as a reference or sample of proper date selection."""
            else:
                DATE_INSTRUCTION3 = """"""
        else:
            DATE_INSTRUCTION3 = """"""
    elif "postgresql" in data_summary.sql_library.lower():
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
            ):
                if (
                    data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower()
                    in ["text"]
                    or "varchar"
                    in data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower()
                ):
                    DATE_INSTRUCTION = """Ensure to convert any date related columns with TEXT / STRING data types to DATE data types. This conversion should be applied in all parts of the SQL query, including the 'WHERE' clause, subqueries, 'CONCAT' function, and any other functions, methods, clauses, or statements, using the 'TO_DATE' function. Make sure that any date-related axes selected are formatted as strings in the final output."""
                else:
                    DATE_INSTRUCTION = """Make sure that any date-related axes selected are formatted as strings in the final output."""
            else:
                DATE_INSTRUCTION = """Make sure that any date-related axes selected are formatted as strings in the final output."""

            if DATE_INSTRUCTION == """""":
                DATE_INSTRUCTION = """Ensuring the correct syntax for date conversion and formatting in all parts of the SQL query is essential to avoid errors and achieve accurate results. When calculating a date interval and formatting it as a string, use the following approach: TO_CHAR(CURRENT_DATE - INTERVAL 'time_period', 'YYYY-MM-DD'). ENSURE the sql query follows the given time duration in the question and chart title, or the default time duration which is "past 1 year" if time duration not exist."""
            else:
                DATE_INSTRUCTION += """ Ensuring the correct syntax for date conversion and formatting in all parts of the SQL query is essential to avoid errors and achieve accurate results. When calculating a date interval and formatting it as a string, use the following approach: TO_CHAR(CURRENT_DATE - INTERVAL 'time_period', 'YYYY-MM-DD'). ENSURE the sql query follows the given time duration in the question and chart title, or the default time duration which is "past 1 year" if time duration not exist."""

            if timeframe.lower() == "yearly":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CAST(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) AS TEXT)" as a reference or sample of proper date selection."""

                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CAST(EXTRACT(YEAR FROM "Date") AS TEXT)" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = """"""
                else:
                    DATE_INSTRUCTION2 = """"""
            elif timeframe.lower() == "quarterly":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY'))::TEXT, '-Q', EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY'))::TEXT)" as a reference or sample of proper date selection."""
                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(EXTRACT(YEAR FROM "Date")::TEXT, '-Q', EXTRACT(QUARTER FROM "Date")::TEXT)" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = """"""
                else:
                    DATE_INSTRUCTION2 = """"""

                if DATE_INSTRUCTION2 == """""":
                    DATE_INSTRUCTION2 = """Never use 'YYYY-Qq', 'YYYY-Q%q' and 'YYYY-%q' for formatting quarter dates in your generated SQL queries. Instead, format the quarter dates by correctly combining the year and quarter using the `EXTRACT` function within the `CONCAT` statement, without using any `SUBSTRING` function where the date column is formatted as 'YYYY-Q1', 'YYYY-Q2', 'YYYY-Q3', and 'YYYY-Q4'."""
                else:
                    DATE_INSTRUCTION2 += """ Never use 'YYYY-Qq', 'YYYY-Q%q' and 'YYYY-%q' for formatting quarter dates in your generated SQL queries. Instead, format the quarter dates by correctly combining the year and quarter using the `EXTRACT` function within the `CONCAT` statement, without using any `SUBSTRING` function where the date column is formatted as 'YYYY-Q1', 'YYYY-Q2', 'YYYY-Q3', and 'YYYY-Q4'."""

            elif timeframe.lower() == "weekly":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY'))::TEXT, '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY'))::TEXT)" as a reference or sample of proper date selection."""
                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(EXTRACT(YEAR FROM "Date")::TEXT, '-W', EXTRACT(WEEK FROM "Date")::TEXT)" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = """"""
                else:
                    DATE_INSTRUCTION2 = """"""

            elif timeframe.lower() == "daily":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "TO_DATE("Date", 'DD/MM/YYYY')" as a reference or sample of proper date selection."""
                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "DATE("Date")" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = """"""
                else:
                    DATE_INSTRUCTION2 = """"""

                DATE_INSTRUCTION2 += """ Avoid using day names in the SQL query."""

            elif timeframe.lower() == "half-yearly":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY'))::TEXT, '-H', CASE WHEN EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) <= 6 THEN '1' ELSE '2' END)" as a reference or sample of proper date selection."""
                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(EXTRACT(YEAR FROM "Date")::TEXT, '-H', CASE WHEN EXTRACT(MONTH FROM "Date") <= 6 THEN '1' ELSE '2' END)" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = """"""
                else:
                    DATE_INSTRUCTION2 = """"""

            elif timeframe.lower() == "monthly":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY'))::TEXT, '-M', LPAD(EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY'))::TEXT, 2, '0'))" as a reference or sample of proper date selection."""
                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "CONCAT(EXTRACT(YEAR FROM "Date")::TEXT, '-M', LPAD(EXTRACT(MONTH FROM "Date")::TEXT, 2, '0'))" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = """"""
                else:
                    DATE_INSTRUCTION2 = """"""

                if DATE_INSTRUCTION2 == """""":
                    DATE_INSTRUCTION2 = """Avoid using month names in the SQL query."""
                else:
                    DATE_INSTRUCTION2 += (
                        """ Avoid using month names in the SQL query."""
                    )
            else:
                DATE_INSTRUCTION2 = """"""
        else:
            DATE_INSTRUCTION = """When calculating a date interval for filtering and formatting it as a string, use the following approach: TO_CHAR(CURRENT_DATE - INTERVAL 'time_period', 'YYYY-MM-DD'). ENSURE the sql query follows the given time duration in the question and chart title, or the default time duration which is "past 1 year" if time duration not exist."""

            DATE_INSTRUCTION2 = """"""

        if (
            isinstance(chart_axis["xAxis_column"], str)
            and chart_axis["xAxis_column"] in data_summary.column_data_tribes.keys()
            and data_summary.column_data_tribes[chart_axis["xAxis_column"]]
            in ["date_related"]
            and chart_axis["xAxis_column"] in data_summary.column_sql_data_types.keys()
            and data_summary.column_sql_data_types[chart_axis["xAxis_column"]].lower()
            not in [
                "tinyint",
                "smallint",
                "mediumint",
                "int",
                "bigint",
                "float",
                "double",
                "decimal",
                "bit",
            ]
        ):
            if time_duration == "Week":
                DATE_INSTRUCTION3 = """If date filtering is required for weekly data, ensure to specify the date range using INTERVAL for weeks, and apply date arithmetic or WHERE BETWEEN functions appropriately. Use the SQL query snippet "WHERE date_column BETWEEN CURRENT_DATE - INTERVAL 'N weeks' AND CURRENT_DATE" as a reference or sample of proper date selection."""
            elif time_duration == "Month":
                DATE_INSTRUCTION3 = """If date filtering is required for monthly data, ensure to specify the date range using INTERVAL for months, and apply date arithmetic or WHERE BETWEEN functions as needed. Use the SQL query snippet "WHERE date_column BETWEEN CURRENT_DATE - INTERVAL 'N months' AND CURRENT_DATE" as a reference or sample of proper date selection."""
            elif time_duration == "Quarter":
                DATE_INSTRUCTION3 = """If date filtering is required for quarterly data, ensure to specify the date range using INTERVAL for quarters, and utilize date arithmetic or WHERE BETWEEN functions accordingly. Use the SQL query snippet "WHERE date_column BETWEEN CURRENT_DATE - INTERVAL 'N quarters' AND CURRENT_DATE" as a reference or sample of proper date selection."""
            elif time_duration == "Year":
                DATE_INSTRUCTION3 = """If date filtering is required for yearly data, ensure to specify the date range using INTERVAL for years, and use date arithmetic or WHERE BETWEEN functions as applicable. Use the SQL query snippet "WHERE date_column BETWEEN CURRENT_DATE - INTERVAL 'N years' AND CURRENT_DATE" as a reference or sample of proper date selection."""
            else:
                DATE_INSTRUCTION3 = """"""
        else:
            DATE_INSTRUCTION3 = """"""
    elif "oracle" in data_summary.sql_library.lower():
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
            ):
                if (
                    data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower()
                    in ["text"]
                    or "varchar"
                    in data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower()
                ):
                    DATE_INSTRUCTION = """Ensure to convert any date related columns with TEXT / STRING data types to DATE data types. This conversion should be applied in all parts of the SQL query, including the 'WHERE' clause, subqueries, 'CONCAT' function, and any other functions, methods, clauses, or statements, using the 'TO_DATE' function. Make sure that any date-related axes selected are formatted as strings in the final output."""
                else:
                    DATE_INSTRUCTION = """Make sure that any date-related axes selected are formatted as strings in the final output."""
            else:
                DATE_INSTRUCTION = """Make sure that any date-related axes selected are formatted as strings in the final output."""

            if DATE_INSTRUCTION == """""":
                DATE_INSTRUCTION = """Ensuring the correct syntax for date conversion and formatting in all parts of the SQL query is essential to avoid errors and achieve accurate results. When calculating a date interval and formatting it as a string, use the following approach: TO_CHAR(SYSDATE - INTERVAL 'time_period' DAY, 'YYYY-MM-DD'). ENSURE the sql query follows the given time duration in the question and chart title, or do not filter by time if time duration not exist."""
            else:
                DATE_INSTRUCTION += """ Ensuring the correct syntax for date conversion and formatting in all parts of the SQL query is essential to avoid errors and achieve accurate results. When calculating a date interval and formatting it as a string, use the following approach: TO_CHAR(SYSDATE - INTERVAL 'time_period' DAY, 'YYYY-MM-DD'). ENSURE the sql query follows the given time duration in the question and chart title, or do not filter by time if time duration not exist."""

            if timeframe.lower() == "yearly":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "TO_CHAR(EXTRACT(YEAR FROM TO_DATE(\"Date\", 'DD/MM/YYYY')))" as a reference or sample of proper date selection."""
                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "TO_CHAR(EXTRACT(YEAR FROM \"Date\"))" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = """"""
                else:
                    DATE_INSTRUCTION2 = """"""
            elif timeframe.lower() == "quarterly":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "TO_CHAR(EXTRACT(YEAR FROM TO_DATE(\"Date\", 'DD/MM/YYYY'))) || '-Q' || TO_CHAR(TO_DATE(\"Date\", 'DD/MM/YYYY'), 'Q')" as a reference or sample of proper date selection."""
                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "TO_CHAR(EXTRACT(YEAR FROM \"Date\")) || '-Q' || TO_CHAR(\"Date\", 'Q')" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = """"""
                else:
                    DATE_INSTRUCTION2 = """"""

                if DATE_INSTRUCTION2 == """""":
                    DATE_INSTRUCTION2 = """Never use 'YYYY-Qq', 'YYYY-Q%q' and 'YYYY-%q' for formatting quarter dates in your generated SQL queries. Instead, format the quarter dates by correctly combining the year and quarter using the `EXTRACT` and `TO_CHAR` functions, without using any `SUBSTR` function where the date column is formatted as 'YYYY-Q1', 'YYYY-Q2', 'YYYY-Q3', and 'YYYY-Q4'."""
                else:
                    DATE_INSTRUCTION2 += """ Never use 'YYYY-Qq', 'YYYY-Q%q' and 'YYYY-%q' for formatting quarter dates in your generated SQL queries. Instead, format the quarter dates by correctly combining the year and quarter using the `EXTRACT` and `TO_CHAR` functions, without using any `SUBSTR` function where the date column is formatted as 'YYYY-Q1', 'YYYY-Q2', 'YYYY-Q3', and 'YYYY-Q4'."""

            elif timeframe.lower() == "weekly":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "TO_CHAR(EXTRACT(YEAR FROM TO_DATE(\"Date\", 'DD/MM/YYYY'))) || '-W' || TO_CHAR(TO_DATE(\"Date\", 'DD/MM/YYYY'), 'IW')" as a reference or sample of proper date selection."""
                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "TO_CHAR(EXTRACT(YEAR FROM \"Date\")) || '-W' || TO_CHAR(\"Date\", 'IW')" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = """"""
                else:
                    DATE_INSTRUCTION2 = """"""

            elif timeframe.lower() == "daily":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "TO_DATE(\"Date\", 'DD/MM/YYYY')" as a reference or sample of proper date selection."""
                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "TRUNC(\"Date\")" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = """"""
                else:
                    DATE_INSTRUCTION2 = """"""

                if DATE_INSTRUCTION2 == """""":
                    DATE_INSTRUCTION2 = """Avoid using day names in the SQL query."""
                else:
                    DATE_INSTRUCTION2 += """ Avoid using day names in the SQL query."""

            elif timeframe.lower() == "half-yearly":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "TO_CHAR(EXTRACT(YEAR FROM TO_DATE(\"Date\", 'DD/MM/YYYY'))) || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE(\"Date\", 'DD/MM/YYYY'), 'MM')) <= 6 THEN '1' ELSE '2' END" as a reference or sample of proper date selection."""
                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "TO_CHAR(EXTRACT(YEAR FROM \"Date\")) || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(\"Date\", 'MM')) <= 6 THEN '1' ELSE '2' END" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = """"""
                else:
                    DATE_INSTRUCTION2 = """"""

            elif timeframe.lower() == "monthly":
                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                ):
                    if (
                        data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                        in ["text"]
                    ) or (
                        "varchar"
                        in data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()
                    ):
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "TO_CHAR(TO_DATE(\"Date\", 'DD/MM/YYYY'), 'YYYY-MM')" as a reference or sample of proper date selection."""
                    elif data_summary.column_sql_data_types[
                        chart_axis["xAxis_column"]
                    ].lower() in [
                        "datetime",
                        "date",
                    ]:
                        DATE_INSTRUCTION2 = """Use the SQL query snippet "TO_CHAR(\"Date\", 'YYYY-MM')" as a reference or sample of proper date selection."""
                    else:
                        DATE_INSTRUCTION2 = """"""
                else:
                    DATE_INSTRUCTION2 = """"""

                if DATE_INSTRUCTION2 == """""":
                    DATE_INSTRUCTION2 = """Avoid using month names in the SQL query."""
                else:
                    DATE_INSTRUCTION2 += (
                        """ Avoid using month names in the SQL query."""
                    )
            else:
                DATE_INSTRUCTION2 = """"""
        else:
            DATE_INSTRUCTION = """When calculating a date interval for filtering and formatting it as a string, use the following approach: TO_CHAR(SYSDATE - INTERVAL 'time_period' DAY, 'YYYY-MM-DD'). ENSURE the sql query follows the given time duration in the question and chart title, or the default time duration which is "past 1 year" if time duration not exist."""

            DATE_INSTRUCTION2 = """"""

        if (
            isinstance(chart_axis["xAxis_column"], str)
            and chart_axis["xAxis_column"] in data_summary.column_data_tribes.keys()
            and data_summary.column_data_tribes[chart_axis["xAxis_column"]]
            in ["date_related"]
            and chart_axis["xAxis_column"] in data_summary.column_sql_data_types.keys()
            and data_summary.column_sql_data_types[chart_axis["xAxis_column"]].lower()
            not in [
                "tinyint",
                "smallint",
                "mediumint",
                "int",
                "bigint",
                "float",
                "double",
                "decimal",
                "bit",
            ]
        ):
            if time_duration == "Week":
                DATE_INSTRUCTION3 = """If date filtering is required for weekly data, ensure to specify the date range using INTERVAL for weeks, and apply date arithmetic or WHERE BETWEEN functions appropriately. Use the SQL query snippet "WHERE date_column BETWEEN SYSDATE - INTERVAL 'N' WEEK AND SYSDATE" as a reference or sample of proper date selection."""
            elif time_duration == "Month":
                DATE_INSTRUCTION3 = """If date filtering is required for monthly data, ensure to specify the date range using INTERVAL for months, and apply date arithmetic or WHERE BETWEEN functions as needed. Use the SQL query snippet "WHERE date_column BETWEEN ADD_MONTHS(SYSDATE, -N) AND SYSDATE" as a reference or sample of proper date selection."""
            elif time_duration == "Quarter":
                DATE_INSTRUCTION3 = """If date filtering is required for quarterly data, ensure to specify the date range using INTERVAL for months (3 months per quarter), and utilize date arithmetic or WHERE BETWEEN functions accordingly. Use the SQL query snippet "WHERE date_column BETWEEN ADD_MONTHS(SYSDATE, -3*N) AND SYSDATE" as a reference or sample of proper date selection."""
            elif time_duration == "Year":
                DATE_INSTRUCTION3 = """If date filtering is required for yearly data, ensure to specify the date range using INTERVAL for years, and use date arithmetic or WHERE BETWEEN functions as applicable. Use the SQL query snippet "WHERE date_column BETWEEN ADD_MONTHS(SYSDATE, -12*N) AND SYSDATE" as a reference or sample of proper date selection."""
            else:
                DATE_INSTRUCTION3 = """"""
                DATE_INSTRUCTION3 = """"""
        else:
            DATE_INSTRUCTION3 = """"""
    else:
        code_level_logger.error(
            f"{data_summary.sql_library} DB is not supported in generate date instructions!",
        )
        raise RuntimeError(
            f"{data_summary.sql_library} DB is not supported in generate date instructions!",
        )

    return DATE_INSTRUCTION, DATE_INSTRUCTION2, DATE_INSTRUCTION3


def fetch_filtered_feedbacks(question, table_name, logger, db_tag="label1"):
    """
    Fetch and filter feedbacks based on the type, question, table name, and DB tag.
    """
    feedback_data = fetch_feedback("question", question, logger)
    return [
        feedback
        for feedback in filter_feedback(feedback_data, filter_liked=True)
        if "table_name" in feedback.keys()
        and feedback["table_name"] == table_name
        and "db_tag" in feedback.keys()
        and feedback["db_tag"] == db_tag
    ]


def generate_bad_samples(
    data_summary: DataSummary,
    chart_type: str,
    chart_axis: dict,
    chart_title: str,
    question: str,
    timeframe: str,
    time_duration: str,
    table_name: str,
    total_num_tokens: int,
    code_level_logger: logging.Logger,
) -> tuple[str, int]:
    BAD_QUERY_SAMPLES: str = ""
    sample_instruction: str = ""
    TOTAL_NUM_TOKENS_WITH_BAD_SAMPLES: int = total_num_tokens

    DB_TAG = data_summary.database_properties.get("db_tag", "")

    if DB_TAG == "":
        code_level_logger.error("DB_TAG is invalid!")
        raise ValueError("DB_TAG is invalid!")

    chart_feedback_data = fetch_feedback("question", question, logger)

    liked_feedbacks = filter_feedback(chart_feedback_data, filter_liked=True)

    if not liked_feedbacks:
        BAD_QUERY_SAMPLES = ""
        return BAD_QUERY_SAMPLES, TOTAL_NUM_TOKENS_WITH_BAD_SAMPLES

    disliked_feedbacks = filter_feedback(chart_feedback_data, filter_liked=False)

    # Further filter the disliked feedback entries to include only those with selected options or "other" text in feedback fields.
    disliked_feedbacks = filter_feedback_by_options(
        disliked_feedbacks,
        [
            "xaxis_data",
            "yaxis_data",
            "zaxis_data",
            "overall_chart",
        ],
        logger,
    )

    # Get failed SQL query charts data from DB
    disliked_feedbacks += fetch_failed_sql_charts(DB_TAG, table_name)

    filtered_disliked_feedbacks = [
        feedback
        for feedback in disliked_feedbacks
        if "table_name" in feedback.keys()
        and feedback["table_name"] == table_name
        and "db_tag" in feedback.keys()
        and feedback["db_tag"] == DB_TAG
    ]

    sql_library_map = {
        "label1": "MySQL",
        "label5": "SQL Server",
        "label2": "PostgreSQL",
        "label4": "Oracle",
    }

    SQL_LIBRARY = sql_library_map.get(DB_TAG)

    if filtered_disliked_feedbacks:
        BAD_QUERY_SAMPLES = f"""
Enhance your understanding of {SQL_LIBRARY} SQL query structuring, syntax, and writing, with a particular emphasis on date-related formatting, by training using the provided DDL with its respective chart titles and SQL query examples.

DDL:\n
{data_summary.database_schema_sql}

Disallowed Narrative Patterns:
- Please avoid generating responses that resemble any of the following examples, as these have been marked as unsatisfactory by users:"""
        sample_instruction = """\n\n
Take special care to avoid generating responses similar to those listed in the samples above. 
These examples were marked as inadequate because they do not fully align with user intent, lack specificity, 
or fail to provide meaningful information for business decisions."""

    instruction_token_count = calculate_token_usage(
        BAD_QUERY_SAMPLES, sample_instruction
    )

    TOTAL_NUM_TOKENS_WITH_BAD_SAMPLES = total_num_tokens + instruction_token_count

    # If Table Chart
    if chart_type in ["table_chart"]:
        x_column = chart_axis["xAxis_column"]
        if (
            isinstance(x_column, str)
            and x_column in data_summary.column_data_tribes
            and data_summary.column_data_tribes[x_column] == "date_related"
        ):
            timeframes = [
                "yearly",
                "quarterly",
                "half-yearly",
                "monthly",
                "weekly",
                "daily",
            ]
            for tf in timeframes:
                # Handle feedbacks for specific timeframes
                filtered_feedbacks_for_timeframe = [
                    feedback
                    for feedback in filtered_disliked_feedbacks
                    if feedback.get("chart_type") == chart_type
                    and feedback.get("time_frame", "").lower() == tf
                ]

                if filtered_feedbacks_for_timeframe:
                    if x_column in data_summary.column_sql_data_types.keys():
                        for idx, chart in enumerate(
                            filtered_feedbacks_for_timeframe, start=1
                        ):
                            # Generate the bad sample string for the current chart
                            bad_sample = (
                                f"Chart Title {idx}: {chart.get('chart_title', '')}\n"
                                f"SQL Query {idx}: {chart.get('sql_query', '')}\n"
                            )

                            # Calculate the token usage of the bad sample
                            current_token_count = calculate_token_usage(bad_sample)

                            # Check if adding this sample exceeds the token limit
                            if (
                                TOTAL_NUM_TOKENS_WITH_BAD_SAMPLES + current_token_count
                                > TARGET_TOKEN_LIMIT
                            ):
                                break

                            # Append the bad sample and update the token count
                            BAD_QUERY_SAMPLES += bad_sample
                            TOTAL_NUM_TOKENS_WITH_BAD_SAMPLES += current_token_count

        else:
            filtered_feedbacks_by_chart_and_no_timeframe = [
                feedback
                for feedback in filtered_disliked_feedbacks
                if feedback.get("chart_type") == "table_chart"
                and not feedback.get("time_frame", "").strip()
            ]

            if filtered_feedbacks_by_chart_and_no_timeframe:
                for idx, chart in enumerate(
                    filtered_feedbacks_by_chart_and_no_timeframe, start=1
                ):
                    # Generate the bad sample string for the current chart
                    bad_sample = (
                        f"Chart Title {idx}: {chart.get('chart_title', '')}\n"
                        f"SQL Query {idx}: {chart.get('sql_query', '')}\n"
                    )

                    # Calculate the token usage of the bad sample
                    current_token_count = calculate_token_usage(bad_sample)

                    # Check if adding this sample exceeds the token limit
                    if (
                        TOTAL_NUM_TOKENS_WITH_BAD_SAMPLES + current_token_count
                        > TARGET_TOKEN_LIMIT
                    ):
                        break

                    # Append the bad sample and update the token count
                    BAD_QUERY_SAMPLES += bad_sample
                    TOTAL_NUM_TOKENS_WITH_BAD_SAMPLES += current_token_count

        if (
            isinstance(chart_axis["xAxis_column"], str)
            and chart_axis["xAxis_column"] in data_summary.column_data_tribes.keys()
            and data_summary.column_data_tribes[chart_axis["xAxis_column"]]
            in ["date_related"]
            and chart_axis["xAxis_column"] in data_summary.column_sql_data_types.keys()
            and data_summary.column_sql_data_types[chart_axis["xAxis_column"]].lower()
            not in [
                "tinyint",
                "smallint",
                "mediumint",
                "int",
                "bigint",
                "float",
                "double",
                "decimal",
                "bit",
            ]
        ):
            if time_duration in [
                "Week",
                "Month",
                "Quarter",
                "Year",
            ]:
                filtered_feedback = [
                    {
                        "chart_type": chart["chart_type"],
                        "chart_title": chart["chart_title"],
                        "feedback": chart["feedback"],
                    }
                    for chart in filtered_disliked_feedbacks
                    if classify_time_duration(chart["chart_title"], chart["question"])
                    == time_duration
                    and chart["chart_type"] == "table_chart"
                ]

                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                    and filtered_feedback
                ):
                    for idx, chart in enumerate(filtered_feedback, start=1):
                        # Generate the bad sample string for the current chart
                        bad_sample = (
                            f"Chart Title {idx}: {chart.get('chart_title', '')}\n"
                            f"SQL Query {idx}: {chart.get('sql_query', '')}\n"
                        )

                        # Calculate the token usage of the bad sample
                        current_token_count = calculate_token_usage(bad_sample)

                        # Check if adding this sample exceeds the token limit
                        if (
                            TOTAL_NUM_TOKENS_WITH_BAD_SAMPLES + current_token_count
                            > TARGET_TOKEN_LIMIT
                        ):
                            break

                        # Append the bad sample and update the token count
                        BAD_QUERY_SAMPLES += bad_sample
                        TOTAL_NUM_TOKENS_WITH_BAD_SAMPLES += current_token_count

    # Not table chart
    else:
        x_column = chart_axis["xAxis_column"]
        if (
            isinstance(x_column, str)
            and x_column in data_summary.column_data_tribes
            and data_summary.column_data_tribes[x_column] == "date_related"
        ):
            timeframes = [
                "yearly",
                "quarterly",
                "half-yearly",
                "monthly",
                "weekly",
                "daily",
            ]
            for tf in timeframes:
                # Handle feedbacks for specific timeframes
                filtered_feedbacks_for_timeframe = [
                    feedback
                    for feedback in filtered_disliked_feedbacks
                    if feedback.get("chart_type") != "table_chart"
                    and feedback.get("time_frame", "").lower() == tf
                ]

                if filtered_feedbacks_for_timeframe:
                    if x_column in data_summary.column_sql_data_types.keys():
                        for idx, chart in enumerate(
                            filtered_feedbacks_for_timeframe, start=1
                        ):
                            # Generate the bad sample string for the current chart
                            bad_sample = (
                                f"Chart Title {idx}: {chart.get('chart_title', '')}\n"
                                f"SQL Query {idx}: {chart.get('sql_query', '')}\n"
                            )

                            # Calculate the token usage of the bad sample
                            current_token_count = calculate_token_usage(bad_sample)

                            # Check if adding this sample exceeds the token limit
                            if (
                                TOTAL_NUM_TOKENS_WITH_BAD_SAMPLES + current_token_count
                                > TARGET_TOKEN_LIMIT
                            ):
                                break

                            # Append the bad sample and update the token count
                            BAD_QUERY_SAMPLES += bad_sample
                            TOTAL_NUM_TOKENS_WITH_BAD_SAMPLES += current_token_count

        else:
            filtered_feedbacks_by_chart_and_no_timeframe = [
                feedback
                for feedback in filtered_disliked_feedbacks
                if feedback.get("chart_type") != "table_chart"
                and not feedback.get("time_frame", "").strip()
            ]

            if filtered_feedbacks_by_chart_and_no_timeframe:
                for idx, chart in enumerate(
                    filtered_feedbacks_by_chart_and_no_timeframe, start=1
                ):
                    # Generate the bad sample string for the current chart
                    bad_sample = (
                        f"Chart Title {idx}: {chart.get('chart_title', '')}\n"
                        f"SQL Query {idx}: {chart.get('sql_query', '')}\n"
                    )

                    # Calculate the token usage of the bad sample
                    current_token_count = calculate_token_usage(bad_sample)

                    # Check if adding this sample exceeds the token limit
                    if (
                        TOTAL_NUM_TOKENS_WITH_BAD_SAMPLES + current_token_count
                        > TARGET_TOKEN_LIMIT
                    ):
                        break

                    # Append the bad sample and update the token count
                    BAD_QUERY_SAMPLES += bad_sample
                    TOTAL_NUM_TOKENS_WITH_BAD_SAMPLES += current_token_count

        if (
            isinstance(chart_axis["xAxis_column"], str)
            and chart_axis["xAxis_column"] in data_summary.column_data_tribes.keys()
            and data_summary.column_data_tribes[chart_axis["xAxis_column"]]
            in ["date_related"]
            and chart_axis["xAxis_column"] in data_summary.column_sql_data_types.keys()
            and data_summary.column_sql_data_types[chart_axis["xAxis_column"]].lower()
            not in [
                "tinyint",
                "smallint",
                "mediumint",
                "int",
                "bigint",
                "float",
                "double",
                "decimal",
                "bit",
            ]
        ):
            x_column = chart_axis["xAxis_column"]

            if time_duration in [
                "Week",
                "Month",
                "Quarter",
                "Year",
            ]:
                filtered_feedback = [
                    {
                        "chart_type": chart["chart_type"],
                        "chart_title": chart["chart_title"],
                        "feedback": chart["feedback"],
                    }
                    for chart in filtered_disliked_feedbacks
                    if classify_time_duration(chart["chart_title"], chart["question"])
                    == time_duration
                    and chart["chart_type"] != "table_chart"
                ]

                if (
                    chart_axis["xAxis_column"]
                    in data_summary.column_sql_data_types.keys()
                    and filtered_feedback
                ):
                    for idx, chart in enumerate(filtered_feedback, start=1):
                        # Generate the bad sample string for the current chart
                        bad_sample = (
                            f"Chart Title {idx}: {chart.get('chart_title', '')}\n"
                            f"SQL Query {idx}: {chart.get('sql_query', '')}\n"
                        )

                        # Calculate the token usage of the bad sample
                        current_token_count = calculate_token_usage(bad_sample)

                        # Check if adding this sample exceeds the token limit
                        if (
                            TOTAL_NUM_TOKENS_WITH_BAD_SAMPLES + current_token_count
                            > TARGET_TOKEN_LIMIT
                        ):
                            break

                        # Append the bad sample and update the token count
                        BAD_QUERY_SAMPLES += bad_sample
                        TOTAL_NUM_TOKENS_WITH_BAD_SAMPLES += current_token_count

    if BAD_QUERY_SAMPLES:
        BAD_QUERY_SAMPLES += sample_instruction

    return BAD_QUERY_SAMPLES, TOTAL_NUM_TOKENS_WITH_BAD_SAMPLES


def generate_query_samples(
    data_summary: DataSummary,
    chart_type: str,
    chart_axis: dict,
    chart_title: str,
    question: str,
    timeframe: str,
    time_duration: str,
    table_name: str,
    total_num_tokens: int,
    code_level_logger: logging.Logger,
) -> tuple[str, int]:
    QUERY_SAMPLES: str = ""
    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES: int = total_num_tokens

    if (
        "mysql" in data_summary.sql_library.lower()
        or "mariadb" in data_summary.sql_library.lower()
    ):
        filtered_liked_feedbacks = fetch_filtered_feedbacks(
            question, table_name, "label1"
        )

        QUERY_SAMPLES = """
Enhance your understanding of MySQL SQL query structuring, syntax, and writing, with a particular emphasis on date-related formatting, by training using the provided DDL with its respective chart titles and SQL query examples.

DDL:
""" + (
            data_summary.database_schema_sql
            if filtered_liked_feedbacks
            else (
                """
CREATE TABLE `table_name` (
    `Date` DATE,
    `Product` VARCHAR(255),
    `EBIT` DECIMAL(10, 2),
    `Revenue` DECIMAL(10, 2),
    `Cost` DECIMAL(10, 2),
    `Revenue_Broadband` DECIMAL(10, 2),
    `Revenue_Entertainment` DECIMAL(10, 2),
    `Revenue_Mobile` DECIMAL(10, 2),
    `Cost_Broadband` DECIMAL(10, 2),
    `Cost_Entertainment` DECIMAL(10, 2),
    `Cost_Mobile` DECIMAL(10, 2),
    PRIMARY KEY (`Date`, `Product`)
);
"""
                if any(
                    data_type.upper() in {"DATE", "DATETIME", "TIMESTAMP"}
                    for data_type in data_summary.column_sql_data_types.values()
                )
                else """
CREATE TABLE `table_name` (
    `Date` VARCHAR(255),
    `Product` VARCHAR(255),
    `EBIT` DECIMAL(10, 2),
    `Revenue` DECIMAL(10, 2),
    `Cost` DECIMAL(10, 2),
    `Earning_per_Cost` DECIMAL(10, 2),
    `Cost_Efficiency` DECIMAL(10, 2),
    `Revenue_Broadband` DECIMAL(10, 2),
    `Revenue_Entertainment` DECIMAL(10, 2),
    `Revenue_Mobile` DECIMAL(10, 2),
    `Cost_Broadband` DECIMAL(10, 2),
    `Cost_Entertainment` DECIMAL(10, 2),
    `Cost_Mobile` DECIMAL(10, 2),
    `Revenue_per_Day` DECIMAL(10, 2),
    `CostVariance_Actual_vs_Budget` DECIMAL(10, 2)
);
"""
            )
        )

        # If Table Chart
        if chart_type in ["table_chart"]:
            x_column = chart_axis["xAxis_column"]
            if (
                isinstance(x_column, str)
                and x_column in data_summary.column_data_tribes
                and data_summary.column_data_tribes[x_column] == "date_related"
            ):
                if timeframe.lower() == "yearly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for Yearly timeframe feedbacks
                        filtered_feedbacks_by_chart_and_yearly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "yearly"
                        ]

                        if not filtered_feedbacks_by_chart_and_yearly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Total Revenue by Product Over the Last 5 Years
SQL Query 1: SELECT CAST(YEAR(STR_TO_DATE(t1.`Date`, '%Y-%m-%d')) AS CHAR) AS `Year`, t1.`Product` AS `Product`, SUM(t1.`Revenue`) AS `Total Revenue` FROM `database_name`.`table_name` t1 JOIN `database_name`.`table_name` t2  ON STR_TO_DATE(t1.`Date`, '%Y-%m-%d') = STR_TO_DATE(t2.`Date`, '%Y-%m-%d') AND t1.`Product` = t2.`Product` WHERE STR_TO_DATE(t1.`Date`, '%Y-%m-%d') >= DATE_SUB(CURDATE(), INTERVAL 5 YEAR) GROUP BY `Year`, `Product` ORDER BY `Year` ASC, `Product`;

Chart Title 2: Yearly Breakdown of Cost and Revenue for Each Product Over the Last 5 Years
SQL Query 2: SELECT CAST(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) AS CHAR) AS `Year`, 'Product' AS `Product`, SUM(`Cost_Entertainment` + `Cost_Mobile` + `Cost_Broadband`) AS `Total Cost`, SUM(`Revenue_Entertainment` + `Revenue_Broadband`) AS `Total Revenue` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= DATE_SUB(CURDATE(), INTERVAL 5 YEAR) GROUP BY `Year`, `Product` ORDER BY `Year` ASC, `Product`;

Chart Title 3: Yearly Average Revenue per Day by Product Over the Last 5 Years
SQL Query 3: SELECT CAST(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) AS CHAR) AS `Year`, 'Product' AS `Product`, AVG(`Revenue_per_Day`) AS `Average Revenue per Day` FROM `database_name`.`table_name` WHERE YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) >= YEAR(CURDATE()) - 5 GROUP BY `Year`, `Product` ORDER BY `Year` ASC, `Product`;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Sum of Revenue by Product for the Last 5 Years
SQL Query 1: SELECT CAST(YEAR(t1.`Date`) AS CHAR) AS `Year`, t1.Product AS `Product`, SUM(t1.`Revenue`) AS `Total Revenue` FROM `database_name`.`table_name` t1 JOIN `database_name`.`table_name` t2 ON t1.`Date` = t2.`Date` AND t1.`Product` = t2.`Product` WHERE YEAR(t1.`Date`) >= YEAR(CURDATE()) - 5 GROUP BY `Year`, `Product` ORDER BY `Year` ASC, `Product`;

Chart Title 2: Yearly Average EBIT Across All Products Over the Last 3 Years
SQL Query 2: SELECT CAST(YEAR(`Date`) AS CHAR) AS `Year`, AVG(`EBIT`) AS `Average EBIT` FROM `database_name`.`table_name` WHERE YEAR(`Date`) >= YEAR(CURDATE()) - 3 GROUP BY `Year` ORDER BY `Year` ASC;

Chart Title 3: Yearly Growth in Broadband Revenue Across All Products Over the Last 6 Years
SQL Query 3: SELECT CAST(YEAR(`Date`) AS CHAR) AS `Year`, (SUM(`Revenue_Broadband`) / LAG(SUM(`Revenue_Broadband`), 1) OVER (ORDER BY YEAR(`Date`)) - 1) * 100 AS `Broadband Revenue Growth (%)` FROM `database_name`.`table_name` WHERE YEAR(`Date`) >= YEAR(CURDATE()) - 6 GROUP BY `Year` ORDER BY `Year` ASC;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_yearly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "half-yearly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for half-yearly timeframe feedbacks
                        filtered_feedbacks_by_chart_and_half_yearly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "half-yearly"
                        ]

                        if not filtered_feedbacks_by_chart_and_half_yearly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Half-Yearly Sum of Revenue per Day and EBIT for the Last 2 Half-Years
SQL Query 1: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-H', IF(MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y')) <= 6, 1, 2)) AS `Half-Year`, SUM(`Revenue_per_Day`) AS `Total Revenue per Day`, SUM(`EBIT`) AS `Total EBIT` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) GROUP BY `Half-Year` ORDER BY `Half-Year`;

Chart Title 2: Half-Yearly Average Earning per Cost by Product Over the Last Year
SQL Query 2: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-H', IF(MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y')) <= 6, 1, 2)) AS `Half-Year`, AVG(`Earning_per_Cost`) AS `Average Earning per Cost`, 'Product' AS `Product` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) GROUP BY `Half-Year`, `Product` ORDER BY `Half-Year`;

Chart Title 3: Half-Yearly Variance in Cost Actual vs. Budget by Product for Past 1 Year
SQL Query 3: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-H', IF(MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y')) <= 6, 1, 2)) AS `Half-Year`, SUM(`CostVariance_Actual_vs_Budget`) AS `Total Cost Variance (Actual vs. Budget)`, 'Product' AS `Product` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) GROUP BY `Half-Year`, `Product` ORDER BY `Half-Year`;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Half-Yearly Average EBIT and Revenue for the Last 3 Years
SQL Query 1: SELECT CONCAT(YEAR(`Date`), '-H', IF(MONTH(`Date`) <= 6, 1, 2)) AS `Half-Year`, AVG(`EBIT`) AS `Average EBIT`, AVG(`Revenue`) AS `Average Revenue` FROM `database_name`.`table_name` WHERE `Date` >= DATE_SUB(CURDATE(), INTERVAL 3 YEAR) GROUP BY `Half-Year` ORDER BY `Half-Year`;

Chart Title 2: Half-Yearly Growth Rate of Broadband Revenue Compared to Entertainment Revenue for the Last 4 Years
SQL Query 2: SELECT CONCAT(YEAR(`Date`), '-H', IF(MONTH(`Date`) <= 6, 1, 2)) AS `Half-Year`, (SUM(`Revenue_Broadband`) / LAG(SUM(`Revenue_Broadband`)) OVER (ORDER BY YEAR(`Date`), IF(MONTH(`Date`) <= 6, 1, 2))) * 100 AS `Broadband Revenue Growth Rate (%)`, (SUM(`Revenue_Entertainment`) / LAG(SUM(`Revenue_Entertainment`)) OVER (ORDER BY YEAR(`Date`), IF(MONTH(`Date`) <= 6, 1, 2))) * 100 AS `Entertainment Revenue Growth Rate (%)` FROM `database_name`.`table_name` WHERE `Date` >= DATE_SUB(CURDATE(), INTERVAL 4 YEAR) GROUP BY `Half-Year` ORDER BY `Half-Year`;

Chart Title 3: Half-Yearly EBIT to Revenue Ratio and Total Cost of Broadband for the Past 2 Years
SQL Query 3: SELECT CONCAT(YEAR(`Date`), '-H', IF(MONTH(`Date`) <= 6, 1, 2)) AS `Half-Year`, (SUM(`EBIT`) / SUM(`Revenue`)) * 100 AS `EBIT to Revenue Ratio (%)`, SUM(`Cost_Broadband`) AS `Total Broadband Cost` FROM `database_name`.`table_name` WHERE `Date` >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR) GROUP BY `Half-Year` ORDER BY `Half-Year`;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_half_yearly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "quarterly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for quarterly timeframe feedbacks
                        filtered_feedbacks_by_chart_and_quarterly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "quarterly"
                        ]

                        if not filtered_feedbacks_by_chart_and_quarterly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Sum of Cost Variance (Actual vs. Budget) by Product for the Past 3 Quarters
Sql Query 1: SELECT CONCAT(YEAR(STR_TO_DATE(t1.`Date`, '%Y-%m-%d')), '-Q', QUARTER(STR_TO_DATE(t1.`Date`, '%Y-%m-%d'))) AS `Quarter`, t1.`Product` AS `Product`, SUM(t1.`CostVariance_Actual_vs_Budget`) AS `Total Cost Variance: Actual vs Budget` FROM  `database_name`.`table_name` t1 JOIN `database_name`.`table_name` t2 ON STR_TO_DATE(t1.`Date`, '%Y-%m-%d') = STR_TO_DATE(t2.`Date`, '%Y-%m-%d') AND t1.`Product` = t2.`Product` WHERE STR_TO_DATE(t1.`Date`, '%Y-%m-%d') >= DATE_SUB(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 3 QUARTER) AND STR_TO_DATE(t1.`Date`, '%Y-%m-%d') <= DATE_FORMAT(CURDATE(), '%Y-%m-31') GROUP BY `Quarter`, `Product` ORDER BY `Quarter`, `Product`;

Chart Title 2: Quarterly Average Cost Efficiency Across All Products for the Last 6 Quarters
SQL Query 2: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-Q', QUARTER(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `Quarter`, AVG(`Cost_Efficiency`) AS `Average Cost Efficiency` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= DATE_SUB(CURDATE(), INTERVAL 1.5 YEAR) GROUP BY `Quarter` ORDER BY `Quarter`;

Chart Title 3: Quarterly Growth Rate of Broadband Revenue Compared to the Previous Quarter
SQL Query 3: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-Q', QUARTER(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `Quarter`, (SUM(`Revenue_Broadband`) / LAG(SUM(`Revenue_Broadband`)) OVER (ORDER BY YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), QUARTER(STR_TO_DATE(`Date`, '%d/%m/%Y'))) - 1) * 100 AS `Broadband Revenue Growth (%)` FROM `database_name`.`table_name` GROUP BY `Quarter` ORDER BY `Quarter`;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Sum of Entertainment Costs for 2022
Sql Query 1: SELECT CONCAT(YEAR(t1.`Date`), '-Q', QUARTER(t1.`Date`)) AS `Quarter`, SUM(t1.`Cost_Entertainment`) AS `Total Entertainment Costs` FROM `database_name`.`table_name` t1 JOIN `database_name`.`table_name` t2 ON t1.`Date` = t2.`Date` WHERE t1.`Date` BETWEEN STR_TO_DATE('2022-01-01', '%Y-%m-%d') AND STR_TO_DATE('2022-12-31', '%Y-%m-%d') GROUP BY `Quarter` ORDER BY `Quarter`;

Chart Title 2: Quarterly Average Revenue per Product for the Past 4 Quarters
SQL Query 2: SELECT CONCAT(YEAR(`Date`), '-Q', QUARTER(`Date`)) AS `Quarter`, 'Product' AS `Product`, AVG(`Revenue`) AS `Average Revenue` FROM `database_name`.`table_name` WHERE `Date` >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) GROUP BY `Quarter`, `Product` ORDER BY `Quarter`, `Product`;

Chart Title 3: Quarterly EBIT Margin (EBIT as a Percentage of Revenue) Over the Last 8 Quarters
SQL Query 3: SELECT CONCAT(YEAR(`Date`), '-Q', QUARTER(`Date`)) AS `Quarter`, (SUM(`EBIT`) / SUM(`Revenue`)) * 100 AS `EBIT Margin (%)` FROM `database_name`.`table_name` WHERE `Date` >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR) GROUP BY `Quarter` ORDER BY `Quarter`;
"""

                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_quarterly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "monthly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for monthly timeframe feedbacks
                        filtered_feedbacks_by_chart_and_monthly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "monthly"
                        ]

                        if not filtered_feedbacks_by_chart_and_monthly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Cost Variance (Actual vs. Budget) by Product (Last Year)
Sql Query 1: SELECT CONCAT(YEAR(STR_TO_DATE(t1.`Date`, '%Y-%m-%d')), '-M', MONTH(STR_TO_DATE(t1.`Date`, '%Y-%m-%d'))) AS `Month`, SUM(t1.`CostVariance_Actual_vs_Budget`) AS `Total Cost Variance (Actual vs. Budget)`, t1.`Product` AS `Product` FROM `database_name`.`table_name` t1 JOIN `database_name`.`table_name` t2 ON STR_TO_DATE(t1.`Date`, '%Y-%m-%d') = STR_TO_DATE(t2.`Date`, '%Y-%m-%d') WHERE YEAR(STR_TO_DATE(t1.`Date`, '%Y-%m-%d')) = YEAR(DATE_SUB(CURDATE(), INTERVAL 1 YEAR)) GROUP BY `Month`, `Product` ORDER BY `Month`;

Chart Title 2: Monthly Total Cost Variance (Actual vs. Budget) by Product for the Current and Previous Year
Sql Query 2: SELECT CONCAT(EXTRACT(YEAR FROM STR_TO_DATE(`Date`, '%d/%m/%Y')), '-M', EXTRACT(MONTH FROM STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `Month`, SUM(`CostVariance_Actual_vs_Budget`) AS `Total Cost Variance (Actual vs. Budget)`, `Product` AS `Product` FROM `database_name`.`table_name` WHERE EXTRACT(YEAR FROM STR_TO_DATE(`Date`, '%d/%m/%Y')) >= EXTRACT(YEAR FROM DATE_SUB(CURDATE(), INTERVAL 1 YEAR)) AND EXTRACT(YEAR FROM STR_TO_DATE(`Date`, '%d/%m/%Y')) <= EXTRACT(YEAR FROM CURDATE()) GROUP BY `Month`, `Product` ORDER BY `Month`;

Chart Title 3: Monthly Total Entertainment Costs and Cost Efficiency Ratio for the Last 3 Months
SQL Query 3: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-M', MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `Month`, SUM(`Cost_Entertainment`) AS `Total Entertainment Costs`, AVG(`Cost_Efficiency`) AS `Average Cost Efficiency Ratio` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH) GROUP BY `Month` ORDER BY `Month`;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue for Broadband and Entertainment for the Current and Previous Year
Sql Query 1: SELECT CONCAT(YEAR(`Date`), '-M', MONTH(`Date`)) AS `Month`, SUM(`Revenue_Broadband`) AS `Total Revenue`, 'Broadband' AS `Product` FROM `database_name`.`table_name` WHERE YEAR(`Date`) >= YEAR(DATE_SUB(CURDATE(), INTERVAL 1 YEAR)) AND YEAR(`Date`) <= YEAR(CURDATE()) AND `Revenue_Broadband` IS NOT NULL GROUP BY `Month`, `Revenue Type` UNION ALL SELECT CONCAT(YEAR(`Date`), '-M', MONTH(`Date`)) AS `Month`, SUM(`Revenue_Entertainment`) AS `Total Revenue`, `Entertainment` AS `Product` FROM `database_name`.`table_name` WHERE YEAR(`Date`) >= YEAR(DATE_SUB(CURDATE(), INTERVAL 1 YEAR)) AND YEAR(`Date`) <= YEAR(CURDATE()) AND `Revenue_Entertainment` IS NOT NULL GROUP BY `Month`, `Revenue Type` ORDER BY `Month`;

Chart Title 2: Monthly Sum of Mobile Costs for Next Year
Sql Query 2: SELECT CONCAT(EXTRACT(YEAR FROM `Date`), '-M', EXTRACT(MONTH FROM `Date`)) AS `Month`, SUM(`Cost_Mobile`) AS `Total Mobile Costs` FROM `database_name`.`table_name` WHERE EXTRACT(YEAR FROM `Date`) = EXTRACT(YEAR FROM DATE_ADD(CURDATE(), INTERVAL 1 YEAR)) GROUP BY `Month` ORDER BY `Month`;

Chart Title 3: Monthly Revenue Growth Rate (Percentage Increase) for Entertainment Over the Last 12 Months
SQL Query 3: SELECT CONCAT(YEAR(t1.`Date`), '-M', MONTH(t1.`Date`)) AS `Month`, ((SUM(t1.`Revenue_Entertainment`) - SUM(t2.`Revenue_Entertainment`)) / SUM(t2.`Revenue_Entertainment`)) * 100 AS `Revenue Growth Rate (%)` FROM `database_name`.`table_name` t1 LEFT JOIN `database_name`.`table_name` t2 ON t1.`Date` = DATE_SUB(t2.`Date`, INTERVAL 1 MONTH) WHERE t1.`Date` >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH) GROUP BY `Month` ORDER BY `Month`;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_monthly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "weekly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for weekly timeframe feedbacks
                        filtered_feedbacks_by_chart_and_weekly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "weekly"
                        ]

                        if not filtered_feedbacks_by_chart_and_weekly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Average Cost Efficiency by Product for the Last 12 Weeks
SQL Query 1: SELECT CONCAT(YEAR(STR_TO_DATE(t1.`Date`, '%Y-%m-%d')), '-W', WEEK(STR_TO_DATE(t1.`Date`, '%Y-%m-%d'))) AS `Week`, t1.`Product` AS `Product`, AVG(t1.`Cost_Efficiency`) AS `Average Cost Efficiency` FROM `database_name`.`table_name` t1 JOIN `database_name`.`table_name` t2 ON STR_TO_DATE(t1.`Date`, '%Y-%m-%d') = STR_TO_DATE(t2.`Date`, '%Y-%m-%d') AND t1.`Product` = t2.`Product` WHERE STR_TO_DATE(t1.`Date`, '%Y-%m-%d') >= DATE_SUB(CURDATE(), INTERVAL 12 WEEK) GROUP BY `Week`, `Product` ORDER BY `Week`, `Product`;

Chart Title 2: Weekly Sum of Revenue and Cost Variance (Actual vs. Budget) Over the Past 8 Weeks
SQL Query 2: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-W', WEEK(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `Week`, SUM(`Revenue`) AS `Total Revenue`, SUM(`CostVariance_Actual_vs_Budget`) AS `Cost Variance (Actual vs. Budget)` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= DATE_SUB(CURDATE(), INTERVAL 8 WEEK) GROUP BY `Week` ORDER BY `Week`;

Chart Title 3: Weekly EBIT Margin (EBIT as a Percentage of Revenue) Over the Last 10 Weeks
SQL Query 3: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-W', WEEK(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `Week`, (SUM(`EBIT`) / SUM(`Revenue`)) * 100 AS `EBIT Margin (%)` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= DATE_SUB(CURDATE(), INTERVAL 10 WEEK) GROUP BY `Week` ORDER BY `Week`;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Revenue for Entertainment in Quarter 4 in Year 2023
SQL Query 1: SELECT CONCAT(YEAR(t1.`Date`), '-W', WEEK(t1.`Date`)) AS `Week`, SUM(t1.`Revenue_Entertainment`) AS `Entertainment Revenue` FROM `database_name`.`table_name` t1 JOIN `database_name`.`table_name` t2 ON t1.`Date` = t2.`Date` WHERE YEAR(t1.`Date`) = 2023 AND QUARTER(t1.`Date`) = 4 GROUP BY `Week` ORDER BY `Week`;

Chart Title 2: Weekly Ratio of Entertainment Costs to Total Revenue Over the Past 12 Weeks
SQL Query 2: SELECT CONCAT(YEAR(`Date`), '-W', WEEK(`Date`)) AS `Week`, (SUM(`Cost_Entertainment`) / SUM(`Revenue`)) * 100 AS `Entertainment Costs to Total Revenue Ratio (%)` FROM `database_name`.`table_name` WHERE `Date` >= DATE_SUB(CURDATE(), INTERVAL 12 WEEK GROUP BY `Week` ORDER BY `Week`;

Chart Title 3: Weekly Variance in Mobile Costs and Broadband Costs for the Last 10 Weeks
SQL Query 3: SELECT CONCAT(YEAR(`Date`), '-W', WEEK(`Date`)) AS `Week`, VARIANCE(`Cost_Mobile`) AS `Variance in Mobile Costs`, VARIANCE(`Cost_Broadband`) AS `Variance in Broadband Costs` FROM `database_name`.`table_name` WHERE `Date` >= DATE_SUB(CURDATE(), INTERVAL 10 WEEK) GROUP BY `Week` ORDER BY `Week`;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_weekly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "daily":
                    if (
                        chart_axis["xAxis_column"]
                        in data_summary.column_sql_data_types.keys()
                    ):
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for daily timeframe feedbacks
                        filtered_feedbacks_by_chart_and_daily_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "daily"
                        ]

                        if not filtered_feedbacks_by_chart_and_daily_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Daily Average Cost Efficiency and Earnings per Cost Over the Last 30 Days
SQL Query 1: SELECT DATE(STR_TO_DATE(t1.`Date`, '%Y-%m-%d')) AS `Date`, AVG(t1.`Cost_Efficiency`) AS `Average Cost Efficiency`, AVG(t1.`Earning_per_Cost`) AS `Average Earnings per Cost` FROM `database_name`.`table_name` t1 JOIN `database_name`.`table_name` t2 ON STR_TO_DATE(t1.`Date`, '%Y-%m-%d') = STR_TO_DATE(t2.`Date`, '%Y-%m-%d') WHERE STR_TO_DATE(t1.`Date`, '%Y-%m-%d') >= CURDATE() - INTERVAL 30 DAY GROUP BY `Date` ORDER BY `Date`;

Chart Title 2: Daily Sum of Revenue and Cost for the Last 2 Weeks
SQL Query 2: SELECT DATE(STR_TO_DATE(`Date`, '%d/%m/%Y')) AS `Date`, SUM(`Revenue`) AS `Total Revenue`, SUM(`Cost`) AS `Total Cost` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= CURDATE() - INTERVAL 14 DAY GROUP BY `Date` ORDER BY `Date`;

Chart Title 3: Daily Change in EBIT (Day-over-Day Difference) for the Past 10 Days
SQL Query 3: SELECT DATE(STR_TO_DATE(`Date`, '%d/%m/%Y')) AS `Date`, `EBIT` - LAG(`EBIT`, 1) OVER (ORDER BY DATE(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `Day-over-Day Change in EBIT` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= CURDATE() - INTERVAL 10 DAY ORDER BY `Date`;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Daily Cost of Entertainment vs. Cost of Mobile for the Last 7 Days
SQL Query 1: SELECT DATE(t1.`Date`) AS `Date`, SUM(t1.`Cost_Entertainment`) AS `Total Cost of Entertainment`, SUM(t1.`Cost_Mobile`) AS `Total Cost of Mobile` FROM `database_name`.`table_name` t1 JOIN `database_name`.`table_name` t2 ON t1.`Date` = t2.`Date` WHERE t1.`Date` >= CURDATE() - INTERVAL 7 DAY GROUP BY `Date` ORDER BY `Date`;

Chart Title 2: Daily EBIT to Revenue Ratio (EBIT as a Percentage of Revenue) for the Last 14 Days
SQL Query 2: SELECT DATE(`Date`) AS `Date`, (SUM(`EBIT`) / NULLIF(SUM(`Revenue`), 0)) * 100 AS `EBIT to Revenue Ratio (%)` FROM `database_name`.`table_name` WHERE `Date` >= CURDATE() - INTERVAL 14 DAY GROUP BY `Date` ORDER BY `Date`;

Chart Title 3: Daily Total Revenue vs. Total Cost for the Last 60 Days
SQL Query 3: SELECT DATE(`Date`) AS `Date`, SUM(`Revenue`) AS `Total Revenue`, SUM(`Cost_Broadband` + `Cost_Entertainment` + `Cost_Mobile`) AS `Total Cost` FROM `database_name`.`table_name` WHERE `Date` >= CURDATE() - INTERVAL 60 DAY GROUP BY `Date` ORDER BY `Date`;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_daily_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

            else:
                filtered_feedbacks_by_chart_and_no_timeframe = [
                    feedback
                    for feedback in filtered_liked_feedbacks
                    if feedback.get("chart_type") == "table_chart"
                    and not feedback.get("time_frame", "").strip()
                ]

                if not filtered_feedbacks_by_chart_and_no_timeframe:
                    QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Top 5 Products by Percentage of Total EBIT
Sql Query 1: SELECT `Product` AS `Product`, (SUM(`EBIT`) / SUM(SUM(`EBIT`)) OVER ()) * 100 AS `Percentage of Total EBIT` FROM `database_name`.`table_name` GROUP BY `Product` ORDER BY `Percentage of Total EBIT` DESC LIMIT 5;

Chart Title 2: Top 3 Products that Generate the Highest Revenue
Sql Query 2: SELECT `Product` AS `Product`, SUM(`Revenue`) AS `Total Revenue` FROM `database_name`.`table_name` GROUP BY `Product` ORDER BY `Total Revenue` DESC LIMIT 3;

Chart Title 3: Total Revenue Generated by Broadband Product
Sql Query 3: SELECT `Broadband` AS `Product`, SUM(`Revenue_Broadband`) AS `Total Revenue` FROM `database_name`.`table_name`;

Chart Title 4: Total Cost Incurred by Entertainment and Broadband Respectively
Sql Query 4: SELECT 'Entertainment' AS `Product`, SUM(`Cost_Entertainment`) AS `Total Cost` FROM `database_name`.`table_name` UNION ALL SELECT 'Broadband' AS `Product`, SUM(`Cost_Broadband`) AS `Total Cost` FROM `database_name`.`table_name`;

Based on DDL 2, here are the chart titles and sql queries.

Chart Title 1: Top 5 Products by Percentage of Total EBIT
Sql Query 1: SELECT `Product` AS `Product`, (SUM(`EBIT`) / SUM(SUM(`EBIT`)) OVER ()) * 100 AS `Percentage of Total EBIT` FROM `database_name`.`table_name` GROUP BY `Product` ORDER BY `Percentage of Total EBIT` DESC LIMIT 5;

Chart Title 2: Top 3 Products that Generate the Highest Revenue
Sql Query 2: SELECT `Product` AS `Product`, SUM(`Revenue`) AS `Total Revenue` FROM `database_name`.`table_name` GROUP BY `Product` ORDER BY `Total Revenue` DESC LIMIT 3;

Chart Title 3: Total Revenue Generated by Broadband Product
Sql Query 3: SELECT 'Broadband' AS `Product`, SUM(`Revenue_Broadband`) AS `Total Revenue` FROM `database_name`.`table_name`;

Chart Title 4: Total Cost Incurred by Entertainment and Broadband Respectively
Sql Query 4: SELECT 'Entertainment' AS `Product`, SUM(`Cost_Entertainment`) AS `Total Cost` FROM `database_name`.`table_name` UNION ALL SELECT 'Broadband' AS `Product`, SUM(`Cost_Broadband`) AS `Total Cost` FROM `database_name`.`table_name`;

"""
                else:
                    # Only append this line if token count allows
                    heading = "\nHere are the chart titles and sql queries\n"
                    new_data_tokens = calculate_token_usage(heading)
                    if (
                        TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                        <= TARGET_TOKEN_LIMIT
                    ):
                        QUERY_SAMPLES += heading
                        TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                    for idx, chart in enumerate(
                        filtered_feedbacks_by_chart_and_no_timeframe,
                        start=1,
                    ):
                        chart_title = chart.get("chart_title", "")
                        sql_query = chart.get("sql_query", "")
                        sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                        # Calculate token usage for the current chart and SQL query
                        new_data_tokens = calculate_token_usage(sample)

                        # Check if appending this data would exceed the token limit
                        if (
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                            <= TARGET_TOKEN_LIMIT
                        ):
                            QUERY_SAMPLES += sample

                            # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                        else:
                            # If appending would exceed, break the loop
                            break

            if (
                isinstance(chart_axis["xAxis_column"], str)
                and chart_axis["xAxis_column"] in data_summary.column_data_tribes.keys()
                and data_summary.column_data_tribes[chart_axis["xAxis_column"]]
                in ["date_related"]
                and chart_axis["xAxis_column"]
                in data_summary.column_sql_data_types.keys()
                and data_summary.column_sql_data_types[
                    chart_axis["xAxis_column"]
                ].lower()
                not in [
                    "tinyint",
                    "smallint",
                    "mediumint",
                    "int",
                    "bigint",
                    "float",
                    "double",
                    "decimal",
                    "bit",
                ]
            ):
                if time_duration == "Week":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Week"
                        and chart["chart_type"] == "table_chart"
                    ]

                    if (
                        chart_axis["xAxis_column"]
                        in data_summary.column_sql_data_types.keys()
                    ):
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Total Revenue by Product for the Past 2 Weeks
SQL Query 1: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-W', WEEK(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `Week`, SUM(`Revenue`) AS `Total Revenue`, `Product` AS `Product` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') BETWEEN CURDATE() - INTERVAL 2 WEEK AND CURDATE() GROUP BY `Week`, `Product` ORDER BY `Week` ASC, `Product`;

Chart Title 2: Weekly Average EBIT for Next 3 Weeks
SQL Query 2: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-W', WEEK(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `Week`, AVG(`EBIT`) AS `Average EBIT` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') BETWEEN CURDATE() AND CURDATE() + INTERVAL 3 WEEK GROUP BY `Week` ORDER BY `Week`;

Chart Title 3: Weekly Total Cost of Entertainment for Last Week
SQL Query 3: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-W', WEEK(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `Week`, SUM(`Cost_Entertainment`) AS `Total Cost of Entertainment` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') BETWEEN CURDATE() - INTERVAL 1 WEEK AND CURDATE() GROUP BY `Week` ORDER BY `Week`;

Chart Title 4: Weekly Maximum Revenue from Week 1 - Week 4 in March 2023
SQL Query 4: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-W', WEEK(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `Week`, MAX(`Revenue`) AS `Maximum Revenue` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') BETWEEN STR_TO_DATE('2023-03-01', '%Y-%m-%d') AND STR_TO_DATE('2023-03-31', '%Y-%m-%d') AND WEEK(STR_TO_DATE(`Date`, '%d/%m/%Y')) BETWEEN 1 AND 4 GROUP BY `Week` ORDER BY `Week`;

"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Total Revenue by Product for the Past 2 Weeks
SQL Query 1: SELECT CONCAT(YEAR(`Date`), '-W', WEEK(`Date`)) AS `Week`, SUM(`Revenue`) AS `Total Revenue`, `Product` AS `Product` FROM `database_name`.`table_name` WHERE `Date` BETWEEN CURDATE() - INTERVAL 2 WEEK AND CURDATE() GROUP BY `Week`, `Product` ORDER BY `Week` ASC, `Product`;

Chart Title 2: Weekly Average EBIT for Next 3 Weeks
SQL Query 2: SELECT CONCAT(YEAR(`Date`), '-W', WEEK(`Date`)) AS `Week`, AVG(`EBIT`) AS `Average EBIT` FROM `database_name`.`table_name` WHERE `Date` BETWEEN CURDATE() AND CURDATE() + INTERVAL 3 WEEK GROUP BY `Week` ORDER BY `Week`;

Chart Title 3: Weekly Total Cost of Entertainment for Last Week
SQL Query 3: SELECT CONCAT(YEAR(`Date`), '-W', WEEK(`Date`)) AS `Week`, SUM(`Cost_Entertainment`) AS `Total Cost of Entertainment` FROM `database_name`.`table_name` WHERE `Date` BETWEEN CURDATE() - INTERVAL 1 WEEK AND CURDATE() GROUP BY `Week` ORDER BY `Week`;

Chart Title 4: Weekly Maximum Revenue from Week 1 - Week 4 in March 2023
SQL Query 4: SELECT CONCAT(YEAR(`Date`), '-W', WEEK(`Date`)) AS `Week`, MAX(`Revenue`) AS `Maximum Revenue` FROM `database_name`.`table_name` WHERE `Date` BETWEEN '2023-03-01' AND '2023-03-31' AND WEEK(`Date`) BETWEEN 1 AND 4 GROUP BY `Week` ORDER BY `Week`;

"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif time_duration == "Month":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Month"
                        and chart["chart_type"] == "table_chart"
                    ]

                    if (
                        chart_axis["xAxis_column"]
                        in data_summary.column_sql_data_types.keys()
                    ):
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue by Product for the Past 6 Months
SQL Query 1: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-M', MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `Month`, SUM(`Revenue`) AS `Total Revenue`, `Product` AS `Product` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= CURDATE() - INTERVAL 6 MONTH GROUP BY `Month`, `Product` ORDER BY `Month` ASC, `Product`;

Chart Title 2: Monthly Average EBIT for Next January
SQL Query 2: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-M', MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `Month`, AVG(`EBIT`) AS `Average EBIT` FROM `database_name`.`table_name` WHERE YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) = YEAR(CURDATE() + INTERVAL 1 YEAR) AND MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y')) = 1 GROUP BY `Month` ORDER BY `Month`;

Chart Title 3: Monthly Cost of Entertainment for March
SQL Query 3: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-M', MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `Month`, SUM(`Cost_Entertainment`) AS `Total Cost of Entertainment` FROM `database_name`.`table_name` WHERE MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y')) = 3 AND YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) = YEAR(CURDATE()) GROUP BY `Month` ORDER BY `Month`;

Chart Title 4: Monthly Revenue from Jan 2022 - Mar 2022
SQL Query 4: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-M', MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `Month`, SUM(`Revenue`) AS `Total Revenue` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') BETWEEN STR_TO_DATE('2022-01-01', '%Y-%m-%d') AND STR_TO_DATE('2022-03-31', '%Y-%m-%d')  GROUP BY `Month` ORDER BY `Month`;

"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue by Product for the Past 6 Months
SQL Query 1: SELECT CONCAT(YEAR(`Date`), '-M', MONTH(`Date`)) AS `Month`, SUM(`Revenue`) AS `Total Revenue`, `Product` AS `Product` FROM `database_name`.`table_name` WHERE `Date` >= CURDATE() - INTERVAL 6 MONTH GROUP BY `Month`, `Product` ORDER BY `Month` ASC, `Product`;

Chart Title 2: Monthly Average EBIT for Next January
SQL Query 2: SELECT CONCAT(YEAR(`Date`), '-M', MONTH(`Date`)) AS `Month`, AVG(`EBIT`) AS `Average EBIT` FROM `database_name`.`table_name` WHERE YEAR(`Date`) = YEAR(CURDATE() + INTERVAL 1 YEAR) AND MONTH(`Date`) = 1 GROUP BY `Month` ORDER BY `Month`;

Chart Title 3: Monthly Cost of Entertainment for March
SQL Query 3: SELECT CONCAT(YEAR(`Date`), '-M', MONTH(`Date`)) AS `Month`, SUM(`Cost_Entertainment`) AS `Total Cost of Entertainment` FROM `database_name`.`table_name` WHERE MONTH(`Date`) = 3 AND YEAR(`Date`) = YEAR(CURDATE()) GROUP BY `Month` ORDER BY `Month`;

Chart Title 4: Monthly Revenue from Jan 2022 - Mar 2022
SQL Query 4: SELECT CONCAT(YEAR(`Date`), '-M', MONTH(`Date`)) AS `Month`, SUM(`Revenue`) AS `Total Revenue` FROM `database_name`.`table_name` WHERE `Date` BETWEEN STR_TO_DATE('2022-01-01', '%Y-%m-%d') AND STR_TO_DATE('2022-03-31', '%Y-%m-%d')  GROUP BY `Month` ORDER BY `Month`;

"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif time_duration == "Quarter":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Quarter"
                        and chart["chart_type"] == "table_chart"
                    ]

                    if (
                        chart_axis["xAxis_column"]
                        in data_summary.column_sql_data_types.keys()
                    ):
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Total Revenue for the Last Q3
SQL Query 1: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-Q', QUARTER(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `Quarter`, SUM(`Revenue`) AS `Total Revenue` FROM `database_name`.`table_name` WHERE QUARTER(STR_TO_DATE(`Date`, '%d/%m/%Y')) = 3 AND STR_TO_DATE(`Date`, '%d/%m/%Y') >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) GROUP BY `Quarter` ORDER BY `Quarter`;

Chart Title 2: Quarterly EBIT for the Next Quarter
SQL Query 2: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-Q', QUARTER(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `Quarter`, SUM(`EBIT`) AS `Total EBIT` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') BETWEEN CURDATE() AND CURDATE() + INTERVAL 1 QUARTER GROUP BY `Quarter` ORDER BY `Quarter`;

Chart Title 3: Quarterly Average Revenue for the Past H2
SQL Query 3: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-Q', QUARTER(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `Quarter`, AVG(`Revenue`) AS `Average Revenue` FROM `database_name`.`table_name` WHERE QUARTER(STR_TO_DATE(`Date`, '%d/%m/%Y')) IN (3, 4) AND STR_TO_DATE(`Date`, '%d/%m/%Y') >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) GROUP BY `Quarter` ORDER BY `Quarter`;

Chart Title 4: Quarterly Total Cost for Q1 2023 - Q3 2023
SQL Query 4: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-Q', QUARTER(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `Quarter`, SUM(`Cost_Entertainment` + `Cost_Broadband` + `Cost_Mobile`) AS `Total Cost` FROM `database_name`.`table_name` WHERE YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) = 2023 AND QUARTER(STR_TO_DATE(`Date`, '%d/%m/%Y')) BETWEEN 1 AND 3 GROUP BY `Quarter` ORDER BY `Quarter`;

"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Total Revenue for the Last Q3
SQL Query 1: SELECT CONCAT(YEAR(`Date`), '-Q', QUARTER(`Date`)) AS `Quarter`, SUM(`Revenue`) AS `Total Revenue` FROM `database_name`.`table_name` WHERE QUARTER(`Date`) = 3 AND `Date` >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) GROUP BY `Quarter` ORDER BY `Quarter`;

Chart Title 2: Quarterly EBIT for the Next Quarter
SQL Query 2: SELECT CONCAT(YEAR(`Date`), '-Q', QUARTER(`Date`)) AS `Quarter`, SUM(`EBIT`) AS `Total EBIT` FROM `database_name`.`table_name` WHERE `Date` BETWEEN CURDATE() AND CURDATE() + INTERVAL 1 QUARTER GROUP BY `Quarter` ORDER BY `Quarter`;

Chart Title 3: Quarterly Average Revenue for the Past H2
SQL Query 3: SELECT CONCAT(YEAR(`Date`), '-Q', QUARTER(`Date`)) AS `Quarter`, AVG(`Revenue`) AS `Average Revenue` FROM `database_name`.`table_name` WHERE QUARTER(`Date`) IN (3, 4) AND `Date` >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) GROUP BY `Quarter` ORDER BY `Quarter`;

Chart Title 4: Quarterly Total Cost for Q1 2023 - Q3 2023
SQL Query 4: SELECT CONCAT(YEAR(`Date`), '-Q', QUARTER(`Date`)) AS `Quarter`, SUM(`Cost_Entertainment` + `Cost_Broadband` + `Cost_Mobile`) AS `Total Cost` FROM `database_name`.`table_name` WHERE YEAR(`Date`) = 2023 AND QUARTER(`Date`) BETWEEN 1 AND 3 GROUP BY `Quarter` ORDER BY `Quarter`;

"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif time_duration == "Year":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Year"
                        and chart["chart_type"] == "table_chart"
                    ]

                    if (
                        chart_axis["xAxis_column"]
                        in data_summary.column_sql_data_types.keys()
                    ):
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Total Revenue by Product Over the Past 5 Years
SQL Query 1: SELECT CAST(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) AS CHAR) AS `Year`, SUM(`Revenue`) AS `Total Revenue`, `Product` AS `Product` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= DATE_SUB(CURDATE(), INTERVAL 5 YEAR) GROUP BY `Year`, `Product` ORDER BY `Year` ASC, `Product`;

Chart Title 2: Yearly Average EBIT for Next Year
SQL Query 2: SELECT CAST(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) AS CHAR) AS `Year`, AVG(`EBIT`) AS `Average EBIT` FROM `database_name`.`table_name` WHERE YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) = YEAR(CURDATE()) + 1 GROUP BY `Year` ORDER BY `Year`;

Chart Title 3: Yearly Total Revenue for 2022
SQL Query 3: SELECT CAST(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) AS CHAR) AS `Year`, SUM(`Revenue`) AS `Total Revenue` FROM `database_name`.`table_name` WHERE YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) = 2022 GROUP BY `Year` ORDER BY `Year`;

Chart Title 4: Yearly Cost and Revenue for the Last 3 Years
SQL Query 4: SELECT CAST(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) AS CHAR) AS `Year`, SUM(`Cost_Entertainment` + `Cost_Broadband` + `Cost_Mobile`) AS `Total Cost`, SUM(`Revenue`) AS `Total Revenue` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= DATE_SUB(CURDATE(), INTERVAL 3 YEAR) GROUP BY `Year` ORDER BY `Year`;

Chart Title 5: Yearly Total Revenue for 2022 - 2023
SQL Query 5: SELECT CAST(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) AS CHAR) AS `Year`, SUM(`Revenue`) AS `Total Revenue` FROM `database_name`.`table_name` WHERE YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) BETWEEN 2022 AND 2023 GROUP BY `Year` ORDER BY `Year`;

"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Total Revenue by Product Over the Past 5 Years
SQL Query 1: SELECT CAST(YEAR(`Date`) AS CHAR) AS `Year`, SUM(`Revenue`) AS `Total Revenue`, `Product` AS `Product` FROM `database_name`.`table_name` WHERE `Date` >= DATE_SUB(CURDATE(), INTERVAL 5 YEAR) GROUP BY `Year`, `Product` ORDER BY `Year` ASC, `Product`;

Chart Title 2: Yearly Average EBIT for Next Year
SQL Query 2: SELECT CAST(YEAR(`Date`) AS CHAR) AS `Year`, AVG(`EBIT`) AS `Average EBIT` FROM `database_name`.`table_name` WHERE YEAR(`Date`) = YEAR(CURDATE()) + 1 GROUP BY `Year` ORDER BY `Year`;

Chart Title 3: Yearly Total Revenue for 2022
SQL Query 3: SELECT CAST(YEAR(`Date`) AS CHAR) AS `Year`, SUM(`Revenue`) AS `Total Revenue` FROM `database_name`.`table_name` WHERE YEAR(`Date`) = 2022 GROUP BY `Year` ORDER BY `Year`;

Chart Title 4: Yearly Cost and Revenue for the Last 3 Years
SQL Query 4: SELECT CAST(YEAR(`Date`) AS CHAR) AS `Year`, SUM(`Cost_Entertainment` + `Cost_Broadband` + `Cost_Mobile`) AS `Total Cost`, SUM(`Revenue`) AS `Total Revenue` FROM `database_name`.`table_name` WHERE `Date` >= DATE_SUB(CURDATE(), INTERVAL 3 YEAR) GROUP BY `Year` ORDER BY `Year`;

Chart Title 5: Yearly Total Revenue for 2022 - 2023
SQL Query 5: SELECT CAST(YEAR(`Date`) AS CHAR) AS `Year`, SUM(`Revenue`) AS `Total Revenue` FROM `database_name`.`table_name` WHERE YEAR(`Date`) BETWEEN 2022 AND 2023 GROUP BY `Year` ORDER BY `Year`;

"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

        # Not table chart
        else:
            x_column = chart_axis["xAxis_column"]
            if (
                isinstance(x_column, str)
                and x_column in data_summary.column_data_tribes.keys()
                and data_summary.column_data_tribes[x_column] == "date_related"
            ):
                if timeframe.lower() == "yearly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        # Handle Yearly Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_yearly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "yearly"
                        ]

                        if not filtered_feedbacks_by_chart_and_yearly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Total Revenue by Product Over the Last 5 Years
SQL Query 1: SELECT CAST(YEAR(STR_TO_DATE(t1.`Date`, '%Y-%m-%d')) AS CHAR) AS `xAxis`, SUM(t1.`Revenue`) AS `yAxis`, t1.`Product` AS `series` 
FROM `database_name`.`table_name` t1 
JOIN `database_name`.`table_name` t2 
ON STR_TO_DATE(t1.`Date`, '%Y-%m-%d') = STR_TO_DATE(t2.`Date`, '%Y-%m-%d') AND t1.`Product` = t2.`Product` 
WHERE STR_TO_DATE(t1.`Date`, '%Y-%m-%d') >= DATE_SUB(CURDATE(), INTERVAL 5 YEAR) 
GROUP BY `xAxis`, `series` ORDER BY `xAxis` ASC, `series`;

Chart Title 2: Yearly Breakdown of Cost and Revenue for Each Product Over the Last 5 Years
SQL Query 2: SELECT CAST(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) AS CHAR) AS `xAxis`, SUM(`Cost_Entertainment` + `Cost_Mobile` + `Cost_Broadband`) AS `yAxis_Cost`, SUM(`Revenue_Entertainment` + `Revenue_Broadband`) AS `yAxis_Revenue`, `Product` AS `series` 
FROM `database_name`.`table_name` 
WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= DATE_SUB(CURDATE(), INTERVAL 5 YEAR) 
GROUP BY `xAxis`, `series` ORDER BY `xAxis` ASC, `series`;

Chart Title 3: Yearly Average Revenue per Day by Product Over the Last 5 Years
SQL Query 3: SELECT CAST(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) AS CHAR) AS `xAxis`, AVG(`Revenue_per_Day`) AS `yAxis`, `Product` AS `series` 
FROM `database_name`.`table_name` 
WHERE YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) >= YEAR(CURDATE()) - 5 
GROUP BY `xAxis`, `series`;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Sum of Revenue by Product for the Last 5 Years
SQL Query 1: SELECT CAST(YEAR(t1.`Date`) AS CHAR) AS `xAxis`, SUM(t1.`Revenue`) AS `yAxis`, t1.`Product` AS `series` 
FROM `database_name`.`table_name` t1 
JOIN `database_name`.`table_name` t2 
ON t1.`Date` = t2.`Date` AND t1.`Product` = t2.`Product` 
WHERE YEAR(t1.`Date`) >= YEAR(CURDATE()) - 5 
GROUP BY `xAxis`, `series` ORDER BY `xAxis`;

Chart Title 2: Yearly Average EBIT Across All Products Over the Last 3 Years
SQL Query 2: SELECT CAST(YEAR(`Date`) AS CHAR) AS `xAxis`, AVG(`EBIT`) AS `yAxis` 
FROM `database_name`.`table_name` 
WHERE YEAR(`Date`) >= YEAR(CURDATE()) - 3 
GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 3: Yearly Growth in Broadband Revenue Across All Products Over the Last 6 Years
SQL Query 3: SELECT CAST(YEAR(`Date`) AS CHAR) AS `xAxis`, (SUM(`Revenue_Broadband`) / LAG(SUM(`Revenue_Broadband`), 1) OVER (ORDER BY YEAR(`Date`)) - 1) * 100 AS `yAxis` 
FROM `database_name`.`table_name` 
WHERE YEAR(`Date`) >= YEAR(CURDATE()) - 6 
GROUP BY `xAxis` ORDER BY `xAxis`;"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_yearly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "half-yearly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        # Handle Half-Yearly Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_half_yearly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "half-yearly"
                        ]

                        if not filtered_feedbacks_by_chart_and_half_yearly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Half-Yearly Sum of Revenue per Day and EBIT for the Last 2 Half-Years
SQL Query 1: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-H', IF(MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y')) <= 6, 1, 2)) AS `xAxis`, SUM(`Revenue_per_Day`) AS `yAxis`, SUM(`EBIT`) AS `yAxis2` 
FROM `database_name`.`table_name` 
WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) 
GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 2: Half-Yearly Average Earning per Cost by Product Over the Last Year
SQL Query 2: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-H', IF(MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y')) <= 6, 1, 2)) AS `xAxis`, AVG(`Earning_per_Cost`) AS `yAxis`, `Product` AS `series` 
FROM `database_name`.`table_name` 
WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) 
GROUP BY `xAxis`, `series` ORDER BY `xAxis`;

Chart Title 3: Half-Yearly Variance in Cost Actual vs. Budget by Product for Past 1 Year
SQL Query 3: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-H', IF(MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y')) <= 6, 1, 2)) AS `xAxis`, SUM(`CostVariance_Actual_vs_Budget`) AS `yAxis`, `Product` AS `series` 
FROM `database_name`.`table_name` 
WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) 
GROUP BY `xAxis`, `series` ORDER BY `xAxis`;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Half-Yearly Average EBIT and Revenue for the Last 3 Years
SQL Query 1: SELECT CONCAT(YEAR(`Date`), '-H', IF(MONTH(`Date`) <= 6, 1, 2)) AS `xAxis`, AVG(`EBIT`) AS `yAxis`, AVG(`Revenue`) AS `yAxis2` 
FROM `database_name`.`table_name` 
WHERE `Date` >= DATE_SUB(CURDATE(), INTERVAL 3 YEAR) 
GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 2: Half-Yearly Growth Rate of Broadband Revenue Compared to Entertainment Revenue for the Last 4 Years
SQL Query 2: SELECT CONCAT(YEAR(`Date`), '-H', IF(MONTH(`Date`) <= 6, 1, 2)) AS `xAxis`, (SUM(`Revenue_Broadband`) / LAG(SUM(`Revenue_Broadband`)) OVER (ORDER BY YEAR(`Date`), IF(MONTH(`Date`) <= 6, 1, 2))) * 100 AS `yAxis`, (SUM(`Revenue_Entertainment`) / LAG(SUM(`Revenue_Entertainment`)) OVER (ORDER BY YEAR(`Date`), IF(MONTH(`Date`) <= 6, 1, 2))) * 100 AS `yAxis2` 
FROM `database_name`.`table_name` 
WHERE `Date` >= DATE_SUB(CURDATE(), INTERVAL 4 YEAR) 
GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 3: Half-Yearly EBIT to Revenue Ratio and Total Cost of Broadband for the Past 2 Years
SQL Query 3: SELECT CONCAT(YEAR(`Date`), '-H', IF(MONTH(`Date`) <= 6, 1, 2)) AS `xAxis`, (SUM(`EBIT`) / SUM(`Revenue`)) * 100 AS `yAxis`, SUM(`Cost_Broadband`) AS `yAxis2` 
FROM `database_name`.`table_name` 
WHERE `Date` >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR) 
GROUP BY `xAxis` ORDER BY `xAxis`;"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_half_yearly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "quarterly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        # Handle Quarterly Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_quarterly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "quarterly"
                        ]

                        if not filtered_feedbacks_by_chart_and_quarterly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Sum of Cost Variance (Actual vs. Budget) by Product for the Past 3 Quarters
Sql Query 1: SELECT CONCAT(YEAR(STR_TO_DATE(t1.`Date`, '%Y-%m-%d')), '-Q', QUARTER(STR_TO_DATE(t1.`Date`, '%Y-%m-%d'))) AS `xAxis`, SUM(t1.`CostVariance_Actual_vs_Budget`) AS `yAxis`, t1.`Product` AS `series` FROM `database_name`.`table_name` t1 JOIN `database_name`.`table_name` t2 ON STR_TO_DATE(t1.`Date`, '%Y-%m-%d') = STR_TO_DATE(t2.`Date`, '%Y-%m-%d') AND t1.`Product` = t2.`Product` WHERE STR_TO_DATE(t1.`Date`, '%Y-%m-%d') >= DATE_SUB(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 3 QUARTER) AND STR_TO_DATE(t1.`Date`, '%Y-%m-%d') <= DATE_FORMAT(CURDATE(), '%Y-%m-31') GROUP BY `xAxis`, `series`;

Chart Title 2: Quarterly Average Cost Efficiency Across All Products for the Last 6 Quarters
SQL Query 2: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-Q', QUARTER(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `xAxis`, AVG(`Cost_Efficiency`) AS `yAxis` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= DATE_SUB(CURDATE(), INTERVAL 1.5 YEAR) GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 3: Quarterly Growth Rate of Broadband Revenue Compared to the Previous Quarter
SQL Query 3: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-Q', QUARTER(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `xAxis`, (SUM(`Revenue_Broadband`) / LAG(SUM(`Revenue_Broadband`)) OVER (ORDER BY YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), QUARTER(STR_TO_DATE(`Date`, '%d/%m/%Y')))) AS yAxis FROM `database_name`.`table_name` GROUP BY `xAxis` ORDER BY `xAxis`;

"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Sum of Entertainment Costs for 2022
Sql Query 1: SELECT CONCAT(YEAR(t1.`Date`), '-Q', QUARTER(t1.`Date`)) AS `xAxis`, SUM(t1.`Cost_Entertainment`) AS `yAxis` FROM `database_name`.`table_name` t1 JOIN `database_name`.`table_name` t2 ON t1.`Date` = t2.`Date` WHERE t1.`Date` BETWEEN STR_TO_DATE('2022-01-01', '%Y-%m-%d') AND STR_TO_DATE('2022-12-31', '%Y-%m-%d') GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 2: Quarterly Average Revenue per Product for the Past 4 Quarters
SQL Query 2: SELECT CONCAT(YEAR(`Date`), '-Q', QUARTER(`Date`)) AS `xAxis`, AVG(`Revenue`) AS `yAxis`, `Product` AS `series` FROM `database_name`.`table_name` WHERE `Date` >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) GROUP BY `xAxis`, `series` ORDER BY `xAxis`;

Chart Title 3: Quarterly EBIT Margin (EBIT as a Percentage of Revenue) Over the Last 8 Quarters
SQL Query 3: SELECT CONCAT(YEAR(`Date`), '-Q', QUARTER(`Date`)) AS `xAxis`, (SUM(`EBIT`) / SUM(`Revenue`)) * 100 AS `yAxis` FROM `database_name`.`table_name` WHERE `Date` >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR) GROUP BY `xAxis` ORDER BY `xAxis`;

"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_quarterly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "monthly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        # Handle Monthly Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_monthly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "monthly"
                        ]
                        if not filtered_feedbacks_by_chart_and_monthly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Cost Variance (Actual vs. Budget) by Product (Last Year)
Sql Query 1: SELECT CONCAT(YEAR(STR_TO_DATE(t1.`Date`, '%Y-%m-%d')), '-M', MONTH(STR_TO_DATE(t1.`Date`, '%Y-%m-%d'))) AS `xAxis`, SUM(t1.`CostVariance_Actual_vs_Budget`) AS `yAxis`, t1.`Product` AS `series` FROM `database_name`.`table_name` t1 JOIN `database_name`.`table_name` t2 ON STR_TO_DATE(t1.`Date`, '%Y-%m-%d') = STR_TO_DATE(t2.`Date`, '%Y-%m-%d') WHERE YEAR(STR_TO_DATE(t1.`Date`, '%Y-%m-%d')) = YEAR(DATE_SUB(CURDATE(), INTERVAL 1 YEAR)) GROUP BY `xAxis`, `series`;

Chart Title 2: Monthly Total Cost Variance (Actual vs. Budget) by Product for the Current and Previous Year
Sql Query 2: SELECT CONCAT(EXTRACT(YEAR FROM STR_TO_DATE(`Date`, '%d/%m/%Y')), '-M', EXTRACT(MONTH FROM STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `xAxis`, SUM(`CostVariance_Actual_vs_Budget`) AS `yAxis`, `Product` AS `series` FROM `database_name`.`table_name` WHERE EXTRACT(YEAR FROM STR_TO_DATE(`Date`, '%d/%m/%Y')) >= EXTRACT(YEAR FROM DATE_SUB(CURDATE(), INTERVAL 1 YEAR)) AND EXTRACT(YEAR FROM STR_TO_DATE(`Date`, '%d/%m/%Y')) <= EXTRACT(YEAR FROM CURDATE()) GROUP BY `xAxis`, `series` ORDER BY `xAxis`;

Chart Title 3: Monthly Total Entertainment Costs and Cost Efficiency Ratio for the Last 3 Months
SQL Query 3: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-M', MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `xAxis`, SUM(`Cost_Entertainment`) AS `yAxis`, AVG(`Cost_Efficiency`) AS `yAxis2` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH) GROUP BY `xAxis` ORDER BY `xAxis`;

"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue for Broadband and Entertainment for the Current and Previous Year
Sql Query 1: SELECT CONCAT(YEAR(`Date`), '-M', MONTH(`Date`)) AS `xAxis`, SUM(`Revenue_Broadband`) AS `yAxis`, 'Broadband' AS `series` FROM `database_name`.`table_name` WHERE YEAR(`Date`) >= YEAR(DATE_SUB(CURDATE(), INTERVAL 1 YEAR)) AND YEAR(`Date`) <= YEAR(CURDATE()) AND `Revenue_Broadband` IS NOT NULL GROUP BY `xAxis`, `series` UNION ALL SELECT CONCAT(YEAR(`Date`), '-M', MONTH(`Date`)) AS `xAxis`, SUM(`Revenue_Entertainment`) AS yAxis, 'Entertainment' AS `series` FROM `database_name`.`table_name` WHERE YEAR(`Date`) >= YEAR(DATE_SUB(CURDATE(), INTERVAL 1 YEAR)) AND YEAR(`Date`) <= YEAR(CURDATE()) AND `Revenue_Entertainment` IS NOT NULL GROUP BY `xAxis`, `series`;

Chart Title 2: Monthly Sum of Mobile Costs for Next Year
Sql Query 2: SELECT CONCAT(EXTRACT(YEAR FROM `Date`), '-M', EXTRACT(MONTH FROM `Date`)) AS `xAxis`, SUM(`Cost_Mobile`) AS `yAxis` FROM `database_name`.`table_name` WHERE EXTRACT(YEAR FROM `Date`) = EXTRACT(YEAR FROM DATE_ADD(CURDATE(), INTERVAL 1 YEAR)) GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 3: Monthly Revenue Growth Rate (Percentage Increase) for Entertainment Over the Last 12 Months
SQL Query 3: SELECT CONCAT(YEAR(t1.`Date`), '-M', MONTH(t1.`Date`)) AS `xAxis`, ((SUM(t1.`Revenue_Entertainment`) - SUM(t2.`Revenue_Entertainment`)) / SUM(t2.`Revenue_Entertainment`)) * 100 AS `yAxis` FROM `database_name`.`table_name` t1 LEFT JOIN `database_name`.`table_name` t2 ON t1.`Date` = DATE_SUB(t2.`Date`, INTERVAL 1 MONTH) WHERE t1.`Date` >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH) GROUP BY `xAxis` ORDER BY `xAxis`;

"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_monthly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "weekly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        # Handle Weekly Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_weekly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "weekly"
                        ]

                        if not filtered_feedbacks_by_chart_and_weekly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Average Cost Efficiency by Product for the Last 12 Weeks
SQL Query 1: SELECT CONCAT(YEAR(STR_TO_DATE(t1.`Date`, '%Y-%m-%d')), '-W', WEEK(STR_TO_DATE(t1.`Date`, '%Y-%m-%d'))) AS `xAxis`, AVG(t1.`Cost_Efficiency`) AS `yAxis`, t1.`Product` AS `series` FROM `database_name`.`table_name` t1 JOIN `database_name`.`table_name` t2 ON STR_TO_DATE(t1.`Date`, '%Y-%m-%d') = STR_TO_DATE(t2.`Date`, '%Y-%m-%d') AND t1.`Product` = t2.`Product` WHERE STR_TO_DATE(t1.`Date`, '%Y-%m-%d') >= DATE_SUB(CURDATE(), INTERVAL 12 WEEK) GROUP BY `xAxis`, `series` ORDER BY `xAxis`;

Chart Title 2: Weekly Sum of Revenue and Cost Variance (Actual vs. Budget) Over the Past 8 Weeks
SQL Query 2: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-W', WEEK(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `xAxis`, SUM(`Revenue`) AS `yAxis`, SUM(`CostVariance_Actual_vs_Budget`) AS `yAxis2` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= DATE_SUB(CURDATE(), INTERVAL 8 WEEK) GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 3: Weekly EBIT Margin (EBIT as a Percentage of Revenue) Over the Last 10 Weeks
SQL Query 3: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-W', WEEK(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `xAxis`, (SUM(`EBIT`) / SUM(`Revenue`)) * 100 AS `yAxis` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= DATE_SUB(CURDATE(), INTERVAL 10 WEEK) GROUP BY `xAxis` ORDER BY `xAxis`;

"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Revenue for Entertainment in Quarter 4 in Year 2023
Sql Query 1: SELECT CONCAT(YEAR(t1.`Date`), '-W', WEEK(t1.`Date`)) AS `xAxis`, SUM(t1.`Revenue_Entertainment`) AS `yAxis` FROM `database_name`.`table_name` t1 JOIN `database_name`.`table_name` t2 ON t1.`Date` = t2.`Date` WHERE YEAR(t1.`Date`) = 2023 AND QUARTER(t1.`Date`) = 4 GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 2: Weekly Ratio of Entertainment Costs to Total Revenue Over the Past 12 Weeks
SQL Query 2: SELECT CONCAT(YEAR(`Date`), '-W', WEEK(`Date`)) AS `xAxis`, (SUM(`Cost_Entertainment`) / SUM(`Revenue`)) * 100 AS `yAxis` FROM `database_name`.`table_name` WHERE `Date` >= DATE_SUB(CURDATE(), INTERVAL 12 WEEK) GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 3: Weekly Variance in Mobile Costs and Broadband Costs for the Last 10 Weeks
SQL Query 3: SELECT CONCAT(YEAR(`Date`), '-W', WEEK(`Date`)) AS `xAxis`, VARIANCE(`Cost_Mobile`) AS `yAxis`, VARIANCE(`Cost_Broadband`) AS `yAxis2` FROM `database_name`.`table_name` WHERE `Date` >= DATE_SUB(CURDATE(), INTERVAL 10 WEEK) GROUP BY `xAxis` ORDER BY `xAxis`;

"""

                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_weekly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "daily":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        # Handle Daily Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_daily_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "daily"
                        ]
                        if not filtered_feedbacks_by_chart_and_daily_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Daily Average Cost Efficiency and Earnings per Cost Over the Last 30 Days
SQL Query 1: SELECT DATE(STR_TO_DATE(t1.`Date`, '%Y-%m-%d')) AS `xAxis`, AVG(t1.`Cost_Efficiency`) AS `yAxis`, AVG(t1.`Earning_per_Cost`) AS `yAxis2` FROM `database_name`.`table_name` t1 JOIN `database_name`.`table_name` t2 ON STR_TO_DATE(t1.`Date`, '%Y-%m-%d') = STR_TO_DATE(t2.`Date`, '%Y-%m-%d') WHERE STR_TO_DATE(t1.`Date`, '%Y-%m-%d') >= CURDATE() - INTERVAL 30 DAY GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 2: Daily Sum of Revenue and Cost for the Last 2 Weeks
SQL Query 2: SELECT DATE(STR_TO_DATE(`Date`, '%d/%m/%Y')) AS `xAxis`, SUM(`Revenue`) AS `yAxis`, SUM(`Cost`) AS `yAxis2` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= CURDATE() - INTERVAL 14 DAY GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 3: Daily Change in EBIT (Day-over-Day Difference) for the Past 10 Days
SQL Query 3: SELECT DATE(STR_TO_DATE(`Date`, '%d/%m/%Y')) AS `xAxis`, `EBIT` - LAG(`EBIT`, 1) OVER (ORDER BY DATE(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `yAxis` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= CURDATE() - INTERVAL 10 DAY ORDER BY `xAxis`;

"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Daily Cost of Entertainment vs. Cost of Mobile for the Last 7 Days
SQL Query 1: SELECT DATE(t1.`Date`) AS `xAxis`, SUM(t1.`Cost_Entertainment`) AS `yAxis`, SUM(t1.`Cost_Mobile`) AS `yAxis2` FROM `database_name`.`table_name` t1 JOIN `database_name`.`table_name` t2 ON t1.`Date` = t2.`Date` WHERE t1.`Date` >= CURDATE() - INTERVAL 7 DAY GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 2: Daily EBIT to Revenue Ratio (EBIT as a Percentage of Revenue) for the Last 14 Days
SQL Query 2: SELECT DATE(`Date`) AS `xAxis`, (SUM(`EBIT`) / NULLIF(SUM(`Revenue`), 0)) * 100 AS `yAxis` FROM `database_name`.`table_name` WHERE `Date` >= CURDATE() - INTERVAL 14 DAY GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 3: Daily Total Revenue vs. Total Cost for the Last 60 Days
SQL Query 3: SELECT DATE(`Date`) AS `xAxis`, SUM(`Revenue`) AS `yAxis`, SUM(`Cost_Broadband` + `Cost_Entertainment` + `Cost_Mobile`) AS `yAxis2` FROM `database_name`.`table_name` WHERE `Date` >= CURDATE() - INTERVAL 60 DAY GROUP BY `xAxis` ORDER BY `xAxis`;

"""

                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_daily_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

            else:
                filtered_feedbacks_by_chart_and_no_timeframe = [
                    feedback
                    for feedback in filtered_liked_feedbacks
                    if feedback.get("chart_type") != "table_chart"
                    and not feedback.get("time_frame", "").strip()
                ]
                if not filtered_feedbacks_by_chart_and_no_timeframe:
                    QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Top 5 Products by Percentage of Total EBIT
Sql Query 1: SELECT `Product` AS `xAxis`, SUM(`EBIT`) / SUM(SUM(`EBIT`)) OVER () * 100 AS `yAxis` FROM `database_name`.`table_name` GROUP BY `xAxis` ORDER BY `yAxis` DESC LIMIT 5;

Chart Title 2: Top 3 Products that Generate the Highest Revenue
Sql Query 2: SELECT `Product` AS `xAxis`, SUM(`Revenue`) AS `yAxis` FROM `database_name`.`table_name` GROUP BY `Product` ORDER BY `yAxis` DESC LIMIT 3;

Chart Title 3: Total Revenue Generated by Broadband Product
Sql Query 3: SELECT 'Broadband' AS `xAxis`, SUM(`Revenue_Broadband`) AS `yAxis` FROM `database_name`.`table_name`;

Chart Title 4: Total Cost Incurred by Entertainment and Broadband Respectively
Sql Query 4: SELECT 'Entertainment' AS `xAxis`, SUM(`Cost_Entertainment`) AS `yAxis` FROM `database_name`.`table_name` UNION ALL SELECT 'Broadband' AS `xAxis`, SUM(`Cost_Broadband`) AS `yAxis` FROM `database_name`.`table_name`;

Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Top 5 Products by Percentage of Total EBIT
Sql Query 1: SELECT `Product` AS `xAxis`, SUM(`EBIT`) / SUM(SUM(`EBIT`)) OVER () * 100 AS `yAxis` FROM `database_name`.`table_name` GROUP BY `xAxis` ORDER BY `yAxis` DESC LIMIT 5;

Chart Title 2: Top 3 Products that Generate the Highest Revenue
Sql Query 2: SELECT `Product` AS `xAxis`, SUM(`Revenue`) AS `yAxis` FROM `database_name`.`table_name` GROUP BY `Product` ORDER BY `yAxis` DESC LIMIT 3;

Chart Title 3: Total Revenue Generated by Broadband Product
Sql Query 3: SELECT 'Broadband' AS `xAxis`, SUM(`Revenue_Broadband`) AS `yAxis` FROM `database_name`.`table_name`;

Chart Title 4: Total Cost Incurred by Entertainment and Broadband Respectively
Sql Query 4: SELECT 'Entertainment' AS `xAxis`, SUM(`Cost_Entertainment`) AS `yAxis` FROM `database_name`.`table_name` UNION ALL SELECT 'Broadband' AS `xAxis`, SUM(`Cost_Broadband`) AS `yAxis` FROM `database_name`.`table_name`;

"""

                else:
                    # Only append this line if token count allows
                    heading = "\nHere are the chart titles and sql queries\n"
                    new_data_tokens = calculate_token_usage(heading)
                    if (
                        TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                        <= TARGET_TOKEN_LIMIT
                    ):
                        QUERY_SAMPLES += heading
                        TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                    for idx, chart in enumerate(
                        filtered_feedbacks_by_chart_and_no_timeframe,
                        start=1,
                    ):
                        chart_title = chart.get("chart_title", "")
                        sql_query = chart.get("sql_query", "")
                        sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                        # Calculate token usage for the current chart and SQL query
                        new_data_tokens = calculate_token_usage(sample)

                        # Check if appending this data would exceed the token limit
                        if (
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                            <= TARGET_TOKEN_LIMIT
                        ):
                            QUERY_SAMPLES += sample

                            # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                        else:
                            # If appending would exceed, break the loop
                            break

            if (
                isinstance(chart_axis["xAxis_column"], str)
                and chart_axis["xAxis_column"] in data_summary.column_data_tribes.keys()
                and data_summary.column_data_tribes[chart_axis["xAxis_column"]]
                in ["date_related"]
                and chart_axis["xAxis_column"]
                in data_summary.column_sql_data_types.keys()
                and data_summary.column_sql_data_types[
                    chart_axis["xAxis_column"]
                ].lower()
                not in [
                    "tinyint",
                    "smallint",
                    "mediumint",
                    "int",
                    "bigint",
                    "float",
                    "double",
                    "decimal",
                    "bit",
                ]
            ):
                x_column = chart_axis["xAxis_column"]

                if time_duration == "Week":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Week"
                        and chart["chart_type"] != "table_chart"
                    ]

                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Total Revenue by Product for the Past 2 Weeks
SQL Query 1: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-W', WEEK(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `xAxis`, SUM(`Revenue`) AS `yAxis`, `Product` AS `series` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') BETWEEN CURDATE() - INTERVAL 2 WEEK AND CURDATE() GROUP BY `xAxis`, `series` ORDER BY `xAxis` ASC, `series`;

Chart Title 2: Weekly Average EBIT for Next 3 Weeks
SQL Query 2: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-W', WEEK(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `xAxis`, AVG(`EBIT`) AS `yAxis` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') BETWEEN CURDATE() AND CURDATE() + INTERVAL 3 WEEK GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 3: Weekly Total Cost of Entertainment for Last Week
SQL Query 3: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-W', WEEK(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `xAxis`, SUM(`Cost_Entertainment`) AS `yAxis` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') BETWEEN CURDATE() - INTERVAL 1 WEEK AND CURDATE() GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 4: Weekly Maximum Revenue from Week 1 - Week 4 in March 2023
SQL Query 4: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-W', WEEK(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `xAxis`, MAX(`Revenue`) AS `yAxis` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') BETWEEN STR_TO_DATE('2023-03-01', '%Y-%m-%d') AND STR_TO_DATE('2023-03-31', '%Y-%m-%d') AND WEEK(STR_TO_DATE(`Date`, '%d/%m/%Y')) BETWEEN 1 AND 4 GROUP BY `xAxis` ORDER BY `xAxis`;

"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Total Revenue by Product for the Past 2 Weeks
SQL Query 1: SELECT CONCAT(YEAR(`Date`), '-W', WEEK(`Date`)) AS `xAxis`, SUM(`Revenue`) AS `yAxis`, `Product` AS `series` FROM `database_name`.`table_name` WHERE `Date` BETWEEN CURDATE() - INTERVAL 2 WEEK AND CURDATE() GROUP BY `xAxis`, `series` ORDER BY `xAxis` ASC, `series`;

Chart Title 2: Weekly Average EBIT for Next 3 Weeks
SQL Query 2: SELECT CONCAT(YEAR(`Date`), '-W', WEEK(`Date`)) AS `xAxis`, AVG(`EBIT`) AS `yAxis` FROM `database_name`.`table_name` WHERE `Date` BETWEEN CURDATE() AND CURDATE() + INTERVAL 3 WEEK GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 3: Weekly Total Cost of Entertainment for Last Week
SQL Query 3: SELECT CONCAT(YEAR(`Date`), '-W', WEEK(`Date`)) AS `xAxis`, SUM(`Cost_Entertainment`) AS `yAxis` FROM `database_name`.`table_name` WHERE `Date` BETWEEN CURDATE() - INTERVAL 1 WEEK AND CURDATE() GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 4: Weekly Maximum Revenue from Week 1 - Week 4 in March 2023
SQL Query 4: SELECT CONCAT(YEAR(`Date`), '-W', WEEK(`Date`)) AS `xAxis`, MAX(`Revenue`) AS `yAxis` FROM `database_name`.`table_name` WHERE `Date` BETWEEN STR_TO_DATE('2023-03-01', '%Y-%m-%d') AND STR_TO_DATE('2023-03-31', '%Y-%m-%d') AND WEEK(`Date`) BETWEEN 1 AND 4 GROUP BY `xAxis` ORDER BY `xAxis`;

"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif time_duration == "Month":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Month"
                        and chart["chart_type"] != "table_chart"
                    ]

                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue by Product for the Past 6 Months
SQL Query 1: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-M', MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `xAxis`, SUM(`Revenue`) AS `yAxis`, `Product` AS `series` FROM `database_name`.`table_name` WHERE (STR_TO_DATE(`Date`, '%d/%m/%Y')) >= CURDATE() - INTERVAL 6 MONTH GROUP BY `xAxis`, `series` ORDER BY `xAxis` ASC, `series`;

Chart Title 2: Monthly Average EBIT for Next January
SQL Query 2: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-M', MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `xAxis`, AVG(`EBIT`) AS `yAxis` FROM `database_name`.`table_name` WHERE YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) = YEAR(CURDATE() + INTERVAL 1 YEAR) AND MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y')) = 1 GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 3: Monthly Cost of Entertainment for March
SQL Query 3: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-M', MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `xAxis`, SUM(`Cost_Entertainment`) AS `yAxis` FROM `database_name`.`table_name` WHERE MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y')) = 3 AND YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) = YEAR(CURDATE()) GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 4: Monthly Revenue from Jan 2022 - Mar 2022
SQL Query 4: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-M', MONTH(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `xAxis`, SUM(`Revenue`) AS `yAxis` FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') BETWEEN STR_TO_DATE('2022-01-01', '%Y-%m-%d') AND STR_TO_DATE('2022-03-31', '%Y-%m-%d') GROUP BY `xAxis` ORDER BY `xAxis`;

"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue by Product for the Past 6 Months
SQL Query 1: SELECT CONCAT(YEAR(`Date`), '-M', MONTH(`Date`)) AS `xAxis`, SUM(`Revenue`) AS `yAxis`, `Product` AS `series` FROM `database_name`.`table_name` WHERE (`Date`) >= CURDATE() - INTERVAL 6 MONTH GROUP BY `xAxis`, `series` ORDER BY `xAxis` ASC, `series`;

Chart Title 2: Monthly Average EBIT for Next January
SQL Query 2: SELECT CONCAT(YEAR(`Date`), '-M', MONTH(`Date`)) AS `xAxis`, AVG(`EBIT`) AS `yAxis` FROM `database_name`.`table_name` WHERE YEAR(`Date`) = YEAR(CURDATE() + INTERVAL 1 YEAR) AND MONTH(`Date`) = 1 GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 3: Monthly Cost of Entertainment for March
SQL Query 3: SELECT CONCAT(YEAR(`Date`), '-M', MONTH(`Date`)) AS `xAxis`, SUM(`Cost_Entertainment`) AS `yAxis` FROM `database_name`.`table_name` WHERE MONTH(`Date`) = 3 AND YEAR(`Date`) = YEAR(CURDATE()) GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 4: Monthly Revenue from Jan 2022 - Mar 2022
SQL Query 4: SELECT CONCAT(YEAR(`Date`), '-M', MONTH(`Date`)) AS `xAxis`, SUM(`Revenue`) AS `yAxis` FROM `database_name`.`table_name` WHERE `Date` BETWEEN STR_TO_DATE('2022-01-01', '%Y-%m-%d') AND STR_TO_DATE('2022-03-31', '%Y-%m-%d') GROUP BY `xAxis` ORDER BY `xAxis`;

"""

                    else:
                        # Only append this line if token count allows
                        heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                        new_data_tokens = calculate_token_usage(heading)
                        if (
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                            <= TARGET_TOKEN_LIMIT
                        ):
                            QUERY_SAMPLES += heading
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                        for idx, chart in enumerate(filtered_feedback, start=1):
                            chart_title = chart.get("chart_title", "")
                            sql_query = chart.get("feedback", "")
                            sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                            # Calculate token usage for the current chart and feedback
                            new_data_tokens = calculate_token_usage(sample)

                            # Check if appending this data would exceed the token limit
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += sample

                                # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            else:
                                # If appending would exceed, break the loop
                                break

                elif time_duration == "Quarter":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Quarter"
                        and chart["chart_type"] != "table_chart"
                    ]
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Total Revenue for the Last Q3
SQL Query 1: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-Q', QUARTER(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `xAxis`, SUM(`Revenue`) AS `yAxis` FROM `database_name`.`table_name` WHERE QUARTER(STR_TO_DATE(`Date`, '%d/%m/%Y')) = 3 AND (STR_TO_DATE(`Date`, '%d/%m/%Y')) >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 2: Quarterly EBIT for the Next Quarter
SQL Query 2: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-Q', QUARTER(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `xAxis`, SUM(`EBIT`) AS `yAxis` FROM `database_name`.`table_name` WHERE (STR_TO_DATE(`Date`, '%d/%m/%Y')) BETWEEN CURDATE() AND CURDATE() + INTERVAL 1 QUARTER GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 3: Quarterly Average Revenue for the Past H2
SQL Query 3: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-Q', QUARTER(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `xAxis`, AVG(`Revenue`) AS `yAxis` FROM `database_name`.`table_name` WHERE QUARTER(STR_TO_DATE(`Date`, '%d/%m/%Y')) IN (3, 4) AND STR_TO_DATE(`Date`, '%d/%m/%Y') >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 4: Quarterly Total Cost for Q1 2023 - Q3 2023
SQL Query 4: SELECT CONCAT(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')), '-Q', QUARTER(STR_TO_DATE(`Date`, '%d/%m/%Y'))) AS `xAxis`, SUM(`Cost_Entertainment` + `Cost_Broadband` + `Cost_Mobile`) AS `yAxis` FROM `database_name`.`table_name` WHERE YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) = 2023 AND QUARTER(STR_TO_DATE(`Date`, '%d/%m/%Y')) BETWEEN 1 AND 3 GROUP BY `xAxis` ORDER BY `xAxis`;

"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Total Revenue for the Last Q3
SQL Query 1: SELECT CONCAT(YEAR(`Date`), '-Q', QUARTER(`Date`)) AS `xAxis`, SUM(`Revenue`) AS `yAxis` FROM `database_name`.`table_name` WHERE QUARTER(`Date`) = 3 AND (`Date`) >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 2: Quarterly EBIT for the Next Quarter
SQL Query 2: SELECT CONCAT(YEAR(`Date`), '-Q', QUARTER(`Date`)) AS `xAxis`, SUM(`EBIT`) AS `yAxis` FROM `database_name`.`table_name` WHERE (`Date`) BETWEEN CURDATE() AND CURDATE() + INTERVAL 1 QUARTER GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 3: Quarterly Average Revenue for the Past H2
SQL Query 3: SELECT CONCAT(YEAR(`Date`), '-Q', QUARTER(`Date`)) AS `xAxis`, AVG(`Revenue`) AS `yAxis` FROM `database_name`.`table_name` WHERE QUARTER(`Date`) IN (3, 4) AND `Date` >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 4: Quarterly Total Cost for Q1 2023 - Q3 2023
SQL Query 4: SELECT CONCAT(YEAR(`Date`), '-Q', QUARTER(`Date`)) AS `xAxis`, SUM(`Cost_Entertainment` + `Cost_Broadband` + `Cost_Mobile`) AS `yAxis` FROM `database_name`.`table_name` WHERE YEAR(`Date`) = 2023 AND QUARTER(`Date`) BETWEEN 1 AND 3 GROUP BY `xAxis` ORDER BY `xAxis`;

"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif time_duration == "Year":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Year"
                        and chart["chart_type"] != "table_chart"
                    ]

                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Total Revenue by Product Over the Past 5 Years
SQL Query 1: SELECT CAST(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) AS CHAR) AS `xAxis`, SUM(`Revenue`) AS `yAxis`, `Product` AS `series` FROM `database_name`.`table_name` WHERE (STR_TO_DATE(`Date`, '%d/%m/%Y')) >= DATE_SUB(CURDATE(), INTERVAL 5 YEAR) GROUP BY `xAxis`, `series` ORDER BY `xAxis` ASC, `series`;

Chart Title 2: Yearly Average EBIT for Next Year
SQL Query 2: SELECT CAST(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) AS CHAR) AS `xAxis`, AVG(`EBIT`) AS `yAxis` FROM `database_name`.`table_name` WHERE YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) = YEAR(CURDATE()) + 1 GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 3: Yearly Total Revenue for 2022
SQL Query 3: SELECT CAST(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) AS CHAR) AS `xAxis`, SUM(`Revenue`) AS `yAxis` FROM `database_name`.`table_name` WHERE YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) = 2022 GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 4: Yearly Cost and Revenue for the Last 3 Years
SQL Query 4: SELECT CAST(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) AS CHAR) AS `xAxis`, SUM(`Cost_Entertainment` + `Cost_Broadband` + `Cost_Mobile`) AS `yAxis`, SUM(`Revenue`) AS `yAxis`2 FROM `database_name`.`table_name` WHERE STR_TO_DATE(`Date`, '%d/%m/%Y') >= DATE_SUB(CURDATE(), INTERVAL 3 YEAR) GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 5: Yearly Total Revenue for 2022 - 2023
SQL Query 5: SELECT CAST(YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) AS CHAR) AS `xAxis`, SUM(`Revenue`) AS `yAxis` FROM `database_name`.`table_name` WHERE YEAR(STR_TO_DATE(`Date`, '%d/%m/%Y')) BETWEEN 2022 AND 2023 GROUP BY `xAxis` ORDER BY `xAxis`;

"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Total Revenue by Product Over the Past 5 Years
SQL Query 1: SELECT CAST(YEAR(`Date`) AS CHAR) AS `xAxis`, SUM(`Revenue`) AS `yAxis`, `Product` AS `series` FROM `database_name`.`table_name` WHERE (`Date`) >= DATE_SUB(CURDATE(), INTERVAL 5 YEAR) GROUP BY `xAxis`, `series` ORDER BY `xAxis` ASC, `series`;

Chart Title 2: Yearly Average EBIT for Next Year
SQL Query 2: SELECT CAST(YEAR(`Date`) AS CHAR) AS `xAxis`, AVG(`EBIT`) AS `yAxis` FROM `database_name`.`table_name` WHERE YEAR(`Date`) = YEAR(CURDATE()) + 1 GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 3: Yearly Total Revenue for 2022
SQL Query 3: SELECT CAST(YEAR(`Date`) AS CHAR) AS `xAxis`, SUM(`Revenue`) AS `yAxis` FROM `database_name`.`table_name` WHERE YEAR(`Date`) = 2022 GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 4: Yearly Cost and Revenue for the Last 3 Years
SQL Query 4: SELECT CAST(YEAR(`Date`) AS CHAR) AS `xAxis`, SUM(`Cost_Entertainment` + `Cost_Broadband` + `Cost_Mobile`) AS `yAxis`, SUM(`Revenue`) AS `yAxis`2 FROM `database_name`.`table_name` WHERE `Date` >= DATE_SUB(CURDATE(), INTERVAL 3 YEAR) GROUP BY `xAxis` ORDER BY `xAxis`;

Chart Title 5: Yearly Total Revenue for 2022 - 2023
SQL Query 5: SELECT CAST(YEAR(`Date`) AS CHAR) AS `xAxis`, SUM(`Revenue`) AS `yAxis` FROM `database_name`.`table_name` WHERE YEAR(`Date`) BETWEEN 2022 AND 2023 GROUP BY `xAxis` ORDER BY `xAxis`;

"""

                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

        if not filtered_liked_feedbacks:
            new_data_tokens = calculate_token_usage(QUERY_SAMPLES)
            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

    elif "sqlserver" in data_summary.sql_library.lower():
        filtered_liked_feedbacks = fetch_filtered_feedbacks(
            question, table_name, "label5"
        )

        QUERY_SAMPLES = """
Enhance your understanding of SQL Server SQL query structuring, syntax, and writing, with a particular emphasis on date-related formatting, by training using the provided chart titles and SQL query examples.

DDL:
""" + (
            data_summary.database_schema_sql
            if filtered_liked_feedbacks
            else (
                """
CREATE TABLE table_name (
    [Date] DATE,
    [Product] VARCHAR(255),
    [EBIT_Margin] DECIMAL(10, 2),
    [Revenue] DECIMAL(10, 2),
    [Cost_Efficiency] DECIMAL(10, 2),
    [Earning_per_Cost] DECIMAL(10, 2),
    [Cost_Mobile] DECIMAL(10, 2),
    [Cost_Broadband] DECIMAL(10, 2),
    [Cost_Entertainment] DECIMAL(10, 2),
    [Revenue_Mobile] DECIMAL(10, 2),
    [Revenue_Broadband] DECIMAL(10, 2),
    [Revenue_Entertainment] DECIMAL(10, 2),
    [RevenueVariance_Actual_vs_Forecast] DECIMAL(10, 2),
    [Revenue_Generation] DECIMAL(10, 2)
);
"""
                if any(
                    data_type.upper() in {"DATE", "DATETIME", "TIMESTAMP"}
                    for data_type in data_summary.column_sql_data_types.values()
                )
                else """
CREATE TABLE table_name (
    [Date] VARCHAR(255),
    [Product] VARCHAR(255),
    [RevenueVariance_Actual_vs_Forecast] DECIMAL(10, 2),
    [Cost_Efficiency] DECIMAL(10, 2),
    [Earning_per_Cost] DECIMAL(10, 2),
    [Revenue_Generation] DECIMAL(10, 2),
    [Revenue_Broadband] DECIMAL(10, 2),
    [Revenue_Entertainment] DECIMAL(10, 2),
    [Revenue_Mobile] DECIMAL(10, 2),
    [Cost_Broadband] DECIMAL(10, 2),
    [Cost_Entertainment] DECIMAL(10, 2),
    [Cost_Mobile] DECIMAL(10, 2),
    [EBIT_Margin] DECIMAL(10, 2)
);
"""
            )
        )

        # If Table Chart
        if chart_type in ["table_chart"]:
            x_column = chart_axis["xAxis_column"]
            if (
                isinstance(x_column, str)
                and x_column in data_summary.column_data_tribes
                and data_summary.column_data_tribes[x_column] == "date_related"
            ):
                if timeframe.lower() == "yearly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for Yearly timeframe feedbacks
                        filtered_feedbacks_by_chart_and_yearly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "yearly"
                        ]

                        if not filtered_feedbacks_by_chart_and_yearly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Total Revenue by Product Over the Last 5 Years
SQL Query 1: SELECT CAST(YEAR(CONVERT(DATE, t1.[Date], 23)) AS CHAR(4)) AS 'Year', t1.[Product] AS 'Product', SUM(t1.[Revenue]) AS 'Total Revenue' FROM [database_name].[table_name] t1 JOIN [database_name].[table_name] t2 ON CONVERT(DATE, t1.[Date], 23) = CONVERT(DATE, t2.[Date], 23) AND t1.[Product] = t2.[Product] WHERE CONVERT(DATE, t1.[Date], 23) >= DATEADD(YEAR, -5, GETDATE()) GROUP BY YEAR(CONVERT(DATE, t1.[Date], 23)), t1.[Product] ORDER BY 'Year' ASC, 'Product';

Chart Title 2: Yearly Breakdown of Cost and Revenue for Each Product Over the Last 5 Years
SQL Query 2: SELECT CAST(YEAR(CONVERT(DATE, [Date], 103)) AS CHAR(4)) AS 'Year', [Product] AS 'Product', SUM([Cost_Entertainment] + [Cost_Mobile] + [Cost_Broadband]) AS 'Total Cost', SUM([Revenue_Entertainment] + [Revenue_Broadband]) AS 'Total Revenue' FROM [database_name].[table_name] WHERE CONVERT(DATE, [Date], 103) >= DATEADD(YEAR, -5, GETDATE()) GROUP BY YEAR(CONVERT(DATE, [Date], 103)), [Product] ORDER BY 'Year' ASC, 'Product';

Chart Title 3: Yearly Average Revenue per Day by Product Over the Last 5 Years
SQL Query 3: SELECT CAST(YEAR(CONVERT(DATE, [Date], 103)) AS CHAR(4)) AS 'Year', [Product] AS 'Product', AVG([Revenue_per_Day]) AS 'Average Revenue per Day' FROM [database_name].[table_name] WHERE YEAR(CONVERT(DATE, [Date], 103)) >= YEAR(GETDATE()) - 5 GROUP BY YEAR(CONVERT(DATE, [Date], 103)), [Product] ORDER BY 'Year' ASC, 'Product';
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Sum of Revenue by Product for the Last 5 Years
SQL Query 1: SELECT CAST(YEAR(t1.Date) AS CHAR(4)) AS 'Year', t1.Product AS 'Product', SUM(t1.Revenue) AS 'Total Revenue' FROM database_name.dbo.table_name t1 JOIN database_name.dbo.table_name t2 ON t1.Date = t2.Date AND t1.Product = t2.Product WHERE YEAR(t1.Date) >= YEAR(GETDATE()) - 5 GROUP BY CAST(YEAR(t1.Date) AS CHAR(4)), t1.Product ORDER BY 'Year' ASC, 'Product';

Chart Title 2: Yearly Average EBIT Across All Products Over the Last 3 Years
SQL Query 2: SELECT CAST(YEAR(Date) AS CHAR(4)) AS 'Year', AVG(EBIT) AS 'Average EBIT' FROM database_name.dbo.table_name WHERE YEAR(Date) >= YEAR(GETDATE()) - 3 GROUP BY CAST(YEAR(Date) AS CHAR(4)) ORDER BY 'Year' ASC;

Chart Title 3: Yearly Growth in Broadband Revenue Across All Products Over the Last 6 Years
SQL Query 3: SELECT CAST(YEAR(Date) AS CHAR(4)) AS [Year], (SUM(Revenue_Broadband) / LAG(SUM(Revenue_Broadband), 1) OVER (ORDER BY YEAR(Date)) - 1) * 100 AS [Broadband Revenue Growth (%)] FROM [database_name].[schema_name].[table_name] WHERE YEAR(Date) >= YEAR(GETDATE()) - 6 GROUP BY YEAR(Date) ORDER BY [Year] ASC;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_yearly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "half-yearly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for half-yearly timeframe feedbacks
                        filtered_feedbacks_by_chart_and_half_yearly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "half-yearly"
                        ]

                        if not filtered_feedbacks_by_chart_and_half_yearly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Half-Yearly Sum of Revenue per Day and EBIT for the Last 2 Half-Years
SQL Query 1: SELECT CONCAT(YEAR(CONVERT(DATE, Date, 103)), '-H', CASE WHEN MONTH(CONVERT(DATE, Date, 103)) <= 6 THEN 1 ELSE 2 END) AS [Half-Year], SUM(Revenue_per_Day) AS [Total Revenue per Day], SUM(EBIT) AS [Total EBIT] FROM [database_name].[schema_name].[table_name] WHERE CONVERT(DATE, Date, 103) >= DATEADD(YEAR, -1, CAST(GETDATE() AS DATE)) GROUP BY YEAR(CONVERT(DATE, Date, 103)), CASE WHEN MONTH(CONVERT(DATE, Date, 103)) <= 6 THEN 1 ELSE 2 END ORDER BY [Half-Year];

Chart Title 2: Half-Yearly Average Earning per Cost by Product Over the Last Year
SQL Query 2: SELECT CONCAT(YEAR(CONVERT(DATE, Date, 103)), '-H',    CASE    WHEN MONTH(CONVERT(DATE, Date, 103)) <= 6 THEN 1    ELSE 2    END) AS [Half-Year], AVG(Earning_per_Cost) AS [Average Earning per Cost], Product AS [Product] FROM [database_name].[schema_name].[table_name] WHERE CONVERT(DATE, Date, 103) >= DATEADD(YEAR, -1, CAST(GETDATE() AS DATE)) GROUP BY YEAR(CONVERT(DATE, Date, 103)), CASE WHEN MONTH(CONVERT(DATE, Date, 103)) <= 6 THEN 1 ELSE 2 END, Product ORDER BY [Half-Year];

Chart Title 3: Half-Yearly Variance in Cost Actual vs. Budget by Product for Past 1 Year
SQL Query 3: SELECT CONCAT(YEAR(CONVERT(DATE, Date, 103)), '-H', CASE WHEN MONTH(CONVERT(DATE, Date, 103)) <= 6 THEN 1 ELSE 2 END) AS [Half-Year], SUM(CostVariance_Actual_vs_Budget) AS [Total Cost Variance (Actual vs. Budget)],  Product AS [Product] FROM [database_name].[schema_name].[table_name] WHERE CONVERT(DATE, Date, 103) >= DATEADD(YEAR, -1, CAST(GETDATE() AS DATE)) GROUP BY YEAR(CONVERT(DATE, Date, 103)), CASE WHEN MONTH(CONVERT(DATE, Date, 103)) <= 6 THEN 1 ELSE 2 END, Product ORDER BY [Half-Year];
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Half-Yearly Average EBIT and Revenue for the Last 3 Years
SQL Query 1: SELECT CONCAT(YEAR(Date), '-H', CASE WHEN MONTH(Date) <= 6 THEN 1 ELSE 2 END) AS [Half-Year], AVG(EBIT) AS [Average EBIT], AVG(Revenue) AS [Average Revenue] FROM [database_name].[schema_name].[table_name] WHERE Date >= DATEADD(YEAR, -3, CAST(GETDATE() AS DATE)) GROUP BY YEAR(Date), CASE WHEN MONTH(Date) <= 6 THEN 1 ELSE 2 END ORDER BY [Half-Year];

Chart Title 2: Half-Yearly Growth Rate of Broadband Revenue Compared to Entertainment Revenue for the Last 4 Years
SQL Query 2: WITH RevenueData AS (SELECT CONCAT(YEAR(Date), '-H', CASE WHEN MONTH(Date) <= 6 THEN 1 ELSE 2 END) AS [Half-Year], SUM(Revenue_Broadband) AS [Total Broadband Revenue], SUM(Revenue_Entertainment) AS [Total Entertainment Revenue]FROM [database_name].[schema_name].[table_name]WHERE Date >= DATEADD(YEAR, -4, CAST(GETDATE() AS DATE))GROUP BY YEAR(Date), CASE WHEN MONTH(Date) <= 6 THEN 1 ELSE 2 END ) SELECT [Half-Year], (SUM([Total Broadband Revenue]) /  LAG(SUM([Total Broadband Revenue])) OVER (ORDER BY YEAR(Date), CASE WHEN MONTH(Date) <= 6 THEN 1 ELSE 2 END)) * 100 AS [Broadband Revenue Growth Rate (%)],(SUM([Total Entertainment Revenue]) /  LAG(SUM([Total Entertainment Revenue])) OVER (ORDER BY YEAR(Date), CASE WHEN MONTH(Date) <= 6 THEN 1 ELSE 2 END)) * 100 AS [Entertainment Revenue Growth Rate (%)] FROM RevenueData GROUP BY [Half-Year] ORDER BY [Half-Year];

Chart Title 3: Half-Yearly EBIT to Revenue Ratio and Total Cost of Broadband for the Past 2 Years
SQL Query 3: SELECT CONCAT(YEAR(Date), '-H', CASE WHEN MONTH(Date) <= 6 THEN 1 ELSE 2 END) AS [Half-Year], (SUM(EBIT) / NULLIF(SUM(Revenue), 0)) * 100 AS [EBIT to Revenue Ratio (%)], SUM(Cost_Broadband) AS [Total Broadband Cost] FROM [database_name].[schema_name].[table_name] WHERE Date >= DATEADD(YEAR, -2, CAST(GETDATE() AS DATE)) GROUP BY YEAR(Date), CASE WHEN MONTH(Date) <= 6 THEN 1 ELSE 2 END ORDER BY [Half-Year];
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_half_yearly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "quarterly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for quarterly timeframe feedbacks
                        filtered_feedbacks_by_chart_and_quarterly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "quarterly"
                        ]

                        if not filtered_feedbacks_by_chart_and_quarterly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Sum of Cost Variance (Actual vs. Budget) by Product for the Past 3 Quarters
Sql Query 1: SELECT CONCAT(YEAR(CONVERT(DATE, t1.Date, 23)), '-Q', DATEPART(QUARTER, CONVERT(DATE, t1.Date, 23))) AS 'Quarter', t1.Product AS 'Product', SUM(t1.CostVariance_Actual_vs_Budget) AS 'Total Cost Variance: Actual vs Budget' FROM [database_name].[table_name] t1 JOIN [database_name].[table_name] t2 ON CONVERT(DATE, t1.Date, 23) = CONVERT(DATE, t2.Date, 23) AND t1.Product = t2.Product WHERE CONVERT(DATE, t1.Date, 23) >= DATEADD(QUARTER, -3, DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()), 0)) AND CONVERT(DATE, t1.Date, 23) <= EOMONTH(GETDATE()) GROUP BY YEAR(CONVERT(DATE, t1.Date, 23)), DATEPART(QUARTER, CONVERT(DATE, t1.Date, 23)), t1.Product ORDER BY 'Quarter', 'Product';

Chart Title 2: Quarterly Average Cost Efficiency Across All Products for the Last 6 Quarters
SQL Query 2: SELECT CONCAT(YEAR(CONVERT(DATE, Date, 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, Date, 103))) AS 'Quarter', AVG(Cost_Efficiency) AS 'Average Cost Efficiency' FROM [database_name].[table_name] WHERE CONVERT(DATE, Date, 103) >= DATEADD(QUARTER, -6, GETDATE()) GROUP BY YEAR(CONVERT(DATE, Date, 103)), DATEPART(QUARTER, CONVERT(DATE, Date, 103)) ORDER BY 'Quarter';

Chart Title 3: Quarterly Growth Rate of Broadband Revenue Compared to the Previous Quarter
SQL Query 3: SELECT CONCAT(YEAR(CONVERT(DATE, Date, 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, Date, 103))) AS 'Quarter', (SUM(Revenue_Broadband) / LAG(SUM(Revenue_Broadband)) OVER (ORDER BY YEAR(CONVERT(DATE, Date, 103)), DATEPART(QUARTER, CONVERT(DATE, Date, 103))) - 1) * 100 AS 'Broadband Revenue Growth (%)' FROM [database_name].[table_name] GROUP BY YEAR(CONVERT(DATE, Date, 103)), DATEPART(QUARTER, CONVERT(DATE, Date, 103)) ORDER BY 'Quarter';
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Sum of Entertainment Costs for 2022
Sql Query 1: SELECT CONCAT(YEAR(t1.Date), '-Q', DATEPART(QUARTER, t1.Date)) AS [Quarter], SUM(t1.Cost_Entertainment) AS [Total Entertainment Costs] FROM [database_name].[schema_name].[table_name] t1 JOIN [database_name].[schema_name].[table_name] t2 ON t1.Date = t2.Date WHERE t1.Date BETWEEN '2022-01-01' AND '2022-12-31' GROUP BY YEAR(t1.Date), DATEPART(QUARTER, t1.Date) ORDER BY [Quarter];

Chart Title 2: Quarterly Average Revenue per Product for the Past 4 Quarters
SQL Query 2: SELECT CONCAT(YEAR(Date), '-Q', DATEPART(QUARTER, Date)) AS [Quarter], Product AS [Product], AVG(Revenue) AS [Average Revenue] FROM [database_name].[schema_name].[table_name] WHERE Date >= DATEADD(YEAR, -1, GETDATE()) GROUP BY YEAR(Date), DATEPART(QUARTER, Date), Product ORDER BY [Quarter], [Product];

Chart Title 3: Quarterly EBIT Margin (EBIT as a Percentage of Revenue) Over the Last 8 Quarters
SQL Query 3: SELECT CONCAT(YEAR(Date), '-Q', DATEPART(QUARTER, Date)) AS [Quarter], (SUM(EBIT) / SUM(Revenue)) * 100 AS [EBIT Margin (%)] FROM [database_name].[schema_name].[table_name] WHERE Date >= DATEADD(YEAR, -2, GETDATE()) GROUP BY YEAR(Date), DATEPART(QUARTER, Date) ORDER BY [Quarter];
"""

                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_quarterly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "monthly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for monthly timeframe feedbacks
                        filtered_feedbacks_by_chart_and_monthly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "monthly"
                        ]

                        if not filtered_feedbacks_by_chart_and_monthly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Cost Variance (Actual vs. Budget) by Product (Last Year)
Sql Query 1: SELECT CONCAT(YEAR(CONVERT(DATE, t1.[Date], 23)), '-M', MONTH(CONVERT(DATE, t1.[Date], 23))) AS [Month], SUM(t1.CostVariance_Actual_vs_Budget) AS [Total Cost Variance (Actual vs. Budget)], t1.Product AS [Product] FROM [database_name].[schema_name].[table_name] t1  JOIN [database_name].[schema_name].[table_name] t2  ON CONVERT(DATE, t1.[Date], 23) = CAST(t2.Date AS DATE) WHERE YEAR(CONVERT(DATE, t1.[Date], 23)) = YEAR(DATEADD(YEAR, -1, CAST(GETDATE() AS DATE))) GROUP BY YEAR(CONVERT(DATE, t1.[Date], 23)), MONTH(CONVERT(DATE, t1.[Date], 23)), t1.Product ORDER BY [Month];

Chart Title 2: Monthly Total Cost Variance (Actual vs. Budget) by Product for the Current and Previous Year
Sql Query 2: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-M', MONTH(CONVERT(DATE, [Date], 103))) AS [Month], SUM([CostVariance_Actual_vs_Budget]) AS [Total Cost Variance (Actual vs. Budget)], [Product] AS [Product] FROM [database_name].[schema_name].[table_name] WHERE YEAR(CONVERT(DATE, [Date], 103)) >= YEAR(DATEADD(YEAR, -1, GETDATE())) AND YEAR(CONVERT(DATE, [Date], 103)) <= YEAR(GETDATE()) GROUP BY YEAR(CONVERT(DATE, [Date], 103)), MONTH(CONVERT(DATE, [Date], 103)), [Product] ORDER BY [Month];

Chart Title 3: Monthly Total Entertainment Costs and Cost Efficiency Ratio for the Last 3 Months
SQL Query 3: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-M', MONTH(CONVERT(DATE, [Date], 103))) AS [Month], SUM([Cost_Entertainment]) AS [Total Entertainment Costs], AVG([Cost_Efficiency]) AS [Average Cost Efficiency Ratio] FROM [database_name].[schema_name].[table_name] WHERE CONVERT(DATE, [Date], 103) >= DATEADD(MONTH, -3, GETDATE()) GROUP BY YEAR(CONVERT(DATE, [Date], 103)), MONTH(CONVERT(DATE, [Date], 103)) ORDER BY [Month];
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue for Broadband and Entertainment for the Current and Previous Year
Sql Query 1: SELECT CONCAT(YEAR([Date]), '-M', MONTH([Date])) AS [Month], SUM([Revenue_Broadband]) AS [Total Revenue], 'Broadband' AS [Product] FROM [database_name].[schema_name].[table_name] WHERE YEAR([Date]) >= YEAR(DATEADD(YEAR, -1, GETDATE())) AND YEAR([Date]) <= YEAR(GETDATE()) AND [Revenue_Broadband] IS NOT NULL GROUP BY YEAR([Date]), MONTH([Date]) UNION ALL SELECT CONCAT(YEAR([Date]), '-M', MONTH([Date])) AS [Month], SUM([Revenue_Entertainment]) AS [Total Revenue], 'Entertainment' AS [Product] FROM [database_name].[schema_name].[table_name] WHERE YEAR([Date]) >= YEAR(DATEADD(YEAR, -1, GETDATE())) AND YEAR([Date]) <= YEAR(GETDATE()) AND [Revenue_Entertainment] IS NOT NULL GROUP BY YEAR([Date]), MONTH([Date]) ORDER BY [Month];

Chart Title 2: Monthly Sum of Mobile Costs for Next Year
Sql Query 2: SELECT CONCAT(YEAR([Date]), '-M', MONTH([Date])) AS [Month], SUM([Cost_Mobile]) AS [Total Mobile Costs] FROM [database_name].[schema_name].[table_name] WHERE YEAR([Date]) = YEAR(DATEADD(YEAR, 1, GETDATE())) GROUP BY YEAR([Date]), MONTH([Date]) ORDER BY [Month];

Chart Title 3: Monthly Revenue Growth Rate (Percentage Increase) for Entertainment Over the Last 12 Months
SQL Query 3: SELECT CONCAT(YEAR(t1.[Date]), '-M', MONTH(t1.[Date])) AS [Month], ((SUM(t1.[Revenue_Entertainment]) - SUM(t2.[Revenue_Entertainment])) / NULLIF(SUM(t2.[Revenue_Entertainment]), 0)) * 100 AS [Revenue Growth Rate (%)] FROM [database_name].[schema_name].[table_name] t1 LEFT JOIN [database_name].[schema_name].[table_name] t2ON t1.[Date] = DATEADD(MONTH, -1, t2.[Date]) WHERE t1.[Date] >= DATEADD(MONTH, -12, GETDATE()) GROUP BY YEAR(t1.[Date]), MONTH(t1.[Date]) ORDER BY [Month];
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_monthly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "weekly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for weekly timeframe feedbacks
                        filtered_feedbacks_by_chart_and_weekly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "weekly"
                        ]

                        if not filtered_feedbacks_by_chart_and_weekly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Average Cost Efficiency by Product for the Last 12 Weeks
SQL Query 1: SELECT CONCAT(YEAR(CONVERT(DATE, t1.[Date], 23)), '-W', DATEPART(WEEK, CONVERT(DATE, t1.[Date], 23))) AS 'Week', t1.[Product] AS 'Product', AVG(t1.[Cost_Efficiency]) AS 'Average Cost Efficiency' FROM [database_name].[table_name] t1 JOIN [database_name].[table_name] t2 ON CONVERT(DATE, t1.[Date], 23) = CONVERT(DATE, t2.[Date], 23) AND t1.[Product] = t2.[Product] WHERE CONVERT(DATE, t1.[Date], 23) >= DATEADD(WEEK, -12, GETDATE()) GROUP BY YEAR(CONVERT(DATE, t1.[Date], 23)), DATEPART(WEEK, CONVERT(DATE, t1.[Date], 23)), t1.[Product] ORDER BY 'Week', 'Product';

Chart Title 2: Weekly Sum of Revenue and Cost Variance (Actual vs. Budget) Over the Past 8 Weeks
SQL Query 2: SELECT CONCAT(YEAR(CONVERT(DATE, Date, 103)), '-W', DATEPART(WEEK, CONVERT(DATE, Date, 103))) AS 'Week', SUM(Revenue) AS 'Total Revenue', SUM(CostVariance_Actual_vs_Budget) AS 'Cost Variance (Actual vs. Budget)' FROM [database_name].[table_name] WHERE CONVERT(DATE, Date, 103) >= DATEADD(WEEK, -8, GETDATE()) GROUP BY YEAR(CONVERT(DATE, Date, 103)), DATEPART(WEEK, CONVERT(DATE, Date, 103)) ORDER BY 'Week';

Chart Title 3: Weekly EBIT Margin (EBIT as a Percentage of Revenue) Over the Last 10 Weeks
SQL Query 3: SELECT CONCAT(YEAR(CONVERT(DATE, Date, 103)), '-W', DATEPART(WEEK, CONVERT(DATE, Date, 103))) AS 'Week', (SUM(EBIT) / SUM(Revenue)) * 100 AS 'EBIT Margin (%)' FROM [database_name].[table_name] WHERE CONVERT(DATE, Date, 103) >= DATEADD(WEEK, -10, GETDATE()) GROUP BY YEAR(CONVERT(DATE, Date, 103)), DATEPART(WEEK, CONVERT(DATE, Date, 103)) ORDER BY 'Week';
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Revenue for Entertainment in Quarter 4 in Year 2023
Sql Query 1: SELECT CONCAT(YEAR(t1.Date), '-W', DATEPART(WEEK, t1.Date)) AS [Week], SUM(t1.Revenue_Entertainment) AS [Entertainment Revenue] FROM [database_name].[schema_name].[table_name] t1 JOIN [database_name].[schema_name].[table_name] t2 ON t1.Date = t2.Date WHERE YEAR(t1.Date) = 2023 AND DATEPART(QUARTER, t1.Date) = 4 GROUP BY YEAR(t1.Date), DATEPART(WEEK, t1.Date) ORDER BY [Week];

Chart Title 2: Weekly Ratio of Entertainment Costs to Total Revenue Over the Past 12 Weeks
SQL Query 2: SELECT CONCAT(YEAR(Date), '-W', DATEPART(WEEK, Date)) AS [Week], (SUM(Cost_Entertainment) / SUM(Revenue)) * 100 AS [Entertainment Costs to Total Revenue Ratio (%)] FROM [database_name].[schema_name].[table_name] WHERE Date >= DATEADD(WEEK, -12, GETDATE()) GROUP BY YEAR(Date), DATEPART(WEEK, Date) ORDER BY [Week];

Chart Title 3: Weekly Variance in Mobile Costs and Broadband Costs for the Last 10 Weeks
SQL Query 3: SELECT CONCAT(YEAR(Date), '-W', DATEPART(WEEK, Date)) AS [Week], VAR(Cost_Mobile) AS [Variance in Mobile Costs], VAR(Cost_Broadband) AS [Variance in Broadband Costs] FROM [database_name].[schema_name].[table_name] WHERE Date >= DATEADD(WEEK, -10, GETDATE()) GROUP BY YEAR(Date), DATEPART(WEEK, Date) ORDER BY [Week];
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_weekly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "daily":
                    if (
                        chart_axis["xAxis_column"]
                        in data_summary.column_sql_data_types.keys()
                    ):
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for daily timeframe feedbacks
                        filtered_feedbacks_by_chart_and_daily_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "daily"
                        ]

                        if not filtered_feedbacks_by_chart_and_daily_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Daily Average Cost Efficiency and Earnings per Cost Over the Last 30 Days
SQL Query 1: SELECT CONVERT(DATE, t1.Date, 23) AS 'Date', AVG(t1.Cost_Efficiency) AS 'Average Cost Efficiency', AVG(t1.Earning_per_Cost) AS 'Average Earnings per Cost' FROM [database_name].[table_name] t1 JOIN [database_name].[table_name] t2 ON CONVERT(DATE, t1.Date, 23) = CONVERT(DATE, t2.Date, 23) WHERE CONVERT(DATE, t1.Date, 23) >= DATEADD(DAY, -30, GETDATE()) GROUP BY CONVERT(DATE, t1.Date, 23) ORDER BY 'Date';

Chart Title 2: Daily Sum of Revenue and Cost for the Last 2 Weeks
SQL Query 2: SELECT CONVERT(DATE, Date, 103) AS 'Date', SUM(Revenue) AS 'Total Revenue', SUM(Cost) AS 'Total Cost' FROM [database_name].[table_name] WHERE CONVERT(DATE, Date, 103) >= DATEADD(DAY, -14, GETDATE()) GROUP BY CONVERT(DATE, Date, 103) ORDER BY 'Date';

Chart Title 3: Daily Change in EBIT (Day-over-Day Difference) for the Past 10 Days
SQL Query 3: SELECT CONVERT(DATE, Date, 103) AS 'Date', EBIT - LAG(EBIT, 1) OVER (ORDER BY CONVERT(DATE, Date, 103)) AS 'Day-over-Day Change in EBIT' FROM [database_name].[table_name] WHERE CONVERT(DATE, Date, 103) >= DATEADD(DAY, -10, GETDATE()) ORDER BY 'Date';
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Daily Cost of Entertainment vs. Cost of Mobile for the Last 7 Days
SQL Query 1: SELECT CAST(t1.Date AS DATE) AS [Date], SUM(t1.Cost_Entertainment) AS [Total Cost of Entertainment], SUM(t1.Cost_Mobile) AS [Total Cost of Mobile] FROM [database_name].[schema_name].[table_name] t1 JOIN [database_name].[schema_name].[table_name] t2 ON t1.Date = t2.Date WHERE t1.Date >= DATEADD(DAY, -7, CAST(GETDATE() AS DATE)) GROUP BY CAST(t1.Date AS DATE) ORDER BY [Date];

Chart Title 2: Daily EBIT to Revenue Ratio (EBIT as a Percentage of Revenue) for the Last 14 Days
SQL Query 2: SELECT CAST(Date AS DATE) AS [Date], (SUM(EBIT) / NULLIF(SUM(Revenue), 0)) * 100 AS [EBIT to Revenue Ratio (%)] FROM [database_name].[schema_name].[table_name] WHERE Date >= DATEADD(DAY, -14, CAST(GETDATE() AS DATE)) GROUP BY CAST(Date AS DATE) ORDER BY [Date];

Chart Title 3: Daily Total Revenue vs. Total Cost for the Last 60 Days
SQL Query 3: SELECT CAST(Date AS DATE) AS [Date], SUM(Revenue) AS [Total Revenue], SUM(Cost_Broadband + Cost_Entertainment + Cost_Mobile) AS [Total Cost] FROM [database_name].[schema_name].[table_name] WHERE Date >= DATEADD(DAY, -60, CAST(GETDATE() AS DATE)) GROUP BY CAST(Date AS DATE) ORDER BY [Date];
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_daily_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

            else:
                filtered_feedbacks_by_chart_and_no_timeframe = [
                    feedback
                    for feedback in filtered_liked_feedbacks
                    if feedback.get("chart_type") == "table_chart"
                    and not feedback.get("time_frame", "").strip()
                ]

                if not filtered_feedbacks_by_chart_and_no_timeframe:
                    QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Top 5 Products by Percentage of Total EBIT
Sql Query 1: SELECT [Product] AS [Product], (SUM([EBIT]) / SUM(SUM([EBIT])) OVER ()) * 100 AS [Percentage of Total EBIT] FROM [database_name].[schema_name].[table_name] GROUP BY [Product] ORDER BY [Percentage of Total EBIT] DESC OFFSET 0 ROWS FETCH NEXT 5 ROWS ONLY;

Chart Title 2: Top 3 Products that Generate the Highest Revenue
Sql Query 2: SELECT [Product] AS [Product], SUM([Revenue]) AS [Total Revenue] FROM [database_name].[schema_name].[table_name] GROUP BY [Product] ORDER BY [Total Revenue] DESC OFFSET 0 ROWS FETCH NEXT 3 ROWS ONLY;

Chart Title 3: Total Revenue Generated by Broadband Product
Sql Query 3: SELECT 'Broadband' AS [Product], SUM([Revenue_Broadband]) AS [Total Revenue] FROM [database_name].[schema_name].[table_name];

Chart Title 4: Total Cost Incurred by Entertainment and Broadband Respectively
Sql Query 4: SELECT 'Entertainment' AS [Product], SUM([Cost_Entertainment]) AS [Total Cost] FROM [database_name].[schema_name].[table_name] UNION ALL SELECT 'Broadband' AS [Product], SUM([Cost_Broadband]) AS [Total Cost] FROM [database_name].[schema_name].[table_name];

Based on DDL 2, here are the chart titles and sql queries.

Chart Title 1: Top 5 Products by Percentage of Total EBIT
Sql Query 1: SELECT [Product] AS [Product], (SUM([EBIT]) / SUM(SUM([EBIT])) OVER ()) * 100 AS [Percentage of Total EBIT] FROM [database_name].[schema_name].[table_name] GROUP BY [Product] ORDER BY [Percentage of Total EBIT] DESC OFFSET 0 ROWS FETCH NEXT 5 ROWS ONLY;

Chart Title 2: Top 3 Products that Generate the Highest Revenue
Sql Query 2: SELECT [Product] AS [Product], SUM([Revenue]) AS [Total Revenue] FROM [database_name].[schema_name].[table_name] GROUP BY [Product] ORDER BY [Total Revenue] DESC OFFSET 0 ROWS FETCH NEXT 3 ROWS ONLY;

Chart Title 3: Total Revenue Generated by Broadband Product
Sql Query 3: SELECT 'Broadband' AS [Product], SUM([Revenue_Broadband]) AS [Total Revenue] FROM [database_name].[schema_name].[table_name];

Chart Title 4: Total Cost Incurred by Entertainment and Broadband Respectively
Sql Query 4: SELECT 'Entertainment' AS [Product], SUM([Cost_Entertainment]) AS [Total Cost] FROM [database_name].[schema_name].[table_name] UNION ALL SELECT 'Broadband' AS [Product], SUM([Cost_Broadband]) AS [Total Cost] FROM [database_name].[schema_name].[table_name];
"""
                else:
                    # Only append this line if token count allows
                    heading = "\nHere are the chart titles and sql queries\n"
                    new_data_tokens = calculate_token_usage(heading)
                    if (
                        TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                        <= TARGET_TOKEN_LIMIT
                    ):
                        QUERY_SAMPLES += heading
                        TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                    for idx, chart in enumerate(
                        filtered_feedbacks_by_chart_and_no_timeframe,
                        start=1,
                    ):
                        chart_title = chart.get("chart_title", "")
                        sql_query = chart.get("sql_query", "")
                        sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                        # Calculate token usage for the current chart and SQL query
                        new_data_tokens = calculate_token_usage(sample)

                        # Check if appending this data would exceed the token limit
                        if (
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                            <= TARGET_TOKEN_LIMIT
                        ):
                            QUERY_SAMPLES += sample

                            # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                        else:
                            # If appending would exceed, break the loop
                            break

            if (
                isinstance(chart_axis["xAxis_column"], str)
                and chart_axis["xAxis_column"] in data_summary.column_data_tribes.keys()
                and data_summary.column_data_tribes[chart_axis["xAxis_column"]]
                in ["date_related"]
                and chart_axis["xAxis_column"]
                in data_summary.column_sql_data_types.keys()
                and data_summary.column_sql_data_types[
                    chart_axis["xAxis_column"]
                ].lower()
                not in [
                    "tinyint",
                    "smallint",
                    "mediumint",
                    "int",
                    "bigint",
                    "float",
                    "double",
                    "decimal",
                    "bit",
                ]
            ):
                if time_duration == "Week":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Week"
                        and chart["chart_type"] == "table_chart"
                    ]

                    if (
                        chart_axis["xAxis_column"]
                        in data_summary.column_sql_data_types.keys()
                    ):
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Total Revenue by Product for the Past 2 Weeks
SQL Query 1: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-W', DATEPART(WEEK, CONVERT(DATE, [Date], 103))) AS [Week], SUM([Revenue]) AS [Total Revenue], [Product] AS [Product] FROM [database_name].[schema_name].[table_name] WHERE CONVERT(DATE, [Date], 103) BETWEEN DATEADD(WEEK, -2, GETDATE()) AND GETDATE() GROUP BY CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-W', DATEPART(WEEK, CONVERT(DATE, [Date], 103))), [Product] ORDER BY [Week], [Product];

Chart Title 2: Weekly Average EBIT for Next 3 Weeks
SQL Query 2: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-W', DATEPART(WEEK, CONVERT(DATE, [Date], 103))) AS [Week], AVG([EBIT]) AS [Average EBIT] FROM [database_name].[schema_name].[table_name] WHERE CONVERT(DATE, [Date], 103) BETWEEN GETDATE() AND DATEADD(WEEK, 3, GETDATE()) GROUP BY CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-W', DATEPART(WEEK, CONVERT(DATE, [Date], 103))) ORDER BY [Week];

Chart Title 3: Weekly Total Cost of Entertainment for Last Week
SQL Query 3: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-W', DATEPART(WEEK, CONVERT(DATE, [Date], 103))) AS [Week], SUM([Cost_Entertainment]) AS [Total Cost of Entertainment] FROM [database_name].[schema_name].[table_name] WHERE CONVERT(DATE, [Date], 103) BETWEEN DATEADD(WEEK, -1, GETDATE()) AND GETDATE() GROUP BY CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-W', DATEPART(WEEK, CONVERT(DATE, [Date], 103))) ORDER BY [Week];

Chart Title 4: Weekly Maximum Revenue from Week 1 - Week 4 in March 2023
SQL Query 4: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-W', DATEPART(WEEK, CONVERT(DATE, [Date], 103))) AS [Week], MAX([Revenue]) AS [Maximum Revenue] FROM [database_name].[schema_name].[table_name] WHERE CONVERT(DATE, [Date], 103) BETWEEN '2023-03-01' AND '2023-03-31' AND DATEPART(WEEK, CONVERT(DATE, [Date], 103)) BETWEEN 1 AND 4 GROUP BY CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-W', DATEPART(WEEK, CONVERT(DATE, [Date], 103))) ORDER BY [Week];
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Total Revenue by Product for the Past 2 Weeks
SQL Query 1: SELECT CONCAT(YEAR([DATE]), '-W', DATEPART(WEEK, [DATE])) AS [Week], SUM([Revenue]) AS [Total Revenue], [Product] AS [Product] FROM [database_name].[schema_name].[table_name] WHERE [DATE] BETWEEN DATEADD(WEEK, -2, GETDATE()) AND GETDATE() GROUP BY CONCAT(YEAR([DATE]), '-W', DATEPART(WEEK, [DATE])), [Product] ORDER BY [Week], [Product];

Chart Title 2: Weekly Average EBIT for Next 3 Weeks
SQL Query 2: SELECT CONCAT(YEAR([DATE]), '-W', DATEPART(WEEK, [DATE])) AS [Week], AVG([EBIT]) AS [Average EBIT] FROM [database_name].[schema_name].[table_name] WHERE [DATE] BETWEEN GETDATE() AND DATEADD(WEEK, 3, GETDATE()) GROUP BY CONCAT(YEAR([DATE]), '-W', DATEPART(WEEK, [DATE])) ORDER BY [Week];

Chart Title 3: Weekly Total Cost of Entertainment for Last Week
SQL Query 3: SELECT CONCAT(YEAR([DATE]), '-W', DATEPART(WEEK, [DATE])) AS [Week], SUM([Cost_Entertainment]) AS [Total Cost of Entertainment] FROM [database_name].[schema_name].[table_name] WHERE [DATE] BETWEEN DATEADD(WEEK, -1, GETDATE()) AND GETDATE() GROUP BY CONCAT(YEAR([DATE]), '-W', DATEPART(WEEK, [DATE])) ORDER BY [Week];

Chart Title 4: Weekly Maximum Revenue from Week 1 - Week 4 in March 2023
SQL Query 4: SELECT CONCAT(YEAR([DATE]), '-W', DATEPART(WEEK, [DATE])) AS [Week], MAX([Revenue]) AS [Maximum Revenue] FROM [database_name].[schema_name].[table_name] WHERE [DATE] BETWEEN '2023-03-01' AND '2023-03-31' AND DATEPART(WEEK, [DATE]) BETWEEN 1 AND 4 GROUP BY CONCAT(YEAR([DATE]), '-W', DATEPART(WEEK, [DATE])) ORDER BY [Week];
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif time_duration == "Month":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Month"
                        and chart["chart_type"] == "table_chart"
                    ]

                    if (
                        chart_axis["xAxis_column"]
                        in data_summary.column_sql_data_types.keys()
                    ):
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue by Product for the Past 6 Months
SQL Query 1: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-M', MONTH(CONVERT(DATE, [Date], 103))) AS [Month], SUM([Revenue]) AS [Total Revenue], [Product] AS [Product] FROM [database_name].[schema_name].[table_name] WHERE CONVERT(DATE, [Date], 103) >= DATEADD(MONTH, -6, GETDATE()) GROUP BY CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-M', MONTH(CONVERT(DATE, [Date], 103))), [Product] ORDER BY [Month] ASC, [Product];

Chart Title 2: Monthly Average EBIT for Next January
SQL Query 2: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-M', MONTH(CONVERT(DATE, [Date], 103))) AS [Month], AVG([EBIT]) AS [Average EBIT] FROM [database_name].[schema_name].[table_name] WHERE YEAR(CONVERT(DATE, [Date], 103)) = YEAR(DATEADD(YEAR, 1, GETDATE())) AND MONTH(CONVERT(DATE, [Date], 103)) = 1 GROUP BY CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-M', MONTH(CONVERT(DATE, [Date], 103))) ORDER BY [Month];

Chart Title 3: Monthly Cost of Entertainment for March
SQL Query 3: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-M', MONTH(CONVERT(DATE, [Date], 103))) AS [Month], SUM([Cost_Entertainment]) AS [Total Cost of Entertainment] FROM [database_name].[schema_name].[table_name] WHERE MONTH(CONVERT(DATE, [Date], 103)) = 3 AND YEAR(CONVERT(DATE, [Date], 103)) = YEAR(GETDATE()) GROUP BY CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-M', MONTH(CONVERT(DATE, [Date], 103))) ORDER BY [Month];

Chart Title 4: Monthly Revenue from Jan 2022 - Mar 2022
SQL Query 4: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-M', MONTH(CONVERT(DATE, [Date], 103))) AS [Month], SUM([Revenue]) AS [Total Revenue] FROM [database_name].[table_name] WHERE CONVERT(DATE, [Date], 103) BETWEEN '2022-01-01' AND '2022-03-31' GROUP BY CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-M', MONTH(CONVERT(DATE, [Date], 103))) ORDER BY [Month];
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue by Product for the Past 6 Months
SQL Query 1: SELECT CONCAT(YEAR([DATE]), '-M', MONTH([DATE])) AS [Month], SUM([Revenue]) AS [Total Revenue], [Product] AS [Product] FROM [database_name].[schema_name].[table_name] WHERE [DATE] >= DATEADD(MONTH, -6, GETDATE()) GROUP BY CONCAT(YEAR([DATE]), '-M', MONTH([DATE])), [Product] ORDER BY [Month] ASC, [Product];

Chart Title 2: Monthly Average EBIT for Next January
SQL Query 2: SELECT CONCAT(YEAR([DATE]), '-M', MONTH([DATE])) AS [Month], AVG([EBIT]) AS [Average EBIT] FROM [database_name].[schema_name].[table_name] WHERE YEAR([DATE]) = YEAR(DATEADD(YEAR, 1, GETDATE())) AND MONTH([DATE]) = 1 GROUP BY CONCAT(YEAR([DATE]), '-M', MONTH([DATE])) ORDER BY [Month];

Chart Title 3: Monthly Cost of Entertainment for March
SQL Query 3: SELECT CONCAT(YEAR([Date]), '-M', MONTH([Date])) AS [Month], SUM([Cost_Entertainment]) AS [Total Cost of Entertainment] FROM [database_name].[schema_name].[table_name] WHERE MONTH([Date]) = 3 AND YEAR([Date]) = YEAR(GETDATE()) GROUP BY CONCAT(YEAR([Date]), '-M', MONTH([Date])) ORDER BY [Month];

Chart Title 4: Monthly Revenue from Jan 2022 - Mar 2022
SQL Query 4: SELECT CONCAT(YEAR([Date]), '-M', MONTH([Date])) AS [Month], SUM([Revenue]) AS [Total Revenue] FROM [database_name].[table_name] WHERE [Date] BETWEEN '2022-01-01' AND '2022-03-31' GROUP BY CONCAT(YEAR([Date]), '-M', MONTH([Date])) ORDER BY [Month];
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif time_duration == "Quarter":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Quarter"
                        and chart["chart_type"] == "table_chart"
                    ]

                    if (
                        chart_axis["xAxis_column"]
                        in data_summary.column_sql_data_types.keys()
                    ):
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Total Revenue for the Last Q3 SQL Query 1: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, [Date], 103))) AS [Quarter], SUM([Revenue]) AS [Total Revenue] FROM [database_name].[table_name] WHERE DATEPART(QUARTER, CONVERT(DATE, [Date], 103)) = 3 AND CONVERT(DATE, [Date], 103) >= DATEADD(YEAR, -1, GETDATE()) GROUP BY CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, [Date], 103))) ORDER BY [Quarter];

Chart Title 2: Quarterly EBIT for the Next Quarter
SQL Query 2: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, [Date], 103))) AS [Quarter], SUM(EBIT) AS [Total EBIT] FROM [database_name].[table_name] WHERE CONVERT(DATE, [Date], 103) BETWEEN GETDATE() AND DATEADD(QUARTER, 1, GETDATE()) GROUP BY CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, [Date], 103))) ORDER BY [Quarter];

Chart Title 3: Quarterly Average Revenue for the Past H2
SQL Query 3: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, [Date], 103))) AS [Quarter], SUM([EBIT]) AS [Total EBIT] FROM [database_name].[table_name] WHERE CONVERT(DATE, [Date], 103) BETWEEN GETDATE() AND DATEADD(QUARTER, 1, GETDATE()) GROUP BY CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, [Date], 103))) ORDER BY [Quarter];

Chart Title 4: Quarterly Total Cost for Q1 2023 - Q3 2023
SQL Query 4: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, [Date], 103))) AS [Quarter], SUM([Cost_Entertainment] + [Cost_Broadband] + [Cost_Mobile]) AS [Total Cost] FROM [database_name].[table_name] WHERE YEAR(CONVERT(DATE, [Date], 103)) = 2023 AND DATEPART(QUARTER, CONVERT(DATE, [Date], 103)) BETWEEN 1 AND 3 GROUP BY CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, [Date], 103))) ORDER BY [Quarter];
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Total Revenue for the Last Q3 SQL Query 1: SELECT CONCAT(YEAR([DATE]), '-Q', DATEPART(QUARTER, [DATE])) AS [Quarter], SUM([Revenue]) AS [Total Revenue] FROM [database_name].[table_name] WHERE DATEPART(QUARTER, [DATE]) = 3 AND [DATE] >= DATEADD(YEAR, -1, GETDATE()) GROUP BY CONCAT(YEAR([DATE]), '-Q', DATEPART(QUARTER, [DATE])) ORDER BY [Quarter];

Chart Title 2: Quarterly EBIT for the Next Quarter
SQL Query 2: SELECT CONCAT(YEAR([DATE]), '-Q', DATEPART(QUARTER, [DATE])) AS [Quarter], SUM(EBIT) AS [Total EBIT] FROM [database_name].[table_name] WHERE [DATE] BETWEEN GETDATE() AND DATEADD(QUARTER, 1, GETDATE()) GROUP BY CONCAT(YEAR([DATE]), '-Q', DATEPART(QUARTER, [DATE])) ORDER BY [Quarter];

Chart Title 3: Quarterly Average Revenue for the Past H2
SQL Query 3: SELECT CONCAT(YEAR([DATE]), '-Q', DATEPART(QUARTER, [DATE])) AS [Quarter], SUM([EBIT]) AS [Total EBIT] FROM [database_name].[table_name] WHERE [DATE] BETWEEN GETDATE() AND DATEADD(QUARTER, 1, GETDATE()) GROUP BY CONCAT(YEAR([DATE]), '-Q', DATEPART(QUARTER, [DATE])) ORDER BY [Quarter];

Chart Title 4: Quarterly Total Cost for Q1 2023 - Q3 2023
SQL Query 4: SELECT CONCAT(YEAR([Date]), '-Q', DATEPART(QUARTER, [Date])) AS [Quarter], SUM([Cost_Entertainment] + [Cost_Broadband] + [Cost_Mobile]) AS [Total Cost] FROM [database_name].[table_name] WHERE YEAR([Date]) = 2023 AND DATEPART(QUARTER, [Date]) BETWEEN 1 AND 3 GROUP BY CONCAT(YEAR([Date]), '-Q', DATEPART(QUARTER, [Date])) ORDER BY [Quarter];
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif time_duration == "Year":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Year"
                        and chart["chart_type"] == "table_chart"
                    ]

                    if (
                        chart_axis["xAxis_column"]
                        in data_summary.column_sql_data_types.keys()
                    ):
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Total Revenue by Product Over the Past 5 Years
SQL Query 1: SELECT CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR) AS [Year], SUM([Revenue]) AS [Total Revenue], [Product] AS [Product] FROM [database_name].[table_name] WHERE CONVERT(DATE, [Date], 103) >= DATEADD(YEAR, -5, GETDATE()) GROUP BY CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR), [Product] ORDER BY [Year] ASC, [Product];

Chart Title 2: Yearly Average EBIT for Next Year
SQL Query 2: SELECT CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR) AS [Year], AVG([EBIT]) AS [Average EBIT] FROM [database_name].[table_name] WHERE YEAR(CONVERT(DATE, [Date], 103)) = YEAR(GETDATE()) + 1 GROUP BY CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR) ORDER BY [Year];

Chart Title 3: Yearly Total Revenue for 2022
SQL Query 3: SELECT CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR) AS [Year], SUM([Revenue]) AS [Total Revenue] FROM [database_name].[table_name] WHERE YEAR(CONVERT(DATE, [Date], 103)) = 2022 GROUP BY CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR) ORDER BY [Year];

Chart Title 4: Yearly Cost and Revenue for the Last 3 Years
SQL Query 4: SELECT CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR) AS [Year], SUM([Cost_Entertainment] + [Cost_Broadband] + [Cost_Mobile]) AS [Total Cost], SUM([Revenue]) AS [Total Revenue] FROM [database_name].[table_name] WHERE CONVERT(DATE, [Date], 103) >= DATEADD(YEAR, -3, GETDATE()) GROUP BY CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR) ORDER BY [Year];

Chart Title 5: Yearly Total Revenue for 2022 - 2023
SQL Query 5: SELECT CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR) AS [Year], SUM([Revenue]) AS [Total Revenue] FROM [database_name].[table_name] WHERE YEAR(CONVERT(DATE, [Date], 103)) BETWEEN 2022 AND 2023 GROUP BY CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR) ORDER BY [Year];
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Total Revenue by Product Over the Past 5 Years
SQL Query 1: SELECT CAST(YEAR([DATE]) AS VARCHAR) AS [Year], SUM([Revenue]) AS [Total Revenue], [Product] AS [Product] FROM [database_name].[table_name] WHERE [DATE] >= DATEADD(YEAR, -5, GETDATE()) GROUP BY CAST(YEAR([DATE]) AS VARCHAR), [Product] ORDER BY [Year] ASC, [Product];

Chart Title 2: Yearly Average EBIT for Next Year
SQL Query 2: SELECT CAST(YEAR([DATE]) AS VARCHAR) AS [Year], AVG([EBIT]) AS [Average EBIT] FROM [database_name].[table_name] WHERE YEAR([DATE]) = YEAR(GETDATE()) + 1 GROUP BY CAST(YEAR([DATE]) AS VARCHAR) ORDER BY [Year];

Chart Title 3: Yearly Total Revenue for 2022
SQL Query 3: SELECT CAST(YEAR([DATE]) AS VARCHAR) AS [Year], SUM([Revenue]) AS [Total Revenue] FROM [database_name].[table_name] WHERE YEAR([DATE]) = 2022 GROUP BY CAST(YEAR([DATE]) AS VARCHAR) ORDER BY [Year];

Chart Title 4: Yearly Cost and Revenue for the Last 3 Years
SQL Query 4: SELECT CAST(YEAR([DATE]) AS VARCHAR) AS [Year], SUM([Cost_Entertainment] + [Cost_Broadband] + [Cost_Mobile]) AS [Total Cost], SUM([Revenue]) AS [Total Revenue] FROM [database_name].[table_name] WHERE [DATE] >= DATEADD(YEAR, -3, GETDATE()) GROUP BY CAST(YEAR([DATE]) AS VARCHAR) ORDER BY [Year];

Chart Title 5: Yearly Total Revenue for 2022 - 2023
SQL Query 5: SELECT CAST(YEAR([DATE]) AS VARCHAR) AS [Year], SUM([Revenue]) AS [Total Revenue] FROM [database_name].[table_name] WHERE YEAR([DATE]) BETWEEN 2022 AND 2023 GROUP BY CAST(YEAR([DATE]) AS VARCHAR) ORDER BY [Year];
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

        # Not table chart
        else:
            x_column = chart_axis["xAxis_column"]
            if (
                isinstance(x_column, str)
                and x_column in data_summary.column_data_tribes.keys()
                and data_summary.column_data_tribes[x_column] == "date_related"
            ):
                if timeframe.lower() == "yearly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        # Handle Yearly Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_yearly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "yearly"
                        ]

                        if not filtered_feedbacks_by_chart_and_yearly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Total Revenue by Product Over the Last 5 Years
SQL Query 1: SELECT CAST(YEAR(CONVERT(DATE, t1.[Date], 120)) AS VARCHAR) AS xAxis, SUM(t1.[Revenue]) AS yAxis, t1.[Product] AS series FROM [database_name].[table_name] t1 JOIN [database_name].[table_name] t2 ON CONVERT(DATE, t1.[Date], 120) = CONVERT(DATE, t2.[Date], 120) AND t1.[Product] = t2.[Product] WHERE CONVERT(DATE, t1.[Date], 120) >= DATEADD(YEAR, -5, GETDATE()) GROUP BY CAST(YEAR(CONVERT(DATE, t1.[Date], 120)) AS VARCHAR), t1.[Product] ORDER BY xAxis ASC, series;

Chart Title 2: Yearly Breakdown of Cost and Revenue for Each Product Over the Last 5 Years
SQL Query 2: SELECT CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR) AS xAxis, SUM([Cost_Entertainment] + [Cost_Mobile] + [Cost_Broadband]) AS yAxis_Cost, SUM([Revenue_Entertainment] + [Revenue_Broadband]) AS yAxis_Revenue, [Product] AS series FROM [database_name].[table_name] WHERE CONVERT(DATE, [Date], 103) >= DATEADD(YEAR, -5, GETDATE()) GROUP BY CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR), [Product] ORDER BY xAxis ASC, series;

Chart Title 3: Yearly Average Revenue per Day by Product Over the Last 5 Years
SQL Query 3: SELECT CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR) AS xAxis, AVG([Revenue_per_Day]) AS yAxis, [Product] AS series FROM [database_name].[table_name] WHERE YEAR(CONVERT(DATE, [Date], 103)) >= YEAR(GETDATE()) - 5 GROUP BY CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR), [Product];
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Sum of Revenue by Product for the Last 5 Years
SQL Query 1: SELECT CAST(YEAR(t1.[Date]) AS VARCHAR) AS xAxis, SUM(t1.[Revenue]) AS yAxis, t1.[Product] AS series FROM [database_name].[table_name] t1 JOIN [database_name].[table_name] t2 ON t1.[Date] = t2.[Date] AND t1.[Product] = t2.[Product] WHERE YEAR(t1.[Date]) >= YEAR(GETDATE()) - 5 GROUP BY CAST(YEAR(t1.[Date]) AS VARCHAR), t1.[Product] ORDER BY xAxis;

Chart Title 2: Yearly Average EBIT Across All Products Over the Last 3 Years
SQL Query 2: SELECT CAST(YEAR([Date]) AS VARCHAR) AS xAxis, AVG([EBIT]) AS yAxis FROM [database_name].[table_name] WHERE YEAR([Date]) >= YEAR(GETDATE()) - 3 GROUP BY CAST(YEAR([Date]) AS VARCHAR) ORDER BY xAxis;

Chart Title 3: Yearly Growth in Broadband Revenue Across All Products Over the Last 6 Years
SQL Query 3: SELECT CAST(YEAR([Date]) AS VARCHAR) AS xAxis, (SUM([Revenue_Broadband]) / LAG(SUM([Revenue_Broadband]), 1) OVER (ORDER BY YEAR([Date])) - 1) * 100 AS yAxis FROM [database_name].[table_name] WHERE YEAR([Date]) >= YEAR(GETDATE()) - 6 GROUP BY CAST(YEAR([Date]) AS VARCHAR) ORDER BY xAxis;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_yearly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "half-yearly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        # Handle Half-Yearly Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_half_yearly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "half-yearly"
                        ]

                        if not filtered_feedbacks_by_chart_and_half_yearly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Half-Yearly Sum of Revenue per Day and EBIT for the Last 2 Half-Years
SQL Query 1: SELECT CONCAT(YEAR(CONVERT(DATE, Date, 103)), '-H', CASE WHEN MONTH(CONVERT(DATE, Date, 103)) <= 6 THEN '1' ELSE '2' END) AS xAxis, SUM(Revenue_per_Day) AS yAxis, SUM(EBIT) AS yAxis2 FROM [database_name].[table_name] WHERE CONVERT(DATE, Date, 103) >= DATEADD(YEAR, -1, GETDATE()) GROUP BY CONCAT(YEAR(Date), '-H', CASE WHEN MONTH(CONVERT(DATE, Date, 103)) <= 6 THEN '1' ELSE '2' END) ORDER BY xAxis;

Chart Title 2: Half-Yearly Average Earning per Cost by Product Over the Last Year
SQL Query 2: SELECT CONCAT(YEAR(CONVERT(DATE, Date, 103)), '-H', CASE WHEN MONTH(CONVERT(DATE, Date, 103)) <= 6 THEN '1' ELSE '2' END) AS xAxis, AVG(Earning_per_Cost) AS yAxis, Product AS series FROM [database_name].[table_name] WHERE CONVERT(DATE, Date, 103) >= DATEADD(YEAR, -1, GETDATE()) GROUP BY CONCAT(YEAR(CONVERT(DATE, Date, 103)), '-H', CASE WHEN MONTH(CONVERT(DATE, Date, 103)) <= 6 THEN '1' ELSE '2' END), Product ORDER BY xAxis;

Chart Title 3: Half-Yearly Variance in Cost Actual vs. Budget by Product for Past 1 Year
SQL Query 3: SELECT CONCAT(YEAR(CONVERT(DATE, Date, 103)), '-H', CASE WHEN MONTH(CONVERT(DATE, Date, 103)) <= 6 THEN '1' ELSE '2' END) AS xAxis, SUM(CostVariance_Actual_vs_Budget) AS yAxis, Product AS series FROM [database_name].[table_name] WHERE CONVERT(DATE, Date, 103) >= DATEADD(YEAR, -1, GETDATE()) GROUP BY CONCAT(YEAR(CONVERT(DATE, Date, 103)), '-H', CASE WHEN MONTH(CONVERT(DATE, Date, 103)) <= 6 THEN '1' ELSE '2' END), Product ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Half-Yearly Average EBIT and Revenue for the Last 3 Years
SQL Query 1: SELECT CONCAT(YEAR(Date), '-H', CASE WHEN MONTH(Date) <= 6 THEN '1' ELSE '2' END) AS xAxis, AVG(EBIT) AS yAxis, AVG(Revenue) AS yAxis2 FROM [database_name].[table_name] WHERE Date >= DATEADD(YEAR, -3, GETDATE()) GROUP BY CONCAT(YEAR(Date), '-H', CASE WHEN MONTH(Date) <= 6 THEN '1' ELSE '2' END) ORDER BY xAxis;

Chart Title 2: Half-Yearly Growth Rate of Broadband Revenue Compared to Entertainment Revenue for the Last 4 Years
SQL Query 2: SELECT CONCAT(YEAR(Date), '-H', CASE WHEN MONTH(Date) <= 6 THEN '1' ELSE '2' END) AS xAxis, (SUM(Revenue_Broadband) / NULLIF(LAG(SUM(Revenue_Broadband), 1) OVER (ORDER BY YEAR(Date), CASE WHEN MONTH(Date) <= 6 THEN '1' ELSE '2' END), 0)) * 100 AS yAxis, (SUM(Revenue_Entertainment) / NULLIF(LAG(SUM(Revenue_Entertainment), 1) OVER (ORDER BY YEAR(Date), CASE WHEN MONTH(Date) <= 6 THEN '1' ELSE '2' END), 0)) * 100 AS yAxis2 FROM [database_name].[table_name] WHERE Date >= DATEADD(YEAR, -4, GETDATE()) GROUP BY CONCAT(YEAR(Date), '-H', CASE WHEN MONTH(Date) <= 6 THEN '1' ELSE '2' END) ORDER BY xAxis;

Chart Title 3: Half-Yearly EBIT to Revenue Ratio and Total Cost of Broadband for the Past 2 Years
SQL Query 3: SELECT CONCAT(YEAR(Date), '-H', CASE WHEN MONTH(Date) <= 6 THEN '1' ELSE '2' END) AS xAxis, (SUM(EBIT) / NULLIF(SUM(Revenue), 0)) * 100 AS yAxis, SUM(Cost_Broadband) AS yAxis2 FROM [database_name].[table_name] WHERE Date >= DATEADD(YEAR, -2, GETDATE()) GROUP BY CONCAT(YEAR(Date), '-H', CASE WHEN MONTH(Date) <= 6 THEN '1' ELSE '2' END) ORDER BY xAxis;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_half_yearly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "quarterly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        # Handle Quarterly Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_quarterly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "quarterly"
                        ]

                        if not filtered_feedbacks_by_chart_and_quarterly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Sum of Cost Variance (Actual vs. Budget) by Product for the Past 3 Quarters
Sql Query 1: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, [Date], 103))) AS xAxis, SUM(t1.[CostVariance_Actual_vs_Budget]) AS yAxis, t1.[Product] AS series FROM [database_name].[table_name] t1 JOIN [database_name].[table_name] t2 ON CONVERT(DATE, t.[Date], 103) = CONVERT(DATE, t2.[Date], 103) AND t1.[Product] = t2.[Product] WHERE CONVERT(DATE, [Date], 103) >= DATEADD(QUARTER, -3, DATEFROMPARTS(YEAR(GETDATE()), 1, 1)) AND CONVERT(DATE, [Date], 103) <= EOMONTH(GETDATE()) GROUP BY CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, [Date])), t1.[Product];

Chart Title 2: Quarterly Average Cost Efficiency Across All Products for the Last 6 Quarters
SQL Query 2: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, [Date], 103))) AS xAxis, AVG([Cost_Efficiency]) AS yAxis FROM [database_name].[table_name] WHERE CONVERT(DATE, [Date], 103) >= DATEADD(MONTH, -18, GETDATE()) GROUP BY CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, [Date], 103))) ORDER BY xAxis;

Chart Title 3: Quarterly Growth Rate of Broadband Revenue Compared to the Previous Quarter
SQL Query 3: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, [Date], 103))) AS xAxis, (SUM([Revenue_Broadband]) * 1.0 / LAG(SUM([Revenue_Broadband])) OVER (ORDER BY YEAR(CONVERT(DATE, [Date], 103)), DATEPART(QUARTER, CONVERT(DATE, [Date], 103)))) AS yAxis FROM [database_name].[table_name] GROUP BY CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, [Date], 103))) ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Sum of Entertainment Costs for 2022
Sql Query 1: SELECT CONCAT(YEAR(t1.Date), '-Q', DATEPART(QUARTER, t1.Date)) AS xAxis, SUM(t1.Cost_Entertainment) AS yAxis FROM [database_name].[table_name] t1 JOIN [database_name].[table_name] t2 ON t1.Date = t2.Date WHERE t1.Date BETWEEN '2022-01-01' AND '2022-12-31' GROUP BY CONCAT(YEAR(t1.Date), '-Q', DATEPART(QUARTER, t1.Date)) ORDER BY xAxis;

Chart Title 2: Quarterly Average Revenue per Product for the Past 4 Quarters
SQL Query 2: SELECT CONCAT(YEAR(Date), '-Q', DATEPART(QUARTER, Date)) AS xAxis, AVG(Revenue) AS yAxis, Product AS series FROM [database_name].[table_name] WHERE Date >= DATEADD(YEAR, -1, GETDATE()) GROUP BY CONCAT(YEAR(Date), '-Q', DATEPART(QUARTER, Date)), Product ORDER BY xAxis;

Chart Title 3: Quarterly EBIT Margin (EBIT as a Percentage of Revenue) Over the Last 8 Quarters
SQL Query 3: SELECT CONCAT(YEAR(Date), '-Q', DATEPART(QUARTER, Date)) AS xAxis, (SUM(EBIT) * 100.0 / SUM(Revenue)) AS yAxis FROM [database_name].[table_name] WHERE Date >= DATEADD(YEAR, -2, GETDATE()) GROUP BY CONCAT(YEAR(Date), '-Q', DATEPART(QUARTER, Date)) ORDER BY xAxis;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_quarterly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "monthly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        # Handle Monthly Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_monthly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "monthly"
                        ]
                        if not filtered_feedbacks_by_chart_and_monthly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Cost Variance (Actual vs. Budget) by Product (Last Year)
Sql Query 1: SELECT CONCAT(YEAR(CONVERT(DATE, Date, 103)), '-M', MONTH(CONVERT(DATE, Date, 103))) AS xAxis, SUM(CostVariance_Actual_vs_Budget) AS yAxis, Product AS series FROM [database_name].[table_name] WHERE YEAR(CONVERT(DATE, Date, 103)) = YEAR(DATEADD(YEAR, -1, GETDATE())) GROUP BY CONCAT(YEAR(CONVERT(DATE, Date, 103)), '-M', MONTH(CONVERT(DATE, Date, 103))), Product ORDER BY xAxis;

Chart Title 2: Monthly Total Cost Variance (Actual vs. Budget) by Product for the Current and Previous Year
Sql Query 2: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-M', MONTH(CONVERT(DATE, [Date], 103))) AS xAxis, SUM(CostVariance_Actual_vs_Budget) AS yAxis, Product AS series FROM [database_name].[table_name] WHERE YEAR(CONVERT(DATE, [Date], 103)) BETWEEN YEAR(DATEADD(YEAR, -1, GETDATE())) AND YEAR(GETDATE()) GROUP BY CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-M', MONTH(CONVERT(DATE, [Date], 103))), Product ORDER BY xAxis;

Chart Title 3: Monthly Total Entertainment Costs and Cost Efficiency Ratio for the Last 3 Months
SQL Query 3: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-M', MONTH(CONVERT(DATE, [Date], 103))) AS xAxis, SUM(Cost_Entertainment) AS yAxis, AVG(Cost_Efficiency) AS yAxis2 FROM [database_name].[table_name] WHERE CONVERT(DATE, [Date], 103) >= DATEADD(MONTH, -3, GETDATE()) GROUP BY CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-M', MONTH(CONVERT(DATE, [Date], 103))) ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue for Broadband and Entertainment for the Current and Previous Year
Sql Query 1: SELECT CONCAT(YEAR(Date), '-M', MONTH(Date)) AS xAxis, SUM(Revenue_Broadband) AS yAxis, 'Broadband' AS series FROM [database_name].[table_name] WHERE YEAR(Date) >= YEAR(DATEADD(YEAR, -1, GETDATE())) AND YEAR(Date) <= YEAR(GETDATE()) AND Revenue_Broadband IS NOT NULL GROUP BY CONCAT(YEAR(Date), '-M', MONTH(Date)), series UNION ALL SELECT CONCAT(YEAR(Date), '-M', MONTH(Date)) AS xAxis, SUM(Revenue_Entertainment) AS yAxis, 'Entertainment' AS series FROM [database_name].[table_name] WHERE YEAR(Date) >= YEAR(DATEADD(YEAR, -1, GETDATE())) AND YEAR(Date) <= YEAR(GETDATE()) AND Revenue_Entertainment IS NOT NULL GROUP BY CONCAT(YEAR(Date), '-M', MONTH(Date)), series;

Chart Title 2: Monthly Sum of Mobile Costs for Next Year
Sql Query 2: SELECT CONCAT(YEAR(Date), '-M', MONTH(Date)) AS xAxis, SUM(Cost_Mobile) AS yAxis FROM [database_name].[table_name] WHERE YEAR(Date) = YEAR(DATEADD(YEAR, 1, GETDATE())) GROUP BY CONCAT(YEAR(Date), '-M', MONTH(Date)) ORDER BY xAxis;

Chart Title 3: Monthly Revenue Growth Rate (Percentage Increase) for Entertainment Over the Last 12 Months
SQL Query 3: SELECT CONCAT(YEAR(t1.Date), '-M', MONTH(t1.Date)) AS xAxis, ((SUM(t1.Revenue_Entertainment) - ISNULL(SUM(t2.Revenue_Entertainment), 0)) / NULLIF(SUM(t2.Revenue_Entertainment), 0)) * 100 AS yAxis FROM [database_name].[table_name] t1 LEFT JOIN [database_name].[table_name] t2 ON t1.Date = DATEADD(MONTH, 1, t2.Date) WHERE t1.Date >= DATEADD(MONTH, -12, GETDATE()) GROUP BY CONCAT(YEAR(t1.Date), '-M', MONTH(t1.Date)) ORDER BY xAxis;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_monthly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "weekly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        # Handle Weekly Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_weekly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "weekly"
                        ]

                        if not filtered_feedbacks_by_chart_and_weekly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Average Cost Efficiency by Product for the Last 12 Weeks
SQL Query 1: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-W', DATEPART(WEEK, CONVERT(DATE, [Date], 103))) AS xAxis, AVG(t1.Cost_Efficiency) AS yAxis, t1.Product AS series FROM [database_name].[table_name] t1 JOIN [database_name].[table_name] t2 ON CONVERT(DATE, t1.[Date], 103) = CONVERT(DATE, t2.[Date], 103) AND t1.Product = t2.Product WHERE CONVERT(DATE, t1.[Date], 103) >= DATEADD(WEEK, -12, GETDATE()) GROUP BY CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-W', DATEPART(WEEK, CONVERT(DATE, [Date], 103))), t1.Product ORDER BY xAxis;

Chart Title 2: Weekly Sum of Revenue and Cost Variance (Actual vs. Budget) Over the Past 8 Weeks
SQL Query 2: SELECT CONCAT(YEAR(CONVERT(DATE, Date, 103)), '-W', DATEPART(WEEK, CONVERT(DATE, Date, 103))) AS xAxis, SUM(Revenue) AS yAxis, SUM(CostVariance_Actual_vs_Budget) AS yAxis2 FROM [database_name].[table_name] WHERE CONVERT(DATE, Date, 103) >= DATEADD(WEEK, -8, GETDATE()) GROUP BY CONCAT(YEAR(CONVERT(DATE, Date, 103)), '-W', DATEPART(WEEK, CONVERT(DATE, Date, 103))) ORDER BY xAxis;

Chart Title 3: Weekly EBIT Margin (EBIT as a Percentage of Revenue) Over the Last 10 Weeks
SQL Query 3: SELECT CONCAT(YEAR(CONVERT(DATE, Date, 103)), '-W', DATEPART(WEEK, CONVERT(DATE, Date, 103))) AS xAxis, (SUM(EBIT) * 100.0 / SUM(Revenue)) AS yAxis FROM [database_name].[table_name] WHERE CONVERT(DATE, Date, 103) >= DATEADD(WEEK, -10, GETDATE()) GROUP BY CONCAT(YEAR(CONVERT(DATE, Date, 103)), '-W', DATEPART(WEEK, CONVERT(DATE, Date, 103))) ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Revenue for Entertainment in Quarter 4 in Year 2023
Sql Query 1: SELECT CONCAT(YEAR(t1.Date), '-W', DATEPART(WEEK, t1.Date)) AS xAxis, SUM(t1.Revenue_Entertainment) AS yAxis FROM [database_name].[table_name] t1 JOIN [database_name].[table_name] t2 ON t1.Date = t2.Date WHERE YEAR(t1.Date) = 2023 AND DATEPART(QUARTER, t1.Date) = 4 GROUP BY CONCAT(YEAR(t1.Date), '-W', DATEPART(WEEK, t1.Date)) ORDER BY xAxis;

Chart Title 2: Weekly Ratio of Entertainment Costs to Total Revenue Over the Past 12 Weeks
SQL Query 2: SELECT CONCAT(YEAR(Date), '-W', DATEPART(WEEK, Date)) AS xAxis, (SUM(Cost_Entertainment) / SUM(Revenue)) * 100 AS yAxis FROM [database_name].[table_name] WHERE Date >= DATEADD(WEEK, -12, GETDATE()) GROUP BY CONCAT(YEAR(Date), '-W', DATEPART(WEEK, Date)) ORDER BY xAxis;

Chart Title 3: Weekly Variance in Mobile Costs and Broadband Costs for the Last 10 Weeks
SQL Query 3: SELECT CONCAT(YEAR(Date), '-W', DATEPART(WEEK, Date)) AS xAxis, VAR(Cost_Mobile) AS yAxis, VAR(Cost_Broadband) AS yAxis2 FROM [database_name].[table_name] WHERE Date >= DATEADD(WEEK, -10, GETDATE()) GROUP BY CONCAT(YEAR(Date), '-W', DATEPART(WEEK, Date)) ORDER BY xAxis;
"""

                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_weekly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "daily":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        # Handle Daily Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_daily_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "daily"
                        ]
                        if not filtered_feedbacks_by_chart_and_daily_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Daily Average Cost Efficiency and Earnings per Cost Over the Last 30 Days
SQL Query 1: SELECT CAST(CONVERT(DATE, t1.[Date], 103) AS DATE) AS xAxis, AVG(t1.Cost_Efficiency) AS yAxis, AVG(t1.Earning_per_Cost) AS yAxis2 FROM [database_name].[table_name] t1 JOIN [database_name].[table_name] t2 ON CONVERT(DATE, t1.[Date], 103) = CONVERT(DATE, t2.[Date], 103) WHERE CONVERT(DATE, t1.[Date], 103) >= DATEADD(DAY, -30, GETDATE()) GROUP BY CAST(CONVERT(DATE, t1.[Date], 103) AS DATE) ORDER BY xAxis;

Chart Title 2: Daily Sum of Revenue and Cost for the Last 2 Weeks
SQL Query 2: SELECT CAST(CONVERT(DATE, Date, 103) AS DATE) AS xAxis, SUM(Revenue) AS yAxis, SUM(Cost) AS yAxis2 FROM [database_name].[table_name] WHERE CONVERT(DATE, Date, 103) >= DATEADD(DAY, -14, GETDATE()) GROUP BY CAST(CONVERT(DATE, Date, 103) AS DATE) ORDER BY xAxis;

Chart Title 3: Daily Change in EBIT (Day-over-Day Difference) for the Past 10 Days
SQL Query 3: SELECT CAST(CONVERT(DATE, Date, 103) AS DATE) AS xAxis, EBIT - LAG(EBIT, 1) OVER (ORDER BY CAST(CONVERT(DATE, Date, 103) AS DATE)) AS yAxis FROM [database_name].[table_name] WHERE CONVERT(DATE, Date, 103) >= DATEADD(DAY, -10, GETDATE()) ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Daily Cost of Entertainment vs. Cost of Mobile for the Last 7 Days
SQL Query 1: SELECT CAST(Date AS DATE) AS xAxis, SUM(t1.Cost_Entertainment) AS yAxis, SUM(t1.Cost_Mobile) AS yAxis2 FROM [database_name].[table_name] t1 JOIN [database_name].[table_name] t2 ON t1.Date = t2.Date WHERE t1.Date >= DATEADD(DAY, -7, GETDATE()) GROUP BY CAST(Date AS DATE) ORDER BY xAxis;

Chart Title 2: Daily EBIT to Revenue Ratio (EBIT as a Percentage of Revenue) for the Last 14 Days
SQL Query 2: SELECT CAST(Date AS DATE) AS xAxis, (SUM(EBIT) / NULLIF(SUM(Revenue), 0)) * 100 AS yAxis FROM [database_name].[table_name] WHERE Date >= DATEADD(DAY, -14, GETDATE()) GROUP BY CAST(Date AS DATE) ORDER BY xAxis;

Chart Title 3: Daily Total Revenue vs. Total Cost for the Last 60 Days
SQL Query 3: SELECT CAST(Date AS DATE) AS xAxis, SUM(Revenue) AS yAxis, SUM(Cost_Broadband + Cost_Entertainment + Cost_Mobile) AS yAxis2 FROM [database_name].[table_name] WHERE Date >= DATEADD(DAY, -60, GETDATE()) GROUP BY CAST(Date AS DATE) ORDER BY xAxis;
"""

                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_daily_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

            else:
                filtered_feedbacks_by_chart_and_no_timeframe = [
                    feedback
                    for feedback in filtered_liked_feedbacks
                    if feedback.get("chart_type") != "table_chart"
                    and not feedback.get("time_frame", "").strip()
                ]
                if not filtered_feedbacks_by_chart_and_no_timeframe:
                    QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Top 5 Products by Percentage of Total EBIT
Sql Query 1: SELECT Product AS xAxis, (SUM(EBIT) * 100.0 / SUM(SUM(EBIT)) OVER ()) AS yAxis FROM [database_name].[table_name] GROUP BY Product ORDER BY yAxis DESC OFFSET 0 ROWS FETCH NEXT 5 ROWS ONLY;

Chart Title 2: Top 3 Products that Generate the Highest Revenue
Sql Query 2: SELECT Product AS xAxis, SUM(Revenue) AS yAxis FROM [database_name].[table_name] GROUP BY Product ORDER BY yAxis DESC OFFSET 0 ROWS FETCH NEXT 3 ROWS ONLY;

Chart Title 3: Total Revenue Generated by Broadband Product
Sql Query 3: SELECT 'Broadband' AS xAxis, SUM(Revenue_Broadband) AS yAxis FROM [database_name].[table_name];

Chart Title 4: Total Cost Incurred by Entertainment and Broadband Respectively
Sql Query 4: SELECT 'Entertainment' AS xAxis, SUM(Cost_Entertainment) AS yAxis FROM [database_name].[table_name] UNION ALL SELECT 'Broadband' AS xAxis, SUM(Cost_Broadband) AS yAxis FROM [database_name].[table_name];

Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Top 5 Products by Percentage of Total EBIT
Sql Query 1: SELECT Product AS xAxis, (SUM(EBIT) * 100.0 / SUM(SUM(EBIT)) OVER ()) AS yAxis FROM [database_name].[table_name] GROUP BY Product ORDER BY yAxis DESC OFFSET 0 ROWS FETCH NEXT 5 ROWS ONLY;

Chart Title 2: Top 3 Products that Generate the Highest Revenue
Sql Query 2: SELECT Product AS xAxis, SUM(Revenue) AS yAxis FROM [database_name].[table_name] GROUP BY Product ORDER BY yAxis DESC OFFSET 0 ROWS FETCH NEXT 3 ROWS ONLY;

Chart Title 3: Total Revenue Generated by Broadband Product
Sql Query 3: SELECT 'Broadband' AS xAxis, SUM(Revenue_Broadband) AS yAxis FROM [database_name].[table_name];

Chart Title 4: Total Cost Incurred by Entertainment and Broadband Respectively
Sql Query 4: SELECT 'Entertainment' AS xAxis, SUM(Cost_Entertainment) AS yAxis FROM [database_name].[table_name] UNION ALL SELECT 'Broadband' AS xAxis, SUM(Cost_Broadband) AS yAxis FROM [database_name].[table_name];
"""

                else:
                    # Only append this line if token count allows
                    heading = "\nHere are the chart titles and sql queries\n"
                    new_data_tokens = calculate_token_usage(heading)
                    if (
                        TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                        <= TARGET_TOKEN_LIMIT
                    ):
                        QUERY_SAMPLES += heading
                        TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                    for idx, chart in enumerate(
                        filtered_feedbacks_by_chart_and_no_timeframe,
                        start=1,
                    ):
                        chart_title = chart.get("chart_title", "")
                        sql_query = chart.get("sql_query", "")
                        sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                        # Calculate token usage for the current chart and SQL query
                        new_data_tokens = calculate_token_usage(sample)

                        # Check if appending this data would exceed the token limit
                        if (
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                            <= TARGET_TOKEN_LIMIT
                        ):
                            QUERY_SAMPLES += sample

                            # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                        else:
                            # If appending would exceed, break the loop
                            break

            if (
                isinstance(chart_axis["xAxis_column"], str)
                and chart_axis["xAxis_column"] in data_summary.column_data_tribes.keys()
                and data_summary.column_data_tribes[chart_axis["xAxis_column"]]
                in ["date_related"]
                and chart_axis["xAxis_column"]
                in data_summary.column_sql_data_types.keys()
                and data_summary.column_sql_data_types[
                    chart_axis["xAxis_column"]
                ].lower()
                not in [
                    "tinyint",
                    "smallint",
                    "mediumint",
                    "int",
                    "bigint",
                    "float",
                    "double",
                    "decimal",
                    "bit",
                ]
            ):
                x_column = chart_axis["xAxis_column"]

                if time_duration == "Week":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Week"
                        and chart["chart_type"] != "table_chart"
                    ]

                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Total Revenue by Product for the Past 2 Weeks
SQL Query 1: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-W', DATEPART(WEEK, CONVERT(DATE, [Date], 103))) AS xAxis, SUM(Revenue) AS yAxis, Product AS series FROM [database_name].[table_name] WHERE CONVERT(DATE, [Date], 103) BETWEEN DATEADD(WEEK, -2, GETDATE()) AND GETDATE() GROUP BY xAxis, series ORDER BY xAxis ASC, series;

Chart Title 2: Weekly Average EBIT for Next 3 Weeks
SQL Query 2: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-W', DATEPART(WEEK, CONVERT(DATE, [Date], 103))) AS xAxis, AVG(EBIT) AS yAxis FROM [database_name].[table_name] WHERE CONVERT(DATE, [Date], 103) BETWEEN GETDATE() AND DATEADD(WEEK, 3, GETDATE()) GROUP BY xAxis ORDER BY xAxis;

Chart Title 3: Weekly Total Cost of Entertainment for Last Week
SQL Query 3: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-W', DATEPART(WEEK, CONVERT(DATE, [Date], 103))) AS xAxis, SUM(Cost_Entertainment) AS yAxis FROM [database_name].[table_name] WHERE CONVERT(DATE, [Date], 103) BETWEEN DATEADD(WEEK, -1, GETDATE()) AND GETDATE() GROUP BY xAxis ORDER BY xAxis;

Chart Title 4: Weekly Maximum Revenue from Week 1 - Week 4 in March 2023
SQL Query 4: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-W', DATEPART(WEEK, CONVERT(DATE, [Date], 103))) AS xAxis, MAX(Revenue) AS yAxis FROM [database_name].[table_name] WHERE CONVERT(DATE, [Date], 103) BETWEEN '2023-03-01' AND '2023-03-31' AND DATEPART(WEEK, CONVERT(DATE, [Date], 103)) BETWEEN 1 AND 4 GROUP BY xAxis ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Total Revenue by Product for the Past 2 Weeks
SQL Query 1: SELECT CONCAT(YEAR([DATE]), '-W', DATEPART(WEEK, [DATE])) AS xAxis, SUM(Revenue) AS yAxis, Product AS series FROM [database_name].[table_name] WHERE [DATE] BETWEEN DATEADD(WEEK, -2, GETDATE()) AND GETDATE() GROUP BY xAxis, series ORDER BY xAxis ASC, series;

Chart Title 2: Weekly Average EBIT for Next 3 Weeks
SQL Query 2: SELECT CONCAT(YEAR([DATE]), '-W', DATEPART(WEEK, [DATE])) AS xAxis, AVG(EBIT) AS yAxis FROM [database_name].[table_name] WHERE [DATE] BETWEEN GETDATE() AND DATEADD(WEEK, 3, GETDATE()) GROUP BY xAxis ORDER BY xAxis;

Chart Title 3: Weekly Total Cost of Entertainment for Last Week
SQL Query 3: SELECT CONCAT(YEAR([DATE]), '-W', DATEPART(WEEK, [DATE])) AS xAxis, SUM(Cost_Entertainment) AS yAxis FROM [database_name].[table_name] WHERE [DATE] BETWEEN DATEADD(WEEK, -1, GETDATE()) AND GETDATE() GROUP BY xAxis ORDER BY xAxis;

Chart Title 4: Weekly Maximum Revenue from Week 1 - Week 4 in March 2023
SQL Query 4: SELECT CONCAT(YEAR([DATE]), '-W', DATEPART(WEEK, [DATE])) AS xAxis, MAX(Revenue) AS yAxis FROM [database_name].[table_name] WHERE [DATE] BETWEEN '2023-03-01' AND '2023-03-31' AND DATEPART(WEEK, [DATE]) BETWEEN 1 AND 4 GROUP BY xAxis ORDER BY xAxis;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif time_duration == "Month":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Month"
                        and chart["chart_type"] != "table_chart"
                    ]

                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue by Product for the Past 6 Months
SQL Query 1: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-M', MONTH(CONVERT(DATE, [Date], 103))) AS xAxis, SUM(Revenue) AS yAxis, Product AS series FROM [database_name].[table_name] WHERE CONVERT(DATE, [Date], 103) >= DATEADD(MONTH, -6, GETDATE()) GROUP BY xAxis, series ORDER BY xAxis ASC, series;

Chart Title 2: Monthly Average EBIT for Next January
SQL Query 2: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-M', MONTH(CONVERT(DATE, [Date], 103))) AS xAxis, AVG(EBIT) AS yAxis FROM [database_name].[table_name] WHERE YEAR(CONVERT(DATE, [Date], 103)) = YEAR(DATEADD(YEAR, 1, GETDATE())) AND MONTH(CONVERT(DATE, [Date], 103)) = 1 GROUP BY xAxis ORDER BY xAxis;

Chart Title 3: Monthly Cost of Entertainment for March
SQL Query 3: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-M', MONTH(CONVERT(DATE, [Date], 103))) AS xAxis, SUM(Cost_Entertainment) AS yAxis FROM [database_name].[table_name] WHERE MONTH(CONVERT(DATE, [Date], 103)) = 3 AND YEAR(CONVERT(DATE, [Date], 103)) = YEAR(GETDATE()) GROUP BY xAxis ORDER BY xAxis;

Chart Title 4: Monthly Revenue from Jan 2022 - Mar 2022
SQL Query 4: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-M', MONTH(CONVERT(DATE, [Date], 103))) AS xAxis, SUM(Revenue) AS yAxis FROM [database_name].[table_name] WHERE CONVERT(DATE, [Date], 103) BETWEEN '2022-01-01' AND '2022-03-31' GROUP BY xAxis ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue by Product for the Past 6 Months
SQL Query 1: SELECT CONCAT(YEAR([DATE]), '-M', MONTH([DATE])) AS xAxis, SUM(Revenue) AS yAxis, Product AS series FROM [database_name].[table_name] WHERE [DATE] >= DATEADD(MONTH, -6, GETDATE()) GROUP BY xAxis, series ORDER BY xAxis ASC, series;

Chart Title 2: Monthly Average EBIT for Next January
SQL Query 2: SELECT CONCAT(YEAR([DATE]), '-M', MONTH([DATE])) AS xAxis, AVG(EBIT) AS yAxis FROM [database_name].[table_name] WHERE YEAR([DATE]) = YEAR(DATEADD(YEAR, 1, GETDATE())) AND MONTH([DATE]) = 1 GROUP BY xAxis ORDER BY xAxis;

Chart Title 3: Monthly Cost of Entertainment for March
SQL Query 3: SELECT CONCAT(YEAR([DATE]), '-M', MONTH([DATE])) AS xAxis, SUM(Cost_Entertainment) AS yAxis FROM [database_name].[table_name] WHERE MONTH([DATE]) = 3 AND YEAR([DATE]) = YEAR(GETDATE()) GROUP BY xAxis ORDER BY xAxis;

Chart Title 4: Monthly Revenue from Jan 2022 - Mar 2022
SQL Query 4: SELECT CONCAT(YEAR([DATE]), '-M', MONTH([DATE])) AS xAxis, SUM(Revenue) AS yAxis FROM [database_name].[table_name] WHERE [DATE] BETWEEN '2022-01-01' AND '2022-03-31' GROUP BY xAxis ORDER BY xAxis;
"""

                    else:
                        # Only append this line if token count allows
                        heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                        new_data_tokens = calculate_token_usage(heading)
                        if (
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                            <= TARGET_TOKEN_LIMIT
                        ):
                            QUERY_SAMPLES += heading
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                        for idx, chart in enumerate(filtered_feedback, start=1):
                            chart_title = chart.get("chart_title", "")
                            sql_query = chart.get("feedback", "")
                            sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                            # Calculate token usage for the current chart and feedback
                            new_data_tokens = calculate_token_usage(sample)

                            # Check if appending this data would exceed the token limit
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += sample

                                # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            else:
                                # If appending would exceed, break the loop
                                break

                elif time_duration == "Quarter":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Quarter"
                        and chart["chart_type"] != "table_chart"
                    ]
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Total Revenue for the Last Q3
SQL Query 1: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, [Date], 103))) AS xAxis, SUM(Revenue) AS yAxis FROM [database_name].[table_name] WHERE DATEPART(QUARTER, CONVERT(DATE, [Date], 103)) = 3 AND CONVERT(DATE, [Date], 103) >= DATEADD(YEAR, -1, GETDATE()) GROUP BY CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, [Date], 103))) ORDER BY xAxis;

Chart Title 2: Quarterly EBIT for the Next Quarter
SQL Query 2: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, [Date], 103))) AS xAxis, SUM(EBIT) AS yAxis FROM [database_name].[table_name] WHERE CONVERT(DATE, [Date], 103) BETWEEN GETDATE() AND DATEADD(QUARTER, 1, GETDATE()) GROUP BY CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, [Date], 103))) ORDER BY xAxis;

Chart Title 3: Quarterly Average Revenue for the Past H2
SQL Query 3: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, [Date], 103))) AS xAxis, AVG(Revenue) AS yAxis FROM [database_name].[table_name] WHERE DATEPART(QUARTER, CONVERT(DATE, [Date], 103)) IN (3, 4) AND CONVERT(DATE, [Date], 103) >= DATEADD(YEAR, -1, GETDATE()) GROUP BY CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, [Date], 103))) ORDER BY xAxis;

Chart Title 4: Quarterly Total Cost for Q1 2023 - Q3 2023
SQL Query 4: SELECT CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, [Date], 103))) AS xAxis, SUM(Cost_Entertainment + Cost_Broadband + Cost_Mobile) AS yAxis FROM [database_name].[table_name] WHERE YEAR(CONVERT(DATE, [Date], 103)) = 2023 AND DATEPART(QUARTER, CONVERT(DATE, [Date], 103)) BETWEEN 1 AND 3 GROUP BY CONCAT(YEAR(CONVERT(DATE, [Date], 103)), '-Q', DATEPART(QUARTER, CONVERT(DATE, [Date], 103))) ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Total Revenue for the Last Q3
SQL Query 1: SELECT CONCAT(YEAR([DATE]), '-Q', DATEPART(QUARTER, [DATE])) AS xAxis, SUM(Revenue) AS yAxis FROM [database_name].[table_name] WHERE DATEPART(QUARTER, [DATE]) = 3 AND [DATE] >= DATEADD(YEAR, -1, GETDATE()) GROUP BY CONCAT(YEAR([DATE]), '-Q', DATEPART(QUARTER, [DATE])) ORDER BY xAxis;

Chart Title 2: Quarterly EBIT for the Next Quarter
SQL Query 2: SELECT CONCAT(YEAR([DATE]), '-Q', DATEPART(QUARTER, [DATE])) AS xAxis, SUM(EBIT) AS yAxis FROM [database_name].[table_name] WHERE [DATE] BETWEEN GETDATE() AND DATEADD(QUARTER, 1, GETDATE()) GROUP BY CONCAT(YEAR([DATE]), '-Q', DATEPART(QUARTER, [DATE])) ORDER BY xAxis;

Chart Title 3: Quarterly Average Revenue for the Past H2
SQL Query 3: SELECT CONCAT(YEAR([DATE]), '-Q', DATEPART(QUARTER, [DATE])) AS xAxis, AVG(Revenue) AS yAxis FROM [database_name].[table_name] WHERE DATEPART(QUARTER, [DATE]) IN (3, 4) AND [DATE] >= DATEADD(YEAR, -1, GETDATE()) GROUP BY CONCAT(YEAR([DATE]), '-Q', DATEPART(QUARTER, [DATE])) ORDER BY xAxis;

Chart Title 4: Quarterly Total Cost for Q1 2023 - Q3 2023
SQL Query 4: SELECT CONCAT(YEAR([Date]), '-Q', DATEPART(QUARTER, [Date])) AS xAxis, SUM(Cost_Entertainment + Cost_Broadband + Cost_Mobile) AS yAxis FROM [database_name].[table_name] WHERE YEAR([Date]) = 2023 AND DATEPART(QUARTER, [Date]) BETWEEN 1 AND 3 GROUP BY CONCAT(YEAR([Date]), '-Q', DATEPART(QUARTER, [Date])) ORDER BY xAxis;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif time_duration == "Year":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Year"
                        and chart["chart_type"] != "table_chart"
                    ]

                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Total Revenue by Product Over the Past 5 Years
SQL Query 1: SELECT CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR) AS xAxis, SUM(Revenue) AS yAxis, Product AS series FROM [database_name].[table_name] WHERE CONVERT(DATE, [Date], 103) >= DATEADD(YEAR, -5, GETDATE()) GROUP BY CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR), Product ORDER BY xAxis ASC, series;

Chart Title 2: Yearly Average EBIT for Next Year
SQL Query 2: SELECT CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR) AS xAxis, AVG(EBIT) AS yAxis FROM [database_name].[table_name] WHERE YEAR(CONVERT(DATE, [Date], 103)) = YEAR(GETDATE()) + 1 GROUP BY CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR) ORDER BY xAxis;

Chart Title 3: Yearly Total Revenue for 2022
SQL Query 3: SELECT CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR) AS xAxis, SUM(Revenue) AS yAxis FROM [database_name].[table_name] WHERE YEAR(CONVERT(DATE, [Date], 103)) = 2022 GROUP BY CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR) ORDER BY xAxis;

Chart Title 4: Yearly Cost and Revenue for the Last 3 Years
SQL Query 4: SELECT CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR) AS xAxis, SUM(Cost_Entertainment + Cost_Broadband + Cost_Mobile) AS yAxis, SUM(Revenue) AS yAxis2 FROM [database_name].[table_name] WHERE CONVERT(DATE, [Date], 103) >= DATEADD(YEAR, -3, GETDATE()) GROUP BY CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR) ORDER BY xAxis;

Chart Title 5: Yearly Total Revenue for 2022 - 2023
SQL Query 5: SELECT CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR) AS xAxis, SUM(Revenue) AS yAxis FROM [database_name].[table_name] WHERE YEAR(CONVERT(DATE, [Date], 103)) BETWEEN 2022 AND 2023 GROUP BY CAST(YEAR(CONVERT(DATE, [Date], 103)) AS VARCHAR) ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Total Revenue by Product Over the Past 5 Years
SQL Query 1: SELECT CAST(YEAR([DATE]) AS VARCHAR) AS xAxis, SUM(Revenue) AS yAxis, Product AS series FROM [database_name].[table_name] WHERE [DATE] >= DATEADD(YEAR, -5, GETDATE()) GROUP BY CAST(YEAR([DATE]) AS VARCHAR), Product ORDER BY xAxis ASC, series;

Chart Title 2: Yearly Average EBIT for Next Year
SQL Query 2: SELECT CAST(YEAR([DATE]) AS VARCHAR) AS xAxis, AVG(EBIT) AS yAxis FROM [database_name].[table_name] WHERE YEAR([DATE]) = YEAR(GETDATE()) + 1 GROUP BY CAST(YEAR([DATE]) AS VARCHAR) ORDER BY xAxis;

Chart Title 3: Yearly Total Revenue for 2022
SQL Query 3: SELECT CAST(YEAR([DATE]) AS VARCHAR) AS xAxis, SUM(Revenue) AS yAxis FROM [database_name].[table_name] WHERE YEAR([DATE]) = 2022 GROUP BY CAST(YEAR([DATE]) AS VARCHAR) ORDER BY xAxis;

Chart Title 4: Yearly Cost and Revenue for the Last 3 Years
SQL Query 4: SELECT CAST(YEAR([DATE]) AS VARCHAR) AS xAxis, SUM(Cost_Entertainment + Cost_Broadband + Cost_Mobile) AS yAxis, SUM(Revenue) AS yAxis2 FROM [database_name].[table_name] WHERE [DATE] >= DATEADD(YEAR, -3, GETDATE()) GROUP BY CAST(YEAR([DATE]) AS VARCHAR) ORDER BY xAxis;

Chart Title 5: Yearly Total Revenue for 2022 - 2023
SQL Query 5: SELECT CAST(YEAR([DATE]) AS VARCHAR) AS xAxis, SUM(Revenue) AS yAxis FROM [database_name].[table_name] WHERE YEAR([DATE]) BETWEEN 2022 AND 2023 GROUP BY CAST(YEAR([DATE]) AS VARCHAR) ORDER BY xAxis;
"""

                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

        if not filtered_liked_feedbacks:
            new_data_tokens = calculate_token_usage(QUERY_SAMPLES)
            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

    elif "postgresql" in data_summary.sql_library.lower():
        filtered_liked_feedbacks = fetch_filtered_feedbacks(
            question, table_name, "label2"
        )

        QUERY_SAMPLES = """
Enhance your understanding of PostgreSQL SQL query structuring, syntax, and writing, with a particular emphasis on date-related formatting, by training using the provided chart titles and SQL query examples.

DDL:
""" + (
            data_summary.database_schema_sql
            if filtered_liked_feedbacks
            else (
                """
CREATE TABLE `table_name` (
    "Date" DATE,
    "Product" VARCHAR(255),
    "EBIT_Margin" DECIMAL(10, 2),
    "Revenue" DECIMAL(10, 2),
    "Cost_Efficiency" DECIMAL(10, 2),
    "Earning_per_Cost" DECIMAL(10, 2),
    "Cost_Mobile" DECIMAL(10, 2),
    "Cost_Broadband" DECIMAL(10, 2),
    "Cost_Entertainment" DECIMAL(10, 2),
    "Revenue_Mobile" DECIMAL(10, 2),
    "Revenue_Broadband" DECIMAL(10, 2),
    "Revenue_Entertainment" DECIMAL(10, 2),
    "RevenueVariance_Actual_vs_Forecast" DECIMAL(10, 2),
    "Revenue_Generation" DECIMAL(10, 2)
);
"""
                if any(
                    data_type.upper() in {"DATE", "DATETIME", "TIMESTAMP"}
                    for data_type in data_summary.column_sql_data_types.values()
                )
                else """
CREATE TABLE `table_name` (
    "Date" VARCHAR(255),
    "Product" VARCHAR(255),
    "RevenueVariance_Actual_vs_Forecast" DECIMAL(10, 2),
    "Cost_Efficiency" DECIMAL(10, 2),
    "Earning_per_Cost" DECIMAL(10, 2),
    "Revenue_Generation" DECIMAL(10, 2),
    "Revenue_Broadband" DECIMAL(10, 2),
    "Revenue_Entertainment" DECIMAL(10, 2),
    "Revenue_Mobile" DECIMAL(10, 2),
    "Cost_Broadband" DECIMAL(10, 2),
    "Cost_Entertainment" DECIMAL(10, 2),
    "Cost_Mobile" DECIMAL(10, 2),
    "EBIT_Margin" DECIMAL(10, 2)
);
"""
            )
        )

        # If Table Chart
        if chart_type in ["table_chart"]:
            x_column = chart_axis["xAxis_column"]
            if (
                isinstance(x_column, str)
                and x_column in data_summary.column_data_tribes
                and data_summary.column_data_tribes[x_column] == "date_related"
            ):
                if timeframe.lower() == "yearly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for Yearly timeframe feedbacks
                        filtered_feedbacks_by_chart_and_yearly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "yearly"
                        ]

                        if not filtered_feedbacks_by_chart_and_yearly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Total Revenue Variance for the Past Two Years
SQL Query 1: SELECT EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) AS "xAxis", SUM("RevenueVariance_Actual_vs_Forecast") AS "yAxis" FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') >= CURRENT_DATE - INTERVAL '2 YEAR' AND TO_DATE("Date", 'DD/MM/YYYY') <= CURRENT_DATE GROUP BY EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) ORDER BY "xAxis";

Chart Title 2: Yearly Total Cost Efficiency for the Current Year and the Previous Year
SQL Query 2: SELECT EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) AS "xAxis", SUM("Cost_Efficiency") AS "yAxis" FROM `table_name` WHERE EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) >= EXTRACT(YEAR FROM CURRENT_DATE - INTERVAL '1 YEAR') AND EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) <= EXTRACT(YEAR FROM CURRENT_DATE) GROUP BY EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) ORDER BY "xAxis";

Chart Title 3: Yearly Total Revenue Generation Forecast for the Next Two Years
SQL Query 3: SELECT EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) AS "xAxis", SUM("Revenue_Generation") AS "yAxis" FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') >= CURRENT_DATE AND TO_DATE("Date", 'DD/MM/YYYY') < CURRENT_DATE + INTERVAL '2 YEAR' GROUP BY EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) ORDER BY "xAxis";
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Total Revenue by Product for the Past 5 Years
SQL Query 1: SELECT EXTRACT(YEAR FROM "Date") AS "xAxis", "Product" AS "series", SUM("Revenue") AS "yAxis" FROM `table_name` WHERE EXTRACT(YEAR FROM "Date") BETWEEN EXTRACT(YEAR FROM CURDATE()) - 5 AND EXTRACT(YEAR FROM CURDATE()) GROUP BY "xAxis", "series";

Chart Title 2: Yearly Total Cost Efficiency vs. Revenue Generation for Broadband Over the Last 3 Years
SQL Query 2: SELECT EXTRACT(YEAR FROM "Date") AS "xAxis", 'Broadband' AS "series", SUM("Cost_Efficiency") AS "yAxis", SUM("Revenue_Generation") AS "yAxis2" FROM `table_name` WHERE "Product" = 'Broadband' AND EXTRACT(YEAR FROM "Date") BETWEEN EXTRACT(YEAR FROM CURDATE()) - 3 AND EXTRACT(YEAR FROM CURDATE()) GROUP BY "xAxis", "series";

Chart Title 3: Yearly Actual vs. Forecasted Total Revenue Variance for the Last 7 Years
SQL Query 3: SELECT EXTRACT(YEAR FROM "Date") AS "xAxis", 'Revenue Variance' AS "series", SUM("RevenueVariance_Actual_vs_Forecast") AS "yAxis" FROM `table_name` WHERE EXTRACT(YEAR FROM "Date") BETWEEN EXTRACT(YEAR FROM CURDATE()) - 7 AND EXTRACT(YEAR FROM CURDATE()) GROUP BY "xAxis", "series";"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_yearly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "half-yearly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for half-yearly timeframe feedbacks
                        filtered_feedbacks_by_chart_and_half_yearly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "half-yearly"
                        ]

                        if not filtered_feedbacks_by_chart_and_half_yearly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Half-Yearly Total Revenue Variance vs. Forecast for the Past Year
SQL Query 1: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-H', CASE WHEN EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) <= 6 THEN 1 ELSE 2 END) AS "xAxis", SUM("RevenueVariance_Actual_vs_Forecast") AS "yAxis" FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) AND TO_DATE("Date", 'DD/MM/YYYY') <= CURDATE() GROUP BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-H', CASE WHEN EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) <= 6 THEN 1 ELSE 2 END) ORDER BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-H', CASE WHEN EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) <= 6 THEN 1 ELSE 2 END);

Chart Title 2: Half-Yearly Average Earning Per Cost Analysis for the Last 2 Years
SQL Query 2: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-H', CASE WHEN EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) <= 6 THEN 1 ELSE 2 END) AS "xAxis", AVG("Earning_per_Cost") AS "yAxis" FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR) AND TO_DATE("Date", 'DD/MM/YYYY') < CURDATE() GROUP BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-H', CASE WHEN EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) <= 6 THEN 1 ELSE 2 END) ORDER BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-H', CASE WHEN EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) <= 6 THEN 1 ELSE 2 END);

Chart Title 3: Half-Yearly Average Cost Efficiency Comparison for the Next 6 Months
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-H', CASE WHEN EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) <= 6 THEN 1 ELSE 2 END) AS "xAxis", AVG("Cost_Efficiency") AS "yAxis" FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') >= CURDATE() AND TO_DATE("Date", 'DD/MM/YYYY') <= DATE_ADD(CURDATE(), INTERVAL 6 MONTH) GROUP BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-H', CASE WHEN EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) <= 6 THEN 1 ELSE 2 END) ORDER BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-H', CASE WHEN EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) <= 6 THEN 1 ELSE 2 END);
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Semi-Annual Revenue Generation for the Past Two Years
SQL Query 1: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-H', CASE WHEN EXTRACT(MONTH FROM "Date") <= 6 THEN 1 ELSE 2 END) AS "xAxis", SUM("Revenue_Generation") AS "yAxis" FROM `table_name` WHERE "Date" >= DATE_SUB(CURRENT_DATE, INTERVAL 2 YEAR) AND "Date" < CURRENT_DATE GROUP BY CONCAT(EXTRACT(YEAR FROM "Date"), '-H', CASE WHEN EXTRACT(MONTH FROM "Date") <= 6 THEN 1 ELSE 2 END) ORDER BY "xAxis";

Chart Title 2: Half-Yearly Cost Efficiency Trends for the Next Year
SQL Query 2: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-H', CASE WHEN EXTRACT(MONTH FROM "Date") <= 6 THEN 1 ELSE 2 END) AS "xAxis", AVG("Cost_Efficiency") AS "yAxis" FROM `table_name` WHERE "Date" >= CURRENT_DATE AND "Date" <= DATE_ADD(CURRENT_DATE, INTERVAL 1 YEAR) GROUP BY CONCAT(EXTRACT(YEAR FROM "Date"), '-H', CASE WHEN EXTRACT(MONTH FROM "Date") <= 6 THEN 1 ELSE 2 END) ORDER BY "xAxis";

Chart Title 3: Half-Yearly EBIT Margin Comparison for the Past Year
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-H', CASE WHEN EXTRACT(MONTH FROM "Date") <= 6 THEN 1 ELSE 2 END) AS "xAxis", AVG("EBIT_Margin") AS "yAxis" FROM `table_name` WHERE "Date" >= DATE_SUB(CURRENT_DATE, INTERVAL 1 YEAR) AND "Date" <= CURRENT_DATE GROUP BY CONCAT(EXTRACT(YEAR FROM "Date"), '-H', CASE WHEN EXTRACT(MONTH FROM "Date") <= 6 THEN 1 ELSE 2 END) ORDER BY "xAxis";
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_half_yearly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "quarterly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for quarterly timeframe feedbacks
                        filtered_feedbacks_by_chart_and_quarterly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "quarterly"
                        ]

                        if not filtered_feedbacks_by_chart_and_quarterly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Average Earning per Cost by Product (Q1 & Q2 2022)
Sql Query 1: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE(\"Date\", 'DD/MM/YYYY')), '-Q', EXTRACT(QUARTER FROM TO_DATE(\"Date\", 'DD/MM/YYYY'))) AS \"xAxis\", \"Product\" AS \"series\", AVG(\"Earning_per_Cost\") AS \"yAxis\" FROM `table_name` WHERE TO_DATE(\"Date\", 'DD/MM/YYYY') BETWEEN TO_DATE('2022-01-01', 'YYYY-MM-DD') AND TO_DATE('2022-06-30', 'YYYY-MM-DD') GROUP BY \"xAxis\", \"series\";

Chart Title 2: Quarterly Total Revenue Generation for the Past Four Quarters
SQL Query 2: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-Q', EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, SUM("Revenue_Generation") AS yAxis FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) AND TO_DATE("Date", 'DD/MM/YYYY') < CURDATE() GROUP BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-Q', EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY'))) ORDER BY xAxis;

Chart Title 3: Quarterly Total Cost Efficiency for the Next Two Quarters
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-Q', EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, SUM("Cost_Efficiency") AS yAxis FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') >= CURDATE() AND TO_DATE("Date", 'DD/MM/YYYY') < DATE_ADD(CURDATE(), INTERVAL 6 MONTH) GROUP BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-Q', EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY'))) ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Total Revenue for Broadband and Mobile Products for Previous Year
Sql Query 1: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) AS "xAxis", SUM("Revenue_Broadband") AS "yAxis", 'Broadband' AS "series" FROM `table_name` WHERE (EXTRACT(YEAR FROM "Date") = EXTRACT(YEAR FROM CURRENT_DATE)AND EXTRACT(QUARTER FROM "Date") <= EXTRACT(QUARTER FROM CURRENT_DATE))OR (EXTRACT(YEAR FROM "Date") = EXTRACT(YEAR FROM CURRENT_DATE) - 1 AND EXTRACT(QUARTER FROM "Date") > EXTRACT(QUARTER FROM CURRENT_DATE)) GROUP BY CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) UNION ALL SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) AS "xAxis", SUM("Revenue_Mobile") AS "yAxis", 'Mobile' AS "series" FROM `table_name` WHERE (EXTRACT(YEAR FROM "Date") = EXTRACT(YEAR FROM CURRENT_DATE) AND EXTRACT(QUARTER FROM "Date") <= EXTRACT(QUARTER FROM CURRENT_DATE)) OR (EXTRACT(YEAR FROM "Date") = EXTRACT(YEAR FROM CURRENT_DATE) - 1 AND EXTRACT(QUARTER FROM "Date") > EXTRACT(QUARTER FROM CURRENT_DATE)) GROUP BY CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) ORDER BY "xAxis", "series";

Chart Title 2: Quarterly Total Revenue for Broadband Products for the Past Three Quarters 
Sql Query 2: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) AS "xAxis", SUM("Revenue_Broadband") AS "yAxis", 'Broadband' AS "series" FROM `table_name` WHERE "Date" >= DATE_TRUNC('quarter', CURRENT_DATE - INTERVAL '9 months') AND "Date" < DATE_TRUNC('quarter', CURRENT_DATE) GROUP BY CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) ORDER BY "xAxis", "series";

Chart Title 3: Quarterly Average Cost Efficiency for Broadband Products for the Next Two Years
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) AS "xAxis", AVG("Cost_Efficiency") AS "yAxis" FROM `table_name` WHERE "Date" >= CURRENT_DATE AND "Date" < CURRENT_DATE + INTERVAL '2 YEAR' GROUP BY CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) ORDER BY "xAxis";
"""

                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_quarterly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "monthly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for monthly timeframe feedbacks
                        filtered_feedbacks_by_chart_and_monthly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "monthly"
                        ]

                        if not filtered_feedbacks_by_chart_and_monthly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue Variance (Actual vs. Forecast) by Product for Last Year
Sql Query 1: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-M', EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS "xAxis", SUM("RevenueVariance_Actual_vs_Forecast") AS "yAxis", "Product" AS "series" FROM `table_name` WHERE EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) = EXTRACT(YEAR FROM CURRENT_DATE) - 1 GROUP BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-M', EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY'))), "Product" ORDER BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-M', EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')));

Chart Title 2: Monthly Average Cost Efficiency by Product for the Past 12 Months
Sql Query 2: SELECT TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM') AS "xAxis","Product" AS "series", AVG("Cost_Efficiency") AS "yAxis" FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') >= TO_DATE(EXTRACT(YEAR FROM CURRENT_DATE) - 1 || '-M' || EXTRACT(MONTH FROM CURRENT_DATE) || '-01', 'YYYY-MM-DD') GROUP BY "xAxis", "series" ORDER BY "xAxis", "series";

Chart Title 3: Monthly Average Earning per Cost for Broadband and Mobile Products in the Past Two Years
Sql Query 3: SELECT TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM') AS "xAxis", "Product" AS "series", AVG("Earning_per_Cost") AS "yAxis" FROM `table_name` WHERE "Product" IN ('BroadBand', 'Mobile') AND TO_DATE("Date", 'DD/MM/YYYY') >= DATE_TRUNC('MONTH', CURRENT_DATE - INTERVAL '2 years')::date AND TO_DATE("Date", 'DD/MM/YYYY') <= CURRENT_DATE::date AND EXTRACT(DAY FROM TO_DATE("Date", 'DD/MM/YYYY')) = 1 GROUP BY TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM'), "Product" ORDER BY TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM'), "Product";

Chart Title 4: Monthly Percentage Contribution of Total Revenue Generation by Product for the Last Year
Sql Query 4: WITH revenue_summary AS (SELECT TO_DATE("Date", 'DD/MM/YYYY') AS "xAxis", SUM("Revenue_Generation") AS "revenue", "Product" FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN DATE_TRUNC('year', CURRENT_DATE - INTERVAL '1 year') AND DATE_TRUNC('year', CURRENT_DATE) - INTERVAL '1 day' GROUP BY TO_DATE("Date", 'DD/MM/YYYY'), "Product") SELECT "xAxis", "Product", ("revenue" / SUM("revenue") OVER (PARTITION BY "xAxis")) * 100 AS "yAxis" FROM revenue_summary ORDER BY "xAxis", "Product";

Chart Title 5: Monthly Total EBIT Margin and Total Earning per Cost for the Last Year
Sql Query 5: SELECT TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM') AS "xAxis", SUM("EBIT_Margin") AS "yAxis", SUM("Earning_per_Cost") AS "yAxis2" FROM `table_name` WHERE EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) = EXTRACT(YEAR FROM CURRENT_DATE) -1 GROUP BY TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM') ORDER BY TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM');

Chart Title 6: Monthly Median Revenue Variance (Actual vs. Forecast) for Top 3 Products in 2023
Sql Query 6: SELECT TO_CHAR(TO_DATE(\"Date\", 'DD/MM/YYYY'), 'YYYY-MM') AS \"xAxis\", PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY \"RevenueVariance_Actual_vs_Forecast\") AS \"yAxis\", \"Product\" AS \"series\" FROM `table_name` WHERE TO_DATE(\"Date\", 'DD/MM/YYYY') BETWEEN DATE_TRUNC('year', '2023-01-01'::date) AND DATE_TRUNC('year', '2024-01-01'::date) AND \"Product\" IN (SELECT \"Product\" FROM `table_name` GROUP BY \"Product\" ORDER BY SUM(\"RevenueVariance_Actual_vs_Forecast\") DESC LIMIT 3) GROUP BY \"Product\", \"xAxis\" ORDER BY \"xAxis\", \"series\";

Chart Title 7: Monthly Percentage Change in Total Revenue Variance (Actual vs. Forecast) for Top 3 Products (H1 vs. H2 2023)
Sql Query 7: SELECT TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM') AS "xAxis", "Product" AS "series", ((SUM("RevenueVariance_Actual_vs_Forecast") FILTER (WHERE TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM') BETWEEN '2023-07' AND '2023-12')) / (SUM("RevenueVariance_Actual_vs_Forecast") FILTER (WHERE TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM') BETWEEN '2023-01' AND '2023-06'))) * 100 AS "yAxis" FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN '2023-01-01' AND '2023-12-31' AND "Product" IN (SELECT "Product" FROM `table_name` GROUP BY "Product" ORDER BY SUM("RevenueVariance_Actual_vs_Forecast") DESC LIMIT 3) GROUP BY "xAxis", "series" ORDER BY "xAxis", "series";
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Cost Forecast for Mobile and Broadband for the Next Three Months
Sql Query 1: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-M', EXTRACT(MONTH FROM "Date")) AS "xAxis", SUM("Cost_Mobile") AS "yAxis", SUM("Cost_Broadband") AS "yAxis2" FROM `table_name` WHERE "Date" > DATE_TRUNC('month', CURRENT_DATE) AND "Date" < DATE_TRUNC('month', CURRENT_DATE + INTERVAL '3 month') GROUP BY CONCAT(EXTRACT(YEAR FROM "Date"), '-M', EXTRACT(MONTH FROM "Date")) ORDER BY CONCAT(EXTRACT(YEAR FROM "Date"), '-M', EXTRACT(MONTH FROM "Date"));

Chart Title 2: Monthly Total Cost Forecast for Broadband and Mobile for the Next Year
Sql Query 2: SELECT TO_CHAR("Date", 'YYYY-MM') AS "xAxis", SUM("Cost_Broadband") AS "yAxis", SUM("Cost_Mobile") AS "yAxis2" FROM `table_name` WHERE "Date" >= DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '1 year' AND "Date" < DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '2 years' GROUP BY TO_CHAR("Date", 'YYYY-MM') ORDER BY TO_CHAR("Date", 'YYYY-MM');
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_monthly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "weekly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for weekly timeframe feedbacks
                        filtered_feedbacks_by_chart_and_weekly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "weekly"
                        ]

                        if not filtered_feedbacks_by_chart_and_weekly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Total Revenue Generated by Broadband Product Over Time
Sql Query 1: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS "xAxis", SUM("Revenue_Broadband") AS "yAxis", 'Broadband' AS "series" FROM `table_name` WHERE "Product" = 'Broadband' GROUP BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY'))) ORDER BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY')));

Chart Title 2: Weekly Total Revenue Variance Comparison for the Past Year
SQL Query 2: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS "xAxis", SUM("RevenueVariance_Actual_vs_Forecast") AS "yAxis" FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) GROUP BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY'))) ORDER BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY')));

Chart Title 3: Weekly Average Cost Efficiency of Products in the Current Year
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS "xAxis", AVG("Cost_Efficiency") AS "yAxis" FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN DATE(CONCAT(EXTRACT(YEAR FROM CURDATE()), '-01-01')) AND CURDATE() GROUP BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY'))) ORDER BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY')));
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Total Revenue from Mobile Products for the Past Year
SQL Query 1: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-W', EXTRACT(WEEK FROM "Date")) AS "xAxis", SUM("Revenue") AS "yAxis", 'Mobile' AS "series" FROM `table_name` WHERE "Date" >= DATE_SUB(CURRENT_DATE, INTERVAL 1 YEAR) AND "Date" < CURRENT_DATE AND "Product" = 'Mobile' GROUP BY CONCAT(EXTRACT(YEAR FROM "Date"), '-W', EXTRACT(WEEK FROM "Date")) ORDER BY "xAxis", "series";

Chart Title 2: Weekly Average Cost Efficiency for All Products for the Next Six Months
SQL Query 2: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-W', EXTRACT(WEEK FROM "Date")) AS "xAxis", AVG("Cost_Efficiency") AS "yAxis" FROM `table_name` WHERE "Date" >= CURRENT_DATE AND "Date" < DATE_ADD(CURRENT_DATE, INTERVAL 6 MONTH) GROUP BY CONCAT(EXTRACT(YEAR FROM "Date"), '-W', EXTRACT(WEEK FROM "Date")) ORDER BY "xAxis";

Chart Title 3: Weekly Total Revenue Variance for Broadband Products for the Past Two Years
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-W', EXTRACT(WEEK FROM "Date")) AS "xAxis", SUM("RevenueVariance_Actual_vs_Forecast") AS "yAxis" FROM `table_name` WHERE "Date" >= DATE_SUB(CURRENT_DATE, INTERVAL 2 YEAR) AND "Date" < CURRENT_DATE AND "Product" = 'Broadband' GROUP BY CONCAT(EXTRACT(YEAR FROM "Date"), '-W', EXTRACT(WEEK FROM "Date")) ORDER BY "xAxis";
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_weekly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "daily":
                    if (
                        chart_axis["xAxis_column"]
                        in data_summary.column_sql_data_types.keys()
                    ):
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for daily timeframe feedbacks
                        filtered_feedbacks_by_chart_and_daily_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "daily"
                        ]

                        if not filtered_feedbacks_by_chart_and_daily_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Ttile 1: Daily Profit Earned by Types of Product in Year 2023
Sql Query 1: SELECT TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM-DD') AS "xAxis", "Product" AS "series", SUM("Revenue") AS "yAxis" FROM `table_name` WHERE EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) = 2023 GROUP BY TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM-DD'), "Product" ORDER BY TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM-DD'), "Product";

Chart Title 2: Daily Total Revenue Variance for All Products in the Past 6 Months
SQL Query 2:
SELECT TO_DATE("Date", 'DD/MM/YYYY') AS "xAxis", SUM("RevenueVariance_Actual_vs_Forecast") AS "yAxis" FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH) AND TO_DATE("Date", 'DD/MM/YYYY') <= CURDATE() GROUP BY TO_DATE("Date", 'DD/MM/YYYY') ORDER BY TO_DATE("Date", 'DD/MM/YYYY');

Chart Title 3: Daily Total Revenue Generation for Broadband Products from Today Forward
SQL Query 3:
SELECT TO_DATE("Date", 'DD/MM/YYYY') AS "xAxis", SUM("Revenue_Generation") AS "yAxis" FROM `table_name` WHERE "Product" = 'Broadband' AND TO_DATE("Date", 'DD/MM/YYYY') >= CURDATE() AND TO_DATE("Date", 'DD/MM/YYYY') <= DATE_ADD(CURDATE(), INTERVAL 1 MONTH) GROUP BY TO_DATE("Date", 'DD/MM/YYYY') ORDER BY TO_DATE("Date", 'DD/MM/YYYY');
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Daily Revenue for Mobile Products for the Past 6 Months
SQL Query 1: SELECT DATE("Date") AS xAxis, SUM("Revenue") AS yAxis, 'Mobile' AS series FROM `table_name` WHERE "Date" >= CURDATE() - INTERVAL 6 MONTH AND "Date" <= CURDATE() GROUP BY DATE("Date") ORDER BY xAxis;

Chart Title 2: Daily Cost Efficiency for All Products for the Next 3 Months
SQL Query 2: SELECT DATE("Date") AS xAxis, AVG("Cost_Efficiency") AS yAxis FROM `table_name` WHERE "Date" >= CURDATE() AND "Date" < CURDATE() + INTERVAL 3 MONTH GROUP BY DATE("Date") ORDER BY xAxis;

Chart Title 3: Daily Revenue Variance for Broadband Products Over the Past Year
SQL Query 3: SELECT DATE("Date") AS xAxis, SUM("RevenueVariance_Actual_vs_Forecast") AS yAxis FROM `table_name` WHERE "Date" >= CURDATE() - INTERVAL 1 YEAR AND "Date" < CURDATE() GROUP BY DATE("Date") ORDER BY xAxis;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_daily_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

            else:
                filtered_feedbacks_by_chart_and_no_timeframe = [
                    feedback
                    for feedback in filtered_liked_feedbacks
                    if feedback.get("chart_type") == "table_chart"
                    and not feedback.get("time_frame", "").strip()
                ]

                if not filtered_feedbacks_by_chart_and_no_timeframe:
                    QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Top 5 Products by Percentage of Total EBIT
SQL Query 1: SELECT "Product" AS xAxis, SUM("EBIT_Margin") / SUM(SUM("EBIT_Margin")) OVER () * 100 AS yAxis FROM `table_name` GROUP BY xAxis ORDER BY yAxis DESC LIMIT 5;

Chart Title 2: Top 3 Products that Generate the Highest Revenue
SQL Query 2: SELECT "Product" AS xAxis, SUM("Revenue") AS yAxis FROM `table_name` GROUP BY "Product" ORDER BY yAxis DESC LIMIT 3;


Chart Title 3: Total Revenue Generated by Broadband Product
SQL Query 3: SELECT 'Broadband' AS xAxis, SUM("Revenue_Broadband") AS yAxis FROM `table_name`;

Chart Title 4: Total Cost Incurred by Entertainment and Broadband Respectively
SQL Query 4: SELECT 'Entertainment' AS xAxis, SUM("Cost_Efficiency") AS yAxis FROM `table_name` UNION ALL SELECT 'Broadband' AS xAxis, SUM("Cost_Broadband") AS yAxis FROM `table_name`;

Based on DDL 2, here are the chart titles and sql queries.

Chart Title 1: Top 5 Products by Percentage of Total EBIT
SQL Query 1: SELECT "Product" AS xAxis, SUM("EBIT_Margin") / SUM(SUM("EBIT_Margin")) OVER () * 100 AS yAxis FROM `table_name` GROUP BY xAxis ORDER BY yAxis DESC LIMIT 5;


Chart Title 2: Top 3 Products that Generate the Highest Revenue
SQL Query 2: SELECT "Product" AS xAxis, SUM("Revenue_Generation") AS yAxis FROM `table_name` GROUP BY "Product" ORDER BY yAxis DESC LIMIT 3;

Chart Title 3: Total Revenue Generated by Broadband Product
SQL Query 3: SELECT 'Broadband' AS xAxis, SUM("Revenue_Broadband") AS yAxis FROM `table_name`;

Chart Title 4: Total Earning Per Cost Incurred by all products
SQL Query 4: SELECT "Product" AS xAxis, SUM("Earning_per_Cost") AS yAxis FROM `table_name` GROUP BY xAxis ORDER BY xAxis;
"""
                else:
                    # Only append this line if token count allows
                    heading = "\nHere are the chart titles and sql queries\n"
                    new_data_tokens = calculate_token_usage(heading)
                    if (
                        TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                        <= TARGET_TOKEN_LIMIT
                    ):
                        QUERY_SAMPLES += heading
                        TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                    for idx, chart in enumerate(
                        filtered_feedbacks_by_chart_and_no_timeframe,
                        start=1,
                    ):
                        chart_title = chart.get("chart_title", "")
                        sql_query = chart.get("sql_query", "")
                        sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                        # Calculate token usage for the current chart and SQL query
                        new_data_tokens = calculate_token_usage(sample)

                        # Check if appending this data would exceed the token limit
                        if (
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                            <= TARGET_TOKEN_LIMIT
                        ):
                            QUERY_SAMPLES += sample

                            # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                        else:
                            # If appending would exceed, break the loop
                            break

            if (
                isinstance(chart_axis["xAxis_column"], str)
                and chart_axis["xAxis_column"] in data_summary.column_data_tribes.keys()
                and data_summary.column_data_tribes[chart_axis["xAxis_column"]]
                in ["date_related"]
                and chart_axis["xAxis_column"]
                in data_summary.column_sql_data_types.keys()
                and data_summary.column_sql_data_types[
                    chart_axis["xAxis_column"]
                ].lower()
                not in [
                    "tinyint",
                    "smallint",
                    "mediumint",
                    "int",
                    "bigint",
                    "float",
                    "double",
                    "decimal",
                    "bit",
                ]
            ):
                if time_duration == "Week":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Week"
                        and chart["chart_type"] == "table_chart"
                    ]

                    if (
                        chart_axis["xAxis_column"]
                        in data_summary.column_sql_data_types.keys()
                    ):
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Total Revenue Generation by Product for the Past 2 Weeks
SQL Query 1: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, SUM(Revenue_Generation) AS yAxis, Product AS series FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN DATE_TRUNC('week', CURRENT_DATE - INTERVAL '2 week') AND DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '6 day' GROUP BY xAxis, series ORDER BY xAxis ASC, series;

Chart Title 2: Weekly Average EBIT Margin for Next 3 Weeks
SQL Query 2: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, AVG(EBIT_Margin) AS yAxis FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN DATE_TRUNC('week', CURRENT_DATE) AND DATE_TRUNC('week', CURRENT_DATE + INTERVAL '3 week') + INTERVAL '6 day' GROUP BY xAxis ORDER BY xAxis;

Chart Title 3: Weekly Total Cost Efficiency for Last Week
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, SUM(Cost_Efficiency) AS yAxis FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN DATE_TRUNC('week', CURRENT_DATE - INTERVAL '1 week') AND DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '6 day' GROUP BY xAxis ORDER BY xAxis;

Chart Title 4: Weekly Maximum Revenue Generation from Week 1 - Week 4 in March 2023
SQL Query 4: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, MAX(Revenue_Generation) AS yAxis FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN DATE '2023-03-01' AND DATE '2023-03-31' AND EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY')) BETWEEN 1 AND 4 GROUP BY xAxis ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Total Revenue Generation by Product for the Past 2 Weeks
SQL Query 1: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-W', EXTRACT(WEEK FROM "Date")) AS xAxis, SUM(Revenue_Generation) AS yAxis, Product AS series FROM `table_name` WHERE "Date" BETWEEN DATE_TRUNC('week', CURRENT_DATE - INTERVAL '2 week') AND DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '6 day' GROUP BY xAxis, series ORDER BY xAxis ASC, series;

Chart Title 2: Weekly Average EBIT Margin for Next 3 Weeks
SQL Query 2: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-W', EXTRACT(WEEK FROM "Date")) AS xAxis, AVG(EBIT_Margin) AS yAxis FROM `table_name` WHERE "Date" BETWEEN DATE_TRUNC('week', CURRENT_DATE) AND DATE_TRUNC('week', CURRENT_DATE + INTERVAL '3 week') + INTERVAL '6 day' GROUP BY xAxis ORDER BY xAxis;

Chart Title 3: Weekly Total Cost Efficiency for Last Week
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-W', EXTRACT(WEEK FROM "Date")) AS xAxis, SUM(Cost_Efficiency) AS yAxis FROM `table_name` WHERE "Date" BETWEEN DATE_TRUNC('week', CURRENT_DATE - INTERVAL '1 week') AND DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '6 day' GROUP BY xAxis ORDER BY xAxis;

Chart Title 4: Weekly Maximum Revenue Generation from Week 1 - Week 4 in March 2023
SQL Query 4: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-W', EXTRACT(WEEK FROM "Date")) AS xAxis, MAX(Revenue_Generation) AS yAxis FROM `table_name` WHERE "Date" BETWEEN DATE '2023-03-01' AND DATE '2023-03-31' AND EXTRACT(WEEK FROM "Date") BETWEEN 1 AND 4 GROUP BY xAxis ORDER BY xAxis;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif time_duration == "Month":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Month"
                        and chart["chart_type"] == "table_chart"
                    ]

                    if (
                        chart_axis["xAxis_column"]
                        in data_summary.column_sql_data_types.keys()
                    ):
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue Generation by Product for the Past 6 Months
SQL Query 1: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-M', EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, SUM(Revenue_Generation) AS yAxis, Product AS series FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') >= CURRENT_DATE - INTERVAL '6 months' GROUP BY xAxis, series ORDER BY xAxis ASC, series;

Chart Title 2: Monthly Average EBIT Margin for Next January
SQL Query 2: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-M', EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, AVG(EBIT_Margin) AS yAxis FROM `table_name` WHERE EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) = EXTRACT(YEAR FROM CURRENT_DATE) + 1 AND EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) = 1 GROUP BY xAxis ORDER BY xAxis;

Chart Title 3: Monthly Total Cost Efficiency for March
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-M', EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, SUM(Cost_Efficiency) AS yAxis FROM `table_name` WHERE EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) = 3 AND EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) = EXTRACT(YEAR FROM CURRENT_DATE) GROUP BY xAxis ORDER BY xAxis;

Chart Title 4: Monthly Total Revenue Variance Actual vs Forecast from Jan 2022 - Mar 2022
SQL Query 4: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-M', EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, SUM(RevenueVariance_Actual_vs_Forecast) AS yAxis FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN DATE '2022-01-01' AND DATE '2022-03-31' GROUP BY xAxis ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue Generation by Product for the Past 6 Months
SQL Query 1: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-M', EXTRACT(MONTH FROM "Date")) AS xAxis, SUM(Revenue_Generation) AS yAxis, Product AS series FROM `table_name` WHERE "Date" >= CURRENT_DATE - INTERVAL '6 months' GROUP BY xAxis, series ORDER BY xAxis ASC, series;

Chart Title 2: Monthly Average EBIT Margin for Next January
SQL Query 2: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-M', EXTRACT(MONTH FROM "Date")) AS xAxis, AVG(EBIT_Margin) AS yAxis FROM `table_name` WHERE EXTRACT(YEAR FROM "Date") = EXTRACT(YEAR FROM CURRENT_DATE) + 1 AND EXTRACT(MONTH FROM "Date") = 1 GROUP BY xAxis ORDER BY xAxis;

Chart Title 3: Monthly Total Cost Efficiency for March
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-M', EXTRACT(MONTH FROM "Date")) AS xAxis, SUM(Cost_Efficiency) AS yAxis FROM `table_name` WHERE EXTRACT(MONTH FROM "Date") = 3 AND EXTRACT(YEAR FROM "Date") = EXTRACT(YEAR FROM CURRENT_DATE) GROUP BY xAxis ORDER BY xAxis;

Chart Title 4: Monthly Total Revenue Variance Actual vs Forecast from Jan 2022 - Mar 2022
SQL Query 4: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-M', EXTRACT(MONTH FROM "Date")) AS xAxis, SUM(RevenueVariance_Actual_vs_Forecast) AS yAxis FROM `table_name` WHERE "Date" BETWEEN DATE '2022-01-01' AND DATE '2022-03-31' GROUP BY xAxis ORDER BY xAxis;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif time_duration == "Quarter":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Quarter"
                        and chart["chart_type"] == "table_chart"
                    ]

                    if (
                        chart_axis["xAxis_column"]
                        in data_summary.column_sql_data_types.keys()
                    ):
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Total Revenue Variance Actual vs Forecast for the Last Q3
SQL Query 1: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-Q', EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, SUM(RevenueVariance_Actual_vs_Forecast) AS yAxis FROM `table_name` WHERE EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY')) = 3 AND TO_DATE("Date", 'DD/MM/YYYY') >= CURRENT_DATE - INTERVAL '1 year' GROUP BY xAxis ORDER BY xAxis;

Chart Title 2: Quarterly Total EBIT Margin for the Next Quarter
SQL Query 2: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-Q', EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, SUM(EBIT_Margin) AS yAxis FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '3 months' GROUP BY xAxis ORDER BY xAxis;

Chart Title 3: Quarterly Average Revenue Generation for the Past H2
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-Q', EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, AVG(Revenue_Generation) AS yAxis FROM `table_name` WHERE EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY')) IN (3,
4) AND TO_DATE("Date", 'DD/MM/YYYY') >= CURRENT_DATE - INTERVAL '1 year' GROUP BY xAxis ORDER BY xAxis;

Chart Title 4: Quarterly Total Earning per Cost for Q1 2023 - Q3 2023
SQL Query 4: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-Q', EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, SUM(Earning_per_Cost) AS yAxis FROM `table_name` WHERE EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) = 2023 AND EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY')) BETWEEN 1 AND 3 GROUP BY xAxis ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Total Revenue Variance Actual vs Forecast for the Last Q3
SQL Query 1: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) AS xAxis, SUM(RevenueVariance_Actual_vs_Forecast) AS yAxis FROM `table_name` WHERE EXTRACT(QUARTER FROM "Date") = 3 AND "Date" >= CURRENT_DATE - INTERVAL '1 year' GROUP BY xAxis ORDER BY xAxis;

Chart Title 2: Quarterly Total EBIT Margin for the Next Quarter
SQL Query 2: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) AS xAxis, SUM(EBIT_Margin) AS yAxis FROM `table_name` WHERE "Date" BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '3 months' GROUP BY xAxis ORDER BY xAxis;

Chart Title 3: Quarterly Average Revenue Generation for the Past H2
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) AS xAxis, AVG(Revenue_Generation) AS yAxis FROM `table_name` WHERE EXTRACT(QUARTER FROM "Date") IN (3,
4) AND "Date" >= CURRENT_DATE - INTERVAL '1 year' GROUP BY xAxis ORDER BY xAxis;

Chart Title 4: Quarterly Total Earning per Cost for Q1 2023 - Q3 2023
SQL Query 4: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) AS xAxis, SUM(Earning_per_Cost) AS yAxis FROM `table_name` WHERE EXTRACT(YEAR FROM "Date") = 2023 AND EXTRACT(QUARTER FROM "Date") BETWEEN 1 AND 3 GROUP BY xAxis ORDER BY xAxis;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif time_duration == "Year":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Year"
                        and chart["chart_type"] == "table_chart"
                    ]

                    if (
                        chart_axis["xAxis_column"]
                        in data_summary.column_sql_data_types.keys()
                    ):
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Percentage Change in Broadband Revenue for the Past 5 Years
SQL Query 1: WITH RevenueData AS (SELECT EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) AS xAxis, SUM(Revenue_Broadband) AS yAxis FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN DATE_TRUNC('year', CURRENT_DATE - INTERVAL '5 year') AND DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '1 year - 1 day' GROUP BY xAxis) SELECT xAxis, yAxis, LAG(yAxis) OVER (ORDER BY xAxis) AS prevYearRevenue, ROUND(((yAxis - LAG(yAxis) OVER (ORDER BY xAxis)) / NULLIF(LAG(yAxis) OVER (ORDER BY xAxis), 0)) * 100, 2) AS PercentageChange FROM RevenueData ORDER BY xAxis;

Chart Title 2: Yearly Average EBIT Margin for Next Year
SQL Query 2: SELECT EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) AS xAxis, AVG(EBIT_Margin) AS yAxis FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN DATE_TRUNC('year', CURRENT_DATE + INTERVAL '1 year') AND DATE_TRUNC('year', CURRENT_DATE + INTERVAL '2 year') + INTERVAL '1 year - 1 day' GROUP BY xAxis ORDER BY xAxis;

Chart Title 3: Yearly Total Revenue Generation for 2024
SQL Query 3: SELECT EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) AS xAxis, SUM(Revenue_Generation) AS yAxis FROM `table_name` WHERE EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) = 2024 GROUP BY xAxis ORDER BY xAxis;

Chart Title 4: Yearly Total Cost and Revenue for the Last 3 Years
SQL Query 4: SELECT EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) AS xAxis, SUM(Cost_Efficiency) AS yAxis, SUM(Revenue) AS yAxis2 FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN DATE_TRUNC('year', CURRENT_DATE - INTERVAL '3 year') AND DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '1 year - 1 day' GROUP BY xAxis ORDER BY xAxis;

Chart Title 5: Yearly Total Revenue Variance for Actual vs Forecast for 2022 - 2023
SQL Query 5: SELECT EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) AS xAxis, SUM(RevenueVariance_Actual_vs_Forecast) AS yAxis FROM `table_name` WHERE EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) BETWEEN 2022 AND 2023 GROUP BY xAxis ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Percentage Change in Broadband Revenue for the Past 5 Years
SQL Query 1: WITH RevenueData AS (SELECT EXTRACT(YEAR FROM "Date") AS xAxis, SUM(Revenue_Broadband) AS yAxis FROM `table_name` WHERE "Date" BETWEEN DATE_TRUNC('year', CURRENT_DATE - INTERVAL '5 year') AND DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '1 year - 1 day' GROUP BY xAxis) SELECT xAxis, yAxis, LAG(yAxis) OVER (ORDER BY xAxis) AS prevYearRevenue, ROUND(((yAxis - LAG(yAxis) OVER (ORDER BY xAxis)) / NULLIF(LAG(yAxis) OVER (ORDER BY xAxis), 0)) * 100, 2) AS PercentageChange FROM RevenueData ORDER BY xAxis;

Chart Title 2: Yearly Average EBIT Margin for Next Year
SQL Query 2: SELECT EXTRACT(YEAR FROM "Date") AS xAxis, AVG(EBIT_Margin) AS yAxis FROM `table_name` WHERE "Date" BETWEEN DATE_TRUNC('year', CURRENT_DATE + INTERVAL '1 year') AND DATE_TRUNC('year', CURRENT_DATE + INTERVAL '2 year') + INTERVAL '1 year - 1 day' GROUP BY xAxis ORDER BY xAxis;

Chart Title 3: Yearly Total Revenue Generation for 2024
SQL Query 3: SELECT EXTRACT(YEAR FROM "Date") AS xAxis, SUM(Revenue_Generation) AS yAxis FROM `table_name` WHERE EXTRACT(YEAR FROM "Date") = 2024 GROUP BY xAxis ORDER BY xAxis;

Chart Title 4: Yearly Total Cost and Revenue for the Last 3 Years
SQL Query 4: SELECT EXTRACT(YEAR FROM "Date") AS xAxis, SUM(Cost_Efficiency) AS yAxis, SUM(Revenue) AS yAxis2 FROM `table_name` WHERE "Date" BETWEEN DATE_TRUNC('year', CURRENT_DATE - INTERVAL '3 year') AND DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '1 year - 1 day' GROUP BY xAxis ORDER BY xAxis;

Chart Title 5: Yearly Total Revenue Variance for Actual vs Forecast for 2022 - 2023
SQL Query 5: SELECT EXTRACT(YEAR FROM "Date") AS xAxis, SUM(RevenueVariance_Actual_vs_Forecast) AS yAxis FROM `table_name` WHERE EXTRACT(YEAR FROM "Date") BETWEEN 2022 AND 2023 GROUP BY xAxis ORDER BY xAxis;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

        # Not table chart
        else:
            x_column = chart_axis["xAxis_column"]
            if (
                isinstance(x_column, str)
                and x_column in data_summary.column_data_tribes.keys()
                and data_summary.column_data_tribes[x_column] == "date_related"
            ):
                if timeframe.lower() == "yearly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        # Handle Yearly Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_yearly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "yearly"
                        ]

                        if not filtered_feedbacks_by_chart_and_yearly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Total Revenue Variance for the Past Two Years
SQL Query 1: SELECT EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) AS "xAxis", SUM("RevenueVariance_Actual_vs_Forecast") AS "yAxis" FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') >= CURRENT_DATE - INTERVAL '2 YEAR' AND TO_DATE("Date", 'DD/MM/YYYY') <= CURRENT_DATE GROUP BY EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) ORDER BY "xAxis";

Chart Title 2: Yearly Total Cost Efficiency for the Current Year and the Previous Year
SQL Query 2: SELECT EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) AS "xAxis", SUM("Cost_Efficiency") AS "yAxis" FROM `table_name` WHERE EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) >= EXTRACT(YEAR FROM CURRENT_DATE - INTERVAL '1 YEAR') AND EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) <= EXTRACT(YEAR FROM CURRENT_DATE) GROUP BY EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) ORDER BY "xAxis";

Chart Title 3: Yearly Total Revenue Generation Forecast for the Next Two Years
SQL Query 3: SELECT EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) AS "xAxis", SUM("Revenue_Generation") AS "yAxis" FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') >= CURRENT_DATE AND TO_DATE("Date", 'DD/MM/YYYY') < CURRENT_DATE + INTERVAL '2 YEAR' GROUP BY EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) ORDER BY "xAxis";
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Total Revenue by Product for the Past 5 Years
SQL Query 1: SELECT EXTRACT(YEAR FROM "Date") AS "xAxis", "Product" AS "series", SUM("Revenue") AS "yAxis" FROM `table_name` WHERE EXTRACT(YEAR FROM "Date") BETWEEN EXTRACT(YEAR FROM CURDATE()) - 5 AND EXTRACT(YEAR FROM CURDATE()) GROUP BY "xAxis", "series";

Chart Title 2: Yearly Total Cost Efficiency vs. Revenue Generation for Broadband Over the Last 3 Years
SQL Query 2: SELECT EXTRACT(YEAR FROM "Date") AS "xAxis", 'Broadband' AS "series", SUM("Cost_Efficiency") AS "yAxis", SUM("Revenue_Generation") AS "yAxis2" FROM `table_name` WHERE "Product" = 'Broadband' AND EXTRACT(YEAR FROM "Date") BETWEEN EXTRACT(YEAR FROM CURDATE()) - 3 AND EXTRACT(YEAR FROM CURDATE()) GROUP BY "xAxis", "series";

Chart Title 3: Yearly Actual vs. Forecasted Total Revenue Variance for the Last 7 Years
SQL Query 3: SELECT EXTRACT(YEAR FROM "Date") AS "xAxis", 'Revenue Variance' AS "series", SUM("RevenueVariance_Actual_vs_Forecast") AS "yAxis" FROM `table_name` WHERE EXTRACT(YEAR FROM "Date") BETWEEN EXTRACT(YEAR FROM CURDATE()) - 7 AND EXTRACT(YEAR FROM CURDATE()) GROUP BY "xAxis", "series";
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_yearly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "half-yearly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        # Handle Half-Yearly Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_half_yearly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "half-yearly"
                        ]

                        if not filtered_feedbacks_by_chart_and_half_yearly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Half-Yearly Total Revenue Variance vs. Forecast for the Past Year
SQL Query 1: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-H', CASE WHEN EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) <= 6 THEN 1 ELSE 2 END) AS "xAxis", SUM("RevenueVariance_Actual_vs_Forecast") AS "yAxis" FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) AND TO_DATE("Date", 'DD/MM/YYYY') <= CURDATE() GROUP BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-H', CASE WHEN EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) <= 6 THEN 1 ELSE 2 END) ORDER BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-H', CASE WHEN EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) <= 6 THEN 1 ELSE 2 END);

Chart Title 2: Half-Yearly Average Earning Per Cost Analysis for the Last 2 Years
SQL Query 2: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-H', CASE WHEN EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) <= 6 THEN 1 ELSE 2 END) AS "xAxis", AVG("Earning_per_Cost") AS "yAxis" FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR) AND TO_DATE("Date", 'DD/MM/YYYY') < CURDATE() GROUP BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-H', CASE WHEN EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) <= 6 THEN 1 ELSE 2 END) ORDER BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-H', CASE WHEN EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) <= 6 THEN 1 ELSE 2 END);

Chart Title 3: Half-Yearly Average Cost Efficiency Comparison for the Next 6 Months
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-H', CASE WHEN EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) <= 6 THEN 1 ELSE 2 END) AS "xAxis", AVG("Cost_Efficiency") AS "yAxis" FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') >= CURDATE() AND TO_DATE("Date", 'DD/MM/YYYY') <= DATE_ADD(CURDATE(), INTERVAL 6 MONTH) GROUP BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-H', CASE WHEN EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) <= 6 THEN 1 ELSE 2 END) ORDER BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-H', CASE WHEN EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) <= 6 THEN 1 ELSE 2 END);
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Semi-Annual Revenue Generation for the Past Two Years
SQL Query 1: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-H', CASE WHEN EXTRACT(MONTH FROM "Date") <= 6 THEN 1 ELSE 2 END) AS "xAxis", SUM("Revenue_Generation") AS "yAxis" FROM `table_name` WHERE "Date" >= DATE_SUB(CURRENT_DATE, INTERVAL 2 YEAR) AND "Date" < CURRENT_DATE GROUP BY CONCAT(EXTRACT(YEAR FROM "Date"), '-H', CASE WHEN EXTRACT(MONTH FROM "Date") <= 6 THEN 1 ELSE 2 END) ORDER BY "xAxis";

Chart Title 2: Half-Yearly Cost Efficiency Trends for the Next Year
SQL Query 2: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-H', CASE WHEN EXTRACT(MONTH FROM "Date") <= 6 THEN 1 ELSE 2 END) AS "xAxis", AVG("Cost_Efficiency") AS "yAxis" FROM `table_name` WHERE "Date" >= CURRENT_DATE AND "Date" <= DATE_ADD(CURRENT_DATE, INTERVAL 1 YEAR) GROUP BY CONCAT(EXTRACT(YEAR FROM "Date"), '-H', CASE WHEN EXTRACT(MONTH FROM "Date") <= 6 THEN 1 ELSE 2 END) ORDER BY "xAxis";

Chart Title 3: Half-Yearly EBIT Margin Comparison for the Past Year
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-H', CASE WHEN EXTRACT(MONTH FROM "Date") <= 6 THEN 1 ELSE 2 END) AS "xAxis", AVG("EBIT_Margin") AS "yAxis" FROM `table_name` WHERE "Date" >= DATE_SUB(CURRENT_DATE, INTERVAL 1 YEAR) AND "Date" <= CURRENT_DATE GROUP BY CONCAT(EXTRACT(YEAR FROM "Date"), '-H', CASE WHEN EXTRACT(MONTH FROM "Date") <= 6 THEN 1 ELSE 2 END) ORDER BY "xAxis";
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_half_yearly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "quarterly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        # Handle Quarterly Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_quarterly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "quarterly"
                        ]

                        if not filtered_feedbacks_by_chart_and_quarterly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Average Earning per Cost by Product (Q1 & Q2 2022)
Sql Query 1: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE(\"Date\", 'DD/MM/YYYY')), '-Q', EXTRACT(QUARTER FROM TO_DATE(\"Date\", 'DD/MM/YYYY'))) AS \"xAxis\",         \"Product\" AS \"series\",         AVG(\"Earning_per_Cost\") AS \"yAxis\" FROM `table_name` WHERE TO_DATE(\"Date\", 'DD/MM/YYYY') BETWEEN TO_DATE('2022-01-01', 'YYYY-MM-DD') AND TO_DATE('2022-06-30', 'YYYY-MM-DD') GROUP BY \"xAxis\", \"series\";

Chart Title 2: Quarterly Total Revenue Generation for the Past Four Quarters
SQL Query 2: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-Q', EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, SUM("Revenue_Generation") AS yAxis FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) AND TO_DATE("Date", 'DD/MM/YYYY') < CURDATE() GROUP BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-Q', EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY'))) ORDER BY xAxis;

Chart Title 3: Quarterly Total Cost Efficiency for the Next Two Quarters
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-Q', EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, SUM("Cost_Efficiency") AS yAxis FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') >= CURDATE() AND TO_DATE("Date", 'DD/MM/YYYY') < DATE_ADD(CURDATE(), INTERVAL 6 MONTH) GROUP BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-Q', EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY'))) ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Total Revenue for Broadband and Mobile Products for Previous Year
Sql Query 1: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) AS "xAxis", SUM("Revenue_Broadband") AS "yAxis", 'Broadband' AS "series" FROM `table_name` WHERE (EXTRACT(YEAR FROM "Date") = EXTRACT(YEAR FROM CURRENT_DATE)AND EXTRACT(QUARTER FROM "Date") <= EXTRACT(QUARTER FROM CURRENT_DATE))OR (EXTRACT(YEAR FROM "Date") = EXTRACT(YEAR FROM CURRENT_DATE) - 1 AND EXTRACT(QUARTER FROM "Date") > EXTRACT(QUARTER FROM CURRENT_DATE)) GROUP BY CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) UNION ALL SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) AS "xAxis", SUM("Revenue_Mobile") AS "yAxis", 'Mobile' AS "series" FROM `table_name` WHERE (EXTRACT(YEAR FROM "Date") = EXTRACT(YEAR FROM CURRENT_DATE) AND EXTRACT(QUARTER FROM "Date") <= EXTRACT(QUARTER FROM CURRENT_DATE)) OR (EXTRACT(YEAR FROM "Date") = EXTRACT(YEAR FROM CURRENT_DATE) - 1 AND EXTRACT(QUARTER FROM "Date") > EXTRACT(QUARTER FROM CURRENT_DATE)) GROUP BY CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) ORDER BY "xAxis", "series";

Chart Title 2: Quarterly Total Revenue for Broadband Products for the Past Three Quarters 
Sql Query 2: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) AS "xAxis", SUM("Revenue_Broadband") AS "yAxis", 'Broadband' AS "series" FROM `table_name` WHERE "Date" >= DATE_TRUNC('quarter', CURRENT_DATE - INTERVAL '9 months') AND "Date" < DATE_TRUNC('quarter', CURRENT_DATE) GROUP BY CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) ORDER BY "xAxis", "series";

Chart Title 3: Quarterly Average Cost Efficiency for Broadband Products for the Next Two Years
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) AS "xAxis", AVG("Cost_Efficiency") AS "yAxis" FROM `table_name` WHERE "Date" >= CURRENT_DATE AND "Date" < CURRENT_DATE + INTERVAL '2 YEAR' GROUP BY CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) ORDER BY "xAxis";
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_quarterly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "monthly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        # Handle Monthly Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_monthly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "monthly"
                        ]
                        if not filtered_feedbacks_by_chart_and_monthly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue Variance (Actual vs. Forecast) by Product for Last Year
Sql Query 1: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-M', EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS "xAxis", SUM("RevenueVariance_Actual_vs_Forecast") AS "yAxis", "Product" AS "series" FROM `table_name` WHERE EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) = EXTRACT(YEAR FROM CURRENT_DATE) - 1 GROUP BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-M', EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY'))), "Product" ORDER BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-M', EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')));

Chart Title 2: Monthly Average Cost Efficiency by Product for the Past 12 Months
Sql Query 2: SELECT TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM') AS "xAxis","Product" AS "series", AVG("Cost_Efficiency") AS "yAxis" FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') >= TO_DATE(EXTRACT(YEAR FROM CURRENT_DATE) - 1 || '-M' || EXTRACT(MONTH FROM CURRENT_DATE) || '-01', 'YYYY-MM-DD') GROUP BY "xAxis", "series" ORDER BY "xAxis", "series";

Chart Title 3: Monthly Average Earning per Cost for Broadband and Mobile Products in the Past Two Years
Sql Query 3: SELECT TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM') AS "xAxis", "Product" AS "series", AVG("Earning_per_Cost") AS "yAxis" FROM `table_name` WHERE "Product" IN ('BroadBand', 'Mobile') AND TO_DATE("Date", 'DD/MM/YYYY') >= DATE_TRUNC('MONTH', CURRENT_DATE - INTERVAL '2 years')::date AND TO_DATE("Date", 'DD/MM/YYYY') <= CURRENT_DATE::date AND EXTRACT(DAY FROM TO_DATE("Date", 'DD/MM/YYYY')) = 1 GROUP BY TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM'), "Product" ORDER BY TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM'), "Product";

Chart Title 4: Monthly Percentage Contribution of Total Revenue Generation by Product for the Last Year
Sql Query 4: WITH revenue_summary AS (SELECT TO_DATE("Date", 'DD/MM/YYYY') AS "xAxis", SUM("Revenue_Generation") AS "revenue", "Product" FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN DATE_TRUNC('year', CURRENT_DATE - INTERVAL '1 year') AND DATE_TRUNC('year', CURRENT_DATE) - INTERVAL '1 day' GROUP BY TO_DATE("Date", 'DD/MM/YYYY'), "Product") SELECT "xAxis", "Product", ("revenue" / SUM("revenue") OVER (PARTITION BY "xAxis")) * 100 AS "yAxis" FROM revenue_summary ORDER BY "xAxis", "Product";

Chart Title 5: Monthly Total EBIT Margin and Total Earning per Cost for the Last Year
Sql Query 5: SELECT TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM') AS "xAxis", SUM("EBIT_Margin") AS "yAxis", SUM("Earning_per_Cost") AS "yAxis2" FROM `table_name` WHERE EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) = EXTRACT(YEAR FROM CURRENT_DATE) -1 GROUP BY TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM') ORDER BY TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM');

Chart Title 6: Monthly Median Revenue Variance (Actual vs. Forecast) for Top 3 Products in 2023
Sql Query 6: SELECT TO_CHAR(TO_DATE(\"Date\", 'DD/MM/YYYY'), 'YYYY-MM') AS \"xAxis\", PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY \"RevenueVariance_Actual_vs_Forecast\") AS \"yAxis\", \"Product\" AS \"series\" FROM `table_name` WHERE TO_DATE(\"Date\", 'DD/MM/YYYY') BETWEEN DATE_TRUNC('year', '2023-01-01'::date) AND DATE_TRUNC('year', '2024-01-01'::date) AND \"Product\" IN (SELECT \"Product\" FROM `table_name` GROUP BY \"Product\" ORDER BY SUM(\"RevenueVariance_Actual_vs_Forecast\") DESC LIMIT 3) GROUP BY \"Product\", \"xAxis\" ORDER BY \"xAxis\", \"series\";

Chart Title 7: Monthly Percentage Change in Total Revenue Variance (Actual vs. Forecast) for Top 3 Products (H1 vs. H2 2023)
Sql Query 7: SELECT TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM') AS "xAxis", "Product" AS "series", ((SUM("RevenueVariance_Actual_vs_Forecast") FILTER (WHERE TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM') BETWEEN '2023-07' AND '2023-12')) / (SUM("RevenueVariance_Actual_vs_Forecast") FILTER (WHERE TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM') BETWEEN '2023-01' AND '2023-06'))) * 100 AS "yAxis" FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN '2023-01-01' AND '2023-12-31' AND "Product" IN (SELECT "Product" FROM `table_name` GROUP BY "Product" ORDER BY SUM("RevenueVariance_Actual_vs_Forecast") DESC LIMIT 3) GROUP BY "xAxis", "series" ORDER BY "xAxis", "series";
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Cost Forecast for Mobile and Broadband for the Next Three Months
Sql Query 1: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-M', EXTRACT(MONTH FROM "Date")) AS "xAxis", SUM("Cost_Mobile") AS "yAxis", SUM("Cost_Broadband") AS "yAxis2" FROM `table_name` WHERE "Date" > DATE_TRUNC('month', CURRENT_DATE) AND "Date" < DATE_TRUNC('month', CURRENT_DATE + INTERVAL '3 month') GROUP BY CONCAT(EXTRACT(YEAR FROM "Date"), '-M', EXTRACT(MONTH FROM "Date")) ORDER BY CONCAT(EXTRACT(YEAR FROM "Date"), '-M', EXTRACT(MONTH FROM "Date"));

Chart Title 2: Monthly Total Cost Forecast for Broadband and Mobile for the Next Year
Sql Query 2: SELECT TO_CHAR("Date", 'YYYY-MM') AS "xAxis", SUM("Cost_Broadband") AS "yAxis", SUM("Cost_Mobile") AS "yAxis2" FROM `table_name` WHERE "Date" >= DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '1 year' AND "Date" < DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '2 years' GROUP BY TO_CHAR("Date", 'YYYY-MM') ORDER BY TO_CHAR("Date", 'YYYY-MM');
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_monthly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "weekly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        # Handle Weekly Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_weekly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "weekly"
                        ]

                        if not filtered_feedbacks_by_chart_and_weekly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Total Revenue Generated by Broadband Product Over Time
Sql Query 1: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS "xAxis", SUM("Revenue_Broadband") AS "yAxis", 'Broadband' AS "series" FROM `table_name` WHERE "Product" = 'Broadband' GROUP BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY'))) ORDER BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY')));

Chart Title 2: Weekly Total Revenue Variance Comparison for the Past Year
SQL Query 2: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS "xAxis", SUM("RevenueVariance_Actual_vs_Forecast") AS "yAxis" FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) GROUP BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY'))) ORDER BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY')));

Chart Title 3: Weekly Average Cost Efficiency of Products in the Current Year
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS "xAxis", AVG("Cost_Efficiency") AS "yAxis" FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN DATE(CONCAT(EXTRACT(YEAR FROM CURDATE()), '-01-01')) AND CURDATE() GROUP BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY'))) ORDER BY CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY')));
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Total Revenue from Mobile Products for the Past Year
SQL Query 1: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-W', EXTRACT(WEEK FROM "Date")) AS "xAxis", SUM("Revenue") AS "yAxis", 'Mobile' AS "series" FROM `table_name` WHERE "Date" >= DATE_SUB(CURRENT_DATE, INTERVAL 1 YEAR) AND "Date" < CURRENT_DATE AND "Product" = 'Mobile' GROUP BY CONCAT(EXTRACT(YEAR FROM "Date"), '-W', EXTRACT(WEEK FROM "Date")) ORDER BY "xAxis", "series";

Chart Title 2: Weekly Average Cost Efficiency for All Products for the Next Six Months
SQL Query 2: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-W', EXTRACT(WEEK FROM "Date")) AS "xAxis", AVG("Cost_Efficiency") AS "yAxis" FROM `table_name` WHERE "Date" >= CURRENT_DATE AND "Date" < DATE_ADD(CURRENT_DATE, INTERVAL 6 MONTH) GROUP BY CONCAT(EXTRACT(YEAR FROM "Date"), '-W', EXTRACT(WEEK FROM "Date")) ORDER BY "xAxis";

Chart Title 3: Weekly Total Revenue Variance for Broadband Products for the Past Two Years
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-W', EXTRACT(WEEK FROM "Date")) AS "xAxis", SUM("RevenueVariance_Actual_vs_Forecast") AS "yAxis" FROM `table_name` WHERE "Date" >= DATE_SUB(CURRENT_DATE, INTERVAL 2 YEAR) AND "Date" < CURRENT_DATE AND "Product" = 'Broadband' GROUP BY CONCAT(EXTRACT(YEAR FROM "Date"), '-W', EXTRACT(WEEK FROM "Date")) ORDER BY "xAxis";
"""

                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_weekly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "daily":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        # Handle Daily Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_daily_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "daily"
                        ]
                        if not filtered_feedbacks_by_chart_and_daily_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Ttile 1: Daily Profit Earned by Types of Product in Year 2023
Sql Query 1: SELECT TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM-DD') AS "xAxis", "Product" AS "series", SUM("Revenue") AS "yAxis" FROM `table_name` WHERE EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) = 2023 GROUP BY TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM-DD'), "Product" ORDER BY TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY-MM-DD'), "Product";

Chart Title 2: Daily Total Revenue Variance for All Products in the Past 6 Months
SQL Query 2:
SELECT TO_DATE("Date", 'DD/MM/YYYY') AS "xAxis", SUM("RevenueVariance_Actual_vs_Forecast") AS "yAxis" FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH) AND TO_DATE("Date", 'DD/MM/YYYY') <= CURDATE() GROUP BY TO_DATE("Date", 'DD/MM/YYYY') ORDER BY TO_DATE("Date", 'DD/MM/YYYY');

Chart Title 3: Daily Total Revenue Generation for Broadband Products from Today Forward
SQL Query 3:
SELECT TO_DATE("Date", 'DD/MM/YYYY') AS "xAxis", SUM("Revenue_Generation") AS "yAxis" FROM `table_name` WHERE "Product" = 'Broadband' AND TO_DATE("Date", 'DD/MM/YYYY') >= CURDATE() AND TO_DATE("Date", 'DD/MM/YYYY') <= DATE_ADD(CURDATE(), INTERVAL 1 MONTH) GROUP BY TO_DATE("Date", 'DD/MM/YYYY') ORDER BY TO_DATE("Date", 'DD/MM/YYYY');
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Daily Revenue for Mobile Products for the Past 6 Months
SQL Query 1: SELECT DATE("Date") AS xAxis, SUM("Revenue") AS yAxis, 'Mobile' AS series FROM `table_name` WHERE "Date" >= CURDATE() - INTERVAL 6 MONTH AND "Date" <= CURDATE() GROUP BY DATE("Date") ORDER BY xAxis;

Chart Title 2: Daily Cost Efficiency for All Products for the Next 3 Months
SQL Query 2: SELECT DATE("Date") AS xAxis, AVG("Cost_Efficiency") AS yAxis FROM `table_name` WHERE "Date" >= CURDATE() AND "Date" < CURDATE() + INTERVAL 3 MONTH GROUP BY DATE("Date") ORDER BY xAxis;

Chart Title 3: Daily Revenue Variance for Broadband Products Over the Past Year
SQL Query 3: SELECT DATE("Date") AS xAxis, SUM("RevenueVariance_Actual_vs_Forecast") AS yAxis FROM `table_name` WHERE "Date" >= CURDATE() - INTERVAL 1 YEAR AND "Date" < CURDATE() GROUP BY DATE("Date") ORDER BY xAxis;
"""

                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_daily_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

            else:
                filtered_feedbacks_by_chart_and_no_timeframe = [
                    feedback
                    for feedback in filtered_liked_feedbacks
                    if feedback.get("chart_type") != "table_chart"
                    and not feedback.get("time_frame", "").strip()
                ]
                if not filtered_feedbacks_by_chart_and_no_timeframe:
                    QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Top 5 Products by Percentage of Total EBIT
SQL Query 1: SELECT "Product" AS xAxis, SUM("EBIT_Margin") / SUM(SUM("EBIT_Margin")) OVER () * 100 AS yAxis FROM `table_name` GROUP BY xAxis ORDER BY yAxis DESC LIMIT 5;

Chart Title 2: Top 3 Products that Generate the Highest Revenue
SQL Query 2: SELECT "Product" AS xAxis, SUM("Revenue") AS yAxis FROM `table_name` GROUP BY "Product" ORDER BY yAxis DESC LIMIT 3;


Chart Title 3: Total Revenue Generated by Broadband Product
SQL Query 3: SELECT 'Broadband' AS xAxis, SUM("Revenue_Broadband") AS yAxis FROM `table_name`;

Chart Title 4: Total Cost Incurred by Entertainment and Broadband Respectively
SQL Query 4: SELECT 'Entertainment' AS xAxis, SUM("Cost_Efficiency") AS yAxis FROM `table_name` UNION ALL SELECT 'Broadband' AS xAxis, SUM("Cost_Broadband") AS yAxis FROM `table_name`;

Based on DDL 2, here are the chart titles and sql queries.

Chart Title 1: Top 5 Products by Percentage of Total EBIT
SQL Query 1: SELECT "Product" AS xAxis, SUM("EBIT_Margin") / SUM(SUM("EBIT_Margin")) OVER () * 100 AS yAxis FROM `table_name` GROUP BY xAxis ORDER BY yAxis DESC LIMIT 5;


Chart Title 2: Top 3 Products that Generate the Highest Revenue
SQL Query 2: SELECT "Product" AS xAxis, SUM("Revenue_Generation") AS yAxis FROM `table_name` GROUP BY "Product" ORDER BY yAxis DESC LIMIT 3;

Chart Title 3: Total Revenue Generated by Broadband Product
SQL Query 3: SELECT 'Broadband' AS xAxis, SUM("Revenue_Broadband") AS yAxis FROM `table_name`;

Chart Title 4: Total Earning Per Cost Incurred by all products
SQL Query 4: SELECT "Product" AS xAxis, SUM("Earning_per_Cost") AS yAxis FROM `table_name` GROUP BY xAxis ORDER BY xAxis;
"""

                else:
                    # Only append this line if token count allows
                    heading = "\nHere are the chart titles and sql queries\n"
                    new_data_tokens = calculate_token_usage(heading)
                    if (
                        TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                        <= TARGET_TOKEN_LIMIT
                    ):
                        QUERY_SAMPLES += heading
                        TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                    for idx, chart in enumerate(
                        filtered_feedbacks_by_chart_and_no_timeframe,
                        start=1,
                    ):
                        chart_title = chart.get("chart_title", "")
                        sql_query = chart.get("sql_query", "")
                        sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                        # Calculate token usage for the current chart and SQL query
                        new_data_tokens = calculate_token_usage(sample)

                        # Check if appending this data would exceed the token limit
                        if (
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                            <= TARGET_TOKEN_LIMIT
                        ):
                            QUERY_SAMPLES += sample

                            # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                        else:
                            # If appending would exceed, break the loop
                            break

            if (
                isinstance(chart_axis["xAxis_column"], str)
                and chart_axis["xAxis_column"] in data_summary.column_data_tribes.keys()
                and data_summary.column_data_tribes[chart_axis["xAxis_column"]]
                in ["date_related"]
                and chart_axis["xAxis_column"]
                in data_summary.column_sql_data_types.keys()
                and data_summary.column_sql_data_types[
                    chart_axis["xAxis_column"]
                ].lower()
                not in [
                    "tinyint",
                    "smallint",
                    "mediumint",
                    "int",
                    "bigint",
                    "float",
                    "double",
                    "decimal",
                    "bit",
                ]
            ):
                x_column = chart_axis["xAxis_column"]

                if time_duration == "Week":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Week"
                        and chart["chart_type"] != "table_chart"
                    ]

                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Total Revenue Generation by Product for the Past 2 Weeks
SQL Query 1: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, SUM(Revenue_Generation) AS yAxis, Product AS series FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN DATE_TRUNC('week', CURRENT_DATE - INTERVAL '2 week') AND DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '6 day' GROUP BY xAxis, series ORDER BY xAxis ASC, series;

Chart Title 2: Weekly Average EBIT Margin for Next 3 Weeks
SQL Query 2: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, AVG(EBIT_Margin) AS yAxis FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN DATE_TRUNC('week', CURRENT_DATE) AND DATE_TRUNC('week', CURRENT_DATE + INTERVAL '3 week') + INTERVAL '6 day' GROUP BY xAxis ORDER BY xAxis;

Chart Title 3: Weekly Total Cost Efficiency for Last Week
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, SUM(Cost_Efficiency) AS yAxis FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN DATE_TRUNC('week', CURRENT_DATE - INTERVAL '1 week') AND DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '6 day' GROUP BY xAxis ORDER BY xAxis;

Chart Title 4: Weekly Maximum Revenue Generation from Week 1 - Week 4 in March 2023
SQL Query 4: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-W', EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, MAX(Revenue_Generation) AS yAxis FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN DATE '2023-03-01' AND DATE '2023-03-31' AND EXTRACT(WEEK FROM TO_DATE("Date", 'DD/MM/YYYY')) BETWEEN 1 AND 4 GROUP BY xAxis ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Total Revenue Generation by Product for the Past 2 Weeks
SQL Query 1: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-W', EXTRACT(WEEK FROM "Date")) AS xAxis, SUM(Revenue_Generation) AS yAxis, Product AS series FROM `table_name` WHERE "Date" BETWEEN DATE_TRUNC('week', CURRENT_DATE - INTERVAL '2 week') AND DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '6 day' GROUP BY xAxis, series ORDER BY xAxis ASC, series;

Chart Title 2: Weekly Average EBIT Margin for Next 3 Weeks
SQL Query 2: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-W', EXTRACT(WEEK FROM "Date")) AS xAxis, AVG(EBIT_Margin) AS yAxis FROM `table_name` WHERE "Date" BETWEEN DATE_TRUNC('week', CURRENT_DATE) AND DATE_TRUNC('week', CURRENT_DATE + INTERVAL '3 week') + INTERVAL '6 day' GROUP BY xAxis ORDER BY xAxis;

Chart Title 3: Weekly Total Cost Efficiency for Last Week
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-W', EXTRACT(WEEK FROM "Date")) AS xAxis, SUM(Cost_Efficiency) AS yAxis FROM `table_name` WHERE "Date" BETWEEN DATE_TRUNC('week', CURRENT_DATE - INTERVAL '1 week') AND DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '6 day' GROUP BY xAxis ORDER BY xAxis;

Chart Title 4: Weekly Maximum Revenue Generation from Week 1 - Week 4 in March 2023
SQL Query 4: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-W', EXTRACT(WEEK FROM "Date")) AS xAxis, MAX(Revenue_Generation) AS yAxis FROM `table_name` WHERE "Date" BETWEEN DATE '2023-03-01' AND DATE '2023-03-31' AND EXTRACT(WEEK FROM "Date") BETWEEN 1 AND 4 GROUP BY xAxis ORDER BY xAxis;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif time_duration == "Month":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Month"
                        and chart["chart_type"] != "table_chart"
                    ]

                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue Generation by Product for the Past 6 Months
SQL Query 1: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-M', EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, SUM(Revenue_Generation) AS yAxis, Product AS series FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') >= CURRENT_DATE - INTERVAL '6 months' GROUP BY xAxis, series ORDER BY xAxis ASC, series;

Chart Title 2: Monthly Average EBIT Margin for Next January
SQL Query 2: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-M', EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, AVG(EBIT_Margin) AS yAxis FROM `table_name` WHERE EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) = EXTRACT(YEAR FROM CURRENT_DATE) + 1 AND EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) = 1 GROUP BY xAxis ORDER BY xAxis;

Chart Title 3: Monthly Total Cost Efficiency for March
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-M', EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, SUM(Cost_Efficiency) AS yAxis FROM `table_name` WHERE EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY')) = 3 AND EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) = EXTRACT(YEAR FROM CURRENT_DATE) GROUP BY xAxis ORDER BY xAxis;

Chart Title 4: Monthly Total Revenue Variance Actual vs Forecast from Jan 2022 - Mar 2022
SQL Query 4: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-M', EXTRACT(MONTH FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, SUM(RevenueVariance_Actual_vs_Forecast) AS yAxis FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN DATE '2022-01-01' AND DATE '2022-03-31' GROUP BY xAxis ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue Generation by Product for the Past 6 Months
SQL Query 1: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-M', EXTRACT(MONTH FROM "Date")) AS xAxis, SUM(Revenue_Generation) AS yAxis, Product AS series FROM `table_name` WHERE "Date" >= CURRENT_DATE - INTERVAL '6 months' GROUP BY xAxis, series ORDER BY xAxis ASC, series;

Chart Title 2: Monthly Average EBIT Margin for Next January
SQL Query 2: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-M', EXTRACT(MONTH FROM "Date")) AS xAxis, AVG(EBIT_Margin) AS yAxis FROM `table_name` WHERE EXTRACT(YEAR FROM "Date") = EXTRACT(YEAR FROM CURRENT_DATE) + 1 AND EXTRACT(MONTH FROM "Date") = 1 GROUP BY xAxis ORDER BY xAxis;

Chart Title 3: Monthly Total Cost Efficiency for March
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-M', EXTRACT(MONTH FROM "Date")) AS xAxis, SUM(Cost_Efficiency) AS yAxis FROM `table_name` WHERE EXTRACT(MONTH FROM "Date") = 3 AND EXTRACT(YEAR FROM "Date") = EXTRACT(YEAR FROM CURRENT_DATE) GROUP BY xAxis ORDER BY xAxis;

Chart Title 4: Monthly Total Revenue Variance Actual vs Forecast from Jan 2022 - Mar 2022
SQL Query 4: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-M', EXTRACT(MONTH FROM "Date")) AS xAxis, SUM(RevenueVariance_Actual_vs_Forecast) AS yAxis FROM `table_name` WHERE "Date" BETWEEN DATE '2022-01-01' AND DATE '2022-03-31' GROUP BY xAxis ORDER BY xAxis;
"""

                    else:
                        # Only append this line if token count allows
                        heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                        new_data_tokens = calculate_token_usage(heading)
                        if (
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                            <= TARGET_TOKEN_LIMIT
                        ):
                            QUERY_SAMPLES += heading
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                        for idx, chart in enumerate(filtered_feedback, start=1):
                            chart_title = chart.get("chart_title", "")
                            sql_query = chart.get("feedback", "")
                            sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                            # Calculate token usage for the current chart and feedback
                            new_data_tokens = calculate_token_usage(sample)

                            # Check if appending this data would exceed the token limit
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += sample

                                # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            else:
                                # If appending would exceed, break the loop
                                break

                elif time_duration == "Quarter":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Quarter"
                        and chart["chart_type"] != "table_chart"
                    ]
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Total Revenue Variance Actual vs Forecast for the Last Q3
SQL Query 1: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-Q', EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, SUM(RevenueVariance_Actual_vs_Forecast) AS yAxis FROM `table_name` WHERE EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY')) = 3 AND TO_DATE("Date", 'DD/MM/YYYY') >= CURRENT_DATE - INTERVAL '1 year' GROUP BY xAxis ORDER BY xAxis;

Chart Title 2: Quarterly Total EBIT Margin for the Next Quarter
SQL Query 2: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-Q', EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, SUM(EBIT_Margin) AS yAxis FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '3 months' GROUP BY xAxis ORDER BY xAxis;

Chart Title 3: Quarterly Average Revenue Generation for the Past H2
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-Q', EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, AVG(Revenue_Generation) AS yAxis FROM `table_name` WHERE EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY')) IN (3,
4) AND TO_DATE("Date", 'DD/MM/YYYY') >= CURRENT_DATE - INTERVAL '1 year' GROUP BY xAxis ORDER BY xAxis;

Chart Title 4: Quarterly Total Earning per Cost for Q1 2023 - Q3 2023
SQL Query 4: SELECT CONCAT(EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')), '-Q', EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY'))) AS xAxis, SUM(Earning_per_Cost) AS yAxis FROM `table_name` WHERE EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) = 2023 AND EXTRACT(QUARTER FROM TO_DATE("Date", 'DD/MM/YYYY')) BETWEEN 1 AND 3 GROUP BY xAxis ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Total Revenue Variance Actual vs Forecast for the Last Q3
SQL Query 1: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) AS xAxis, SUM(RevenueVariance_Actual_vs_Forecast) AS yAxis FROM `table_name` WHERE EXTRACT(QUARTER FROM "Date") = 3 AND "Date" >= CURRENT_DATE - INTERVAL '1 year' GROUP BY xAxis ORDER BY xAxis;

Chart Title 2: Quarterly Total EBIT Margin for the Next Quarter
SQL Query 2: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) AS xAxis, SUM(EBIT_Margin) AS yAxis FROM `table_name` WHERE "Date" BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '3 months' GROUP BY xAxis ORDER BY xAxis;

Chart Title 3: Quarterly Average Revenue Generation for the Past H2
SQL Query 3: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) AS xAxis, AVG(Revenue_Generation) AS yAxis FROM `table_name` WHERE EXTRACT(QUARTER FROM "Date") IN (3,
4) AND "Date" >= CURRENT_DATE - INTERVAL '1 year' GROUP BY xAxis ORDER BY xAxis;

Chart Title 4: Quarterly Total Earning per Cost for Q1 2023 - Q3 2023
SQL Query 4: SELECT CONCAT(EXTRACT(YEAR FROM "Date"), '-Q', EXTRACT(QUARTER FROM "Date")) AS xAxis, SUM(Earning_per_Cost) AS yAxis FROM `table_name` WHERE EXTRACT(YEAR FROM "Date") = 2023 AND EXTRACT(QUARTER FROM "Date") BETWEEN 1 AND 3 GROUP BY xAxis ORDER BY xAxis;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif time_duration == "Year":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Year"
                        and chart["chart_type"] != "table_chart"
                    ]

                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Percentage Change in Broadband Revenue for the Past 5 Years
SQL Query 1: WITH RevenueData AS (SELECT EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) AS xAxis, SUM(Revenue_Broadband) AS yAxis FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN DATE_TRUNC('year', CURRENT_DATE - INTERVAL '5 year') AND DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '1 year - 1 day' GROUP BY xAxis) SELECT xAxis, yAxis, LAG(yAxis) OVER (ORDER BY xAxis) AS prevYearRevenue, ROUND(((yAxis - LAG(yAxis) OVER (ORDER BY xAxis)) / NULLIF(LAG(yAxis) OVER (ORDER BY xAxis),
0)) * 100,
2) AS PercentageChange FROM RevenueData ORDER BY xAxis;

Chart Title 2: Yearly Average EBIT Margin for Next Year
SQL Query 2: SELECT EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) AS xAxis, AVG(EBIT_Margin) AS yAxis FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN DATE_TRUNC('year', CURRENT_DATE + INTERVAL '1 year') AND DATE_TRUNC('year', CURRENT_DATE + INTERVAL '2 year') + INTERVAL '1 year - 1 day' GROUP BY xAxis ORDER BY xAxis;

Chart Title 3: Yearly Total Revenue Generation for 2024
SQL Query 3: SELECT EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) AS xAxis, SUM(Revenue_Generation) AS yAxis FROM `table_name` WHERE EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) = 2024 GROUP BY xAxis ORDER BY xAxis;

Chart Title 4: Yearly Total Cost and Revenue for the Last 3 Years
SQL Query 4: SELECT EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) AS xAxis, SUM(Cost_Efficiency) AS yAxis, SUM(Revenue) AS yAxis2 FROM `table_name` WHERE TO_DATE("Date", 'DD/MM/YYYY') BETWEEN DATE_TRUNC('year', CURRENT_DATE - INTERVAL '3 year') AND DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '1 year - 1 day' GROUP BY xAxis ORDER BY xAxis;

Chart Title 5: Yearly Total Revenue Variance for Actual vs Forecast for 2022 - 2023
SQL Query 5: SELECT EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) AS xAxis, SUM(RevenueVariance_Actual_vs_Forecast) AS yAxis FROM `table_name` WHERE EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) BETWEEN 2022 AND 2023 GROUP BY xAxis ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Percentage Change in Broadband Revenue for the Past 5 Years
SQL Query 1: WITH RevenueData AS (SELECT EXTRACT(YEAR FROM "Date") AS xAxis, SUM(Revenue_Broadband) AS yAxis FROM `table_name` WHERE "Date" BETWEEN DATE_TRUNC('year', CURRENT_DATE - INTERVAL '5 year') AND DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '1 year - 1 day' GROUP BY xAxis) SELECT xAxis, yAxis, LAG(yAxis) OVER (ORDER BY xAxis) AS prevYearRevenue, ROUND(((yAxis - LAG(yAxis) OVER (ORDER BY xAxis)) / NULLIF(LAG(yAxis) OVER (ORDER BY xAxis),
0)) * 100,
2) AS PercentageChange FROM RevenueData ORDER BY xAxis;

Chart Title 2: Yearly Average EBIT Margin for Next Year
SQL Query 2: SELECT EXTRACT(YEAR FROM "Date") AS xAxis, AVG(EBIT_Margin) AS yAxis FROM `table_name` WHERE "Date" BETWEEN DATE_TRUNC('year', CURRENT_DATE + INTERVAL '1 year') AND DATE_TRUNC('year', CURRENT_DATE + INTERVAL '2 year') + INTERVAL '1 year - 1 day' GROUP BY xAxis ORDER BY xAxis;

Chart Title 3: Yearly Total Revenue Generation for 2024
SQL Query 3: SELECT EXTRACT(YEAR FROM "Date") AS xAxis, SUM(Revenue_Generation) AS yAxis FROM `table_name` WHERE EXTRACT(YEAR FROM "Date") = 2024 GROUP BY xAxis ORDER BY xAxis;

Chart Title 4: Yearly Total Cost and Revenue for the Last 3 Years
SQL Query 4: SELECT EXTRACT(YEAR FROM "Date") AS xAxis, SUM(Cost_Efficiency) AS yAxis, SUM(Revenue) AS yAxis2 FROM `table_name` WHERE "Date" BETWEEN DATE_TRUNC('year', CURRENT_DATE - INTERVAL '3 year') AND DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '1 year - 1 day' GROUP BY xAxis ORDER BY xAxis;

Chart Title 5: Yearly Total Revenue Variance for Actual vs Forecast for 2022 - 2023
SQL Query 5: SELECT EXTRACT(YEAR FROM "Date") AS xAxis, SUM(RevenueVariance_Actual_vs_Forecast) AS yAxis FROM `table_name` WHERE EXTRACT(YEAR FROM "Date") BETWEEN 2022 AND 2023 GROUP BY xAxis ORDER BY xAxis;
"""

                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

        if not filtered_liked_feedbacks:
            new_data_tokens = calculate_token_usage(QUERY_SAMPLES)
            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

    elif "oracle" in data_summary.sql_library.lower():
        filtered_liked_feedbacks = fetch_filtered_feedbacks(
            question, table_name, "label4"
        )

        QUERY_SAMPLES = """
Enhance your understanding of Oracle SQL query structuring, syntax, and writing, with a particular emphasis on date-related formatting, by training using the provided DDL with its respective chart titles and SQL query examples.

DDL:
""" + (
            data_summary.database_schema_sql
            if filtered_liked_feedbacks
            else (
                """
CREATE TABLE table_name (
    Date DATE,
    Product VARCHAR2(255),
    EBIT NUMBER(10, 2),
    Revenue NUMBER(10, 2),
    Cost NUMBER(10, 2),
    Revenue_Broadband NUMBER(10, 2),
    Revenue_Entertainment NUMBER(10, 2),
    Revenue_Mobile NUMBER(10, 2),
    Cost_Broadband NUMBER(10, 2),
    Cost_Entertainment NUMBER(10, 2),
    Cost_Mobile NUMBER(10, 2),
    CONSTRAINT pk_table_name PRIMARY KEY (Date, Product)
);
"""
                if any(
                    data_type.upper() in {"DATE", "DATETIME", "TIMESTAMP"}
                    for data_type in data_summary.column_sql_data_types.values()
                )
                else """
CREATE TABLE table_name (
    Date VARCHAR2(255),
    Product VARCHAR2(255),
    EBIT NUMBER(10, 2),
    Revenue NUMBER(10, 2),
    Cost NUMBER(10, 2),
    Earning_per_Cost NUMBER(10, 2),
    Cost_Efficiency NUMBER(10, 2),
    Revenue_Broadband NUMBER(10, 2),
    Revenue_Entertainment NUMBER(10, 2),
    Revenue_Mobile NUMBER(10, 2),
    Cost_Broadband NUMBER(10, 2),
    Cost_Entertainment NUMBER(10, 2),
    Cost_Mobile NUMBER(10, 2),
    Revenue_per_Day NUMBER(10, 2),
    CostVariance_Actual_vs_Budget NUMBER(10, 2)
);
"""
            )
        )

        # If Table Chart
        if chart_type in ["table_chart"]:
            x_column = chart_axis["xAxis_column"]
            if (
                isinstance(x_column, str)
                and x_column in data_summary.column_data_tribes
                and data_summary.column_data_tribes[x_column] == "date_related"
            ):
                if timeframe.lower() == "yearly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for Yearly timeframe feedbacks
                        filtered_feedbacks_by_chart_and_yearly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "yearly"
                        ]

                        if not filtered_feedbacks_by_chart_and_yearly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Total Revenue by Product Over the Last 5 Years
SQL Query 1: SELECT TO_CHAR(TO_DATE(t1."Date", 'YYYY-MM-DD'), 'YYYY') AS "Year", t1."Product" AS "Product", SUM(t1."Revenue") AS "Total Revenue" FROM "database_name"."table_name" t1 JOIN "database_name"."table_name" t2 ON TO_DATE(t1."Date", 'YYYY-MM-DD') = TO_DATE(t2."Date", 'YYYY-MM-DD') AND t1."Product" = t2."Product" WHERE TO_DATE(t1."Date", 'YYYY-MM-DD') >= ADD_MONTHS(SYSDATE, -60) GROUP BY TO_CHAR(TO_DATE(t1."Date", 'YYYY')), t1."Product" ORDER BY "Year" ASC, "Product";

Chart Title 2: Yearly Breakdown of Cost and Revenue for Each Product Over the Last 5 Years
SQL Query 2: SELECT TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY') AS "Year", "Product" AS "Product", SUM("Cost_Entertainment" + "Cost_Mobile" + "Cost_Broadband") AS "Total Cost", SUM("Revenue_Entertainment" + "Revenue_Broadband") AS "Total Revenue" FROM "database_name"."table_name" WHERE TO_DATE("Date", 'DD/MM/YYYY') >= ADD_MONTHS(SYSDATE, -60) GROUP BY TO_CHAR(TO_DATE("Date", 'YYYY')), "Product" ORDER BY "Year" ASC, "Product";

Chart Title 3: Yearly Average Revenue per Day by Product Over the Last 5 Years
SQL Query 3: SELECT TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY') AS "Year", "Product" AS "Product", AVG("Revenue_per_Day") AS "Average Revenue per Day" FROM "database_name"."table_name" WHERE EXTRACT(YEAR FROM TO_DATE("Date", 'DD/MM/YYYY')) >= EXTRACT(YEAR FROM SYSDATE) - 5 GROUP BY TO_CHAR(TO_DATE("Date", 'YYYY')), "Product" ORDER BY "Year" ASC, "Product";
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Sum of Revenue by Product for the Last 5 Years
SQL Query 1: SELECT TO_CHAR(EXTRACT(YEAR FROM t1."Date")) AS "Year", t1."Product" AS "Product", SUM(t1."Revenue") AS "Total Revenue" FROM "database_name"."table_name" t1 JOIN "database_name"."table_name" t2 ON t1."Date" = t2."Date" AND t1."Product" = t2."Product" WHERE EXTRACT(YEAR FROM t1."Date") >= EXTRACT(YEAR FROM SYSDATE) - 5 GROUP BY TO_CHAR(EXTRACT(YEAR FROM t1."Date")), t1."Product" ORDER BY "Year" ASC, "Product";

Chart Title 2: Yearly Average EBIT Across All Products Over the Last 3 Years
SQL Query 2: SELECT TO_CHAR(EXTRACT(YEAR FROM "Date")) AS "Year", AVG("EBIT") AS "Average EBIT" FROM "database_name"."table_name" WHERE EXTRACT(YEAR FROM "Date") >= EXTRACT(YEAR FROM SYSDATE) - 3 GROUP BY TO_CHAR(EXTRACT(YEAR FROM "Date")) ORDER BY "Year" ASC;

Chart Title 3: Yearly Growth in Broadband Revenue Across All Products Over the Last 6 Years
SQL Query 3: SELECT TO_CHAR(EXTRACT(YEAR FROM "Date")) AS "Year", (SUM("Revenue_Broadband") / LAG(SUM("Revenue_Broadband"), 1) OVER (ORDER BY EXTRACT(YEAR FROM "Date")) - 1) * 100 AS "Broadband Revenue Growth (%)" FROM "database_name"."table_name" WHERE EXTRACT(YEAR FROM "Date") >= EXTRACT(YEAR FROM SYSDATE) - 6 GROUP BY TO_CHAR(EXTRACT(YEAR FROM "Date")) ORDER BY "Year" ASC;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_yearly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "half-yearly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for half-yearly timeframe feedbacks
                        filtered_feedbacks_by_chart_and_half_yearly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "half-yearly"
                        ]

                        if not filtered_feedbacks_by_chart_and_half_yearly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Half-Yearly Sum of Revenue per Day and EBIT for the Last 2 Half-Years
SQL Query 1: SELECT TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY') || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'MM')) <= 6 THEN 1 ELSE 2 END AS "Half-Year", SUM("Revenue_per_Day") AS "Total Revenue per Day", SUM("EBIT") AS "Total EBIT" FROM "database_name"."table_name" WHERE TO_DATE("Date", 'DD/MM/YYYY') >= ADD_MONTHS(SYSDATE, -12) GROUP BY TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY'), CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'MM')) <= 6 THEN 1 ELSE 2 END ORDER BY "Half-Year";

Chart Title 2: Half-Yearly Average Earning per Cost by Product Over the Last Year
SQL Query 2: SELECT TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY') || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'MM')) <= 6 THEN 1 ELSE 2 END AS "Half-Year", AVG("Earning_per_Cost") AS "Average Earning per Cost", "Product" FROM "database_name"."table_name" WHERE TO_DATE("Date", 'DD/MM/YYYY') >= ADD_MONTHS(SYSDATE, -12) GROUP BY TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY'), CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'MM')) <= 6 THEN 1 ELSE 2 END, "Product" ORDER BY "Half-Year";

Chart Title 3: Half-Yearly Variance in Cost Actual vs. Budget by Product for Past 1 Year
SQL Query 3: SELECT TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY') || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'MM')) <= 6 THEN 1 ELSE 2 END AS "Half-Year", SUM("CostVariance_Actual_vs_Budget") AS "Total Cost Variance (Actual vs. Budget)", "Product" FROM "database_name"."table_name" WHERE TO_DATE("Date", 'DD/MM/YYYY') >= ADD_MONTHS(SYSDATE, -12) GROUP BY TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY'), CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'MM')) <= 6 THEN 1 ELSE 2 END, "Product" ORDER BY "Half-Year";
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Half-Yearly Average EBIT and Revenue for the Last 3 Years
SQL Query 1: SELECT TO_CHAR(Date, 'YYYY') || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(Date, 'MM')) <= 6 THEN 1 ELSE 2 END AS "Half-Year", AVG(EBIT) AS "Average EBIT", AVG(Revenue) AS "Average Revenue" FROM "database_name"."table_name" WHERE Date >= ADD_MONTHS(SYSDATE, -36) GROUP BY TO_CHAR(Date, 'YYYY'), CASE WHEN TO_NUMBER(TO_CHAR(Date, 'MM')) <= 6 THEN 1 ELSE 2 END ORDER BY "Half-Year";

Chart Title 2: Half-Yearly Growth Rate of Broadband Revenue Compared to Entertainment Revenue for the Last 4 Years
SQL Query 2: SELECT TO_CHAR(Date, 'YYYY') || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(Date, 'MM')) <= 6 THEN 1 ELSE 2 END AS "Half-Year", (SUM(Revenue_Broadband) / LAG(SUM(Revenue_Broadband)) OVER (ORDER BY TO_CHAR(Date, 'YYYY'), CASE WHEN TO_NUMBER(TO_CHAR(Date, 'MM')) <= 6 THEN 1 ELSE 2 END)) * 100 AS "Broadband Revenue Growth Rate (%)", (SUM(Revenue_Entertainment) / LAG(SUM(Revenue_Entertainment)) OVER (ORDER BY TO_CHAR(Date, 'YYYY'), CASE WHEN TO_NUMBER(TO_CHAR(Date, 'MM')) <= 6 THEN 1 ELSE 2 END)) * 100 AS "Entertainment Revenue Growth Rate (%)" FROM "database_name"."table_name" WHERE Date >= ADD_MONTHS(SYSDATE, -48) GROUP BY TO_CHAR(Date, 'YYYY'), CASE WHEN TO_NUMBER(TO_CHAR(Date, 'MM')) <= 6 THEN 1 ELSE 2 END ORDER BY "Half-Year";

Chart Title 3: Half-Yearly EBIT to Revenue Ratio and Total Cost of Broadband for the Past 2 Years
SQL Query 3: SELECT TO_CHAR(Date, 'YYYY') || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(Date, 'MM')) <= 6 THEN 1 ELSE 2 END AS "Half-Year", (SUM(EBIT) / SUM(Revenue)) * 100 AS "EBIT to Revenue Ratio (%)", SUM(Cost_Broadband) AS "Total Broadband Cost" FROM "database_name"."table_name" WHERE Date >= ADD_MONTHS(SYSDATE, -24) GROUP BY TO_CHAR(Date, 'YYYY'), CASE WHEN TO_NUMBER(TO_CHAR(Date, 'MM')) <= 6 THEN 1 ELSE 2 END ORDER BY "Half-Year";
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_half_yearly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "quarterly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for quarterly timeframe feedbacks
                        filtered_feedbacks_by_chart_and_quarterly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "quarterly"
                        ]

                        if not filtered_feedbacks_by_chart_and_quarterly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Sum of Cost Variance (Actual vs. Budget) by Product for the Past 3 Quarters
Sql Query 1: SELECT TO_CHAR(TO_DATE(t1."Date", 'YYYY-MM-DD'), 'YYYY') || '-Q' || TO_CHAR(TO_DATE(t1."Date", 'YYYY-MM-DD'), 'Q') AS "Quarter", t1."Product" AS "Product", SUM(t1."CostVariance_Actual_vs_Budget") AS "Total Cost Variance: Actual vs Budget" FROM "database_name"."table_name" t1 JOIN "database_name"."table_name" t2 ON TO_DATE(t1."Date", 'YYYY-MM-DD') = TO_DATE(t2."Date", 'YYYY-MM-DD') AND t1."Product" = t2."Product" WHERE TO_DATE(t1."Date", 'YYYY-MM-DD') >= ADD_MONTHS(TRUNC(SYSDATE, 'Q'), -9) AND TO_DATE(t1."Date", 'YYYY-MM-DD') <= LAST_DAY(SYSDATE) GROUP BY TO_CHAR(TO_DATE(t1."Date", 'YYYY-Q')), t1."Product" ORDER BY "Quarter", "Product";

Chart Title 2: Quarterly Average Cost Efficiency Across All Products for the Last 6 Quarters
SQL Query 2: SELECT TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY') || '-Q' || TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'Q') AS "Quarter", AVG("Cost_Efficiency") AS "Average Cost Efficiency" FROM "database_name"."table_name" WHERE TO_DATE("Date", 'DD/MM/YYYY') >= ADD_MONTHS(SYSDATE, -18) GROUP BY TO_CHAR(TO_DATE("Date", 'YYYY-Q')) ORDER BY "Quarter";

Chart Title 3: Quarterly Growth Rate of Broadband Revenue Compared to the Previous Quarter
SQL Query 3: SELECT TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'YYYY') || '-Q' || TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'Q') AS "Quarter", (SUM("Revenue_Broadband") / LAG(SUM("Revenue_Broadband"), 1) OVER (ORDER BY TO_CHAR(TO_DATE("Date", 'YYYY-Q'))) - 1) * 100 AS "Broadband Revenue Growth (%)" FROM "database_name"."table_name" GROUP BY TO_CHAR(TO_DATE("Date", 'YYYY-Q')) ORDER BY "Quarter";
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Sum of Entertainment Costs for 2022
Sql Query 1: SELECT TO_CHAR(EXTRACT(YEAR FROM t1."Date")) || '-Q' || TO_CHAR(t1."Date", 'Q') AS "Quarter", SUM(t1."Cost_Entertainment") AS "Total Entertainment Costs" FROM "database_name"."table_name" t1 JOIN "database_name"."table_name" t2 ON t1."Date" = t2."Date" WHERE t1."Date" BETWEEN TO_DATE('2022-01-01', 'YYYY-MM-DD') AND TO_DATE('2022-12-31', 'YYYY-MM-DD') GROUP BY TO_CHAR(EXTRACT(YEAR FROM t1."Date")) || '-Q' || TO_CHAR(t1."Date", 'Q') ORDER BY "Quarter";

Chart Title 2: Quarterly Average Revenue per Product for the Past 4 Quarters
SQL Query 2: SELECT TO_CHAR(EXTRACT(YEAR FROM "Date")) || '-Q' || TO_CHAR("Date", 'Q') AS "Quarter", "Product", AVG("Revenue") AS "Average Revenue" FROM "database_name"."table_name" WHERE "Date" >= ADD_MONTHS(SYSDATE, -12) GROUP BY TO_CHAR(EXTRACT(YEAR FROM "Date")) || '-Q' || TO_CHAR("Date", 'Q'), "Product" ORDER BY "Quarter", "Product";

Chart Title 3: Quarterly EBIT Margin (EBIT as a Percentage of Revenue) Over the Last 8 Quarters
SQL Query 3: SELECT TO_CHAR(EXTRACT(YEAR FROM "Date")) || '-Q' || TO_CHAR("Date", 'Q') AS "Quarter", (SUM("EBIT") / SUM("Revenue")) * 100 AS "EBIT Margin (%)" FROM "database_name"."table_name" WHERE "Date" >= ADD_MONTHS(SYSDATE, -24) GROUP BY TO_CHAR(EXTRACT(YEAR FROM "Date")) || '-Q' || TO_CHAR("Date", 'Q') ORDER BY "Quarter";
"""

                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_quarterly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "monthly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for monthly timeframe feedbacks
                        filtered_feedbacks_by_chart_and_monthly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "monthly"
                        ]

                        if not filtered_feedbacks_by_chart_and_monthly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Cost Variance (Actual vs. Budget) by Product (Last Year)
Sql Query 1: SELECT TO_CHAR(t1.Date, 'YYYY-MM') AS "Month", SUM(t1.CostVariance_Actual_vs_Budget) AS "Total Cost Variance (Actual vs. Budget)", t1.Product AS "Product" FROM "database_name"."table_name" t1 JOIN "database_name"."table_name" t2 ON t1.Date = t2.Date WHERE TO_CHAR(t1.Date, 'YYYY') = TO_CHAR(ADD_MONTHS(SYSDATE, -12), 'YYYY') GROUP BY TO_CHAR(t1.Date, 'YYYY-MM'), t1.Product ORDER BY "Month";

Chart Title 2: Monthly Total Cost Variance (Actual vs. Budget) by Product for the Current and Previous Year
Sql Query 2: SELECT TO_CHAR(Date, 'YYYY-MM') AS "Month", SUM(CostVariance_Actual_vs_Budget) AS "Total Cost Variance (Actual vs. Budget)", Product AS "Product" FROM "database_name"."table_name" WHERE TO_CHAR(Date, 'YYYY') >= TO_CHAR(ADD_MONTHS(SYSDATE, -12), 'YYYY') AND TO_CHAR(Date, 'YYYY') <= TO_CHAR(SYSDATE, 'YYYY') GROUP BY TO_CHAR(Date, 'YYYY-MM'), Product ORDER BY "Month";

Chart Title 3: Monthly Total Entertainment Costs and Cost Efficiency Ratio for the Last 3 Months
SQL Query 3: SELECT TO_CHAR(Date, 'YYYY-MM') AS "Month", SUM(Cost_Entertainment) AS "Total Entertainment Costs", AVG(Cost_Efficiency) AS "Average Cost Efficiency Ratio" FROM "database_name"."table_name" WHERE Date >= ADD_MONTHS(SYSDATE, -3) GROUP BY TO_CHAR(Date, 'YYYY-MM') ORDER BY "Month";
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue for Broadband and Entertainment for the Current and Previous Year
Sql Query 1: SELECT TO_CHAR(Date, 'YYYY-MM') AS "Month", SUM(Revenue_Broadband) AS "Total Revenue", 'Broadband' AS "Product" FROM "database_name"."table_name" WHERE EXTRACT(YEAR FROM Date) >= EXTRACT(YEAR FROM ADD_MONTHS(SYSDATE, -12)) AND EXTRACT(YEAR FROM Date) <= EXTRACT(YEAR FROM SYSDATE) AND Revenue_Broadband IS NOT NULL GROUP BY TO_CHAR(Date, 'YYYY-MM') UNION ALL SELECT TO_CHAR(Date, 'YYYY-MM') AS "Month", SUM(Revenue_Entertainment) AS "Total Revenue", 'Entertainment' AS "Product" FROM "database_name"."table_name" WHERE EXTRACT(YEAR FROM Date) >= EXTRACT(YEAR FROM ADD_MONTHS(SYSDATE, -12)) AND EXTRACT(YEAR FROM Date) <= EXTRACT(YEAR FROM SYSDATE) AND Revenue_Entertainment IS NOT NULL GROUP BY TO_CHAR(Date, 'YYYY-MM') ORDER BY "Month";

Chart Title 2: Monthly Sum of Mobile Costs for Next Year
Sql Query 2: SELECT TO_CHAR(Date, 'YYYY-MM') AS "Month", SUM(Cost_Mobile) AS "Total Mobile Costs" FROM "database_name"."table_name" WHERE EXTRACT(YEAR FROM Date) = EXTRACT(YEAR FROM ADD_MONTHS(SYSDATE, 12)) GROUP BY TO_CHAR(Date, 'YYYY-MM') ORDER BY "Month";

Chart Title 3: Monthly Revenue Growth Rate (Percentage Increase) for Entertainment Over the Last 12 Months
SQL Query 3: SELECT TO_CHAR(t1.Date, 'YYYY-MM') AS "Month", ((SUM(t1.Revenue_Entertainment) - COALESCE(SUM(t2.Revenue_Entertainment), 0)) / NULLIF(SUM(t2.Revenue_Entertainment), 0)) * 100 AS "Revenue Growth Rate (%)" FROM "database_name"."table_name" t1 LEFT JOIN "database_name"."table_name" t2 ON t1.Date = ADD_MONTHS(t2.Date, 1) WHERE t1.Date >= ADD_MONTHS(SYSDATE, -12) GROUP BY TO_CHAR(t1.Date, 'YYYY-MM') ORDER BY "Month";
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_monthly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "weekly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for weekly timeframe feedbacks
                        filtered_feedbacks_by_chart_and_weekly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "weekly"
                        ]

                        if not filtered_feedbacks_by_chart_and_weekly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Average Cost Efficiency by Product for the Last 12 Weeks
SQL Query 1: SELECT TO_CHAR(TO_DATE(t1."Date", 'YYYY-MM-DD'), 'IYYY') || '-W' || TO_CHAR(TO_DATE(t1."Date", 'YYYY-MM-DD'), 'IW') AS "Week", t1."Product" AS "Product", AVG(t1."Cost_Efficiency") AS "Average Cost Efficiency" FROM "database_name"."table_name" t1 JOIN "database_name"."table_name" t2 ON TO_DATE(t1."Date", 'YYYY-MM-DD') = TO_DATE(t2."Date", 'YYYY-MM-DD') AND t1."Product" = t2."Product" WHERE TO_DATE(t1."Date", 'YYYY-MM-DD') >= SYSDATE - (7 * 12) GROUP BY TO_CHAR(TO_DATE(t1."Date", 'IYYY-IW')), t1."Product" ORDER BY "Week", "Product";

Chart Title 2: Weekly Sum of Revenue and Cost Variance (Actual vs. Budget) Over the Past 8 Weeks
SQL Query 2: SELECT TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'IYYY') || '-W' || TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'IW') AS "Week", SUM("Revenue") AS "Total Revenue", SUM("CostVariance_Actual_vs_Budget") AS "Cost Variance (Actual vs. Budget)" FROM "database_name"."table_name" WHERE TO_DATE("Date", 'DD/MM/YYYY') >= SYSDATE - (7 * 8) GROUP BY TO_CHAR(TO_DATE("Date", 'IYYY-IW')) ORDER BY "Week";

Chart Title 3: Weekly EBIT Margin (EBIT as a Percentage of Revenue) Over the Last 10 Weeks
SQL Query 3: SELECT TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'IYYY') || '-W' || TO_CHAR(TO_DATE("Date", 'DD/MM/YYYY'), 'IW') AS "Week", (SUM("EBIT") / SUM("Revenue")) * 100 AS "EBIT Margin (%)" FROM "database_name"."table_name" WHERE TO_DATE("Date", 'DD/MM/YYYY') >= SYSDATE - (7 * 10) GROUP BY TO_CHAR(TO_DATE("Date", 'IYYY-IW')) ORDER BY "Week";
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Revenue for Entertainment in Quarter 4 in Year 2023
Sql Query 1: SELECT TO_CHAR(t1."Date", 'IYYY') || '-W' || TO_CHAR(t1."Date", 'IW') AS "Week", SUM(t1."Revenue_Entertainment") AS "Entertainment Revenue" FROM "database_name"."table_name" t1 JOIN "database_name"."table_name" t2 ON t1."Date" = t2."Date" WHERE EXTRACT(YEAR FROM t1."Date") = 2023 AND EXTRACT(QUARTER FROM t1."Date") = 4 GROUP BY TO_CHAR(t1."Date", 'IYYY-IW') ORDER BY "Week";

Chart Title 2: Weekly Ratio of Entertainment Costs to Total Revenue Over the Past 12 Weeks
SQL Query 2: SELECT TO_CHAR("Date", 'IYYY') || '-W' || TO_CHAR("Date", 'IW') AS "Week", (SUM("Cost_Entertainment") / SUM("Revenue")) * 100 AS "Entertainment Costs to Total Revenue Ratio (%)" FROM "database_name"."table_name" WHERE "Date" >= SYSDATE - (7 * 12) GROUP BY TO_CHAR("Date", 'IYYY-IW') ORDER BY "Week";

Chart Title 3: Weekly Variance in Mobile Costs and Broadband Costs for the Last 10 Weeks
SQL Query 3: SELECT TO_CHAR("Date", 'IYYY') || '-W' || TO_CHAR("Date", 'IW') AS "Week", VARIANCE("Cost_Mobile") AS "Variance in Mobile Costs", VARIANCE("Cost_Broadband") AS "Variance in Broadband Costs" FROM "database_name"."table_name" WHERE "Date" >= SYSDATE - (7 * 10) GROUP BY TO_CHAR("Date", 'IYYY-IW') ORDER BY "Week";
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_weekly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "daily":
                    if (
                        chart_axis["xAxis_column"]
                        in data_summary.column_sql_data_types.keys()
                    ):
                        # Check if the column is of type text or varchar
                        column_type = data_summary.column_sql_data_types.get(
                            chart_axis["xAxis_column"], ""
                        ).lower()

                        # Filter for daily timeframe feedbacks
                        filtered_feedbacks_by_chart_and_daily_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") == "table_chart"
                            and feedback.get("time_frame", "").lower() == "daily"
                        ]

                        if not filtered_feedbacks_by_chart_and_daily_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Daily Average Cost Efficiency and Earnings per Cost Over the Last 30 Days
SQL Query 1: SELECT TO_DATE(t1."Date", 'YYYY-MM-DD') AS "Date", AVG(t1."Cost_Efficiency") AS "Average Cost Efficiency", AVG(t1."Earning_per_Cost") AS "Average Earnings per Cost" FROM "database_name"."table_name" t1 JOIN "database_name"."table_name" t2 ON TO_DATE(t1."Date", 'YYYY-MM-DD') = TO_DATE(t2."Date", 'YYYY-MM-DD') WHERE TO_DATE(t1."Date", 'YYYY-MM-DD') >= SYSDATE - 30 GROUP BY TO_DATE(t1."Date", 'YYYY-MM-DD') ORDER BY "Date";

Chart Title 2: Daily Sum of Revenue and Cost for the Last 2 Weeks
SQL Query 2: SELECT TO_DATE("Date", 'DD/MM/YYYY') AS "Date", SUM("Revenue") AS "Total Revenue", SUM("Cost") AS "Total Cost" FROM "database_name"."table_name" WHERE TO_DATE("Date", 'DD/MM/YYYY') >= SYSDATE - 14 GROUP BY TO_DATE("Date", 'DD/MM/YYYY') ORDER BY "Date";

Chart Title 3: Daily Change in EBIT (Day-over-Day Difference) for the Past 10 Days
SQL Query 3: SELECT TO_DATE("Date", 'DD/MM/YYYY') AS "Date", "EBIT" - LAG("EBIT", 1) OVER (ORDER BY TO_DATE("Date", 'DD/MM/YYYY')) AS "Day-over-Day Change in EBIT" FROM "database_name"."table_name" WHERE TO_DATE("Date", 'DD/MM/YYYY') >= SYSDATE - 10 ORDER BY "Date";
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Daily Cost of Entertainment vs. Cost of Mobile for the Last 7 Days
SQL Query 1: SELECT TO_DATE(t1."Date", 'YYYY-MM-DD') AS "Date", SUM(t1."Cost_Entertainment") AS "Total Cost of Entertainment", SUM(t1."Cost_Mobile") AS "Total Cost of Mobile" FROM "database_name"."table_name" t1 JOIN "database_name"."table_name" t2 ON t1."Date" = t2."Date" WHERE TO_DATE(t1."Date", 'YYYY-MM-DD') >= SYSDATE - 7 GROUP BY TO_DATE(t1."Date", 'YYYY-MM-DD') ORDER BY "Date";

Chart Title 2: Daily EBIT to Revenue Ratio (EBIT as a Percentage of Revenue) for the Last 14 Days
SQL Query 2: SELECT TO_DATE("Date", 'YYYY-MM-DD') AS "Date", (SUM("EBIT") / NULLIF(SUM("Revenue"),
0)) * 100 AS "EBIT to Revenue Ratio (%)" FROM "database_name"."table_name" WHERE TO_DATE("Date", 'YYYY-MM-DD') >= SYSDATE - 14 GROUP BY TO_DATE("Date", 'YYYY-MM-DD') ORDER BY "Date";

Chart Title 3: Daily Total Revenue vs. Total Cost for the Last 60 Days
SQL Query 3: SELECT TO_DATE("Date", 'YYYY-MM-DD') AS "Date", SUM("Revenue") AS "Total Revenue", SUM("Cost_Broadband" + "Cost_Entertainment" + "Cost_Mobile") AS "Total Cost" FROM "database_name"."table_name" WHERE TO_DATE("Date", 'YYYY-MM-DD') >= SYSDATE - 60 GROUP BY TO_DATE("Date", 'YYYY-MM-DD') ORDER BY "Date";
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_daily_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

            else:
                filtered_feedbacks_by_chart_and_no_timeframe = [
                    feedback
                    for feedback in filtered_liked_feedbacks
                    if feedback.get("chart_type") == "table_chart"
                    and not feedback.get("time_frame", "").strip()
                ]

                if not filtered_feedbacks_by_chart_and_no_timeframe:
                    QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Top 5 Products by Percentage of Total EBIT
Sql Query 1: SELECT Product AS "Product", (SUM(EBIT) / SUM(SUM(EBIT)) OVER ()) * 100 AS "Percentage of Total EBIT" FROM "database_name"."table_name" GROUP BY Product ORDER BY "Percentage of Total EBIT" DESC FETCH FIRST 5 ROWS ONLY;

Chart Title 2: Top 3 Products that Generate the Highest Revenue
Sql Query 2: SELECT Product AS "Product", SUM(Revenue) AS "Total Revenue" FROM "database_name"."table_name" GROUP BY Product ORDER BY "Total Revenue" DESC FETCH FIRST 3 ROWS ONLY;

Chart Title 3: Total Revenue Generated by Broadband Product
Sql Query 3: SELECT 'Broadband' AS "Product", SUM(Revenue_Broadband) AS "Total Revenue" FROM "database_name"."table_name";

Chart Title 4: Total Cost Incurred by Entertainment and Broadband Respectively
Sql Query 4: SELECT 'Entertainment' AS "Product", SUM(Cost_Entertainment) AS "Total Cost" FROM "database_name"."table_name" UNION ALL SELECT 'Broadband' AS "Product", SUM(Cost_Broadband) AS "Total Cost" FROM "database_name"."table_name";

Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Top 5 Products by Percentage of Total EBIT
Sql Query 1: SELECT Product AS "Product", (SUM(EBIT) / SUM(SUM(EBIT)) OVER ()) * 100 AS "Percentage of Total EBIT" FROM "database_name"."table_name" GROUP BY Product ORDER BY "Percentage of Total EBIT" DESC FETCH FIRST 5 ROWS ONLY;

Chart Title 2: Top 3 Products that Generate the Highest Revenue
Sql Query 2: SELECT Product AS "Product", SUM(Revenue) AS "Total Revenue" FROM "database_name"."table_name" GROUP BY Product ORDER BY "Total Revenue" DESC FETCH FIRST 3 ROWS ONLY;

Chart Title 3: Total Revenue Generated by Broadband Product
Sql Query 3: SELECT 'Broadband' AS "Product", SUM(Revenue_Broadband) AS "Total Revenue" FROM "database_name"."table_name";

Chart Title 4: Total Cost Incurred by Entertainment and Broadband Respectively
Sql Query 4: SELECT 'Entertainment' AS "Product", SUM(Cost_Entertainment) AS "Total Cost" FROM "database_name"."table_name" UNION ALL SELECT 'Broadband' AS "Product", SUM(Cost_Broadband) AS "Total Cost" FROM "database_name"."table_name";
"""
                else:
                    # Only append this line if token count allows
                    heading = "\nHere are the chart titles and sql queries\n"
                    new_data_tokens = calculate_token_usage(heading)
                    if (
                        TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                        <= TARGET_TOKEN_LIMIT
                    ):
                        QUERY_SAMPLES += heading
                        TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                    for idx, chart in enumerate(
                        filtered_feedbacks_by_chart_and_no_timeframe,
                        start=1,
                    ):
                        chart_title = chart.get("chart_title", "")
                        sql_query = chart.get("sql_query", "")
                        sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                        # Calculate token usage for the current chart and SQL query
                        new_data_tokens = calculate_token_usage(sample)

                        # Check if appending this data would exceed the token limit
                        if (
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                            <= TARGET_TOKEN_LIMIT
                        ):
                            QUERY_SAMPLES += sample

                            # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                        else:
                            # If appending would exceed, break the loop
                            break

            if (
                isinstance(chart_axis["xAxis_column"], str)
                and chart_axis["xAxis_column"] in data_summary.column_data_tribes.keys()
                and data_summary.column_data_tribes[chart_axis["xAxis_column"]]
                in ["date_related"]
                and chart_axis["xAxis_column"]
                in data_summary.column_sql_data_types.keys()
                and data_summary.column_sql_data_types[
                    chart_axis["xAxis_column"]
                ].lower()
                not in [
                    "tinyint",
                    "smallint",
                    "mediumint",
                    "int",
                    "bigint",
                    "float",
                    "double",
                    "decimal",
                    "bit",
                ]
            ):
                if time_duration == "Week":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Week"
                        and chart["chart_type"] == "table_chart"
                    ]

                    if (
                        chart_axis["xAxis_column"]
                        in data_summary.column_sql_data_types.keys()
                    ):
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Total Revenue by Product for the Past 2 Weeks
SQL Query 1: SELECT TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'IW'), 'YYYY-IW') AS "Week", SUM(Revenue) AS "Total Revenue", Product AS "Product" FROM database_name.table_name WHERE TO_DATE(Date, 'DD/MM/YYYY') BETWEEN SYSDATE - INTERVAL '14' DAY AND SYSDATE GROUP BY TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'IW'), 'YYYY-IW'), Product ORDER BY "Week" ASC, Product;

Chart Title 2: Weekly Average EBIT for Next 3 Weeks
SQL Query 2: SELECT TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'IW'), 'YYYY-IW') AS "Week", AVG(EBIT) AS "Average EBIT" FROM database_name.table_name WHERE TO_DATE(Date, 'DD/MM/YYYY') BETWEEN SYSDATE AND SYSDATE + INTERVAL '21' DAY GROUP BY TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'IW'), 'YYYY-IW') ORDER BY "Week";

Chart Title 3: Weekly Total Cost of Entertainment for Last Week
SQL Query 3: SELECT TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'IW'), 'YYYY-IW') AS "Week", SUM(Cost_Entertainment) AS "Total Cost of Entertainment" FROM database_name.table_name WHERE TO_DATE(Date, 'DD/MM/YYYY') BETWEEN SYSDATE - INTERVAL '7' DAY AND SYSDATE GROUP BY TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'IW'), 'YYYY-IW') ORDER BY "Week";

Chart Title 4: Weekly Maximum Revenue from Week 1 - Week 4 in March 2023
SQL Query 4: SELECT TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'IW'), 'YYYY-IW') AS "Week", MAX(Revenue) AS "Maximum Revenue" FROM database_name.table_name WHERE TO_DATE(Date, 'DD/MM/YYYY') BETWEEN TO_DATE('2023-03-01', 'YYYY-MM-DD') AND TO_DATE('2023-03-31', 'YYYY-MM-DD') AND TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'IW'), 'WW') BETWEEN 1 AND 4 GROUP BY TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'IW'), 'YYYY-IW') ORDER BY "Week";
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Total Revenue by Product for the Past 2 Weeks
SQL Query 1: SELECT TO_CHAR(TRUNC(Date, 'IW'), 'YYYY-IW') AS "Week", SUM(Revenue) AS "Total Revenue", Product AS "Product" FROM database_name.table_name WHERE Date BETWEEN SYSDATE - INTERVAL '14' DAY AND SYSDATE GROUP BY TO_CHAR(TRUNC(Date, 'IW'), 'YYYY-IW'), Product ORDER BY "Week" ASC, Product;

Chart Title 2: Weekly Average EBIT for Next 3 Weeks
SQL Query 2: SELECT TO_CHAR(TRUNC(Date, 'IW'), 'YYYY-IW') AS "Week", AVG(EBIT) AS "Average EBIT" FROM database_name.table_name WHERE Date BETWEEN SYSDATE AND SYSDATE + INTERVAL '21' DAY GROUP BY TO_CHAR(TRUNC(Date, 'IW'), 'YYYY-IW') ORDER BY "Week";

Chart Title 3: Weekly Total Cost of Entertainment for Last Week
SQL Query 3: SELECT TO_CHAR(TRUNC(Date, 'IW'), 'YYYY-IW') AS "Week", SUM(Cost_Entertainment) AS "Total Cost of Entertainment" FROM database_name.table_name WHERE Date BETWEEN SYSDATE - INTERVAL '7' DAY AND SYSDATE GROUP BY TO_CHAR(TRUNC(Date, 'IW'), 'YYYY-IW') ORDER BY "Week";

Chart Title 4: Weekly Maximum Revenue from Week 1 - Week 4 in March 2023
SQL Query 4: SELECT TO_CHAR(TRUNC(Date, 'IW'), 'YYYY-IW') AS "Week", MAX(Revenue) AS "Maximum Revenue" FROM database_name.table_name WHERE Date BETWEEN TO_DATE('2023-03-01', 'YYYY-MM-DD') AND TO_DATE('2023-03-31', 'YYYY-MM-DD') AND TO_CHAR(TRUNC(Date, 'IW'), 'WW') BETWEEN 1 AND 4 GROUP BY TO_CHAR(TRUNC(Date, 'IW'), 'YYYY-IW') ORDER BY "Week";
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif time_duration == "Month":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Month"
                        and chart["chart_type"] == "table_chart"
                    ]

                    if (
                        chart_axis["xAxis_column"]
                        in data_summary.column_sql_data_types.keys()
                    ):
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue by Product for the Past 6 Months
SQL Query 1: SELECT TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'MM'), 'YYYY-MM') AS "Month", SUM(Revenue) AS "Total Revenue", Product AS "Product" FROM database_name.table_name WHERE TO_DATE(Date, 'DD/MM/YYYY') >= ADD_MONTHS(SYSDATE, -6) GROUP BY TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'MM'), 'YYYY-MM'), Product ORDER BY "Month" ASC, Product;

Chart Title 2: Monthly Average EBIT for Next January
SQL Query 2: SELECT TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'MM'), 'YYYY-MM') AS "Month", AVG(EBIT) AS "Average EBIT" FROM database_name.table_name WHERE EXTRACT(YEAR FROM TO_DATE(Date, 'DD/MM/YYYY')) = EXTRACT(YEAR FROM ADD_MONTHS(SYSDATE, 12)) AND EXTRACT(MONTH FROM TO_DATE(Date, 'DD/MM/YYYY')) = 1 GROUP BY TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'MM'), 'YYYY-MM') ORDER BY "Month";

Chart Title 3: Monthly Cost of Entertainment for March
SQL Query 3: SELECT TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'MM'), 'YYYY-MM') AS "Month", SUM(Cost_Entertainment) AS "Total Cost of Entertainment" FROM database_name.table_name WHERE EXTRACT(MONTH FROM TO_DATE(Date, 'DD/MM/YYYY')) = 3 AND EXTRACT(YEAR FROM TO_DATE(Date, 'DD/MM/YYYY')) = EXTRACT(YEAR FROM SYSDATE) GROUP BY TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'MM'), 'YYYY-MM') ORDER BY "Month";

Chart Title 4: Monthly Revenue from Jan 2022 - Mar 2022
SQL Query 4: SELECT TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'MM'), 'YYYY-MM') AS "Month", SUM(Revenue) AS "Total Revenue" FROM database_name.table_name WHERE TO_DATE(Date, 'DD/MM/YYYY') BETWEEN TO_DATE('2022-01-01', 'YYYY-MM-DD') AND TO_DATE('2022-03-31', 'YYYY-MM-DD') GROUP BY TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'MM'), 'YYYY-MM') ORDER BY "Month";
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue by Product for the Past 6 Months
SQL Query 1: SELECT TO_CHAR(TRUNC(Date, 'MM'), 'YYYY-MM') AS "Month", SUM(Revenue) AS "Total Revenue", Product AS "Product" FROM database_name.table_name WHERE Date >= ADD_MONTHS(SYSDATE, -6) GROUP BY TO_CHAR(TRUNC(Date, 'MM'), 'YYYY-MM'), Product ORDER BY "Month" ASC, Product;

Chart Title 2: Monthly Average EBIT for Next January
SQL Query 2: SELECT TO_CHAR(TRUNC(Date, 'MM'), 'YYYY-MM') AS "Month", AVG(EBIT) AS "Average EBIT" FROM database_name.table_name WHERE EXTRACT(YEAR FROM Date) = EXTRACT(YEAR FROM ADD_MONTHS(SYSDATE, 12)) AND EXTRACT(MONTH FROM Date) = 1 GROUP BY TO_CHAR(TRUNC(Date, 'MM'), 'YYYY-MM') ORDER BY "Month";

Chart Title 3: Monthly Cost of Entertainment for March
SQL Query 3: SELECT TO_CHAR(TRUNC(Date, 'MM'), 'YYYY-MM') AS "Month", SUM(Cost_Entertainment) AS "Total Cost of Entertainment" FROM database_name.table_name WHERE EXTRACT(MONTH FROM Date) = 3 AND EXTRACT(YEAR FROM Date) = EXTRACT(YEAR FROM SYSDATE) GROUP BY TO_CHAR(TRUNC(Date, 'MM'), 'YYYY-MM') ORDER BY "Month";

Chart Title 4: Monthly Revenue from Jan 2022 - Mar 2022
SQL Query 4: SELECT TO_CHAR(TRUNC(Date, 'MM'), 'YYYY-MM') AS "Month", SUM(Revenue) AS "Total Revenue" FROM database_name.table_name WHERE Date BETWEEN TO_DATE('2022-01-01', 'YYYY-MM-DD') AND TO_DATE('2022-03-31', 'YYYY-MM-DD') GROUP BY TO_CHAR(TRUNC(Date, 'MM'), 'YYYY-MM') ORDER BY "Month";
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif time_duration == "Quarter":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Quarter"
                        and chart["chart_type"] == "table_chart"
                    ]

                    if (
                        chart_axis["xAxis_column"]
                        in data_summary.column_sql_data_types.keys()
                    ):
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Total Revenue for the Last Q3 SQL Query 1: SELECT TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'Q'), 'YYYY-Q') AS "Quarter", SUM(Revenue) AS "Total Revenue" FROM database_name.table_name WHERE EXTRACT(QUARTER FROM TO_DATE(Date, 'DD/MM/YYYY')) = 3 AND TO_DATE(Date, 'DD/MM/YYYY') >= ADD_MONTHS(SYSDATE, -12) GROUP BY TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'Q'), 'YYYY-Q') ORDER BY "Quarter";

Chart Title 2: Quarterly EBIT for the Next Quarter
SQL Query 2: SELECT TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'Q'), 'YYYY-Q') AS "Quarter", SUM(EBIT) AS "Total EBIT" FROM database_name.table_name WHERE TO_DATE(Date, 'DD/MM/YYYY') BETWEEN SYSDATE AND ADD_MONTHS(SYSDATE, 3) GROUP BY TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'Q'), 'YYYY-Q') ORDER BY "Quarter";

Chart Title 3: Quarterly Average Revenue for the Past H2
SQL Query 3: SELECT TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'Q'), 'YYYY-Q') AS "Quarter", AVG(Revenue) AS "Average Revenue" FROM database_name.table_name WHERE EXTRACT(QUARTER FROM TO_DATE(Date, 'DD/MM/YYYY')) IN (3, 4) AND TO_DATE(Date, 'DD/MM/YYYY') >= ADD_MONTHS(SYSDATE, -12) GROUP BY TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'Q'), 'YYYY-Q') ORDER BY "Quarter";

Chart Title 4: Quarterly Total Cost for Q1 2023 - Q3 2023
SQL Query 4: SELECT TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'Q'), 'YYYY-Q') AS "Quarter", SUM(Cost_Entertainment + Cost_Broadband + Cost_Mobile) AS "Total Cost" FROM database_name.table_name WHERE EXTRACT(YEAR FROM TO_DATE(Date, 'DD/MM/YYYY')) = 2023 AND EXTRACT(QUARTER FROM TO_DATE(Date, 'DD/MM/YYYY')) BETWEEN 1 AND 3 GROUP BY TO_CHAR(TRUNC(TO_DATE(Date, 'DD/MM/YYYY'), 'Q'), 'YYYY-Q') ORDER BY "Quarter";
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Total Revenue for the Last Q3 SQL Query 1: SELECT TO_CHAR(TRUNC(Date, 'Q'), 'YYYY-Q') AS "Quarter", SUM(Revenue) AS "Total Revenue" FROM database_name.table_name WHERE EXTRACT(QUARTER FROM Date) = 3 AND Date >= ADD_MONTHS(SYSDATE, -12) GROUP BY TO_CHAR(TRUNC(Date, 'Q'), 'YYYY-Q') ORDER BY "Quarter";

Chart Title 2: Quarterly EBIT for the Next Quarter
SQL Query 2: SELECT TO_CHAR(TRUNC(Date, 'Q'), 'YYYY-Q') AS "Quarter", SUM(EBIT) AS "Total EBIT" FROM database_name.table_name WHERE Date BETWEEN SYSDATE AND ADD_MONTHS(SYSDATE, 3) GROUP BY TO_CHAR(TRUNC(Date, 'Q'), 'YYYY-Q') ORDER BY "Quarter";

Chart Title 3: Quarterly Average Revenue for the Past H2
SQL Query 3: SELECT TO_CHAR(TRUNC(Date, 'Q'), 'YYYY-Q') AS "Quarter", AVG(Revenue) AS "Average Revenue" FROM database_name.table_name WHERE EXTRACT(QUARTER FROM Date) IN (3, 4) AND Date >= ADD_MONTHS(SYSDATE, -12) GROUP BY TO_CHAR(TRUNC(Date, 'Q'), 'YYYY-Q') ORDER BY "Quarter";

Chart Title 4: Quarterly Total Cost for Q1 2023 - Q3 2023
SQL Query 4: SELECT TO_CHAR(TRUNC(Date, 'Q'), 'YYYY-Q') AS "Quarter", SUM(Cost_Entertainment + Cost_Broadband + Cost_Mobile) AS "Total Cost" FROM database_name.table_name WHERE EXTRACT(YEAR FROM Date) = 2023 AND EXTRACT(QUARTER FROM Date) BETWEEN 1 AND 3 GROUP BY TO_CHAR(TRUNC(Date, 'Q'), 'YYYY-Q') ORDER BY "Quarter";
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif time_duration == "Year":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Year"
                        and chart["chart_type"] == "table_chart"
                    ]

                    if (
                        chart_axis["xAxis_column"]
                        in data_summary.column_sql_data_types.keys()
                    ):
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Total Revenue by Product Over the Past 5 Years
SQL Query 1: SELECT TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') AS "Year", SUM(Revenue) AS "Total Revenue", Product AS "Product" FROM database_name.table_name WHERE TO_DATE(Date, 'DD/MM/YYYY') >= ADD_MONTHS(SYSDATE, -60) GROUP BY TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY'), Product ORDER BY "Year" ASC, "Product";

Chart Title 2: Yearly Average EBIT for Next Year
SQL Query 2: SELECT TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') AS "Year", AVG(EBIT) AS "Average EBIT" FROM database_name.table_name WHERE TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') = TO_CHAR(ADD_MONTHS(SYSDATE, 12), 'YYYY') GROUP BY TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') ORDER BY "Year";

Chart Title 3: Yearly Total Revenue for 2022
SQL Query 3: SELECT TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') AS "Year", SUM(Revenue) AS "Total Revenue" FROM database_name.table_name WHERE TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') = '2022' GROUP BY TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') ORDER BY "Year";

Chart Title 4: Yearly Cost and Revenue for the Last 3 Years
SQL Query 4: SELECT TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') AS "Year", SUM(Cost_Entertainment + Cost_Broadband + Cost_Mobile) AS "Total Cost", SUM(Revenue) AS "Total Revenue" FROM database_name.table_name WHERE TO_DATE(Date, 'DD/MM/YYYY') >= ADD_MONTHS(SYSDATE, -36) GROUP BY TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') ORDER BY "Year";

Chart Title 5: Yearly Total Revenue for 2022 - 2023
SQL Query 5: SELECT TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') AS "Year", SUM(Revenue) AS "Total Revenue" FROM database_name.table_name WHERE TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') BETWEEN '2022' AND '2023' GROUP BY TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') ORDER BY "Year";
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Total Revenue by Product Over the Past 5 Years
SQL Query 1: SELECT TO_CHAR(Date, 'YYYY') AS "Year", SUM(Revenue) AS "Total Revenue", Product AS "Product" FROM database_name.table_name WHERE Date >= ADD_MONTHS(SYSDATE, -60) GROUP BY TO_CHAR(Date, 'YYYY'), Product ORDER BY "Year" ASC, "Product";

Chart Title 2: Yearly Average EBIT for Next Year
SQL Query 2: SELECT TO_CHAR(Date, 'YYYY') AS "Year", AVG(EBIT) AS "Average EBIT" FROM database_name.table_name WHERE TO_CHAR(Date, 'YYYY') = TO_CHAR(ADD_MONTHS(SYSDATE, 12), 'YYYY') GROUP BY TO_CHAR(Date, 'YYYY') ORDER BY "Year";

Chart Title 3: Yearly Total Revenue for 2022
SQL Query 3: SELECT TO_CHAR(Date, 'YYYY') AS "Year", SUM(Revenue) AS "Total Revenue" FROM database_name.table_name WHERE TO_CHAR(Date, 'YYYY') = '2022' GROUP BY TO_CHAR(Date, 'YYYY') ORDER BY "Year";

Chart Title 4: Yearly Cost and Revenue for the Last 3 Years
SQL Query 4: SELECT TO_CHAR(Date, 'YYYY') AS "Year", SUM(Cost_Entertainment + Cost_Broadband + Cost_Mobile) AS "Total Cost", SUM(Revenue) AS "Total Revenue" FROM database_name.table_name WHERE Date >= ADD_MONTHS(SYSDATE, -36) GROUP BY TO_CHAR(Date, 'YYYY') ORDER BY "Year";

Chart Title 5: Yearly Total Revenue for 2022 - 2023
SQL Query 5: SELECT TO_CHAR(Date, 'YYYY') AS "Year", SUM(Revenue) AS "Total Revenue" FROM database_name.table_name WHERE TO_CHAR(Date, 'YYYY') BETWEEN '2022' AND '2023' GROUP BY TO_CHAR(Date, 'YYYY') ORDER BY "Year";
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

        # Not table chart
        else:
            x_column = chart_axis["xAxis_column"]
            if (
                isinstance(x_column, str)
                and x_column in data_summary.column_data_tribes.keys()
                and data_summary.column_data_tribes[x_column] == "date_related"
            ):
                if timeframe.lower() == "yearly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        # Handle Yearly Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_yearly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "yearly"
                        ]

                        if not filtered_feedbacks_by_chart_and_yearly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Total Revenue by Product Over the Last 5 Years
SQL Query 1: SELECT TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'YYYY') AS xAxis, SUM(t1.Revenue) AS yAxis, t1.Product AS series FROM database_name.table_name t1 JOIN database_name.table_name t2 ON TO_DATE(t1.Date, 'YYYY-MM-DD') = TO_DATE(t2.Date, 'YYYY-MM-DD') AND t1.Product = t2.Product WHERE TO_DATE(t1.Date, 'YYYY-MM-DD') >= ADD_MONTHS(SYSDATE, -60) GROUP BY TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'YYYY'), t1.Product ORDER BY xAxis ASC, series;

Chart Title 2: Yearly Breakdown of Cost and Revenue for Each Product Over the Last 5 Years
SQL Query 2: SELECT TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') AS xAxis, SUM(Cost_Entertainment + Cost_Mobile + Cost_Broadband) AS yAxis_Cost, SUM(Revenue_Entertainment + Revenue_Broadband) AS yAxis_Revenue, Product AS series FROM database_name.table_name WHERE TO_DATE(Date, 'DD/MM/YYYY') >= ADD_MONTHS(SYSDATE, -60) GROUP BY TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY'), Product ORDER BY xAxis ASC, series;

Chart Title 3: Yearly Average Revenue per Day by Product Over the Last 5 Years
SQL Query 3: SELECT TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') AS xAxis, AVG(Revenue_per_Day) AS yAxis, Product AS series FROM database_name.table_name WHERE TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') >= TO_CHAR(ADD_MONTHS(SYSDATE, -60), 'YYYY') GROUP BY TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY'), Product;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Sum of Revenue by Product for the Last 5 Years
SQL Query 1: SELECT TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'YYYY') AS xAxis, SUM(t1.Revenue) AS yAxis, t1.Product AS series FROM database_name.table_name t1 JOIN database_name.table_name t2 ON TO_DATE(t1.Date, 'YYYY-MM-DD') = TO_DATE(t2.Date, 'YYYY-MM-DD') AND t1.Product = t2.Product WHERE TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'YYYY') >= TO_CHAR(ADD_MONTHS(SYSDATE, -60), 'YYYY') GROUP BY TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'YYYY'), t1.Product ORDER BY xAxis;

Chart Title 2: Yearly Average EBIT Across All Products Over the Last 3 Years
SQL Query 2: SELECT TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') AS xAxis, AVG(EBIT) AS yAxis FROM database_name.table_name WHERE TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') >= TO_CHAR(ADD_MONTHS(SYSDATE, -36), 'YYYY') GROUP BY TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') ORDER BY xAxis;

Chart Title 3: Yearly Growth in Broadband Revenue Across All Products Over the Last 6 Years
SQL Query 3: SELECT TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') AS xAxis, (SUM(Revenue_Broadband) / LAG(SUM(Revenue_Broadband), 1) OVER (ORDER BY TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY')) - 1) * 100 AS yAxis FROM database_name.table_name WHERE TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') >= TO_CHAR(ADD_MONTHS(SYSDATE, -72), 'YYYY') GROUP BY TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') ORDER BY xAxis;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_yearly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "half-yearly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        # Handle Half-Yearly Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_half_yearly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "half-yearly"
                        ]

                        if not filtered_feedbacks_by_chart_and_half_yearly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Half-Yearly Sum of Revenue per Day and EBIT for the Last 2 Half-Years
SQL Query 1: SELECT TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'MM')) <= 6 THEN '1' ELSE '2' END AS xAxis, SUM(Revenue_per_Day) AS yAxis, SUM(EBIT) AS yAxis2 FROM database_name.table_name WHERE TO_DATE(Date, 'DD/MM/YYYY') >= ADD_MONTHS(SYSDATE, -6) GROUP BY TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'MM')) <= 6 THEN '1' ELSE '2' END ORDER BY xAxis;

Chart Title 2: Half-Yearly Average Earning per Cost by Product Over the Last Year
SQL Query 2: SELECT TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'MM')) <= 6 THEN '1' ELSE '2' END AS xAxis, AVG(Earning_per_Cost) AS yAxis, Product AS series FROM database_name.table_name WHERE TO_DATE(Date, 'DD/MM/YYYY') >= ADD_MONTHS(SYSDATE, -12) GROUP BY TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'MM')) <= 6 THEN '1' ELSE '2' END, Product ORDER BY xAxis;

Chart Title 3: Half-Yearly Variance in Cost Actual vs. Budget by Product for Past 1 Year
SQL Query 3: SELECT TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'MM')) <= 6 THEN '1' ELSE '2' END AS xAxis, SUM(CostVariance_Actual_vs_Budget) AS yAxis, Product AS series FROM database_name.table_name WHERE TO_DATE(Date, 'DD/MM/YYYY') >= ADD_MONTHS(SYSDATE, -12) GROUP BY TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'MM')) <= 6 THEN '1' ELSE '2' END, Product ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Half-Yearly Average EBIT and Revenue for the Last 3 Years
SQL Query 1: SELECT TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'MM')) <= 6 THEN '1' ELSE '2' END AS xAxis, AVG(EBIT) AS yAxis, AVG(Revenue) AS yAxis2 FROM database_name.table_name WHERE TO_DATE(Date, 'YYYY-MM-DD') >= ADD_MONTHS(SYSDATE, -36) GROUP BY TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'MM')) <= 6 THEN '1' ELSE '2' END ORDER BY xAxis;

Chart Title 2: Half-Yearly Growth Rate of Broadband Revenue Compared to Entertainment Revenue for the Last 4 Years
SQL Query 2: SELECT TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'MM')) <= 6 THEN '1' ELSE '2' END AS xAxis, (SUM(Revenue_Broadband) / LAG(SUM(Revenue_Broadband)) OVER (PARTITION BY TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'MM')) <= 6 THEN '1' ELSE '2' END ORDER BY TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'MM')) <= 6 THEN '1' ELSE '2' END)) * 100 AS yAxis, (SUM(Revenue_Entertainment) / LAG(SUM(Revenue_Entertainment)) OVER (PARTITION BY TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'MM')) <= 6 THEN '1' ELSE '2' END ORDER BY TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'MM')) <= 6 THEN '1' ELSE '2' END)) * 100 AS yAxis2 FROM database_name.table_name WHERE TO_DATE(Date, 'YYYY-MM-DD') >= ADD_MONTHS(SYSDATE, -48) GROUP BY TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'MM')) <= 6 THEN '1' ELSE '2' END ORDER BY xAxis;

Chart Title 3: Half-Yearly EBIT to Revenue Ratio and Total Cost of Broadband for the Past 2 Years
SQL Query 3: SELECT TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'MM')) <= 6 THEN '1' ELSE '2' END AS xAxis, (SUM(EBIT) / SUM(Revenue)) * 100 AS yAxis, SUM(Cost_Broadband) AS yAxis2 FROM database_name.table_name WHERE TO_DATE(Date, 'YYYY-MM-DD') >= ADD_MONTHS(SYSDATE, -24) GROUP BY TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') || '-H' || CASE WHEN TO_NUMBER(TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'MM')) <= 6 THEN '1' ELSE '2' END ORDER BY xAxis;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_half_yearly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "quarterly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            chart_axis["xAxis_column"]
                        ].lower()

                        # Handle Quarterly Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_quarterly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "quarterly"
                        ]

                        if not filtered_feedbacks_by_chart_and_quarterly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Sum of Cost Variance (Actual vs. Budget) by Product for the Past 3 Quarters
Sql Query 1: SELECT TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'YYYY') || '-Q' || TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'Q') AS xAxis, SUM(t1.CostVariance_Actual_vs_Budget) AS yAxis, t1.Product AS series FROM database_name.table_name t1 JOIN database_name.table_name t2 ON TO_DATE(t1.Date, 'YYYY-MM-DD') = TO_DATE(t2.Date, 'YYYY-MM-DD') AND t1.Product = t2.Product WHERE TO_DATE(t1.Date, 'YYYY-MM-DD') >= ADD_MONTHS(TRUNC(SYSDATE, 'Q'), -9) AND TO_DATE(t1.Date, 'YYYY-MM-DD') <= TRUNC(SYSDATE, 'MONTH') GROUP BY TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'YYYY') || '-Q' || TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'Q'), t1.Product;

Chart Title 2: Quarterly Average Cost Efficiency Across All Products for the Last 6 Quarters
SQL Query 2: SELECT TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') || '-Q' || TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'Q') AS xAxis, AVG(Cost_Efficiency) AS yAxis FROM database_name.table_name WHERE TO_DATE(Date, 'DD/MM/YYYY') >= ADD_MONTHS(TRUNC(SYSDATE, 'Q'), -18) GROUP BY TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') || '-Q' || TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'Q') ORDER BY xAxis;

Chart Title 3: Quarterly Growth Rate of Broadband Revenue Compared to the Previous Quarter
SQL Query 3: SELECT TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') || '-Q' || TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'Q') AS xAxis, (SUM(Revenue_Broadband) / LAG(SUM(Revenue_Broadband), 1) OVER (ORDER BY TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY'), TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'Q'))) - 1) * 100 AS yAxis FROM database_name.table_name GROUP BY TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') || '-Q' || TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'Q') ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Sum of Entertainment Costs for 2022
Sql Query 1: SELECT TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'YYYY') || '-Q' || TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'Q') AS xAxis, SUM(t1.Cost_Entertainment) AS yAxis FROM database_name.table_name t1 JOIN database_name.table_name t2 ON TO_DATE(t1.Date, 'YYYY-MM-DD') = TO_DATE(t2.Date, 'YYYY-MM-DD') WHERE TO_DATE(t1.Date, 'YYYY-MM-DD') BETWEEN TO_DATE('2022-01-01', 'YYYY-MM-DD') AND TO_DATE('2022-12-31', 'YYYY-MM-DD') GROUP BY TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'YYYY') || '-Q' || TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'Q') ORDER BY xAxis;

Chart Title 2: Quarterly Average Revenue per Product for the Past 4 Quarters
SQL Query 2: SELECT TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') || '-Q' || TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'Q') AS xAxis, AVG(Revenue) AS yAxis, Product AS series FROM database_name.table_name WHERE TO_DATE(Date, 'YYYY-MM-DD') >= ADD_MONTHS(TRUNC(SYSDATE, 'Q'), -12) GROUP BY TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') || '-Q' || TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'Q'), Product ORDER BY xAxis;

Chart Title 3: Quarterly EBIT Margin (EBIT as a Percentage of Revenue) Over the Last 8 Quarters
SQL Query 3: SELECT TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') || '-Q' || TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'Q') AS xAxis, (SUM(EBIT) / SUM(Revenue)) * 100 AS yAxis FROM database_name.table_name WHERE TO_DATE(Date, 'YYYY-MM-DD') >= ADD_MONTHS(TRUNC(SYSDATE, 'Q'), -24) GROUP BY TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') || '-Q' || TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'Q') ORDER BY xAxis;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_quarterly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "monthly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        # Handle Monthly Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_monthly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "monthly"
                        ]
                        if not filtered_feedbacks_by_chart_and_monthly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Cost Variance (Actual vs. Budget) by Product (Last Year)
Sql Query 1: SELECT TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'YYYY') || '-M' || TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'MM') AS xAxis, SUM(t1.CostVariance_Actual_vs_Budget) AS yAxis, t1.Product AS series FROM database_name.table_name t1 JOIN database_name.table_name t2 ON t1.Date = t2.Date WHERE TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'YYYY') = TO_CHAR(ADD_MONTHS(SYSDATE, -12), 'YYYY') GROUP BY xAxis, series;

Chart Title 2: Monthly Total Cost Variance (Actual vs. Budget) by Product for the Current and Previous Year
Sql Query 2: SELECT TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') || '-M' || TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'MM') AS xAxis, SUM(CostVariance_Actual_vs_Budget) AS yAxis, Product AS series FROM database_name.table_name WHERE EXTRACT(YEAR FROM TO_DATE(Date, 'DD/MM/YYYY')) BETWEEN EXTRACT(YEAR FROM ADD_MONTHS(SYSDATE, -12)) AND EXTRACT(YEAR FROM SYSDATE) GROUP BY xAxis, series ORDER BY xAxis;

Chart Title 3: Monthly Total Entertainment Costs and Cost Efficiency Ratio for the Last 3 Months
SQL Query 3: SELECT TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') || '-M' || TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'MM') AS xAxis, SUM(Cost_Entertainment) AS yAxis, AVG(Cost_Efficiency) AS yAxis2 FROM database_name.table_name WHERE TO_DATE(Date, 'DD/MM/YYYY') >= ADD_MONTHS(SYSDATE, -3) GROUP BY xAxis ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue for Broadband and Entertainment for the Current and Previous Year
Sql Query 1: SELECT TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') || '-M' || TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'MM') AS xAxis, SUM(Revenue_Broadband) AS yAxis, 'Broadband' AS series FROM database_name.table_name WHERE EXTRACT(YEAR FROM TO_DATE(Date, 'YYYY-MM-DD')) BETWEEN EXTRACT(YEAR FROM ADD_MONTHS(SYSDATE, -12)) AND EXTRACT(YEAR FROM SYSDATE) AND Revenue_Broadband IS NOT NULL GROUP BY xAxis, series UNION ALL SELECT TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') || '-M' || TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'MM') AS xAxis, SUM(Revenue_Entertainment) AS yAxis, 'Entertainment' AS series FROM database_name.table_name WHERE EXTRACT(YEAR FROM TO_DATE(Date, 'YYYY-MM-DD')) BETWEEN EXTRACT(YEAR FROM ADD_MONTHS(SYSDATE, -12)) AND EXTRACT(YEAR FROM SYSDATE) AND Revenue_Entertainment IS NOT NULL GROUP BY xAxis, series;

Chart Title 2: Monthly Sum of Mobile Costs for Next Year
Sql Query 2: SELECT TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') || '-M' || TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'MM') AS xAxis, SUM(Cost_Mobile) AS yAxis FROM database_name.table_name WHERE EXTRACT(YEAR FROM TO_DATE(Date, 'YYYY-MM-DD')) = EXTRACT(YEAR FROM ADD_MONTHS(SYSDATE, 12)) GROUP BY xAxis ORDER BY xAxis;

Chart Title 3: Monthly Revenue Growth Rate (Percentage Increase) for Entertainment Over the Last 12 Months
SQL Query 3: SELECT TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'YYYY') || '-M' || TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'MM') AS xAxis, ((SUM(t1.Revenue_Entertainment) - SUM(t2.Revenue_Entertainment)) / NULLIF(SUM(t2.Revenue_Entertainment), 0)) * 100 AS yAxis FROM database_name.table_name t1 LEFT JOIN database_name.table_name t2 ON t1.Date = ADD_MONTHS(t2.Date, 1) WHERE t1.Date >= ADD_MONTHS(SYSDATE, -12) GROUP BY xAxis ORDER BY xAxis;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_monthly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "weekly":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        # Handle Weekly Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_weekly_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "weekly"
                        ]

                        if not filtered_feedbacks_by_chart_and_weekly_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Average Cost Efficiency by Product for the Last 12 Weeks
SQL Query 1: SELECT TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'YYYY') || '-W' || TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'IW') AS xAxis, AVG(t1.Cost_Efficiency) AS yAxis, t1.Product AS series FROM database_name.table_name t1 JOIN database_name.table_name t2 ON TO_DATE(t1.Date, 'YYYY-MM-DD') = TO_DATE(t2.Date, 'YYYY-MM-DD') AND t1.Product = t2.Product WHERE TO_DATE(t1.Date, 'YYYY-MM-DD') >= SYSDATE - INTERVAL '84' DAY GROUP BY TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'YYYY') || '-W' || TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'IW'), t1.Product ORDER BY xAxis;

Chart Title 2: Weekly Sum of Revenue and Cost Variance (Actual vs. Budget) Over the Past 8 Weeks
SQL Query 2: SELECT TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') || '-W' || TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'IW') AS xAxis, SUM(Revenue) AS yAxis, SUM(CostVariance_Actual_vs_Budget) AS yAxis2 FROM database_name.table_name WHERE TO_DATE(Date, 'DD/MM/YYYY') >= SYSDATE - INTERVAL '56' DAY GROUP BY TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') || '-W' || TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'IW') ORDER BY xAxis;

Chart Title 3: Weekly EBIT Margin (EBIT as a Percentage of Revenue) Over the Last 10 Weeks
SQL Query 3: SELECT TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') || '-W' || TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'IW') AS xAxis, (SUM(EBIT) / SUM(Revenue)) * 100 AS yAxis FROM database_name.table_name WHERE TO_DATE(Date, 'DD/MM/YYYY') >= SYSDATE - INTERVAL '70' DAY GROUP BY TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY') || '-W' || TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'IW') ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Revenue for Entertainment in Quarter 4 in Year 2023
Sql Query 1: SELECT TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'YYYY') || '-W' || TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'IW') AS xAxis, SUM(t1.Revenue_Entertainment) AS yAxis FROM database_name.table_name t1 WHERE EXTRACT(YEAR FROM TO_DATE(t1.Date, 'YYYY-MM-DD')) = 2023 AND EXTRACT(QUARTER FROM TO_DATE(t1.Date, 'YYYY-MM-DD')) = 4 GROUP BY TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'YYYY') || '-W' || TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'IW') ORDER BY xAxis;

Chart Title 2: Weekly Ratio of Entertainment Costs to Total Revenue Over the Past 12 Weeks
SQL Query 2: SELECT TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') || '-W' || TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'IW') AS xAxis, (SUM(Cost_Entertainment) / SUM(Revenue)) * 100 AS yAxis FROM database_name.table_name WHERE TO_DATE(Date, 'YYYY-MM-DD') >= SYSDATE - INTERVAL '84' DAY GROUP BY TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') || '-W' || TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'IW') ORDER BY xAxis;

Chart Title 3: Weekly Variance in Mobile Costs and Broadband Costs for the Last 10 Weeks
SQL Query 3: SELECT TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') || '-W' || TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'IW') AS xAxis, VAR_POP(Cost_Mobile) AS yAxis, VAR_POP(Cost_Broadband) AS yAxis2 FROM database_name.table_name WHERE TO_DATE(Date, 'YYYY-MM-DD') >= SYSDATE - INTERVAL '70' DAY GROUP BY TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY') || '-W' || TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'IW') ORDER BY xAxis;
"""

                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_weekly_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif timeframe.lower() == "daily":
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        # Handle Daily Timeframe Feedbacks
                        filtered_feedbacks_by_chart_and_daily_timeframe = [
                            feedback
                            for feedback in filtered_liked_feedbacks
                            if feedback.get("chart_type") != "table_chart"
                            and feedback.get("time_frame", "").lower() == "daily"
                        ]
                        if not filtered_feedbacks_by_chart_and_daily_timeframe:
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Daily Average Cost Efficiency and Earnings per Cost Over the Last 30 Days
SQL Query 1: SELECT TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'YYYY-MM-DD') AS xAxis, AVG(t1.Cost_Efficiency) AS yAxis, AVG(t1.Earning_per_Cost) AS yAxis2 FROM database_name.table_name t1 WHERE TO_DATE(t1.Date, 'YYYY-MM-DD') >= SYSDATE - INTERVAL '30' DAY GROUP BY TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'YYYY-MM-DD') ORDER BY xAxis;

Chart Title 2: Daily Sum of Revenue and Cost for the Last 2 Weeks
SQL Query 2: SELECT TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY-MM-DD') AS xAxis, SUM(Revenue) AS yAxis, SUM(Cost) AS yAxis2 FROM database_name.table_name WHERE TO_DATE(Date, 'DD/MM/YYYY') >= SYSDATE - INTERVAL '14' DAY GROUP BY TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY-MM-DD') ORDER BY xAxis;

Chart Title 3: Daily Change in EBIT (Day-over-Day Difference) for the Past 10 Days
SQL Query 3: SELECT TO_CHAR(TO_DATE(Date, 'DD/MM/YYYY'), 'YYYY-MM-DD') AS xAxis, EBIT - LAG(EBIT, 1) OVER (ORDER BY TO_DATE(Date, 'DD/MM/YYYY')) AS yAxis FROM database_name.table_name WHERE TO_DATE(Date, 'DD/MM/YYYY') >= SYSDATE - INTERVAL '10' DAY ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Daily Cost of Entertainment vs. Cost of Mobile for the Last 7 Days
SQL Query 1: SELECT TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'YYYY-MM-DD') AS xAxis, SUM(t1.Cost_Entertainment) AS yAxis, SUM(t1.Cost_Mobile) AS yAxis2 FROM database_name.table_name t1 JOIN database_name.table_name t2 ON t1.Date = t2.Date WHERE TO_DATE(t1.Date, 'YYYY-MM-DD') >= SYSDATE - INTERVAL '7' DAY GROUP BY TO_CHAR(TO_DATE(t1.Date, 'YYYY-MM-DD'), 'YYYY-MM-DD') ORDER BY xAxis;

Chart Title 2: Daily EBIT to Revenue Ratio (EBIT as a Percentage of Revenue) for the Last 14 Days
SQL Query 2: SELECT TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY-MM-DD') AS xAxis, (SUM(EBIT) / NULLIF(SUM(Revenue), 0)) * 100 AS yAxis FROM database_name.table_name WHERE TO_DATE(Date, 'YYYY-MM-DD') >= SYSDATE - INTERVAL '14' DAY GROUP BY TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY-MM-DD') ORDER BY xAxis;

Chart Title 3: Daily Total Revenue vs. Total Cost for the Last 60 Days
SQL Query 3: SELECT TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY-MM-DD') AS xAxis, SUM(Revenue) AS yAxis, SUM(Cost_Broadband + Cost_Entertainment + Cost_Mobile) AS yAxis2 FROM database_name.table_name WHERE TO_DATE(Date, 'YYYY-MM-DD') >= SYSDATE - INTERVAL '60' DAY GROUP BY TO_CHAR(TO_DATE(Date, 'YYYY-MM-DD'), 'YYYY-MM-DD') ORDER BY xAxis;
"""

                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(
                                filtered_feedbacks_by_chart_and_daily_timeframe,
                                start=1,
                            ):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("sql_query", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and SQL query
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

            else:
                filtered_feedbacks_by_chart_and_no_timeframe = [
                    feedback
                    for feedback in filtered_liked_feedbacks
                    if feedback.get("chart_type") != "table_chart"
                    and not feedback.get("time_frame", "").strip()
                ]
                if not filtered_feedbacks_by_chart_and_no_timeframe:
                    QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Top 5 Products by Percentage of Total EBIT
Sql Query 1: SELECT Product AS xAxis, (SUM(EBIT) / SUM(SUM(EBIT)) OVER ()) * 100 AS yAxis FROM database_name.table_name GROUP BY Product ORDER BY yAxis DESC FETCH FIRST 5 ROWS ONLY;

Chart Title 2: Top 3 Products that Generate the Highest Revenue
Sql Query 2: SELECT Product AS xAxis, SUM(Revenue) AS yAxis FROM database_name.table_name GROUP BY Product ORDER BY yAxis DESC FETCH FIRST 3 ROWS ONLY;

Chart Title 3: Total Revenue Generated by Broadband Product
Sql Query 3: SELECT 'Broadband' AS xAxis, SUM(Revenue_Broadband) AS yAxis FROM database_name.table_name;

Chart Title 4: Total Cost Incurred by Entertainment and Broadband Respectively
Sql Query 4: SELECT 'Entertainment' AS xAxis, SUM(Cost_Entertainment) AS yAxis FROM database_name.table_name UNION ALL SELECT 'Broadband' AS xAxis, SUM(Cost_Broadband) AS yAxis FROM database_name.table_name;

Based on DDL 2, here are the chart titles and sql queries.

Chart Title 1: Top 5 Products by Percentage of Total EBIT
Sql Query 1: SELECT Product AS xAxis, (SUM(EBIT) / SUM(SUM(EBIT)) OVER ()) * 100 AS yAxis FROM database_name.table_name GROUP BY Product ORDER BY yAxis DESC FETCH FIRST 5 ROWS ONLY;

Chart Title 2: Top 3 Products that Generate the Highest Revenue
Sql Query 2: SELECT Product AS xAxis, SUM(Revenue) AS yAxis FROM database_name.table_name GROUP BY Product ORDER BY yAxis DESC FETCH FIRST 3 ROWS ONLY;

Chart Title 3: Total Revenue Generated by Broadband Product
Sql Query 3: SELECT 'Broadband' AS xAxis, SUM(Revenue_Broadband) AS yAxis FROM database_name.table_name;

Chart Title 4: Total Cost Incurred by Entertainment and Broadband Respectively
Sql Query 4: SELECT 'Entertainment' AS xAxis, SUM(Cost_Entertainment) AS yAxis FROM database_name.table_name UNION ALL SELECT 'Broadband' AS xAxis, SUM(Cost_Broadband) AS yAxis FROM database_name.table_name;
"""

                else:
                    # Only append this line if token count allows
                    heading = "\nHere are the chart titles and sql queries\n"
                    new_data_tokens = calculate_token_usage(heading)
                    if (
                        TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                        <= TARGET_TOKEN_LIMIT
                    ):
                        QUERY_SAMPLES += heading
                        TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                    for idx, chart in enumerate(
                        filtered_feedbacks_by_chart_and_no_timeframe,
                        start=1,
                    ):
                        chart_title = chart.get("chart_title", "")
                        sql_query = chart.get("sql_query", "")
                        sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                        # Calculate token usage for the current chart and SQL query
                        new_data_tokens = calculate_token_usage(sample)

                        # Check if appending this data would exceed the token limit
                        if (
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                            <= TARGET_TOKEN_LIMIT
                        ):
                            QUERY_SAMPLES += sample

                            # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                        else:
                            # If appending would exceed, break the loop
                            break

            if (
                isinstance(chart_axis["xAxis_column"], str)
                and chart_axis["xAxis_column"] in data_summary.column_data_tribes.keys()
                and data_summary.column_data_tribes[chart_axis["xAxis_column"]]
                in ["date_related"]
                and chart_axis["xAxis_column"]
                in data_summary.column_sql_data_types.keys()
                and data_summary.column_sql_data_types[
                    chart_axis["xAxis_column"]
                ].lower()
                not in [
                    "tinyint",
                    "smallint",
                    "mediumint",
                    "int",
                    "bigint",
                    "float",
                    "double",
                    "decimal",
                    "bit",
                ]
            ):
                x_column = chart_axis["xAxis_column"]

                if time_duration == "Week":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Week"
                        and chart["chart_type"] != "table_chart"
                    ]

                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Total Revenue by Product for the Past 2 Weeks
SQL Query 1: SELECT TO_CHAR(Date, 'YYYY-"W"W') AS xAxis, SUM(Revenue) AS yAxis, Product AS series FROM database_name.table_name WHERE Date BETWEEN SYSDATE - INTERVAL '14' DAY AND SYSDATE GROUP BY TO_CHAR(Date, 'YYYY-"W"W'), Product ORDER BY xAxis ASC, series;

Chart Title 2: Weekly Average EBIT for Next 3 Weeks
SQL Query 2: SELECT TO_CHAR(Date, 'YYYY-"W"W') AS xAxis, AVG(EBIT) AS yAxis FROM database_name.table_name WHERE Date BETWEEN SYSDATE AND SYSDATE + INTERVAL '21' DAY GROUP BY TO_CHAR(Date, 'YYYY-"W"W') ORDER BY xAxis;

Chart Title 3: Weekly Total Cost of Entertainment for Last Week
SQL Query 3: SELECT TO_CHAR(Date, 'YYYY-"W"W') AS xAxis, SUM(Cost_Entertainment) AS yAxis FROM database_name.table_name WHERE Date BETWEEN SYSDATE - INTERVAL '7' DAY AND SYSDATE GROUP BY TO_CHAR(Date, 'YYYY-"W"W') ORDER BY xAxis;

Chart Title 4: Weekly Maximum Revenue from Week 1 - Week 4 in March 2023
SQL Query 4: SELECT TO_CHAR(Date, 'YYYY-"W"W') AS xAxis, MAX(Revenue) AS yAxis FROM database_name.table_name WHERE Date BETWEEN TO_DATE('2023-03-01', 'YYYY-MM-DD') AND TO_DATE('2023-03-31', 'YYYY-MM-DD') AND EXTRACT(WEEK FROM Date) BETWEEN 1 AND 4 GROUP BY TO_CHAR(Date, 'YYYY-"W"W') ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Weekly Total Revenue by Product for the Past 2 Weeks
SQL Query 1: SELECT Date AS xAxis, SUM(Revenue) AS yAxis, Product AS series FROM database_name.table_name WHERE Date BETWEEN SYSDATE - INTERVAL '14' DAY AND SYSDATE GROUP BY Date, Product ORDER BY xAxis ASC, series;

Chart Title 2: Weekly Average EBIT for Next 3 Weeks
SQL Query 2: SELECT Date AS xAxis, AVG(EBIT) AS yAxis FROM database_name.table_name WHERE Date BETWEEN SYSDATE AND SYSDATE + INTERVAL '21' DAY GROUP BY Date ORDER BY xAxis;

Chart Title 3: Weekly Total Cost of Entertainment for Last Week
SQL Query 3: SELECT Date AS xAxis, SUM(Cost_Entertainment) AS yAxis FROM database_name.table_name WHERE Date BETWEEN SYSDATE - INTERVAL '7' DAY AND SYSDATE GROUP BY Date ORDER BY xAxis;

Chart Title 4: Weekly Maximum Revenue from Week 1 - Week 4 in March 2023
SQL Query 4: SELECT Date AS xAxis, MAX(Revenue) AS yAxis FROM database_name.table_name WHERE Date BETWEEN TO_DATE('2023-03-01', 'YYYY-MM-DD') AND TO_DATE('2023-03-31', 'YYYY-MM-DD') AND EXTRACT(WEEK FROM Date) BETWEEN 1 AND 4 GROUP BY Date ORDER BY xAxis;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif time_duration == "Month":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Month"
                        and chart["chart_type"] != "table_chart"
                    ]

                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue by Product for the Past 6 Months
SQL Query 1: SELECT TO_CHAR(Date, 'YYYY-"M"MM') AS xAxis, SUM(Revenue) AS yAxis, Product AS series FROM database_name.table_name WHERE Date >= ADD_MONTHS(SYSDATE, -6) GROUP BY TO_CHAR(Date, 'YYYY-"M"MM'), Product ORDER BY xAxis ASC, series;

Chart Title 2: Monthly Average EBIT for Next January
SQL Query 2: SELECT TO_CHAR(Date, 'YYYY-"M"MM') AS xAxis, AVG(EBIT) AS yAxis FROM database_name.table_name WHERE EXTRACT(YEAR FROM Date) = EXTRACT(YEAR FROM ADD_MONTHS(SYSDATE, 12)) AND EXTRACT(MONTH FROM Date) = 1 GROUP BY TO_CHAR(Date, 'YYYY-"M"MM') ORDER BY xAxis;

Chart Title 3: Monthly Cost of Entertainment for March
SQL Query 3: SELECT TO_CHAR(Date, 'YYYY-"M"MM') AS xAxis, SUM(Cost_Entertainment) AS yAxis FROM database_name.table_name WHERE EXTRACT(MONTH FROM Date) = 3 AND EXTRACT(YEAR FROM Date) = EXTRACT(YEAR FROM SYSDATE) GROUP BY TO_CHAR(Date, 'YYYY-"M"MM') ORDER BY xAxis;

Chart Title 4: Monthly Revenue from Jan 2022 - Mar 2022
SQL Query 4: SELECT TO_CHAR(Date, 'YYYY-"M"MM') AS xAxis, SUM(Revenue) AS yAxis FROM database_name.table_name WHERE Date BETWEEN TO_DATE('2022-01-01', 'YYYY-MM-DD') AND TO_DATE('2022-03-31', 'YYYY-MM-DD') GROUP BY TO_CHAR(Date, 'YYYY-"M"MM') ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Monthly Total Revenue by Product for the Past 6 Months
SQL Query 1: SELECT Date AS xAxis, SUM(Revenue) AS yAxis, Product AS series FROM database_name.table_name WHERE Date >= ADD_MONTHS(SYSDATE, -6) GROUP BY Date, Product ORDER BY xAxis ASC, series;

Chart Title 2: Monthly Average EBIT for Next January
SQL Query 2: SELECT Date AS xAxis, AVG(EBIT) AS yAxis FROM database_name.table_name WHERE EXTRACT(YEAR FROM Date) = EXTRACT(YEAR FROM ADD_MONTHS(SYSDATE, 12)) AND EXTRACT(MONTH FROM Date) = 1 GROUP BY Date ORDER BY xAxis;

Chart Title 3: Monthly Cost of Entertainment for March
SQL Query 3: SELECT Date AS xAxis, SUM(Cost_Entertainment) AS yAxis FROM database_name.table_name WHERE EXTRACT(MONTH FROM Date) = 3 AND EXTRACT(YEAR FROM Date) = EXTRACT(YEAR FROM SYSDATE) GROUP BY Date ORDER BY xAxis;

Chart Title 4: Monthly Revenue from Jan 2022 - Mar 2022
SQL Query 4: SELECT Date AS xAxis, SUM(Revenue) AS yAxis FROM database_name.table_name WHERE Date BETWEEN TO_DATE('2022-01-01', 'YYYY-MM-DD') AND TO_DATE('2022-03-31', 'YYYY-MM-DD') GROUP BY Date ORDER BY xAxis;
"""

                    else:
                        # Only append this line if token count allows
                        heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                        new_data_tokens = calculate_token_usage(heading)
                        if (
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                            <= TARGET_TOKEN_LIMIT
                        ):
                            QUERY_SAMPLES += heading
                            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                        for idx, chart in enumerate(filtered_feedback, start=1):
                            chart_title = chart.get("chart_title", "")
                            sql_query = chart.get("feedback", "")
                            sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                            # Calculate token usage for the current chart and feedback
                            new_data_tokens = calculate_token_usage(sample)

                            # Check if appending this data would exceed the token limit
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += sample

                                # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            else:
                                # If appending would exceed, break the loop
                                break

                elif time_duration == "Quarter":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Quarter"
                        and chart["chart_type"] != "table_chart"
                    ]
                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Total Revenue for the Last Q3
SQL Query 1: SELECT TO_CHAR(Date, 'YYYY-"Q"Q') AS xAxis, SUM(Revenue) AS yAxis FROM database_name.table_name WHERE TO_CHAR(Date, 'Q') = 3 AND Date >= ADD_MONTHS(TRUNC(SYSDATE, 'YEAR'), -12) GROUP BY TO_CHAR(Date, 'YYYY-"Q"Q') ORDER BY xAxis;

Chart Title 2: Quarterly EBIT for the Next Quarter
SQL Query 2: SELECT TO_CHAR(Date, 'YYYY-"Q"Q') AS xAxis, SUM(EBIT) AS yAxis FROM database_name.table_name WHERE Date BETWEEN TRUNC(SYSDATE, 'Q') AND ADD_MONTHS(TRUNC(SYSDATE, 'Q'), 3) GROUP BY TO_CHAR(Date, 'YYYY-"Q"Q') ORDER BY xAxis;

Chart Title 3: Quarterly Average Revenue for the Past H2
SQL Query 3: SELECT TO_CHAR(Date, 'YYYY-"Q"Q') AS xAxis, AVG(Revenue) AS yAxis FROM database_name.table_name WHERE TO_CHAR(Date, 'Q') IN (3, 4) AND Date >= ADD_MONTHS(TRUNC(SYSDATE, 'YEAR'), -12) GROUP BY TO_CHAR(Date, 'YYYY-"Q"Q') ORDER BY xAxis;

Chart Title 4: Quarterly Total Cost for Q1 2023 - Q3 2023
SQL Query 4: SELECT TO_CHAR(Date, 'YYYY-"Q"Q') AS xAxis, SUM(Cost_Entertainment + Cost_Broadband + Cost_Mobile) AS yAxis FROM database_name.table_name WHERE EXTRACT(YEAR FROM Date) = 2023 AND TO_CHAR(Date, 'Q') BETWEEN 1 AND 3 GROUP BY TO_CHAR(Date, 'YYYY-"Q"Q') ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Quarterly Total Revenue for the Last Q3
SQL Query 1: SELECT Date AS xAxis, SUM(Revenue) AS yAxis FROM database_name.table_name WHERE TO_CHAR(Date, 'Q') = 3 AND Date >= ADD_MONTHS(TRUNC(SYSDATE, 'YEAR'), -12) GROUP BY Date ORDER BY xAxis;

Chart Title 2: Quarterly EBIT for the Next Quarter
SQL Query 2: SELECT Date AS xAxis, SUM(EBIT) AS yAxis FROM database_name.table_name WHERE Date BETWEEN TRUNC(SYSDATE, 'Q') AND ADD_MONTHS(TRUNC(SYSDATE, 'Q'), 3) GROUP BY Date ORDER BY xAxis;

Chart Title 3: Quarterly Average Revenue for the Past H2
SQL Query 3: SELECT Date AS xAxis, AVG(Revenue) AS yAxis FROM database_name.table_name WHERE TO_CHAR(Date, 'Q') IN (3, 4) AND Date >= ADD_MONTHS(TRUNC(SYSDATE, 'YEAR'), -12) GROUP BY Date ORDER BY xAxis;

Chart Title 4: Quarterly Total Cost for Q1 2023 - Q3 2023
SQL Query 4: SELECT Date AS xAxis, SUM(Cost_Entertainment + Cost_Broadband + Cost_Mobile) AS yAxis FROM database_name.table_name WHERE EXTRACT(YEAR FROM Date) = 2023 AND TO_CHAR(Date, 'Q') BETWEEN 1 AND 3 GROUP BY Date ORDER BY xAxis;
"""
                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

                elif time_duration == "Year":
                    filtered_feedback = [
                        {
                            "chart_type": chart["chart_type"],
                            "chart_title": chart["chart_title"],
                            "feedback": chart["feedback"],
                        }
                        for chart in filtered_liked_feedbacks
                        if classify_time_duration(
                            chart["chart_title"], chart["question"]
                        )
                        == "Year"
                        and chart["chart_type"] != "table_chart"
                    ]

                    if x_column in data_summary.column_sql_data_types.keys():
                        column_type = data_summary.column_sql_data_types[
                            x_column
                        ].lower()

                        if not filtered_feedback:
                            # Static samples used if no feedback is available
                            if "text" == column_type or "varchar" in column_type:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Total Revenue by Product Over the Past 5 Years
SQL Query 1: SELECT TO_CHAR(Date, 'YYYY') AS xAxis, SUM(Revenue) AS yAxis, Product AS series FROM database_name.table_name WHERE Date >= ADD_MONTHS(TRUNC(SYSDATE, 'YEAR'), -60) GROUP BY TO_CHAR(Date, 'YYYY'), Product ORDER BY xAxis ASC, series;

Chart Title 2: Yearly Average EBIT for Next Year
SQL Query 2: SELECT TO_CHAR(Date, 'YYYY') AS xAxis, AVG(EBIT) AS yAxis FROM database_name.table_name WHERE EXTRACT(YEAR FROM Date) = EXTRACT(YEAR FROM SYSDATE) + 1 GROUP BY TO_CHAR(Date, 'YYYY') ORDER BY xAxis;

Chart Title 3: Yearly Total Revenue for 2022
SQL Query 3: SELECT TO_CHAR(Date, 'YYYY') AS xAxis, SUM(Revenue) AS yAxis FROM database_name.table_name WHERE EXTRACT(YEAR FROM Date) = 2022 GROUP BY TO_CHAR(Date, 'YYYY') ORDER BY xAxis;

Chart Title 4: Yearly Cost and Revenue for the Last 3 Years
SQL Query 4: SELECT TO_CHAR(Date, 'YYYY') AS xAxis, SUM(Cost_Entertainment + Cost_Broadband + Cost_Mobile) AS yAxis, SUM(Revenue) AS yAxis2 FROM database_name.table_name WHERE Date >= ADD_MONTHS(TRUNC(SYSDATE, 'YEAR'), -36) GROUP BY TO_CHAR(Date, 'YYYY') ORDER BY xAxis;

Chart Title 5: Yearly Total Revenue for 2022 - 2023
SQL Query 5: SELECT TO_CHAR(Date, 'YYYY') AS xAxis, SUM(Revenue) AS yAxis FROM database_name.table_name WHERE EXTRACT(YEAR FROM Date) BETWEEN 2022 AND 2023 GROUP BY TO_CHAR(Date, 'YYYY') ORDER BY xAxis;
"""
                            elif column_type in ["datetime", "date"]:
                                QUERY_SAMPLES += """
Based on DDL, here are the chart titles and sql queries.

Chart Title 1: Yearly Total Revenue by Product Over the Past 5 Years
SQL Query 1: SELECT Date AS xAxis, SUM(Revenue) AS yAxis, Product AS series FROM database_name.table_name WHERE Date >= ADD_MONTHS(TRUNC(SYSDATE, 'YEAR'), -60) GROUP BY Date, Product ORDER BY xAxis ASC, series;

Chart Title 2: Yearly Average EBIT for Next Year
SQL Query 2: SELECT Date AS xAxis, AVG(EBIT) AS yAxis FROM database_name.table_name WHERE EXTRACT(YEAR FROM Date) = EXTRACT(YEAR FROM SYSDATE) + 1 GROUP BY Date ORDER BY xAxis;

Chart Title 3: Yearly Total Revenue for 2022
SQL Query 3: SELECT Date AS xAxis, SUM(Revenue) AS yAxis FROM database_name.table_name WHERE EXTRACT(YEAR FROM Date) = 2022 GROUP BY Date ORDER BY xAxis;

Chart Title 4: Yearly Cost and Revenue for the Last 3 Years
SQL Query 4: SELECT Date AS xAxis, SUM(Cost_Entertainment + Cost_Broadband + Cost_Mobile) AS yAxis, SUM(Revenue) AS yAxis2 FROM database_name.table_name WHERE Date >= ADD_MONTHS(TRUNC(SYSDATE, 'YEAR'), -36) GROUP BY Date ORDER BY xAxis;

Chart Title 5: Yearly Total Revenue for 2022 - 2023
SQL Query 5: SELECT Date AS xAxis, SUM(Revenue) AS yAxis FROM database_name.table_name WHERE EXTRACT(YEAR FROM Date) BETWEEN 2022 AND 2023 GROUP BY Date ORDER BY xAxis;
"""

                        else:
                            # Only append this line if token count allows
                            heading = "\nHere are the chart titles and sql queries based on feedback:\n"
                            new_data_tokens = calculate_token_usage(heading)
                            if (
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                <= TARGET_TOKEN_LIMIT
                            ):
                                QUERY_SAMPLES += heading
                                TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

                            for idx, chart in enumerate(filtered_feedback, start=1):
                                chart_title = chart.get("chart_title", "")
                                sql_query = chart.get("feedback", "")
                                sample = f"Chart Title {idx}: {chart_title}\nSQL Query {idx}: {sql_query}\n\n"

                                # Calculate token usage for the current chart and feedback
                                new_data_tokens = calculate_token_usage(sample)

                                # Check if appending this data would exceed the token limit
                                if (
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES + new_data_tokens
                                    <= TARGET_TOKEN_LIMIT
                                ):
                                    QUERY_SAMPLES += sample

                                    # Update TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES with the new token count
                                    TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += (
                                        new_data_tokens
                                    )

                                else:
                                    # If appending would exceed, break the loop
                                    break

        if not filtered_liked_feedbacks:
            new_data_tokens = calculate_token_usage(QUERY_SAMPLES)
            TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES += new_data_tokens

    else:
        code_level_logger.error(
            f"{data_summary.sql_library} DB is not supported in generate query samples!",
        )
        raise RuntimeError(
            f"{data_summary.sql_library} DB is not supported in generate query samples!",
        )

    return QUERY_SAMPLES, TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES


def generate_median_instruction(
    data_summary: DataSummary,
    code_level_logger: logging.Logger,
) -> str:
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
        code_level_logger.error(
            f"{data_summary.sql_library} DB is not supported in SQL query generator!",
        )
        raise RuntimeError(
            f"{data_summary.sql_library} DB is not supported in SQL query generator!",
        )

    return MEDIAN_INSTRUCTION


def generate_datatype_instruction(
    data_summary: DataSummary,
) -> str:
    if "oracle" in data_summary.sql_library.lower():
        column_sql_data_type = data_summary.column_sql_data_types.copy()

        for column_sql_data_type_key in list(column_sql_data_type.keys()):
            if column_sql_data_type[column_sql_data_type_key].upper() != "CLOB":
                del column_sql_data_type[column_sql_data_type_key]

        DATATYPE_INSTRUCTION = f"""- Use the query snippet that uses 'DBMS_LOB.SUBSTR("KEY", 4000, 1)' as a reference, and replace "KEY" in the query snippet with the actual column name for {list(column_sql_data_type.keys())} columns."""
    else:
        DATATYPE_INSTRUCTION = """"""

    return DATATYPE_INSTRUCTION


def generate_syntax_instruction(
    data_summary: DataSummary,
) -> str:
    if (
        "postgresql" in data_summary.sql_library.lower()
        or "oracle" in data_summary.sql_library.lower()
    ):
        SYNTAX_INSTRUCTION = (
            """- Do not use 'CORR' function for correlation between two columns."""
        )
    else:
        SYNTAX_INSTRUCTION = """"""

    return SYNTAX_INSTRUCTION


def generate_chart_axis_instruction(
    chart_axis: dict,
    chart_type: str,
) -> Tuple[str, list]:
    chart_axis_edited, chart_axis_title_edited, AXIS_KEY_LIST = (
        generate_cleaned_chart_axis(chart_axis)
    )

    if chart_type in ["table_chart"]:
        CHART_AXIS_INSTRUCTION = """"""
    else:
        CHART_AXIS_INSTRUCTION = f"""ENSURE that all column aliases in the SQL query generated EXCLUSIVELY utilize the names from the Axis Key List below.
Axis Key List: {AXIS_KEY_LIST}
DO NOT INCLUDE ANY additional columns aliases in the SQL query generated that are NOT PART of the Axis Key List. Revalidate the column aliases to check for any invalid aliases that is not in the Axis Key List and revise the query if necessary. This is ABSOLUTELY CRITICAL for the query's correctness!

Use the provided columns as guidelines for generating the SQL query, including other necessary columns as needed:
Chart Columns Used: {chart_axis_edited}

Use these chart axis titles as additional context reference for generating SQL query:
Chart Axis Titles: {chart_axis_title_edited}"""

    return CHART_AXIS_INSTRUCTION, AXIS_KEY_LIST


def _generate_sql(
    llama70b_client: Any,
    data_summary: DataSummary,
    chart_id: int,
    chart_type: str,
    chart_axis: dict,
    filters: dict,
    aggregations: list,
    database_name: str,
    table_name: str,
    logging_url: str,
    code_level_logger: logging.Logger,
    question: Union[str, None] = None,
    chart_title: Union[str, None] = None,
    instruction: Union[str, None] = None,
):
    if question is not None and instruction is not None:
        code_level_logger.error("Question and Instruction must not be used together!")
        raise RuntimeError("Question and Instruction must not be used together!")

    normalized_chart_type = normalize_chart_type(chart_type)

    FILTER_INSTRUCTION = generate_filter_instruction(filters)

    AGGREGATION_INSTRUCTION = generate_aggregation_instruction(
        aggregations,
        chart_type,
        data_summary,
    )

    AXIS_INSTRUCTIONS = generate_axis_instruction(
        chart_type,
        chart_axis,
        code_level_logger,
    )

    TABLE_INSTRUCTION = generate_table_instruction(
        data_summary,
        database_name,
        table_name,
    )

    BACKTICK_INSTRUCTION = generate_backtick_instruction(
        data_summary,
    )

    ALIAS_INSTRUCTION = generate_alias_instruction(
        chart_type,
    )

    NATIVE_LANG = generate_sql_native_lang(
        data_summary,
        code_level_logger,
    )

    if chart_title is not None and question is not None:
        timeframe = classify_timeframe(chart_title, question)
        time_duration = classify_time_duration(chart_title, question)
    elif instruction is not None:
        timeframe = classify_instruction_timeframe(instruction)
        time_duration = classify_instruction_time_duration(instruction)

    DATE_INSTRUCTION, DATE_INSTRUCTION2, DATE_INSTRUCTION3 = generate_date_instructions(
        data_summary,
        chart_axis,
        timeframe,
        time_duration,
        code_level_logger,
    )

    MEDIAN_INSTRUCTION = generate_median_instruction(
        data_summary,
        code_level_logger,
    )

    DATATYPE_INSTRUCTION = generate_datatype_instruction(
        data_summary,
    )

    SYNTAX_INSTRUCTION = generate_syntax_instruction(
        data_summary,
    )

    CHART_AXIS_INSTRUCTION, AXIS_KEY_LIST = generate_chart_axis_instruction(
        chart_axis,
        chart_type,
    )

    system_prompt_beginning = f"""You are a skilled SQL query assistant specializing in {data_summary.sql_library} SQL queries. Your task is to generate a {data_summary.sql_library} SQL query that visually answers a given question using specified data visualizations, particularly a {normalized_chart_type}. Your query must adhere to {os.getenv("INDUSTRY_DOMAIN")} industry standards, avoid common pitfalls, and comply with the provided instructions.

Instructions:
- Your SQL query must be error-free.
- GENERATE only the SQL query and NEVER INCLUDE explanations before or after the SQL query.
- Ensure that the data retrieved from the SQL query aligns with the provided chart title.
- NEVER INCLUDE '```sql' and '```' in the generated SQL query.
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
- MUST INCLUDE all non-aggregated columns from the SELECT clause in the GROUP BY clause to comply 'only_full_group_by' mode!
- ENSURE to use aggregation on numerical columns when using GROUP BY clause.
- ENSURE the SQL query is COMPLETE and NEVER ENDS abruptly.
- ENSURE to END the generated SQL query with a semicolon.
- ENSURE all columns in Chart Column Used given are used in the generated SQL query.
- {DATE_INSTRUCTION2}
- IF a time frame exists in the question, ALWAYS REFER to the question's time frame when specifying the time frame in the SQL query.
- STRICTLY REFRAIN from generating columns for specific series only.
- USE numeric representations for dates to maintain consistency.
- STRICTLY AVOID concatenating any symbol with the numerical columns (e.g., `CONCAT(ROUND(SUM(CostVariance_Actual_vs_Budget) / SUM(SUM(CostVariance_Actual_vs_Budget)) OVER () * 100, 1), '%')`).
{ALIAS_INSTRUCTION}
- ONLY USE GROUP BY and ORDER BY clause for xAxis and series columns, and NEVER include aggregated columns.
- ENSURE to have the same data type between the column and the filter value.
- Avoid using 'LIMIT' unless the title or question pertains to 'top', 'lowest', 'highest', or similar topics.
- ENSURE y-axis related columns (e.g., 'yAxisBar', 'yAxisLine', 'yAxis', 'yAxis2', 'yAxis3', etc.) are numerical columns.
- ENSURE to follow the time duration and time frame if exist in the chart title or question.
- ENSURE to differentiate date-related column and non date-related column to avoid date filtering and date conversion error.
- ENSURE the key performance indicator or metric is calculated accurately using the correct and appropriate data column(s).
- ENSURE that aggregation logic (such as sum, average, or count) and any applied operators (like filters or sorting) are accurate.
- ENSURE that the date formats are consistently applied across all parts of the set operators (UNION, INTERSECT, MINUS, etc.) query and apply consistent date filters across both parts of the set operators (UNION, INTERSECT, MINUS, etc.) query if used.
- ENSURE that the data retrieved by the generated SQL query aligns perfectly with both the chart title and the main question.
- ENSURE that the queried data is presented in a way that is easily understandable by a human audience (e.g., convert boolean data to 'True' or 'False').
- ENSURE to apply the relevant key performance indicator (KPI) or metric formula in your generated sql query consistently when the necessary data column(s) are available and sufficient for accurate calculation.
- If the question and chart title indicates a time duration such as "past 12 months," ensure that the data range is from the current date minus 1 year. If the question and chart title specifies "past year" or "last year," use data exclusively from the previous calendar year. Similarly, if the title specifies "next year" or "upcoming year," use data exclusively for the next calendar year.
- Test your SQL query with a smaller dataset first to catch any syntax errors or logical issues before running it on the full dataset.
- {AXIS_INSTRUCTIONS}
- {TABLE_INSTRUCTION}
- {BACKTICK_INSTRUCTION}
- {MEDIAN_INSTRUCTION}
{DATATYPE_INSTRUCTION}
{SYNTAX_INSTRUCTION}"""

    system_prompt_ending = f"""
Please follow the chart axis instructions below:
{CHART_AXIS_INSTRUCTION}

For more context, you are provided a database SQL schema, database table description, and database column description to support the sql query generation. Ensure to use only the column from the column information.

Database SQL Schema:
{data_summary.database_schema_sql}

Database Table Description:
{data_summary.table_description}

{generate_column_information_prompt(data_summary.column_description_dict,data_summary.column_sample_dict,data_summary.column_display_name_dict,data_summary.column_n_unique_value_dict,data_summary.column_data_tribes)}

{FILTER_INSTRUCTION}

{AGGREGATION_INSTRUCTION}

{DATE_INSTRUCTION3}

FUNCTIONS AND OPERATOR REFERENCE
---
{NATIVE_LANG}

Your complete adherence to each instruction is non-negotiable and critical to the success of the task. No instruction can be missed, and every aspect of the SQL query must align precisely with all the instructions provided. Please review each instruction carefully and ensure full compliance before finalizing your SQL query. NEVER INCLUDE explanations or notes. PLEASE DO NOT HALLUCINATE!!

"""

    if question is not None and chart_title is not None:
        user_prompt = f"""Please think step-by-step. Generate the {data_summary.sql_library} sql query based on the question and chart title below.

Question: {question}

Chart Title: {chart_title}"""

    elif instruction is not None:
        user_prompt = f"""Please think step-by-step. Generate the {data_summary.sql_library} sql query based on the instruction below.

Instruction: {instruction}"""

    start_narrative = perf_counter()

    messages = []

    # Start with the system prompt (without samples instruction for now)
    system_prompt = system_prompt_beginning + "\n\n" + system_prompt_ending

    total_num_tokens = calculate_token_usage(user_prompt, system_prompt)

    if question is not None and chart_title is not None:
        QUERY_SAMPLES, TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES = generate_query_samples(
            data_summary,
            chart_type,
            chart_axis,
            chart_title,
            question,
            timeframe,
            time_duration,
            table_name,
            total_num_tokens,
            code_level_logger,
        )
    else:
        QUERY_SAMPLES = ""
        TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES = 0

    total_num_tokens = TOTAL_NUM_TOKENS_WITH_GOOD_SAMPLES

    if total_num_tokens <= TARGET_TOKEN_LIMIT:
        system_prompt = (
            system_prompt_beginning
            + "\n\n"
            + QUERY_SAMPLES
            + "\n\n"
            + system_prompt_ending
        )

    if question is not None and chart_title is not None:
        BAD_QUERY_SAMPLES, TOTAL_NUM_TOKENS_WITH_BAD_SAMPLES = generate_bad_samples(
            data_summary,
            chart_type,
            chart_axis,
            chart_title,
            question,
            timeframe,
            time_duration,
            table_name,
            total_num_tokens,
            logger,
        )
    else:
        BAD_QUERY_SAMPLES = ""
        TOTAL_NUM_TOKENS_WITH_BAD_SAMPLES = 0

    total_num_tokens = TOTAL_NUM_TOKENS_WITH_BAD_SAMPLES

    if total_num_tokens <= TARGET_TOKEN_LIMIT:
        system_prompt = (
            system_prompt_beginning
            + "\n\n"
            + QUERY_SAMPLES
            + "\n\n"
            + BAD_QUERY_SAMPLES
            + "\n\n"
            + system_prompt_ending
        )

    messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

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

    MODULEID_GENERATE_SQL = os.getenv("MODULEID_GENERATE_SQL", "")

    if MODULEID_GENERATE_SQL == "":
        code_level_logger.error("MODULEID_GENERATE_SQL is invalid!")
        raise ValueError("MODULEID_GENERATE_SQL is invalid!")

    log_chart_data = {
        "chart_id": chart_id,
        "sql_query": response,
    }

    logging_url_chart = logging_url + "chart"
    log_response = requests.post(
        logging_url_chart, json=log_chart_data, verify=False
    ).json()

    if log_response.get("chart_id", None) is not None:
        chart_id = log_response["chart_id"]

    formatted_data = {
        "chart_id": chart_id,
        "module_id": int(MODULEID_GENERATE_SQL),
        "messages": messages,
        "output": response,
        "inference_time": chart_sql_inference_time,
        "llm_model": os.getenv("LLAMA70B_MODEL"),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }

    logging_url_llm_calls = logging_url + "chart-llm-calls"
    requests.put(logging_url_llm_calls, json=formatted_data, verify=False)

    if chart_type in ["histogram_chart"]:
        validate_numerical_columns_for_histogram(
            response,
            data_summary,
            code_level_logger,
        )

    sql_string, sql_string_raw = postprocess_sql(
        response,
        database_name,
        table_name,
        data_summary,
        AXIS_KEY_LIST,
        code_level_logger,
    )

    verify_sql_statement(
        data_summary,
        sql_string,
        code_level_logger,
    )

    return sql_string, sql_string_raw


def generate_sql_query(
    llama70b_client: Any,
    data_summary: DataSummary,
    chart_type_data: dict,
    filters: dict,
    aggregations: list,
    database_name: str,
    table_name: str,
    logging_url: str,
    session_id: str,
    code_level_logger: logging.Logger,
):
    with PerformanceLogger(session_id):
        if "main_question" in chart_type_data and "main_title" in chart_type_data:
            main_chart_question = chart_type_data["main_question"]
            main_chart_title = chart_type_data["main_title"]
            instruction = None
        elif "main_instruction" in chart_type_data:
            instruction = chart_type_data["main_instruction"]
            main_chart_question = None
            main_chart_title = None
        else:
            code_level_logger.error("Question and Instruction is empty!")
            raise RuntimeError("Question and Instruction is empty!")

        main_chart_type = chart_type_data["main_chart_type"]
        main_chart_axis = chart_type_data["main_chart_axis"]
        main_chart_id = chart_type_data["chart_id"]
        sub_chart_data_list = chart_type_data["sub_questions"]
        main_chart_id = chart_type_data["chart_id"]

        main_chart_sql: str = ""
        main_chart_sql_raw: str = ""

        if main_chart_axis != {}:
            for trial in range(1):
                try:
                    main_chart_sql, main_chart_sql_raw = _generate_sql(
                        llama70b_client,
                        data_summary,
                        main_chart_id,
                        main_chart_type,
                        main_chart_axis,
                        filters,
                        aggregations,
                        database_name,
                        table_name,
                        logging_url,
                        code_level_logger,
                        main_chart_question,
                        main_chart_title,
                        instruction,
                    )
                    break
                except Exception:
                    print(traceback.format_exc())

        chart_type_data["main_chart_sql"] = main_chart_sql
        chart_type_data["main_chart_sql_raw"] = main_chart_sql_raw

        for sub_chart_idx, sub_chart_data in enumerate(sub_chart_data_list):
            if "question" in sub_chart_data and "chart_title" in sub_chart_data:
                sub_chart_question = sub_chart_data["question"]
                sub_chart_title = sub_chart_data["chart_title"]
                instruction = None
            elif "main_instruction" in sub_chart_data:
                instruction = sub_chart_data["main_instruction"]
                sub_chart_question = None
                sub_chart_title = None
            else:
                code_level_logger.error("Question and Instruction is empty!")
                raise RuntimeError("Question and Instruction is empty!")

            sub_chart_type = sub_chart_data["chart_type"]
            sub_chart_axis = sub_chart_data["chart_axis"]
            sub_chart_id = sub_chart_data["chart_id"]

            sub_chart_sql = ""

            if sub_chart_axis != {}:
                for trial in range(1):
                    try:
                        sub_chart_sql, sub_chart_sql_raw = _generate_sql(
                            llama70b_client,
                            data_summary,
                            sub_chart_id,
                            sub_chart_type,
                            sub_chart_axis,
                            filters,
                            aggregations,
                            database_name,
                            table_name,
                            logging_url,
                            code_level_logger,
                            sub_chart_question,
                            sub_chart_title,
                            instruction,
                        )
                        break
                    except Exception:
                        print(traceback.format_exc())
                        # logger.error(traceback.format_exc())
            sub_chart_data_list[sub_chart_idx]["chart_sql"] = sub_chart_sql
            sub_chart_data_list[sub_chart_idx]["chart_sql_raw"] = sub_chart_sql_raw

        main_chart_sql = chart_type_data.get("main_chart_sql", {})

        return chart_type_data


def generate_beautiful_table_sql_query(
    database_name: str,
    table_name: str,
    sql_library: str,
    data_summary: DataSummary,
):
    if "postgresql" in sql_library.lower():
        table_sql_query = f"""SELECT * FROM {table_name} LIMIT 100;"""
    elif "oracle" in sql_library.lower():
        table_sql_query = (
            f"""SELECT * FROM \"{table_name}\" FETCH FIRST 100 ROWS ONLY"""
        )
    else:
        table_sql_query = (
            f"""SELECT * FROM `{database_name}`.`{table_name}` LIMIT 100;"""
        )

    if data_summary.table_join_sql_query != "":
        table_join_sql_query = data_summary.table_join_sql_query.strip().rstrip(";")
        table_sql_query = table_sql_query.replace(
            f"`{database_name}`.`{table_name}`",
            f"({table_join_sql_query}) AS joined_table",
        )
        table_sql_query = table_sql_query.replace(
            f"'{database_name}'.'{table_name}'",
            f"({table_join_sql_query}) AS joined_table",
        )
        table_sql_query = table_sql_query.replace(
            f'"{database_name}"."{table_name}"',
            f"({table_join_sql_query}) AS joined_table",
        )
        table_sql_query = table_sql_query.replace(
            f"{database_name}.{table_name}",
            f"({table_join_sql_query}) AS joined_table",
        )
        table_sql_query = table_sql_query.replace(
            f"`{table_name}`",
            f"({table_join_sql_query}) AS joined_table",
        )
        table_sql_query = table_sql_query.replace(
            f"'{table_name}'",
            f"({table_join_sql_query}) AS joined_table",
        )
        table_sql_query = table_sql_query.replace(
            f'"{table_name}"',
            f"({table_join_sql_query}) AS joined_table",
        )
        table_sql_query = table_sql_query.replace(
            f"{table_name}",
            f"({table_join_sql_query}) AS joined_table",
        )

    return table_sql_query
