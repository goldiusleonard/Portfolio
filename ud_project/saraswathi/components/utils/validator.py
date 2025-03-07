import re


def validate_and_fix_xAxis_title(xAxis_title: str, data: list) -> str:
    patterns = {
        "Year": r"^\d{4}$",
        "Half-Year": r"^\d{4}-H[1-2]$",
        "Quarter": r"^\d{4}-Q[1-4]$",
        "Month": r"^\d{4}-M\d{1,2}$",
        "Week": r"^\d{4}-W\d{1,2}$",
        "Day": r"^\d{4}-\d{2}-\d{2}$",
    }

    # Ensure all data items are strings
    for item in data:
        if not isinstance(item, str):
            return xAxis_title

    if xAxis_title in patterns and all(
        re.match(patterns[xAxis_title], item) for item in data
    ):
        return xAxis_title

    for correct_title, pattern in patterns.items():
        if all(re.match(pattern, item) for item in data):
            return correct_title

    return xAxis_title
