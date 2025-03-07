import sys

sys.stdout.reconfigure(encoding="utf-8")
from datetime import datetime


def timestamp_generation():
    formmated_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return formmated_timestamp


# Define a function to handle missing values
def handle_missing_value(value, default="None"):
    """Returns the value if it exists, otherwise returns the default value."""
    return value if value else default


# Function to display a progress bar
def display_progress_bar(current, total, bar_length=20):
    percent = float(current) * 100 / total
    bar_fill = int(round(bar_length * percent / 100))
    bar = "#" * bar_fill + "-" * (bar_length - bar_fill)
    sys.stdout.write("\rProgress: [%s] %.2f%%" % (bar, percent))
    sys.stdout.flush()
