import re
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import seaborn as sns
import squarify
from matplotlib import pyplot as plt
from scipy.interpolate import make_interp_spline


def visualize_group_bar_chart(chart_json: dict, save_path: str):
    categories = []

    for chart_json_key in chart_json:
        if not re.search(r"y([23456789])?Name", chart_json_key, re.IGNORECASE):
            continue
        categories.append(chart_json[chart_json_key])

    if "Y" in chart_json and chart_json["Y"] != []:
        bars1 = chart_json["Y"]
    else:
        bars1 = []

    if "Y2" in chart_json and chart_json["Y2"] != []:
        bars2 = chart_json["Y2"]
    else:
        bars2 = []

    if "Y3" in chart_json and chart_json["Y3"] != []:
        bars3 = chart_json["Y3"]
    else:
        bars3 = []

    if "Y4" in chart_json and chart_json["Y4"] != []:
        bars4 = chart_json["Y4"]
    else:
        bars4 = []

    # Width of each bar
    if bars4 != []:
        bar_width = 0.2
    elif bars3 != []:
        bar_width = 0.3
    elif bars2 != []:
        bar_width = 0.35
    else:
        bar_width = 0.9

    # X positions for the bars
    x = chart_json["X"]

    x_axis: list = []

    # Create the grouped bar chart
    if bars1 != []:
        x_axis = list(range(len(x)))
        plt.bar(range(len(x)), bars1, width=bar_width, label=categories[0])

    if bars2 != []:
        x_axis = [x_val + bar_width for x_val in range(len(x))]
        plt.bar(x_axis, bars2, width=bar_width, label=categories[1])

    if bars3 != []:
        x_axis = [x_val + (2 * bar_width) for x_val in range(len(x))]
        plt.bar(x_axis, bars3, width=bar_width, label=categories[2])

    if bars4 != []:
        x_axis = [x_val + (3 * bar_width) for x_val in range(len(x))]
        plt.bar(x_axis, bars4, width=bar_width, label=categories[3])

    # Set labels and title
    plt.xlabel(chart_json["xAxis"])
    plt.ylabel(chart_json["yAxis"])
    plt.title(chart_json["Chart_Title"])

    # Set xticks and xticklabels
    plt.xticks(range(len(x)), x)
    plt.xticks(rotation=90)

    # Show the legend
    plt.legend()

    # Display the chart
    plt.savefig(
        Path(save_path)
        / f"{chart_json['Chart_Name']} (Position {chart_json['Chart_Position']})",
    )
    plt.close()


def visualize_bar_chart(chart_json: dict, save_path: str):
    plt.bar(chart_json["X"], chart_json["Y"])
    plt.xlabel(chart_json["xAxis_Description"])
    plt.ylabel(chart_json["yAxis_Description"])
    plt.title(chart_json["Chart_Title"])
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(
        Path(save_path)
        / f"{chart_json['Chart_Name']} (Position {chart_json['Chart_Position']})",
    )
    plt.close()


def visualize_column_chart(chart_json: dict, save_path: str):
    plt.barh(chart_json["X"], chart_json["Y"])
    plt.xlabel(chart_json["yAxis_Description"])
    plt.ylabel(chart_json["xAxis_Description"])
    plt.title(chart_json["Chart_Title"])
    plt.xticks(rotation=90)
    plt.tight_layout()

    plt.savefig(
        Path(save_path)
        / f"{chart_json['Chart_Name']} (Position {chart_json['Chart_Position']})",
    )
    plt.close()


def visualize_radar_chart(chart_json: dict, save_path: str):
    labels = chart_json["X"]
    values_Q1 = chart_json["Y"]
    values_Q2 = chart_json.get("Y2", [])
    values_Q3 = chart_json.get("Y3", [])

    num_vars = len(labels)

    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()

    values_Q1 += values_Q1[:1]
    values_Q2 += values_Q2[:1]
    values_Q3 += values_Q3[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(subplot_kw=dict(polar=True))

    ax.fill(angles, values_Q1, color="blue", alpha=0.25, label=chart_json["yName"])
    if values_Q2:
        ax.fill(
            angles,
            values_Q2,
            color="green",
            alpha=0.25,
            label=chart_json["y2Name"],
        )
    if values_Q3:
        ax.fill(angles, values_Q3, color="red", alpha=0.25, label=chart_json["y3Name"])

    plt.legend(loc="upper right")
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    plt.title(chart_json["Chart_Title"])
    plt.xticks(rotation=90)

    plt.savefig(
        Path(save_path)
        / f"{chart_json['Chart_Name']} (Position {chart_json['Chart_Position']})",
    )
    plt.close()


def visualize_pie_chart(chart_json: dict, save_path: str):
    plt.pie(chart_json["Y"], labels=chart_json["X"], autopct="%1.1f%%", startangle=140)
    plt.axis("equal")
    plt.title(chart_json["Chart_Title"])
    plt.xticks(rotation=90)

    plt.savefig(
        Path(save_path)
        / f"{chart_json['Chart_Name']} (Position {chart_json['Chart_Position']})",
    )
    plt.close()


def visualize_pyramid_chart(chart_json: dict, save_path: str):
    data = {"number": chart_json["Y"], "stage": chart_json["X"]}

    fig = px.funnel(data, x="number", y="stage", title=chart_json["Chart_Title"])
    fig.update_layout(
        xaxis_title=chart_json["xAxis_Description"],
        yaxis_title=chart_json["yAxis_Description"],
    )

    fig.savefig(
        Path(save_path)
        / f"{chart_json['Chart_Name']} (Position {chart_json['Chart_Position']})",
    )
    plt.close()


def visualize_area_chart(chart_json: dict, save_path: str):
    x = chart_json["X"]
    y1 = chart_json["Y"]
    y2 = chart_json.get("Y2", [])
    y3 = chart_json.get("Y3", [])

    # All arrays should have the same length
    max_len = max(len(y1), len(y2), len(y3))
    y1 += [0] * (max_len - len(y1))
    y2 += [0] * (max_len - len(y2))
    y3 += [0] * (max_len - len(y3))

    plt.stackplot(
        x,
        y1,
        y2,
        y3,
        labels=[
            chart_json["yName"],
            chart_json.get("y2Name", ""),
            chart_json.get("y3Name", ""),
        ],
    )
    plt.legend(loc="upper left")
    plt.xlabel(chart_json["xAxis_Description"])
    plt.ylabel(chart_json["yAxis_Description"])
    plt.title(chart_json["Chart_Title"])
    plt.xticks(rotation=90)

    plt.savefig(
        Path(save_path)
        / f"{chart_json['Chart_Name']} (Position {chart_json['Chart_Position']})",
    )
    plt.close()


def visualize_histogram_chart(chart_json: dict, save_path: str):
    data = chart_json["data"][0]["data"]
    x_values = [entry["x"] for entry in data]
    y_values = [entry["y"] for entry in data]

    # Flatten x and y values based on their frequencies
    repeated_x = [val for val, freq in zip(x_values, y_values) for _ in range(freq)]

    # Plotting the histogram
    plt.hist(repeated_x, bins=len(x_values), edgecolor="black", alpha=0.7)
    plt.xlabel(chart_json["Chart_Axis"]["xAxis_title"])  # Label X-axis
    plt.ylabel(chart_json["yAxis_Description"])  # Label Y-axis
    plt.title(chart_json["Visual_Title"])  # Set chart title
    plt.grid(True)
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(
        Path(save_path)
        / f"{chart_json['Chart_Name']} (Position {chart_json['Chart_Position']})",
    )
    plt.close()


def visualize_group_column_chart(chart_json: dict, save_path: str):
    categories = []

    for chart_json_key in chart_json:
        if not re.search(r"y([23456789])?Name", chart_json_key, re.IGNORECASE):
            continue
        categories.append(chart_json[chart_json_key])

    if "Y" in chart_json and chart_json["Y"] != []:
        bars1 = chart_json["Y"]
    else:
        bars1 = []

    if "Y2" in chart_json and chart_json["Y2"] != []:
        bars2 = chart_json["Y2"]
    else:
        bars2 = []

    if "Y3" in chart_json and chart_json["Y3"] != []:
        bars3 = chart_json["Y3"]
    else:
        bars3 = []

    if "Y4" in chart_json and chart_json["Y4"] != []:
        bars4 = chart_json["Y4"]
    else:
        bars4 = []

    # Width of each bar
    if bars4 != []:
        bar_width = 0.2
    elif bars3 != []:
        bar_width = 0.3
    elif bars2 != []:
        bar_width = 0.35
    else:
        bar_width = 0.9

    # X positions for the bars
    x = chart_json["X"]

    x_axis: list = []

    # Create the grouped bar chart
    if bars1 != []:
        x_axis = list(range(len(x)))
        plt.barh(x_axis, bars1, height=bar_width, label=categories[0])

    if bars2 != []:
        x_axis = [x_val + bar_width for x_val in x_axis]
        plt.barh(x_axis, bars2, height=bar_width, label=categories[1])

    if bars3 != []:
        x_axis = [x_val + bar_width for x_val in x_axis]
        plt.barh(x_axis, bars3, height=bar_width, label=categories[2])

    if bars4 != []:
        x_axis = [x_val + bar_width for x_val in x_axis]
        plt.barh(x_axis, bars4, height=bar_width, label=categories[3])

    # Set labels and title
    plt.xlabel(chart_json["yAxis"])
    plt.ylabel(chart_json["xAxis"])
    plt.title(chart_json["Chart_Title"])

    # Set yticks and yticklabels
    plt.yticks(range(len(x)), x)
    plt.xticks(rotation=90)

    # Show the legend
    plt.legend()

    # Display the chart
    plt.savefig(
        Path(save_path)
        / f"{chart_json['Chart_Name']} (Position {chart_json['Chart_Position']})",
    )
    plt.close()


def visualize_treemap_chart(chart_json: dict, save_path: str):
    labels = []
    values = []

    if "X" in chart_json and chart_json["X"] != []:
        labels.extend(chart_json["X"])

    if "X2" in chart_json and chart_json["X2"] != []:
        labels.extend(chart_json["X2"])

    if "X3" in chart_json and chart_json["X3"] != []:
        labels.extend(chart_json["X3"])

    if "Y" in chart_json and chart_json["Y"] != []:
        values.extend(chart_json["Y"])

    if "Y2" in chart_json and chart_json["Y2"] != []:
        values.extend(chart_json["Y2"])

    if "Y3" in chart_json and chart_json["Y3"] != []:
        values.extend(chart_json["Y3"])

    data = {"labels": labels, "values": values}
    df = pd.DataFrame(data)

    sns.set_style(style="whitegrid")  # set seaborn plot style
    sizes = df["values"].values  # proportions of the categories
    label = df["labels"]

    squarify.plot(sizes=sizes, label=label, alpha=0.6).set(
        title="Treemap with Squarify",
    )
    plt.axis("off")
    plt.xticks(rotation=90)
    plt.savefig(
        Path(save_path)
        / f"{chart_json['Chart_Name']} (Position {chart_json['Chart_Position']})",
    )
    plt.close()


def visualize_line_chart(chart_json: dict, save_path: str):
    if "Y" in chart_json and chart_json["Y"] != []:
        line1_data = chart_json["Y"]
    else:
        line1_data = []

    if "Y2" in chart_json and chart_json["Y2"] != []:
        line2_data = chart_json["Y2"]
    else:
        line2_data = []

    if "Y3" in chart_json and chart_json["Y3"] != []:
        line3_data = chart_json["Y3"]
    else:
        line3_data = []

    if "Y4" in chart_json and chart_json["Y4"] != []:
        line4_data = chart_json["Y4"]
    else:
        line4_data = []

    if "Y5" in chart_json and chart_json["Y5"] != []:
        line5_data = chart_json["Y5"]
    else:
        line5_data = []

    if "Y6" in chart_json and chart_json["Y6"] != []:
        line6_data = chart_json["Y6"]
    else:
        line6_data = []

    if "Y7" in chart_json and chart_json["Y7"] != []:
        line7_data = chart_json["Y7"]
    else:
        line7_data = []

    if "Y8" in chart_json and chart_json["Y8"] != []:
        line8_data = chart_json["Y8"]
    else:
        line8_data = []

    if "Y9" in chart_json and chart_json["Y9"] != []:
        line9_data = chart_json["Y9"]
    else:
        line9_data = []

    # Create the line chart
    if line1_data != []:
        plt.plot(chart_json["X"], line1_data, label=chart_json["yName"])

    if line2_data != []:
        plt.plot(chart_json["X"], line2_data, label=chart_json["y2Name"])

    if line3_data != []:
        plt.plot(chart_json["X"], line3_data, label=chart_json["y3Name"])

    if line4_data != []:
        plt.plot(chart_json["X"], line4_data, label=chart_json["y4Name"])

    if line5_data != []:
        plt.plot(chart_json["X"], line5_data, label=chart_json["y5Name"])

    if line6_data != []:
        plt.plot(chart_json["X"], line6_data, label=chart_json["y6Name"])

    if line7_data != []:
        plt.plot(chart_json["X"], line7_data, label=chart_json["y7Name"])

    if line8_data != []:
        plt.plot(chart_json["X"], line8_data, label=chart_json["y8Name"])

    if line9_data != []:
        plt.plot(chart_json["X"], line9_data, label=chart_json["y9Name"])

    # Set labels and title
    plt.xlabel(chart_json["xAxis"])
    plt.ylabel(chart_json["yAxis"])
    plt.title(chart_json["Chart_Title"])
    plt.xticks(rotation=90)

    # Show the legend
    plt.legend()

    # Display the chart
    plt.savefig(
        Path(save_path)
        / f"{chart_json['Chart_Name']} (Position {chart_json['Chart_Position']})",
    )
    plt.close()


def visualize_spline_chart(chart_json: dict, save_path: str):
    if "Y" in chart_json and chart_json["Y"] != []:
        line1_data = chart_json["Y"]
    else:
        line1_data = []

    if "Y2" in chart_json and chart_json["Y2"] != []:
        line2_data = chart_json["Y2"]
    else:
        line2_data = []

    if "Y3" in chart_json and chart_json["Y3"] != []:
        line3_data = chart_json["Y3"]
    else:
        line3_data = []

    if "Y4" in chart_json and chart_json["Y4"] != []:
        line4_data = chart_json["Y4"]
    else:
        line4_data = []

    if "Y5" in chart_json and chart_json["Y5"] != []:
        line5_data = chart_json["Y5"]
    else:
        line5_data = []

    if "Y6" in chart_json and chart_json["Y6"] != []:
        line6_data = chart_json["Y6"]
    else:
        line6_data = []

    if "Y7" in chart_json and chart_json["Y7"] != []:
        line7_data = chart_json["Y7"]
    else:
        line7_data = []

    if "Y8" in chart_json and chart_json["Y8"] != []:
        line8_data = chart_json["Y8"]
    else:
        line8_data = []

    if "Y9" in chart_json and chart_json["Y9"] != []:
        line9_data = chart_json["Y9"]
    else:
        line9_data = []

    # Create the line chart
    if line1_data != []:
        X_Y_Spline1 = make_interp_spline(chart_json["X"], line1_data)
        X_ = np.linspace(chart_json["X"].min(), chart_json["X"].max(), 500)
        Y_ = X_Y_Spline1(X_)
        plt.plot(X_, Y_, label=chart_json["yName"])

    if line2_data != []:
        X_Y_Spline2 = make_interp_spline(chart_json["X"], line2_data)
        X_ = np.linspace(chart_json["X"].min(), chart_json["X"].max(), 500)
        Y_ = X_Y_Spline2(X_)
        plt.plot(X_, Y_, label=chart_json["y2Name"])

    if line3_data != []:
        X_Y_Spline3 = make_interp_spline(chart_json["X"], line3_data)
        X_ = np.linspace(chart_json["X"].min(), chart_json["X"].max(), 500)
        Y_ = X_Y_Spline3(X_)
        plt.plot(X_, Y_, label=chart_json["y3Name"])

    if line4_data != []:
        X_Y_Spline4 = make_interp_spline(chart_json["X"], line4_data)
        X_ = np.linspace(chart_json["X"].min(), chart_json["X"].max(), 500)
        Y_ = X_Y_Spline4(X_)
        plt.plot(X_, Y_, label=chart_json["y4Name"])

    if line5_data != []:
        X_Y_Spline5 = make_interp_spline(chart_json["X"], line5_data)
        X_ = np.linspace(chart_json["X"].min(), chart_json["X"].max(), 500)
        Y_ = X_Y_Spline5(X_)
        plt.plot(X_, Y_, label=chart_json["y5Name"])

    if line6_data != []:
        X_Y_Spline6 = make_interp_spline(chart_json["X"], line6_data)
        X_ = np.linspace(chart_json["X"].min(), chart_json["X"].max(), 500)
        Y_ = X_Y_Spline6(X_)
        plt.plot(X_, Y_, label=chart_json["y6Name"])

    if line7_data != []:
        X_Y_Spline7 = make_interp_spline(chart_json["X"], line7_data)
        X_ = np.linspace(chart_json["X"].min(), chart_json["X"].max(), 500)
        Y_ = X_Y_Spline7(X_)
        plt.plot(X_, Y_, label=chart_json["y7Name"])

    if line8_data != []:
        X_Y_Spline8 = make_interp_spline(chart_json["X"], line8_data)
        X_ = np.linspace(chart_json["X"].min(), chart_json["X"].max(), 500)
        Y_ = X_Y_Spline8(X_)
        plt.plot(X_, Y_, label=chart_json["y8Name"])

    if line9_data != []:
        X_Y_Spline9 = make_interp_spline(chart_json["X"], line9_data)
        X_ = np.linspace(chart_json["X"].min(), chart_json["X"].max(), 500)
        Y_ = X_Y_Spline9(X_)
        plt.plot(X_, Y_, label=chart_json["y9Name"])

    # Set labels and title
    plt.xlabel(chart_json["xAxis"])
    plt.ylabel(chart_json["yAxis"])
    plt.title(chart_json["Chart_Title"])
    plt.xticks(rotation=90)

    # Show the legend
    plt.legend()

    # Display the chart
    plt.savefig(
        Path(save_path)
        / f"{chart_json['Chart_Name']} (Position {chart_json['Chart_Position']})",
    )
    plt.close()


def visualize_combo_chart(chart_json: dict, save_path: str):
    x = chart_json["X"]
    bar_data = chart_json["Y"]
    line_data = chart_json["Y2"]

    # Create the bar chart
    bar_width = 0.35
    plt.bar(x, bar_data, width=bar_width, label=chart_json["yAxis"])

    # Create the line chart on the secondary y-axis
    plt.twinx()
    plt.plot(
        x,
        line_data,
        marker="o",
        linestyle="-",
        color="r",
        label=chart_json["y2Axis"],
    )

    # Set labels and title
    plt.xlabel(chart_json["xAxis"])
    plt.ylabel(chart_json["yAxis"])
    plt.title(chart_json["Chart_Title"])
    plt.xticks(rotation=90)

    # Show the legend
    plt.legend(loc="upper left")

    # Display the chart
    plt.savefig(
        Path(save_path)
        / f"{chart_json['Chart_Name']} (Position {chart_json['Chart_Position']})",
    )
    plt.close()


def visualize_table_chart(chart_json: dict, save_path: str):
    # Create a DataFrame
    df = pd.DataFrame(chart_json["data"])

    # Create a table chart
    fig, ax = plt.subplots()
    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        loc="center",
        cellLoc="center",
    )

    # Adjust table appearance
    table.auto_set_font_size(False)
    table.set_fontsize(24)
    table.auto_set_column_width(col=list(range(len(df.columns))))

    # Hide axes and ticks
    ax.axis("off")

    # Display the chart
    plt.savefig(
        Path(save_path)
        / f"{chart_json['Chart_Name']} (Position {chart_json['Chart_Position']})",
    )
    plt.close()


CHART_VISUALIZER_FUNCTIONS = {
    "bar_chart": visualize_bar_chart,  # done
    "column_chart": visualize_column_chart,  # done
    "barlinecombo_chart": visualize_combo_chart,  # done
    "line_chart": visualize_line_chart,  # done
    "spline_chart": visualize_line_chart,  # changed to line chart
    "grouped_column_chart": visualize_group_column_chart,  # done
    "grouped_bar_chart": visualize_group_bar_chart,  # done
    "radar_chart": visualize_radar_chart,  # done
    "histogram_chart": visualize_histogram_chart,  # done
    "area_chart": visualize_area_chart,  # done
    "pie_chart": visualize_pie_chart,  # done
    "pyramidfunnel_chart": visualize_pyramid_chart,  # done
    "TreemapMulti_chart": visualize_treemap_chart,  # done
    "table_chart": visualize_table_chart,  # done
    "full_table_chart": visualize_table_chart,  # done
    "aggregated_table_chart": visualize_table_chart,  # done
}
