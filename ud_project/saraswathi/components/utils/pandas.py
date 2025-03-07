import logging
import re

import pandas as pd

logger = logging.getLogger("saraswati-agent")


def remove_null_x_axis(
    chart_data: pd.DataFrame,
    chart_axis: dict,
) -> pd.DataFrame:
    """The function `remove_null_x_axis` removes rows with null values in the x-axis column of a DataFrame
    based on specified criteria.

    :param chart_data: pd.DataFrame - This is the data used to create the chart. It contains the values
    for the x-axis and y-axis
    :type chart_data: pd.DataFrame
    :param chart_axis: The `chart_axis` parameter is a dictionary that contains information about the
    chart's axis configuration. It may include keys such as "xAxis_column" which specifies the column in
    the `chart_data` DataFrame that corresponds to the x-axis values
    :type chart_axis: dict
    :return: The function `remove_null_x_axis` is returning the modified `chart_data` DataFrame after
    removing any rows where the x-axis values are null or missing.
    """
    if "xAxis" in chart_data.columns:
        chart_data.dropna(subset=["xAxis"], inplace=True)
    elif (
        "xAxis_column" in chart_axis
        and isinstance(chart_axis["xAxis_column"], str)
        and chart_axis["xAxis_column"] in chart_data.columns
    ):
        chart_data.dropna(subset=[chart_axis["xAxis_column"]], inplace=True)

    return chart_data


def remove_null_series(
    chart_data: pd.DataFrame,
    chart_axis: dict,
) -> pd.DataFrame:
    if "series" in chart_data.columns:
        chart_data.dropna(subset=["xAxis"], inplace=True)
    elif (
        "series_column" in chart_axis
        and isinstance(chart_axis["series_column"], str)
        and chart_axis["series_column"] in chart_data.columns
    ):
        chart_data.dropna(subset=[chart_axis["series_column"]], inplace=True)

    return chart_data


def determine_date_frequency(date_series: pd.Series):
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


def sort_pandas_date(df: pd.DataFrame, date_column_name: str) -> pd.DataFrame:
    def parse_date(date_str):
        # Split the date string by delimiters
        parts = date_str.split("-")
        if len(parts) == 1:
            # Year only
            return (int(parts[0]), 0, 0)
        if "W" in parts[1]:
            # Year-Week format
            year, week = parts[0], parts[1].split("W")[1]
            return (int(year), int(week), 0)
        if "H" in parts[1]:
            # Year-Half format
            year, half = parts[0], parts[1].split("H")[1]
            return (int(year), int(half), 0)
        if "Q" in parts[1]:
            # Year-Quarter format
            year, quarter = parts[0], parts[1].split("Q")[1]
            return (int(year), int(quarter), 0)
        if "M" in parts[1]:
            # Year-Month format
            year, month = parts[0], parts[1].split("M")[1]
            return (int(year), int(month), 0)
        if len(parts) == 2:
            # Year-Month format
            year, month = parts
            return (int(year), int(month), 0)
        if len(parts) == 3:
            # Year-Month-Day format
            year, month, day = parts
            return (int(year), int(month), int(day))
        # Default case
        return (0, 0, 0)

    try:
        df = df.sort_values(by=date_column_name, key=lambda x: x.apply(parse_date))
    except Exception:
        pass

    return df


def detect_and_sort_pandas_date(df: pd.DataFrame, date_column_name: str) -> tuple:
    def parse_date(date_str):
        # Split the date string by delimiters
        parts = date_str.split("-")
        if len(parts) == 1:
            # Year only
            return (int(parts[0]), 0, 0)
        if "W" in parts[1]:
            # Year-Week format
            year, week = parts[0], parts[1].split("W")[1]
            return (int(year), int(week), 0)
        if "H" in parts[1]:
            # Year-Half format
            year, half = parts[0], parts[1].split("H")[1]
            return (int(year), int(half), 0)
        if "Q" in parts[1]:
            # Year-Quarter format
            year, quarter = parts[0], parts[1].split("Q")[1]
            return (int(year), int(quarter), 0)
        if "M" in parts[1]:
            # Year-Month format
            year, month = parts[0], parts[1].split("M")[1]
            return (int(year), int(month), 0)
        if len(parts) == 2:
            # Year-Month format
            year, month = parts
            return (int(year), int(month), 0)
        if len(parts) == 3:
            # Year-Month-Day format
            year, month, day = parts
            return (int(year), int(month), int(day))
        # Default case
        raise RuntimeError("Not Date!")

    try:
        df = df.sort_values(by=date_column_name, key=lambda x: x.apply(parse_date))
        return df, True  # Return the sorted DataFrame and True if sorting is successful
    except Exception:
        return df, False  # Return the original DataFrame and False if sorting fails


def clean_column_names(df):
    # create a copy of the dataframe to avoid modifying the original data
    cleaned_df = df.copy()

    # iterate over column names in the dataframe
    for col in cleaned_df.columns:
        # check if column name contains any special characters or spaces
        if re.search("[^0-9a-zA-Z_]", col):
            # replace special characters and spaces with underscores
            new_col = re.sub("[^0-9a-zA-Z_]", "_", col)
            # rename the column in the cleaned dataframe
            cleaned_df.rename(columns={col: new_col}, inplace=True)

    # return the cleaned dataframe
    return cleaned_df


def file_to_df(file_location: str):
    """Get summary of data from file location"""
    file_name = file_location.split("/")[-1]
    df = None
    if "csv" in file_name:
        df = pd.read_csv(file_location)
    elif "xlsx" in file_name:
        df = pd.read_excel(file_location)
    elif "json" in file_name:
        df = pd.read_json(file_location, orient="records")
    elif "parquet" in file_name:
        df = pd.read_parquet(file_location)
    elif "feather" in file_name:
        df = pd.read_feather(file_location)

    return df


def read_dataframe(file_location):
    file_extension = file_location.split(".")[-1]
    if file_extension == "json":
        try:
            df = pd.read_json(file_location, orient="records")
        except ValueError:
            df = pd.read_json(file_location, orient="table")
    elif file_extension == "csv":
        df = pd.read_csv(file_location)
    elif file_extension in ["xls", "xlsx"]:
        df = pd.read_excel(file_location)
    elif file_extension == "parquet":
        df = pd.read_parquet(file_location)
    elif file_extension == "feather":
        df = pd.read_feather(file_location)
    elif file_extension == "tsv":
        df = pd.read_csv(file_location, sep="\t")
    else:
        raise ValueError("Unsupported file type")

    # clean column names and check if they have changed
    cleaned_df = clean_column_names(df)
    if cleaned_df.columns.tolist() != df.columns.tolist() or len(df) > 4500:
        if len(df) > 4500:
            cleaned_df = cleaned_df.sample(4500)
        # write the cleaned DataFrame to the original file on disk
        if file_extension == "csv":
            cleaned_df.to_csv(file_location, index=False)
        elif file_extension in ["xls", "xlsx"]:
            cleaned_df.to_excel(file_location, index=False)
        elif file_extension == "parquet":
            cleaned_df.to_parquet(file_location, index=False)
        elif file_extension == "feather":
            cleaned_df.to_feather(file_location, index=False)
        elif file_extension == "json":
            with open(file_location, "w") as f:
                f.write(cleaned_df.to_json(orient="records"))
        else:
            raise ValueError("Unsupported file type")

    return cleaned_df
