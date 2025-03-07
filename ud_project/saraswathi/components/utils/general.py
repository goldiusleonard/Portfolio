import ast
import base64
import hashlib
import io
import json
import logging
import os
import re
from copy import deepcopy
from typing import Any, List, Union

import matplotlib.pyplot as plt
import numpy as np
from diskcache import Cache
from PIL import Image

logger = logging.getLogger("saraswati-agent")


def is_valid_decimal(val: str) -> bool:
    """Helper function to validate decimal strings."""
    try:
        stripped = val.strip()
        if stripped.startswith("-"):
            stripped = stripped[1:]
        parts = stripped.split(".")
        return (
            len(parts) <= 2 and all(part.isdigit() for part in parts) and bool(stripped)
        )
    except AttributeError:
        return False


def validate_and_add_time_info(title, time_frame="", time_duration=""):
    # Create a list of synonyms or related words to avoid redundancy
    time_keywords = {
        "quarter": ["quarterly", "quarter", "q1", "q2", "q3", "q4"],
        "month": [
            "monthly",
            "month",
            "jan",
            "feb",
            "mar",
            "apr",
            "may",
            "jun",
            "jul",
            "aug",
            "sep",
            "oct",
            "nov",
            "dec",
        ],
        "year": ["yearly", "year", "annual", "annum", "fy"],
        "week": ["weekly", "week"],
        "day": ["daily", "day"],
        "half-year": [
            "half-yearly",
            "half-year",
            "first half",
            "second half",
            "semiannual",
            "biannual",
            "h1",
            "h2",
        ],
        "decade": ["decade", "decennial"],
        "century": ["century", "centennial"],
    }

    # Add common time-related phrases
    time_phrases = [
        "past",
        "last",
        "previous",
        "prior",
        "preceding",
        "next",
        "coming",
        "upcoming",
        "following",
        "future",
        "prospective",
        "forthcoming",
        "current",
        "present",
        "ongoing",
        "existing",
        "ytd",
        "year-to-date",
        "mtd",
        "month-to-date",
        "qtd",
        "quarter-to-date",
        "rolling",
        "trailing",
        "moving",
        "cumulative",
        "fiscal",
        "calendar",
        "short-term",
        "mid-term",
        "long-term",
        "historical",
        "projected",
        "forecasted",
        "to date",
        "since inception",
        "life-to-date",
        "period",
        "duration",
        "timeframe",
        "interval",
    ]

    def is_redundant(phrase, text):
        phrase_lower = phrase.lower()
        text_lower = text.lower()

        if phrase_lower in text_lower:
            return True

        phrase_words = phrase_lower.split()
        for word in phrase_words:
            if word in time_phrases and word in text_lower:
                return True

            for synonyms in time_keywords.values():
                if word in synonyms and any(
                    syn.lower() in text_lower for syn in synonyms
                ):
                    return True

        return False

    time_info = []

    if time_frame and not is_redundant(time_frame, title):
        time_info.append(time_frame)

    if time_duration and not is_redundant(time_duration, title):
        time_info.append(time_duration)

    if time_info:
        title = f"{title.rstrip(', ')}, {', '.join(time_info)}"

    return title.strip()


def get_display_name(column_display_names: str) -> list:
    column_names = deepcopy(column_display_names)

    # Add double quotes to the keys
    column_names = re.sub(r"(\w+):", r'"\1":', column_names)

    # Add curly braces to the string
    column_names = "{" + column_names + "}"

    # Add double quotes after the colon until the newline followed by double quotes
    column_names = re.sub(r':\s(.*?)(?=\n")', r': "\1",', column_names)

    # Add double quotes after the colon until closing curly brace ( For example: `"Date": Date and stuff}`` )
    column_names = re.sub(r":\s(.*?)(?=\n})", r': "\1",', column_names)

    column_name_list = list(ast.literal_eval(column_names).values())

    return column_name_list


def remove_unused_keys_UPS(UPS_dicts: list) -> list:
    EXCEPTION_KEYS = [
        "Subscription_ID",
        "Subscription_Name",
        "Shared_User_ID",
        "Client_ID",
        "User_ID",
        "Aggregated_Table_Column",
        "Aggregated_Table_JSON",
        "Chart_Query",
        "Chart_SQL_Library",
        "Chart_Name",
        "Chart_Axis",
        "Visual_Title",
        "Chart_Title",
        "Chart_Type",
        "Chart_Position",
        "xAxis",
        "xAxis_Description",
        "yAxis",
        "yAxis_Description",
        "Database_Properties",
    ]

    for UPS_dict_idx, UPS_dict in enumerate(UPS_dicts):
        keys_to_remove = []
        for key in UPS_dict.keys():
            if UPS_dict[key] in [[], {}, ""] and key not in EXCEPTION_KEYS:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del UPS_dicts[UPS_dict_idx][key]

        if "Aggregated_Table_JSON" in UPS_dict.keys() and isinstance(
            UPS_dict["Aggregated_Table_JSON"],
            dict,
        ):
            Aggregated_Table_JSON = UPS_dict["Aggregated_Table_JSON"]
            Aggregated_Table_JSON_keys = list(Aggregated_Table_JSON.keys())
            for inner_key in Aggregated_Table_JSON_keys:
                if (
                    Aggregated_Table_JSON[inner_key] in [[], {}, ""]
                    and inner_key not in EXCEPTION_KEYS
                ):
                    del Aggregated_Table_JSON[inner_key]
            UPS_dicts[UPS_dict_idx]["Aggregated_Table_JSON"] = Aggregated_Table_JSON

        # Remove visual title for main chart position 2 onwards
        if int(UPS_dict["Chart_Position"]) > 1:
            if "Visual_Title" in UPS_dict.keys():
                del UPS_dicts[UPS_dict_idx]["Visual_Title"]

        # Remove visual title & chart title for Aggregated_Table_JSON
        if "Aggregated_Table_JSON" in UPS_dict.keys() and isinstance(
            UPS_dict["Aggregated_Table_JSON"],
            dict,
        ):
            Aggregated_Table_JSON = UPS_dict["Aggregated_Table_JSON"]
            Aggregated_Table_JSON_keys = list(Aggregated_Table_JSON.keys())

            for key in ["Visual_Title", "Chart_Title"]:
                if key in Aggregated_Table_JSON_keys:
                    del Aggregated_Table_JSON[key]

            UPS_dicts[UPS_dict_idx]["Aggregated_Table_JSON"] = Aggregated_Table_JSON

    return UPS_dicts


def arrange_UPS(UPS_dicts: list) -> list:
    chart_name_list = []
    visual_idx = 0
    for UPS_dict_idx, UPS_dict in enumerate(UPS_dicts):
        if "table" in UPS_dict["Chart_Name"].lower():
            continue

        if UPS_dict["Chart_Name"] not in chart_name_list:
            visual_idx += 1
            chart_name_list.append(UPS_dict["Chart_Name"])

        UPS_dicts[UPS_dict_idx]["Chart_Name"] = f"Visual {visual_idx}"

        if (
            "Aggregated_Table_JSON" in UPS_dict.keys()
            and UPS_dict["Aggregated_Table_JSON"] != {}
        ):
            UPS_dicts[UPS_dict_idx]["Aggregated_Table_JSON"]["Chart_Name"] = (
                f"Visual {visual_idx}"
            )

    return UPS_dicts


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


def get_aggregated_columns(chart_axis: dict):
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
):
    has_aggregation: bool = False

    for keyword in keywords:
        if keyword.lower().strip() in string_input.lower():
            has_aggregation = True

    return has_aggregation


def check_negative_value(value_list: list) -> bool:
    is_negative = False
    for value in value_list:
        if isinstance(value, int) or isinstance(value, float):
            if value < 0:
                is_negative = True
                break

    return is_negative


def normalize_chart_type(
    chart_type: str,
):
    chart_type_normalization_dict = {
        "columnnegative_chart": "column chart",
        "forecast_line_chart": "line chart",
    }
    if chart_type in list(chart_type_normalization_dict.keys()):
        chart_type = chart_type_normalization_dict[chart_type]

    normalized_chart_type = chart_type.replace("_", " ")

    return normalized_chart_type


def format_number(num):
    """Convert a number into a string with K, M, B, T, P, E, Z, Y suffix.

    Args:
    num (int or float): The number to format.
    precision (int): The number of decimal places to show (default is 1).

    Return:
    str: The formatted number with suffix.

    """
    suffixes = ["", "K", "M", "B", "T", "P", "E", "Z", "Y"]
    is_negative = num < 0
    num = abs(num)

    precision = 3
    for suffix in suffixes:
        if num < 1000:
            num = round(num, 3)
            num_str = str(num)
            if "." in num_str:
                num_str_decimal = num_str.split(".")[1]
                num_precision = num_str_decimal_len = len(num_str_decimal)
                for i in range(num_str_decimal_len):
                    if num_str_decimal[num_str_decimal_len - 1 - i] == "0":
                        num_precision -= 1
                    else:
                        break
                precision = min(3, num_precision)
            else:
                precision = 0
            formatted_num = f"{num:.{precision}f}{suffix}"
            break
        num /= 1000

    if is_negative:
        formatted_num = "(-" + formatted_num + ")"

    return formatted_num


def calculate_bins(data):
    """The function `calculate_bins` determines the number of bins for a histogram based on the specified
    method, such as Sturges, Rice, or Square Root.

    :param data: The `calculate_bins` function you provided is used to calculate the number of bins for
    a histogram based on different methods. To use this function, you need to pass in the data for which
    you want to calculate the bins. The function also accepts an optional parameter `method` which
    specifies the method to
    :param method: The `method` parameter in the `calculate_bins` function determines the method used to
    calculate the number of bins for a histogram. The available methods are:, defaults to sturges
    (optional)
    :return: The `calculate_bins` function returns the number of bins calculated based on the specified
    method for binning the data. The method can be one of the following: 'sqrt', 'sturges', 'rice',
    'scott', or 'freedman-diaconis'. The function calculates the number of bins using different formulas
    depending on the chosen method and returns the result as an integer.
    """
    n = len(data)

    bins_dict = {
        "sqrt": int(np.sqrt(n)),
        "sturges": int(np.ceil(np.log2(n) + 1)),
        "rice": int(np.ceil(2 * n ** (1 / 3))),
    }

    return bins_dict


def get_dirs(path: str) -> List[str]:
    return next(os.walk(path))[1]


def plot_raster(rasters: Union[str, List[str]], figsize: tuple = (10, 10)):
    plt.figure(figsize=figsize)

    if isinstance(rasters, str):
        rasters = [rasters]

    images = []

    # Load images, convert to RGB if needed, and resize to the same height
    max_height = 0
    for raster in rasters:
        decoded_image = base64.b64decode(raster)
        image_buffer = io.BytesIO(decoded_image)
        image = Image.open(image_buffer)

        # Convert RGBA images to RGB
        if image.mode == "RGBA":
            image = image.convert("RGB")

        max_height = max(max_height, image.height)

    for raster in rasters:
        decoded_image = base64.b64decode(raster)
        image_buffer = io.BytesIO(decoded_image)
        image = Image.open(image_buffer)

        # Convert RGBA images to RGB
        if image.mode == "RGBA":
            image = image.convert("RGB")

        # Resize the image to have the same height as max_height while preserving the aspect ratio
        width = int(image.width * (max_height / image.height))
        image = image.resize((width, max_height), Image.LANCZOS)

        # Convert the image back to numpy array
        image = np.array(image)

        images.append(image)

    # Concatenate images horizontally and normalize image data
    concatenated_image = np.concatenate(images, axis=1)
    if concatenated_image.dtype == np.float32 or concatenated_image.dtype == np.float64:
        concatenated_image = np.clip(concatenated_image, 0, 1)
    else:
        concatenated_image = np.clip(concatenated_image, 0, 255)

    plt.imshow(concatenated_image)
    plt.axis("off")
    plt.box(False)
    plt.show()


def cache_request(cache: Cache, params: Any, values: Any = None) -> Any:
    # Generate a unique key for the request

    key = hashlib.md5(json.dumps(params, sort_keys=True).encode("utf-8")).hexdigest()
    # Check if the request is cached
    if key in cache and values is None:
        print("retrieving from cache")
        return cache[key]

    # Cache the provided values and return them
    if values:
        print("saving to cache")
        cache[key] = values
    return values


def clean_code_snippet(code_string):
    # Extract code snippet using regex
    cleaned_snippet = re.search(r"```(?:\w+)?\s*([\s\S]*?)\s*```", code_string)

    if cleaned_snippet:
        cleaned_snippet = cleaned_snippet.group(1)
    else:
        cleaned_snippet = code_string

    # remove non-printable characters
    cleaned_snippet = re.sub(r"[\x00-\x1F]+", " ", cleaned_snippet)

    return cleaned_snippet


def is_within_max_length(chart_data: list, maximum_length: int) -> bool:
    for data in chart_data:
        if len(data) > maximum_length:
            return False

    return True


def map_original_list_with_sorted_x(original_x: dict, sorted_x: list):
    sorted_list = []

    for sublist in original_x:
        sorted_sublist = sorted(sublist, key=lambda x: sorted_x.index(x["X_Value"]))
        sorted_list.append(sorted_sublist)

    return sorted_list
