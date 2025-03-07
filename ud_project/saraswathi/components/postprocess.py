import logging
import re
import traceback
import numpy as np
import pandas as pd

from datetime import datetime
from logging_library.performancelogger.performance_logger import PerformanceLogger

logger = logging.getLogger(__name__)


def find_highest_phrases(text):
    pattern = r"(top|highest|largest|biggest|maximum|max)\s+(\d+)"
    matches = re.findall(pattern, text.lower())
    return [(match[0], int(match[1])) for match in matches]


def find_lowest_phrases(text):
    pattern = r"(bottom|lowest|smallest|minimum|min)\s+(\d+)"
    matches = re.findall(pattern, text.lower())
    return [(match[0], int(match[1])) for match in matches]


def find_latest_phrases(text):
    pattern = r"(latest|last|past|recent|newest|previous|prior|earlier)"
    matches = re.findall(pattern, text.lower())
    return matches


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%a")
    except ValueError:
        pass

    try:
        return datetime.strptime(date_str, "%A")
    except ValueError:
        pass

    try:
        return datetime.strptime(date_str, "%Y-%B")
    except ValueError:
        pass

    try:
        return datetime.strptime(date_str, "%Y-%b")
    except ValueError:
        pass

    raise RuntimeError(f"{date_str} is not parsable by date parser!")


def postprocess_df_categorical(
    chart_title: str,
    chart_axis: dict,
    df: pd.DataFrame,
    max_number_of_categories: int = 10000,
):
    df_columns = list(df.columns)

    if "xAxis" in df_columns:
        xAxis_column_name = "xAxis"
    elif "xAxis_column" in chart_axis and chart_axis["xAxis_column"] in df_columns:
        xAxis_column_name = chart_axis["xAxis_column"]
    else:
        return df

    if "yAxis" in df_columns:
        yAxis_column_name = "yAxis"
    elif "yAxis_column" in chart_axis and chart_axis["yAxis_column"] in df_columns:
        yAxis_column_name = chart_axis["yAxis_column"]
    else:
        return df

    groupby_columns = df_columns.copy()
    groupby_columns.remove(yAxis_column_name)

    try:
        if "total" in chart_title.lower() or "sum" in chart_title.lower():
            aggregated_df = df.groupby(by=groupby_columns).sum()
        elif "average" in chart_title.lower() or "mean" in chart_title.lower():
            aggregated_df = df.groupby(by=groupby_columns).mean()
        else:
            aggregated_df = df.groupby(by=groupby_columns).sum()
    except Exception:
        print(f"Error Aggregating Column by {groupby_columns}")
        print(df)
        return df

    postprocessed_data = {}
    if len(groupby_columns) == 1:
        postprocessed_data[xAxis_column_name] = list(aggregated_df.index)
    elif len(groupby_columns) > 1:
        postprocessed_data[xAxis_column_name] = list(
            aggregated_df.index.get_level_values(0),
        )
    else:
        return df

    for column in aggregated_df.columns:
        postprocessed_data[column] = list(aggregated_df[column])

    postprocessed_df = pd.DataFrame(postprocessed_data)
    postprocessed_df = postprocessed_df.fillna(
        {
            col: 0 if postprocessed_df[col].dtype in [np.float64, np.int64] else "null"
            for col in postprocessed_df.columns
        },
    )

    if len(postprocessed_df) > max_number_of_categories:
        highest_phrases_found = find_highest_phrases(chart_title)
        order_by = "highest"

        if len(highest_phrases_found) > 0:
            max_highest_phrase_number = 0
            for highest_phrase, highest_phrase_number in highest_phrases_found:
                max_highest_phrase_number = max(
                    max_highest_phrase_number,
                    highest_phrase_number,
                )

            max_number_of_categories = min(
                max_highest_phrase_number,
                max_number_of_categories,
            )
            order_by = "highest"
        else:
            lowest_phrases_found = find_lowest_phrases(chart_title)
            if len(lowest_phrases_found) > 0:
                max_lowest_phrase_number = 0
                for lowest_phrase, lowest_phrase_number in lowest_phrases_found:
                    max_lowest_phrase_number = max(
                        max_lowest_phrase_number,
                        lowest_phrase_number,
                    )

                max_number_of_categories = min(
                    max_lowest_phrase_number,
                    max_number_of_categories,
                )
                order_by = "lowest"

        if order_by == "lowest":
            postprocessed_df = postprocessed_df.sort_values(
                by=yAxis_column_name,
                ascending=True,
            )
        elif order_by == "highest":
            postprocessed_df = postprocessed_df.sort_values(
                by=yAxis_column_name,
                ascending=False,
            )

        postprocessed_df = postprocessed_df.head(max_number_of_categories)

    if "parsed_dates" in postprocessed_df.columns:
        postprocessed_df["parsed_dates"] = postprocessed_df[xAxis_column_name].apply(
            parse_date,
        )
        postprocessed_df = postprocessed_df.sort_values(
            by="parsed_dates",
            ascending=True,
        )
        postprocessed_df = postprocessed_df.drop(columns=["parsed_dates"])
    else:
        numeric_regex = re.compile(r"^\d+$")
        numeric_elements = df.copy()[
            df.copy()[xAxis_column_name]
            .astype(str)
            .apply(lambda x: bool(numeric_regex.match(x)))
        ]
        non_numeric_elements = df.copy()[
            ~df.copy()[xAxis_column_name]
            .astype(str)
            .apply(lambda x: bool(numeric_regex.match(x)))
        ]

        if len(non_numeric_elements) > 0:
            postprocessed_df = postprocessed_df.sort_values(
                by=xAxis_column_name,
                ascending=True,
            )
        else:
            numeric_elements[xAxis_column_name] = numeric_elements[
                xAxis_column_name
            ].astype(int)
            numeric_elements = numeric_elements.sort_values(by=xAxis_column_name)
            numeric_elements[xAxis_column_name] = numeric_elements[
                xAxis_column_name
            ].astype(str)
            df[xAxis_column_name] = numeric_elements[xAxis_column_name]

    return postprocessed_df


def postprocess_df_categorical_with_series(
    chart_title: str,
    chart_axis: dict,
    df: pd.DataFrame,
    max_number_of_categories: int = 10000,
):
    df_columns = list(df.columns)

    if "xAxis" in df_columns:
        xAxis_column_name = "xAxis"
    elif "xAxis_column" in chart_axis and chart_axis["xAxis_column"] in df_columns:
        xAxis_column_name = chart_axis["xAxis_column"]
    else:
        return df

    yAxis_column_names = []

    for idx in range(1, len(df_columns)):
        if idx == 1:
            if "yAxis" in df_columns:
                yAxis_column_names.append("yAxis")
            elif (
                "yAxis_column" in chart_axis
                and chart_axis["yAxis_column"] in df_columns
            ):
                yAxis_column_names.append(chart_axis["yAxis_column"])
            else:
                return df
        elif f"yAxis{idx}" in df_columns:
            yAxis_column_names.append(f"yAxis{idx}")
        elif (
            f"yAxis{idx}_column" in chart_axis
            and chart_axis[f"yAxis{idx}_column"] in df_columns
        ):
            yAxis_column_names.append(chart_axis[f"yAxis{idx}_column"])

    if "series" in df_columns:
        series_column_name = "series"
    elif "series_column" in chart_axis and chart_axis["series_column"] in df_columns:
        series_column_name = chart_axis["series_column"]
    else:
        series_column_name = ""

    groupby_columns = df_columns.copy()
    for yAxis_column_name in yAxis_column_names:
        groupby_columns.remove(yAxis_column_name)

    # Make Sure xAxis is the first
    groupby_columns.remove(xAxis_column_name)
    groupby_columns.insert(0, xAxis_column_name)

    if len(groupby_columns) > 1:
        if series_column_name != "":
            groupby_columns.remove(series_column_name)
            groupby_columns.insert(1, series_column_name)
        else:
            series_column_name = groupby_columns[1]

    try:
        if "total" in chart_title.lower() or "sum" in chart_title.lower():
            aggregated_df = df.groupby(by=groupby_columns).sum()
        elif "average" in chart_title.lower() or "mean" in chart_title.lower():
            aggregated_df = df.groupby(by=groupby_columns).mean()
        else:
            aggregated_df = df.groupby(by=groupby_columns).sum()
    except Exception:
        print(f"Error Aggregating Column by {groupby_columns}")
        print(df)
        return df

    postprocessed_data = {}

    if series_column_name == "":
        postprocessed_data[xAxis_column_name] = list(aggregated_df.index)
    else:
        postprocessed_data[xAxis_column_name] = list(
            aggregated_df.index.get_level_values(0),
        )
        postprocessed_data[series_column_name] = list(
            aggregated_df.index.get_level_values(1),
        )

    for column in aggregated_df.columns:
        postprocessed_data[column] = list(aggregated_df[column])

    postprocessed_df = pd.DataFrame(postprocessed_data)
    postprocessed_df = postprocessed_df.fillna(
        {
            col: 0 if postprocessed_df[col].dtype in [np.float64, np.int64] else "null"
            for col in postprocessed_df.columns
        },
    )

    if len(postprocessed_df) > max_number_of_categories:
        highest_phrases_found = find_highest_phrases(chart_title)
        order_by = "highest"

        if len(highest_phrases_found) > 0:
            max_highest_phrase_number = 0
            for highest_phrase, highest_phrase_number in highest_phrases_found:
                max_highest_phrase_number = max(
                    max_highest_phrase_number,
                    highest_phrase_number,
                )

            max_number_of_categories = min(
                max_highest_phrase_number,
                max_number_of_categories,
            )
            order_by = "highest"
        else:
            lowest_phrases_found = find_lowest_phrases(chart_title)
            if len(lowest_phrases_found) > 0:
                max_lowest_phrase_number = 0
                for lowest_phrase, lowest_phrase_number in lowest_phrases_found:
                    max_lowest_phrase_number = max(
                        max_lowest_phrase_number,
                        lowest_phrase_number,
                    )

                max_number_of_categories = min(
                    max_lowest_phrase_number,
                    max_number_of_categories,
                )
                order_by = "lowest"

        if order_by == "lowest":
            postprocessed_df = postprocessed_df.sort_values(
                by=yAxis_column_name,
                ascending=True,
            )
        elif order_by == "highest":
            postprocessed_df = postprocessed_df.sort_values(
                by=yAxis_column_name,
                ascending=False,
            )

        postprocessed_df = postprocessed_df.head(max_number_of_categories)

    if "parsed_dates" in postprocessed_df.columns:
        postprocessed_df["parsed_dates"] = postprocessed_df[xAxis_column_name].apply(
            parse_date,
        )
        postprocessed_df = postprocessed_df.sort_values(
            by="parsed_dates",
            ascending=True,
        )
        postprocessed_df = postprocessed_df.drop(columns=["parsed_dates"])
    else:
        numeric_regex = re.compile(r"^\d+$")
        numeric_elements = df.copy()[
            df.copy()[xAxis_column_name]
            .astype(str)
            .apply(lambda x: bool(numeric_regex.match(x)))
        ]
        non_numeric_elements = df.copy()[
            ~df.copy()[xAxis_column_name]
            .astype(str)
            .apply(lambda x: bool(numeric_regex.match(x)))
        ]

        if len(non_numeric_elements) > 0:
            postprocessed_df = postprocessed_df.sort_values(
                by=xAxis_column_name,
                ascending=True,
            )
        else:
            numeric_elements[xAxis_column_name] = numeric_elements[
                xAxis_column_name
            ].astype(int)
            numeric_elements = numeric_elements.sort_values(by=xAxis_column_name)
            numeric_elements[xAxis_column_name] = numeric_elements[
                xAxis_column_name
            ].astype(str)
            df[xAxis_column_name] = numeric_elements[xAxis_column_name]

    return postprocessed_df


def postprocess_df_card(
    chart_axis: dict,
    df: pd.DataFrame,
) -> pd.DataFrame:
    df_columns = list(df.columns)

    if "xAxis" in df_columns:
        xAxis_column_name = "xAxis"
    elif "xAxis_column" in chart_axis and chart_axis["xAxis_column"] in df_columns:
        xAxis_column_name = chart_axis["xAxis_column"]
    else:
        return df

    if "yAxis" in df_columns:
        yAxis_column_name = "yAxis"
    elif "yAxis_column" in chart_axis and chart_axis["yAxis_column"] in df_columns:
        yAxis_column_name = chart_axis["yAxis_column"]
    else:
        return df

    if "series" in df_columns:
        series_column_name = "series"
    elif "series_column" in chart_axis and chart_axis["series_column"] in df_columns:
        series_column_name = chart_axis["series_column"]
    else:
        series_column_name = ""

    # Drop rows with null value
    df_cleaned = df.dropna(subset=[xAxis_column_name])
    df_cleaned = df_cleaned.dropna(subset=[yAxis_column_name])
    if series_column_name != "":
        df_cleaned = df_cleaned.dropna(subset=[series_column_name])

    return df_cleaned


def postprocess_df_scatter(
    chart_axis: dict,
    df: pd.DataFrame,
) -> pd.DataFrame:
    df_columns = list(df.columns)

    if "xAxis" in df_columns:
        xAxis_column_name = "xAxis"
    elif "xAxis_column" in chart_axis and chart_axis["xAxis_column"] in df_columns:
        xAxis_column_name = chart_axis["xAxis_column"]
    else:
        return df

    if "yAxis" in df_columns:
        yAxis_column_name = "yAxis"
    elif "yAxis_column" in chart_axis and chart_axis["yAxis_column"] in df_columns:
        yAxis_column_name = chart_axis["yAxis_column"]
    else:
        return df

    if "series" in df_columns:
        series_column_name = "series"
    elif "series_column" in chart_axis and chart_axis["series_column"] in df_columns:
        series_column_name = chart_axis["series_column"]
    else:
        series_column_name = ""

    # Drop rows with null value
    df_cleaned = df.dropna(subset=[xAxis_column_name])
    df_cleaned = df_cleaned.dropna(subset=[yAxis_column_name])
    if series_column_name != "":
        df_cleaned = df_cleaned.dropna(subset=[series_column_name])

    return df_cleaned


def postprocess_df_bubble(
    chart_axis: dict,
    df: pd.DataFrame,
) -> pd.DataFrame:
    df_columns = list(df.columns)

    if "xAxis" in df_columns:
        xAxis_column_name = "xAxis"
    elif "xAxis_column" in chart_axis and chart_axis["xAxis_column"] in df_columns:
        xAxis_column_name = chart_axis["xAxis_column"]
    else:
        return df

    if "yAxis" in df_columns:
        yAxis_column_name = "yAxis"
    elif "yAxis_column" in chart_axis and chart_axis["yAxis_column"] in df_columns:
        yAxis_column_name = chart_axis["yAxis_column"]
    else:
        return df

    if "zAxis" in df_columns:
        zAxis_column_name = "zAxis"
    elif "zAxis_column" in chart_axis and chart_axis["zAxis_column"] in df_columns:
        zAxis_column_name = chart_axis["zAxis_column"]
    else:
        return df

    if "series" in df_columns:
        series_column_name = "series"
    elif "series_column" in chart_axis and chart_axis["series_column"] in df_columns:
        series_column_name = chart_axis["series_column"]
    else:
        series_column_name = ""

    # Drop rows with null value
    df_cleaned = df.dropna(subset=[xAxis_column_name])
    df_cleaned = df_cleaned.dropna(subset=[yAxis_column_name])
    df_cleaned = df_cleaned.dropna(subset=[zAxis_column_name])
    if series_column_name != "":
        df_cleaned = df_cleaned.dropna(subset=[series_column_name])

    return df_cleaned


def postprocess_df_treemap(
    chart_title: str,
    chart_axis: dict,
    df: pd.DataFrame,
    max_number_of_categories: int = 10000,
):
    df_columns = list(df.columns)

    if "xAxis" in df_columns:
        xAxis_column_name = "xAxis"
    elif "xAxis_column" in chart_axis and chart_axis["xAxis_column"] in df_columns:
        xAxis_column_name = chart_axis["xAxis_column"]
    else:
        return df

    yAxis_column_names = []

    for idx in range(1, len(df_columns)):
        if idx == 1:
            if "yAxis" in df_columns:
                yAxis_column_names.append("yAxis")
            elif (
                "yAxis_column" in chart_axis
                and chart_axis["yAxis_column"] in df_columns
            ):
                yAxis_column_names.append(chart_axis["yAxis_column"])
            else:
                return df
        elif f"yAxis{idx}" in df_columns:
            yAxis_column_names.append(f"yAxis{idx}")
        elif (
            f"yAxis{idx}_column" in chart_axis
            and chart_axis[f"yAxis{idx}_column"] in df_columns
        ):
            yAxis_column_names.append(chart_axis[f"yAxis{idx}_column"])

    if "series" in df_columns:
        series_column_name = "series"
    elif "series_column" in chart_axis and chart_axis["series_column"] in df_columns:
        series_column_name = chart_axis["series_column"]
    else:
        series_column_name = ""

    groupby_columns = df_columns.copy()
    for yAxis_column_name in yAxis_column_names:
        groupby_columns.remove(yAxis_column_name)

    # Make Sure xAxis is the first
    groupby_columns.remove(xAxis_column_name)
    groupby_columns.insert(0, xAxis_column_name)

    if len(groupby_columns) > 1:
        if series_column_name != "":
            groupby_columns.remove(series_column_name)
            groupby_columns.insert(1, series_column_name)
        else:
            series_column_name = groupby_columns[1]

    try:
        if "total" in chart_title.lower() or "sum" in chart_title.lower():
            aggregated_df = df.groupby(by=groupby_columns).sum()
        elif "average" in chart_title.lower() or "mean" in chart_title.lower():
            aggregated_df = df.groupby(by=groupby_columns).mean()
        else:
            aggregated_df = df.groupby(by=groupby_columns).sum()
    except Exception:
        print(f"Error Aggregating Column by {groupby_columns}")
        print(df)
        return df

    postprocessed_data = {}

    if series_column_name == "":
        postprocessed_data[xAxis_column_name] = list(aggregated_df.index)
    else:
        postprocessed_data[xAxis_column_name] = list(
            aggregated_df.index.get_level_values(0),
        )
        postprocessed_data[series_column_name] = list(
            aggregated_df.index.get_level_values(1),
        )

    for column in aggregated_df.columns:
        postprocessed_data[column] = list(aggregated_df[column])

    postprocessed_df = pd.DataFrame(postprocessed_data)
    postprocessed_df = postprocessed_df.fillna(
        {
            col: 0 if postprocessed_df[col].dtype in [np.float64, np.int64] else "null"
            for col in postprocessed_df.columns
        },
    )

    if len(postprocessed_df) > max_number_of_categories:
        highest_phrases_found = find_highest_phrases(chart_title)
        order_by = "highest"

        if len(highest_phrases_found) > 0:
            max_highest_phrase_number = 0
            for highest_phrase, highest_phrase_number in highest_phrases_found:
                max_highest_phrase_number = max(
                    max_highest_phrase_number,
                    highest_phrase_number,
                )

            max_number_of_categories = min(
                max_highest_phrase_number,
                max_number_of_categories,
            )
            order_by = "highest"
        else:
            lowest_phrases_found = find_lowest_phrases(chart_title)
            if len(lowest_phrases_found) > 0:
                max_lowest_phrase_number = 0
                for lowest_phrase, lowest_phrase_number in lowest_phrases_found:
                    max_lowest_phrase_number = max(
                        max_lowest_phrase_number,
                        lowest_phrase_number,
                    )

                max_number_of_categories = min(
                    max_lowest_phrase_number,
                    max_number_of_categories,
                )
                order_by = "lowest"

        if order_by == "lowest":
            postprocessed_df = postprocessed_df.sort_values(
                by=yAxis_column_names,
                ascending=True,
            )
        elif order_by == "highest":
            postprocessed_df = postprocessed_df.sort_values(
                by=yAxis_column_names,
                ascending=False,
            )

        postprocessed_df = postprocessed_df.head(max_number_of_categories)

    postprocessed_df = postprocessed_df.sort_values(
        by=yAxis_column_names,
        ascending=False,
    )

    return postprocessed_df


def postprocess_df_barline_categorical_order(
    chart_title: str,
    chart_axis: dict,
    df: pd.DataFrame,
    max_number_of_categories: int = 10000,
):
    df_columns = list(df.columns)

    if "xAxis" in df_columns:
        xAxis_column_name = "xAxis"
    elif "xAxis_column" in chart_axis and chart_axis["xAxis_column"] in df_columns:
        xAxis_column_name = chart_axis["xAxis_column"]
    else:
        return df

    yAxis_column_names = []

    if "yAxisBar" in df_columns:
        yAxis_column_names.append("yAxisBar")
    elif (
        "yAxisBar_column" in chart_axis and chart_axis["yAxisBar_column"] in df_columns
    ):
        yAxis_column_names.append(chart_axis["yAxisBar_column"])
    else:
        return df

    if "yAxisLine" in df_columns:
        yAxis_column_names.append("yAxisLine")
    elif (
        "yAxisLine_column" in chart_axis
        and chart_axis["yAxisLine_column"] in df_columns
    ):
        yAxis_column_names.append(chart_axis["yAxisLine_column"])
    else:
        return df

    if "series" in df_columns:
        series_column_name = "series"
    elif "series_column" in chart_axis and chart_axis["series_column"] in df_columns:
        series_column_name = chart_axis["series_column"]
    else:
        series_column_name = ""

    groupby_columns = df_columns.copy()
    for yAxis_column_name in yAxis_column_names:
        groupby_columns.remove(yAxis_column_name)

    # Make Sure xAxis is the first
    groupby_columns.remove(xAxis_column_name)
    groupby_columns.insert(0, xAxis_column_name)

    if len(groupby_columns) > 1:
        if series_column_name != "":
            groupby_columns.remove(series_column_name)
            groupby_columns.insert(1, series_column_name)
        else:
            series_column_name = groupby_columns[1]

    try:
        if "total" in chart_title.lower() or "sum" in chart_title.lower():
            aggregated_df = df.groupby(by=groupby_columns).sum()
        elif "average" in chart_title.lower() or "mean" in chart_title.lower():
            aggregated_df = df.groupby(by=groupby_columns).mean()
        else:
            aggregated_df = df.groupby(by=groupby_columns).sum()
    except Exception:
        print(f"Error Aggregating Column by {groupby_columns}")
        print(df)
        return df

    postprocessed_data = {}

    if series_column_name == "":
        postprocessed_data[xAxis_column_name] = list(aggregated_df.index)
    else:
        postprocessed_data[xAxis_column_name] = list(
            aggregated_df.index.get_level_values(0),
        )
        postprocessed_data[series_column_name] = list(
            aggregated_df.index.get_level_values(1),
        )

    for column in aggregated_df.columns:
        postprocessed_data[column] = list(aggregated_df[column])

    postprocessed_df = pd.DataFrame(postprocessed_data)
    postprocessed_df = postprocessed_df.fillna(
        {
            col: 0 if postprocessed_df[col].dtype in [np.float64, np.int64] else "null"
            for col in postprocessed_df.columns
        },
    )

    if "parsed_dates" in postprocessed_df.columns:
        postprocessed_df["parsed_dates"] = postprocessed_df[xAxis_column_name].apply(
            parse_date,
        )
        postprocessed_df = postprocessed_df.sort_values(
            by="parsed_dates",
            ascending=True,
        )
        postprocessed_df = postprocessed_df.drop(columns=["parsed_dates"])
    else:
        numeric_regex = re.compile(r"^\d+$")
        numeric_elements = df.copy()[
            df.copy()[xAxis_column_name]
            .astype(str)
            .apply(lambda x: bool(numeric_regex.match(x)))
        ]
        non_numeric_elements = df.copy()[
            ~df.copy()[xAxis_column_name]
            .astype(str)
            .apply(lambda x: bool(numeric_regex.match(x)))
        ]

        if len(non_numeric_elements) > 0:
            postprocessed_df = postprocessed_df.sort_values(
                by=xAxis_column_name,
                ascending=True,
            )
        else:
            numeric_elements[xAxis_column_name] = numeric_elements[
                xAxis_column_name
            ].astype(int)
            numeric_elements = numeric_elements.sort_values(by=xAxis_column_name)
            numeric_elements[xAxis_column_name] = numeric_elements[
                xAxis_column_name
            ].astype(str)
            df[xAxis_column_name] = numeric_elements[xAxis_column_name]

    if len(postprocessed_df) > max_number_of_categories:
        latest_phrases_found = find_latest_phrases(chart_title)

        if len(latest_phrases_found) > 0:
            postprocessed_df = postprocessed_df.tail(max_number_of_categories)
        else:
            postprocessed_df = postprocessed_df.head(max_number_of_categories)

    return postprocessed_df


def postprocess_df_grouped_categorical(
    chart_title: str,
    chart_axis: dict,
    df: pd.DataFrame,
    max_number_of_categories: int = 10000,
):
    df_columns = list(df.columns)

    if "xAxis" in df_columns:
        xAxis_column_name = "xAxis"
    elif "xAxis_column" in chart_axis and chart_axis["xAxis_column"] in df_columns:
        xAxis_column_name = chart_axis["xAxis_column"]
    else:
        return df

    yAxis_column_names = []

    for idx in range(1, len(df_columns)):
        if idx == 1:
            if "yAxis" in df_columns:
                yAxis_column_names.append("yAxis")
            elif (
                "yAxis_column" in chart_axis
                and chart_axis["yAxis_column"] in df_columns
            ):
                yAxis_column_names.append(chart_axis["yAxis_column"])
            else:
                return df
        elif f"yAxis{idx}" in df_columns:
            yAxis_column_names.append(f"yAxis{idx}")
        elif (
            f"yAxis{idx}_column" in chart_axis
            and chart_axis[f"yAxis{idx}_column"] in df_columns
        ):
            yAxis_column_names.append(chart_axis[f"yAxis{idx}_column"])

    if "series" in df_columns:
        series_column_name = "series"
    elif "series_column" in chart_axis and chart_axis["series_column"] in df_columns:
        series_column_name = chart_axis["series_column"]
    else:
        series_column_name = ""

    groupby_columns = df_columns.copy()
    for yAxis_column_name in yAxis_column_names:
        groupby_columns.remove(yAxis_column_name)

    # Make Sure xAxis is the first
    groupby_columns.remove(xAxis_column_name)
    groupby_columns.insert(0, xAxis_column_name)

    if len(groupby_columns) > 1:
        if series_column_name != "":
            groupby_columns.remove(series_column_name)
            groupby_columns.insert(1, series_column_name)
        else:
            series_column_name = groupby_columns[1]

    try:
        if "total" in chart_title.lower() or "sum" in chart_title.lower():
            aggregated_df = df.groupby(by=groupby_columns).sum()
        elif "average" in chart_title.lower() or "mean" in chart_title.lower():
            aggregated_df = df.groupby(by=groupby_columns).mean()
        else:
            aggregated_df = df.groupby(by=groupby_columns).sum()
    except Exception:
        print(f"Error Aggregating Column by {groupby_columns}")
        print(df)
        return df

    postprocessed_data = {}

    if series_column_name == "":
        postprocessed_data[xAxis_column_name] = list(aggregated_df.index)
    else:
        postprocessed_data[xAxis_column_name] = list(
            aggregated_df.index.get_level_values(0),
        )
        postprocessed_data[series_column_name] = list(
            aggregated_df.index.get_level_values(1),
        )

    for column in aggregated_df.columns:
        postprocessed_data[column] = list(aggregated_df[column])

    postprocessed_df = pd.DataFrame(postprocessed_data)
    postprocessed_df = postprocessed_df.fillna(
        {
            col: 0 if postprocessed_df[col].dtype in [np.float64, np.int64] else "null"
            for col in postprocessed_df.columns
        },
    )

    if len(postprocessed_df) > max_number_of_categories:
        highest_phrases_found = find_highest_phrases(chart_title)
        order_by = "highest"

        if len(highest_phrases_found) > 0:
            max_highest_phrase_number = 0
            for highest_phrase, highest_phrase_number in highest_phrases_found:
                max_highest_phrase_number = max(
                    max_highest_phrase_number,
                    highest_phrase_number,
                )

            max_number_of_categories = min(
                max_highest_phrase_number,
                max_number_of_categories,
            )
            order_by = "highest"
        else:
            lowest_phrases_found = find_lowest_phrases(chart_title)
            if len(lowest_phrases_found) > 0:
                max_lowest_phrase_number = 0
                for lowest_phrase, lowest_phrase_number in lowest_phrases_found:
                    max_lowest_phrase_number = max(
                        max_lowest_phrase_number,
                        lowest_phrase_number,
                    )

                max_number_of_categories = min(
                    max_lowest_phrase_number,
                    max_number_of_categories,
                )
                order_by = "lowest"

        if order_by == "lowest":
            postprocessed_df = postprocessed_df.sort_values(
                by=yAxis_column_names,
                ascending=True,
            )
        elif order_by == "highest":
            postprocessed_df = postprocessed_df.sort_values(
                by=yAxis_column_names,
                ascending=False,
            )

        postprocessed_df = postprocessed_df.head(max_number_of_categories)

    if series_column_name == "":
        if "parsed_dates" in postprocessed_df.columns:
            postprocessed_df["parsed_dates"] = postprocessed_df[
                xAxis_column_name
            ].apply(parse_date)
            postprocessed_df = postprocessed_df.sort_values(
                by="parsed_dates",
                ascending=True,
            )
            postprocessed_df = postprocessed_df.drop(columns=["parsed_dates"])
        else:
            numeric_regex = re.compile(r"^\d+$")
            numeric_elements = df.copy()[
                df.copy()[xAxis_column_name]
                .astype(str)
                .apply(lambda x: bool(numeric_regex.match(x)))
            ]
            non_numeric_elements = df.copy()[
                ~df.copy()[xAxis_column_name]
                .astype(str)
                .apply(lambda x: bool(numeric_regex.match(x)))
            ]

            if len(non_numeric_elements) > 0:
                try:
                    postprocessed_df = postprocessed_df.sort_values(
                        by=xAxis_column_name,
                        ascending=True,
                    )
                except Exception:
                    print("Error Postprocessed DataFrame:")
                    print(postprocessed_df)
                    print(traceback.format_exc())
                    # logger.error(traceback.format_exc())
            else:
                numeric_elements[xAxis_column_name] = numeric_elements[
                    xAxis_column_name
                ].astype(int)
                numeric_elements = numeric_elements.sort_values(by=xAxis_column_name)
                numeric_elements[xAxis_column_name] = numeric_elements[
                    xAxis_column_name
                ].astype(str)
                df[xAxis_column_name] = numeric_elements[xAxis_column_name]
    elif "parsed_dates" in postprocessed_df.columns:
        postprocessed_df["parsed_dates"] = postprocessed_df[xAxis_column_name].apply(
            parse_date,
        )
        postprocessed_df = postprocessed_df.sort_values(
            by=["parsed_dates", series_column_name],
            ascending=True,
        )
        postprocessed_df = postprocessed_df.drop(columns=["parsed_dates"])
    else:
        numeric_regex = re.compile(r"^\d+$")
        numeric_elements = df.copy()[
            df.copy()[xAxis_column_name]
            .astype(str)
            .apply(lambda x: bool(numeric_regex.match(x)))
        ]
        non_numeric_elements = df.copy()[
            ~df.copy()[xAxis_column_name]
            .astype(str)
            .apply(lambda x: bool(numeric_regex.match(x)))
        ]

        if len(non_numeric_elements) > 0:
            postprocessed_df = postprocessed_df.sort_values(
                by=[xAxis_column_name, series_column_name],
                ascending=True,
            )
        else:
            numeric_elements[xAxis_column_name] = numeric_elements[
                xAxis_column_name
            ].astype(int)
            numeric_elements = numeric_elements.sort_values(
                by=[xAxis_column_name, series_column_name],
            )
            numeric_elements[xAxis_column_name] = numeric_elements[
                xAxis_column_name
            ].astype(str)
            df[xAxis_column_name] = numeric_elements[xAxis_column_name]

    return postprocessed_df


def postprocess_df_categorical_order(
    chart_title: str,
    chart_axis: dict,
    df: pd.DataFrame,
    max_number_of_categories: int = 10000,
):
    df_columns = list(df.columns)

    if "xAxis" in df_columns:
        xAxis_column_name = "xAxis"
    elif "xAxis_column" in chart_axis and chart_axis["xAxis_column"] in df_columns:
        xAxis_column_name = chart_axis["xAxis_column"]
    else:
        return df

    yAxis_column_names = []

    for idx in range(1, len(df_columns)):
        if idx == 1:
            if "yAxis" in df_columns:
                yAxis_column_names.append("yAxis")
            elif (
                "yAxis_column" in chart_axis
                and chart_axis["yAxis_column"] in df_columns
            ):
                yAxis_column_names.append(chart_axis["yAxis_column"])
            else:
                return df
        elif f"yAxis{idx}" in df_columns:
            yAxis_column_names.append(f"yAxis{idx}")
        elif (
            f"yAxis{idx}_column" in chart_axis
            and chart_axis[f"yAxis{idx}_column"] in df_columns
        ):
            yAxis_column_names.append(chart_axis[f"yAxis{idx}_column"])

    if "series" in df_columns:
        series_column_name = "series"
    elif "series_column" in chart_axis and chart_axis["series_column"] in df_columns:
        series_column_name = chart_axis["series_column"]
    else:
        series_column_name = ""

    groupby_columns = df_columns.copy()
    for yAxis_column_name in yAxis_column_names:
        groupby_columns.remove(yAxis_column_name)

    # Make Sure xAxis is the first
    groupby_columns.remove(xAxis_column_name)
    groupby_columns.insert(0, xAxis_column_name)

    if len(groupby_columns) > 1:
        if series_column_name != "":
            groupby_columns.remove(series_column_name)
            groupby_columns.insert(1, series_column_name)
        else:
            series_column_name = groupby_columns[1]

    try:
        if "total" in chart_title.lower() or "sum" in chart_title.lower():
            aggregated_df = df.groupby(by=groupby_columns).sum()
        elif "average" in chart_title.lower() or "mean" in chart_title.lower():
            aggregated_df = df.groupby(by=groupby_columns).mean()
        else:
            aggregated_df = df.groupby(by=groupby_columns).sum()
    except Exception:
        print(f"Error Aggregating Column by {groupby_columns}")
        print(df)
        return df

    postprocessed_data = {}

    if series_column_name == "":
        postprocessed_data[xAxis_column_name] = list(aggregated_df.index)
    else:
        postprocessed_data[xAxis_column_name] = list(
            aggregated_df.index.get_level_values(0),
        )
        postprocessed_data[series_column_name] = list(
            aggregated_df.index.get_level_values(1),
        )

    for column in aggregated_df.columns:
        postprocessed_data[column] = list(aggregated_df[column])

    postprocessed_df = pd.DataFrame(postprocessed_data)
    postprocessed_df = postprocessed_df.fillna(
        {
            col: 0 if postprocessed_df[col].dtype in [np.float64, np.int64] else "null"
            for col in postprocessed_df.columns
        },
    )

    if "parsed_dates" in postprocessed_df.columns:
        postprocessed_df["parsed_dates"] = postprocessed_df[xAxis_column_name].apply(
            parse_date,
        )
        postprocessed_df = postprocessed_df.sort_values(
            by="parsed_dates",
            ascending=True,
        )
        postprocessed_df = postprocessed_df.drop(columns=["parsed_dates"])
    else:
        numeric_regex = re.compile(r"^\d+$")
        numeric_elements = df.copy()[
            df.copy()[xAxis_column_name]
            .astype(str)
            .apply(lambda x: bool(numeric_regex.match(x)))
        ]
        non_numeric_elements = df.copy()[
            ~df.copy()[xAxis_column_name]
            .astype(str)
            .apply(lambda x: bool(numeric_regex.match(x)))
        ]

        if len(non_numeric_elements) > 0:
            postprocessed_df = postprocessed_df.sort_values(
                by=xAxis_column_name,
                ascending=True,
            )
        else:
            numeric_elements[xAxis_column_name] = numeric_elements[
                xAxis_column_name
            ].astype(int)
            numeric_elements = numeric_elements.sort_values(by=xAxis_column_name)
            numeric_elements[xAxis_column_name] = numeric_elements[
                xAxis_column_name
            ].astype(str)
            df[xAxis_column_name] = numeric_elements[xAxis_column_name]

    if len(postprocessed_df) > max_number_of_categories:
        latest_phrases_found = find_latest_phrases(chart_title)

        if len(latest_phrases_found) > 0:
            postprocessed_df = postprocessed_df.tail(max_number_of_categories)
        else:
            postprocessed_df = postprocessed_df.head(max_number_of_categories)

    return postprocessed_df


def postprocess_df_numerical(
    chart_title: str,
    chart_axis: dict,
    df: pd.DataFrame,
    max_number_of_points: int = 100,
):
    df_columns = list(df.columns)

    if "xAxis" in df_columns:
        xAxis_column_name = "xAxis"
    elif "xAxis_column" in chart_axis and chart_axis["xAxis_column"] in df_columns:
        xAxis_column_name = chart_axis["xAxis_column"]
    else:
        return df

    yAxis_column_names = []

    for idx in range(1, len(df_columns)):
        if idx == 1:
            if "yAxis" in df_columns:
                yAxis_column_names.append("yAxis")
            elif (
                "yAxis_column" in chart_axis
                and chart_axis["yAxis_column"] in df_columns
            ):
                yAxis_column_names.append(chart_axis["yAxis_column"])
            else:
                return df
        elif f"yAxis{idx}" in df_columns:
            yAxis_column_names.append(f"yAxis{idx}")
        elif (
            f"yAxis{idx}_column" in chart_axis
            and chart_axis[f"yAxis{idx}_column"] in df_columns
        ):
            yAxis_column_names.append(chart_axis[f"yAxis{idx}_column"])

    if "series" in df_columns:
        series_column_name = "series"
    elif "series_column" in chart_axis and chart_axis["series_column"] in df_columns:
        series_column_name = chart_axis["series_column"]
    else:
        series_column_name = ""

    groupby_columns = df_columns.copy()
    for yAxis_column_name in yAxis_column_names:
        groupby_columns.remove(yAxis_column_name)

    # Make Sure xAxis is the first
    groupby_columns.remove(xAxis_column_name)
    groupby_columns.insert(0, xAxis_column_name)

    if len(groupby_columns) > 1:
        if series_column_name != "":
            groupby_columns.remove(series_column_name)
            groupby_columns.insert(1, series_column_name)
        else:
            series_column_name = groupby_columns[1]

    try:
        if "total" in chart_title.lower() or "sum" in chart_title.lower():
            aggregated_df = df.groupby(by=groupby_columns).sum()
        elif "average" in chart_title.lower() or "mean" in chart_title.lower():
            aggregated_df = df.groupby(by=groupby_columns).mean()
        else:
            aggregated_df = df.groupby(by=groupby_columns).sum()
    except Exception:
        print(f"Error Aggregating Column by {groupby_columns}")
        print(df)
        return df

    postprocessed_data = {}

    if series_column_name == "":
        postprocessed_data[xAxis_column_name] = list(aggregated_df.index)
    else:
        postprocessed_data[xAxis_column_name] = list(
            aggregated_df.index.get_level_values(0),
        )
        postprocessed_data[series_column_name] = list(
            aggregated_df.index.get_level_values(1),
        )

    for column in aggregated_df.columns:
        postprocessed_data[column] = list(aggregated_df[column])

    postprocessed_df = pd.DataFrame(postprocessed_data)
    postprocessed_df = postprocessed_df.fillna(
        {
            col: 0 if postprocessed_df[col].dtype in [np.float64, np.int64] else "null"
            for col in postprocessed_df.columns
        },
    )

    if len(postprocessed_df) > max_number_of_points:
        # check type
        if isinstance(postprocessed_df[xAxis_column_name].values.tolist()[0], int):
            xAxis_type = "int"
        else:
            xAxis_type = "float"

        min_value = min(postprocessed_df[xAxis_column_name])
        max_value = max(postprocessed_df[xAxis_column_name])

        value_range = max_value - min_value

        if value_range >= max_number_of_points:
            if xAxis_type == "int":
                increment = abs(int(max_value - min_value)) / max_number_of_points
            elif xAxis_type == "float":
                increment = abs(float(max_value - min_value)) / max_number_of_points
        else:
            increment = abs(float(max_value - min_value)) / max_number_of_points
            xAxis_type = "float"

        if increment == 0.00:
            if "parsed_dates" in postprocessed_df.columns:
                postprocessed_df["parsed_dates"] = postprocessed_df[
                    xAxis_column_name
                ].apply(parse_date)
                postprocessed_df = postprocessed_df.sort_values(
                    by="parsed_dates",
                    ascending=True,
                )
                postprocessed_df = postprocessed_df.drop(columns=["parsed_dates"])
            else:
                numeric_regex = re.compile(r"^\d+$")
                numeric_elements = df.copy()[
                    df.copy()[xAxis_column_name]
                    .astype(str)
                    .apply(lambda x: bool(numeric_regex.match(x)))
                ]
                non_numeric_elements = df.copy()[
                    ~df.copy()[xAxis_column_name]
                    .astype(str)
                    .apply(lambda x: bool(numeric_regex.match(x)))
                ]

                if len(non_numeric_elements) > 0:
                    postprocessed_df = postprocessed_df.sort_values(
                        by=xAxis_column_name,
                        ascending=True,
                    )
                else:
                    numeric_elements[xAxis_column_name] = numeric_elements[
                        xAxis_column_name
                    ].astype(int)
                    numeric_elements = numeric_elements.sort_values(
                        by=xAxis_column_name,
                    )
                    numeric_elements[xAxis_column_name] = numeric_elements[
                        xAxis_column_name
                    ].astype(str)
                    df[xAxis_column_name] = numeric_elements[xAxis_column_name]
            return postprocessed_df

        if xAxis_type == "int":
            postprocessed_df["bin"] = pd.cut(
                postprocessed_df[xAxis_column_name],
                bins=max_number_of_points,
                labels=[
                    f"{int(min_value + (i*increment))} - {int(min_value + ((i+1)*increment))}"
                    for i in range(max_number_of_points)
                ],
            )
        else:
            postprocessed_df["bin"] = pd.cut(
                postprocessed_df[xAxis_column_name],
                bins=max_number_of_points,
                labels=[
                    f"{float(min_value + (i*increment))} - {float(min_value + ((i+1)*increment))}"
                    for i in range(max_number_of_points)
                ],
            )

        postprocessed_df.drop(xAxis_column_name, axis="columns", inplace=True)
        postprocessed_df.rename({"bin": xAxis_column_name}, inplace=True)

    if "parsed_dates" in postprocessed_df.columns:
        postprocessed_df["parsed_dates"] = postprocessed_df[xAxis_column_name].apply(
            parse_date,
        )
        postprocessed_df = postprocessed_df.sort_values(
            by="parsed_dates",
            ascending=True,
        )
        postprocessed_df = postprocessed_df.drop(columns=["parsed_dates"])
    else:
        numeric_regex = re.compile(r"^\d+$")
        numeric_elements = df.copy()[
            df.copy()[xAxis_column_name]
            .astype(str)
            .apply(lambda x: bool(numeric_regex.match(x)))
        ]
        non_numeric_elements = df.copy()[
            ~df.copy()[xAxis_column_name]
            .astype(str)
            .apply(lambda x: bool(numeric_regex.match(x)))
        ]

        if len(non_numeric_elements) > 0:
            postprocessed_df = postprocessed_df.sort_values(
                by=xAxis_column_name,
                ascending=True,
            )
        else:
            numeric_elements[xAxis_column_name] = numeric_elements[
                xAxis_column_name
            ].astype(int)
            numeric_elements = numeric_elements.sort_values(by=xAxis_column_name)
            numeric_elements[xAxis_column_name] = numeric_elements[
                xAxis_column_name
            ].astype(str)
            df[xAxis_column_name] = numeric_elements[xAxis_column_name]

    return postprocessed_df


def _postprocess_df(
    chart_title: str,
    chart_type: str,
    chart_axis: dict,
    df: pd.DataFrame,
    code_level_logger: logging.Logger,
) -> pd.DataFrame:
    if df.empty:
        return df

    if len(df.columns) < 1 or df.iloc[:, 0].isna().all():
        return df

    postprocessed_df: pd.DataFrame = df.copy()
    if chart_type not in ["table_chart", "aggregated_table_chart", "full_table_chart"]:
        postprocessed_df = postprocessed_df.fillna(
            {
                col: (
                    0
                    if postprocessed_df[col].dtype in [np.float64, np.int64]
                    else "null"
                )
                for col in postprocessed_df.columns
            },
        )

    # bar_chart, column_chart, histogram_chart set max to 12 bars.
    # grouped_bar_chart, grouped_column_chart set max to 12 main category (can be more than 12 bars).
    # radar_chart set max to 12 categories.
    # TreemapMulti_chart set max to 9 sub categories.
    # pyramidfunnel_chart set max to 12 categories.
    # pie_chart set max to 9 categories.
    # line_chart, spline_chart, area_chart set max to 12 points.
    # barlinecombo_chart set max to 12 categories and points.
    # table_chart, scatterplot_chart no limit.

    # Categorical Charts
    if chart_type in [
        "bar_chart",
        "column_chart",
        "pyramidfunnel_chart",
        "histogram_chart",
        "pie_chart",
    ]:
        postprocessed_df = postprocess_df_categorical(
            chart_title,
            chart_axis,
            postprocessed_df,
        )
    elif chart_type in ["radar_chart"]:
        postprocessed_df = postprocess_df_categorical_with_series(
            chart_title,
            chart_axis,
            postprocessed_df,
        )
    # Ordered Charts
    elif chart_type in ["line_chart", "spline_chart", "area_chart", "radar_chart"]:
        if "xAxis" in postprocessed_df.columns:
            xaxis_column_name = "xAxis"
        elif (
            "xAxis_column" in chart_axis
            and chart_axis["xAxis_column"] in postprocessed_df.columns
        ):
            xaxis_column_name = chart_axis["xAxis_column"]
        else:
            return postprocessed_df

        if isinstance(
            postprocessed_df[xaxis_column_name].values.tolist()[0],
            int,
        ) or isinstance(postprocessed_df[xaxis_column_name].values.tolist()[0], float):
            postprocessed_df = postprocess_df_numerical(
                chart_title,
                chart_axis,
                postprocessed_df,
            )
        else:
            postprocessed_df = postprocess_df_categorical_order(
                chart_title,
                chart_axis,
                postprocessed_df,
            )
    # Ordered + Categorical Charts
    elif chart_type in ["barlinecombo_chart"]:
        if "xAxis" in postprocessed_df.columns:
            xaxis_column_name = "xAxis"
        elif (
            "xAxis_column" in chart_axis
            and chart_axis["xAxis_column"] in postprocessed_df.columns
        ):
            xaxis_column_name = chart_axis["xAxis_column"]
        else:
            return postprocessed_df

        if isinstance(
            postprocessed_df[xaxis_column_name].values.tolist()[0],
            int,
        ) or isinstance(postprocessed_df[xaxis_column_name].values.tolist()[0], float):
            postprocessed_df = postprocess_df_numerical(
                chart_title,
                chart_axis,
                postprocessed_df,
            )
        else:
            postprocessed_df = postprocess_df_barline_categorical_order(
                chart_title,
                chart_axis,
                postprocessed_df,
            )
    # Bubble Charts
    elif chart_type in ["bubbleplot_chart"]:
        postprocessed_df = postprocess_df_bubble(
            chart_axis,
            postprocessed_df,
        )
    # TreeMap Charts
    elif chart_type in [
        "TreemapMulti_chart",
    ]:
        postprocessed_df = postprocess_df_treemap(
            chart_title,
            chart_axis,
            postprocessed_df,
        )
    # Multiple Categorical Charts
    elif chart_type in [
        "grouped_bar_chart",
        "grouped_column_chart",
    ]:
        postprocessed_df = postprocess_df_grouped_categorical(
            chart_title,
            chart_axis,
            postprocessed_df,
        )
    elif chart_type in ["table_chart", "aggregated_table_chart", "full_table_chart"]:
        pass
    elif chart_type in ["scatterplot_chart"]:
        postprocessed_df = postprocess_df_scatter(
            chart_axis,
            postprocessed_df,
        )
    elif chart_type in ["card_chart"]:
        postprocessed_df = postprocess_df_card(
            chart_axis,
            postprocessed_df,
        )
    else:
        code_level_logger.error(
            f"Chart Type {chart_type} is not supported in postprocessing!"
        )
        raise RuntimeError(
            f"Chart Type {chart_type} is not supported in postprocessing!",
        )

    return postprocessed_df


def postprocess_chart_data(
    chart_data: dict,
    session_id: str,
    code_level_logger: logging.Logger,
):
    with PerformanceLogger(session_id):
        if "main_title" in chart_data:
            main_chart_title = chart_data["main_title"]
        elif "main_instruction" in chart_data:
            main_chart_title = chart_data["main_instruction"]
        else:
            code_level_logger.error("Question and Instruction is empty!")
            raise RuntimeError("Question and Instruction is empty!")

        main_chart_type = chart_data["main_chart_type"]
        main_chart_axis = chart_data["main_chart_axis"]
        main_chart_data = chart_data["chart_data"]

        chart_data["chart_data"] = _postprocess_df(
            main_chart_title,
            main_chart_type,
            main_chart_axis,
            main_chart_data,
            code_level_logger,
        )

        sub_questions_data = chart_data["sub_questions"]

        for sub_question_data_idx, sub_question_data in enumerate(sub_questions_data):
            if "chart_title" in chart_data:
                sub_chart_title = chart_data["chart_title"]
            elif "main_instruction" in chart_data:
                sub_chart_title = chart_data["main_instruction"]
            else:
                raise RuntimeError("Question and Instruction is empty!")

            sub_chart_title = sub_question_data["chart_title"]
            sub_chart_type = sub_question_data["chart_type"]
            sub_chart_axis = sub_question_data["chart_axis"]
            sub_chart_data = sub_question_data["chart_data"]

            sub_questions_data[sub_question_data_idx]["chart_data"] = _postprocess_df(
                sub_chart_title,
                sub_chart_type,
                sub_chart_axis,
                sub_chart_data,
                code_level_logger,
            )

        chart_data["sub_questions"] = sub_questions_data

        return chart_data


def postprocess_updater_chart_json(
    chart_json: dict, chart_data: pd.DataFrame, code_level_logger: logging.Logger
):
    chart_title = chart_json["Chart_Title"]
    chart_type = chart_json["Chart_Type"]
    chart_axis = chart_json["Chart_Axis"]

    postprocessed_chart_data = _postprocess_df(
        chart_title,
        chart_type,
        chart_axis,
        chart_data,
        code_level_logger,
    )

    return postprocessed_chart_data
