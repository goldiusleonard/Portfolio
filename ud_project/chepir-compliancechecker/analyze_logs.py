# Log Analysis Tool for Chepir API
# Analyzes request processing times from log files and generates visualization.

import glob
import numpy as np
import os
import re

from datetime import datetime
from matplotlib import pyplot as plt
from typing import List


# Find all API log files including rotated ones (*.log and *.log.1-5)
def find_log_files(log_dir: str = "logs") -> List[str]:
    base_pattern = os.path.join(log_dir, "chepir_api_v2_*.log*")
    log_files = [
        f
        for f in glob.glob(base_pattern)
        if os.path.isfile(f)
        and (f.endswith(".log") or any(f.endswith(f".log.{i}") for i in range(1, 6)))
    ]
    return sorted(log_files, key=os.path.getmtime, reverse=True)


# Extract processing times from API log files (matching 'Request processed in X.XXs')
def extract_processing_times(log_files: List[str]) -> List[float]:
    times = []
    pattern = r"Request processed in (\d+\.\d+)s"

    for log_file in log_files:
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                times.extend(
                    [
                        float(match.group(1))
                        for line in f
                        if (match := re.search(pattern, line))
                    ]
                )
        except Exception as e:
            print(f"Error processing {log_file}: {str(e)}")

    return times


# Generate histogram visualization of processing times (with stats overlay)
def plot_histogram(times: List[float], output_dir: str = "output"):
    if not times:
        print("No processing times found in logs")
        return

    # Setup
    os.makedirs(output_dir, exist_ok=True)
    plt.figure(figsize=(12, 6))

    # Calculate statistics
    mean_time = np.mean(times)
    median_time = np.median(times)

    # Calculate integer-based bins
    max_time = int(np.ceil(max(times)))
    bins = range(0, max_time + 2)

    # Create histogram with integer bins
    plt.hist(times, bins=bins, edgecolor="black", align="left")
    plt.title("Distribution of Chepir Agent Processing Times")
    plt.xlabel("Processing Time (seconds)")
    plt.ylabel("Number of Requests")

    # Set x-axis ticks to integers
    plt.xticks(bins)

    # Add grid lines at integer positions
    plt.grid(True, axis="x", alpha=0.3)

    # Add statistical overlays
    plt.axvline(
        mean_time,
        color="red",
        linestyle="dashed",
        linewidth=1,
        label=f"Mean: {mean_time:.2f}s",
    )
    plt.axvline(
        median_time,
        color="green",
        linestyle="dashed",
        linewidth=1,
        label=f"Median: {median_time:.2f}s",
    )

    # Add stats box
    plt.text(
        0.95,
        0.95,
        f"Total Requests: {len(times)}\n"
        f"Mean Time: {mean_time:.2f}s\n"
        f"Median Time: {median_time:.2f}s\n"
        f"Min Time: {min(times):.2f}s\n"
        f"Max Time: {max(times):.2f}s",
        transform=plt.gca().transAxes,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )

    # Finalize plot
    plt.legend()

    # Save and display
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"chepir_processing_times_{timestamp}.png")
    plt.savefig(output_path)
    print(f"Histogram saved to: {output_path}")
    plt.show()


def main():
    # Find and validate log files
    log_files = find_log_files()
    if not log_files:
        print("No log files found matching pattern 'chepir_api_v2_*.log*'")
        return

    print(f"Found {len(log_files)} log files:")
    for f in log_files:
        print(f"- {f}")

    # Process files and generate visualization
    times = extract_processing_times(log_files)
    if times:
        print(f"\nExtracted {len(times)} processing times")
        plot_histogram(times)
    else:
        print("No processing times found in log files")


if __name__ == "__main__":
    main()
