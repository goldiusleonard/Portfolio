import json
import os
import requests
import numpy as np
import pandas as pd
import logging

from typing import Any
from time import perf_counter
from .utils import calculate_token_usage
from logging_library.performancelogger.performance_logger import PerformanceLogger

VISUAL_INSIGHT_TEMPLATE = {
    "Subscription_ID": "",
    "Subscription_Name": "",
    "Client_ID": "",
    "User_ID": "",
    "Shared_User_ID": "",
    "Chart_Name": "",
    "Chart_Type": "text_content",
    "Chart_Position": "",
    "Chart_Title": "Visual Description",
    "Card_Content": "",
}

BUSINESS_RECOMMENDATION_TEMPLATE = {
    "Subscription_ID": "",
    "Subscription_Name": "",
    "Client_ID": "starhub_001",
    "User_ID": "goldius.leo@userdata.tech",
    "Shared_User_ID": "",
    "Chart_Name": "",
    "Chart_Type": "text_content",
    "Chart_Position": "",
    "Chart_Title": "Business recommendation",
    "Card_Content": "",
}


def generate_visual_description(
    llama70b_client: Any,
    user_query: str,
    chart_data: dict,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    chart_data_final = chart_data.copy()

    if "Subscription_ID" in chart_data_final.keys():
        del chart_data_final["Subscription_ID"]

    if "Subscription_Name" in chart_data_final.keys():
        del chart_data_final["Subscription_Name"]

    if "User_ID" in chart_data_final.keys():
        del chart_data_final["User_ID"]

    if "Shared_User_ID" in chart_data_final.keys():
        del chart_data_final["Shared_User_ID"]

    if "Chart_Name" in chart_data_final.keys():
        del chart_data_final["Chart_Name"]

    if "Chart_Query" in chart_data_final.keys():
        del chart_data_final["Chart_Query"]

    if "Chart_SQL_Library" in chart_data_final.keys():
        del chart_data_final["Chart_SQL_Library"]

    if "Chart_Position" in chart_data_final.keys():
        del chart_data_final["Chart_Position"]

    if "Client_ID" in chart_data_final.keys():
        del chart_data_final["Client_ID"]

    if "Visual_Title" in chart_data_final.keys():
        del chart_data_final["Visual_Title"]

    if "Chart_ID" in chart_data_final.keys():
        del chart_data_final["Chart_ID"]

    if "Aggregated_Table_JSON" in chart_data_final.keys():
        del chart_data_final["Aggregated_Table_JSON"]

    if "Aggregated_Table_Column" in chart_data_final.keys():
        del chart_data_final["Aggregated_Table_Column"]

    if "Database_Identifier" in chart_data_final.keys():
        del chart_data_final["Database_Identifier"]

    if chart_data_final["Chart_Type"] == "scatterplot_chart":
        summary_report = summarize_scatterplot_data(chart_data_final["Chart_Data"])
        chart_data_final["Summary_Report"] = summary_report
        del chart_data_final["Chart_Data"]

    if chart_data_final["Chart_Type"] == "bubbleplot_chart":
        summary_report = summarize_bubbleplot_data(chart_data_final["Chart_Data"])
        chart_data_final["Summary_Report"] = summary_report
        del chart_data_final["Chart_Data"]

    if chart_data_final["Chart_Type"] == "histogram_chart":
        data_values = [item["X_Value"] for item in chart_data_final["Chart_Data"]]

        n_bins = chart_data_final["Number_of_Bins"]["sturges"]
        hist, bin_edges = np.histogram(data_values, bins=n_bins)
        binned_data = {"Bins": bin_edges.tolist(), "Counts": hist.tolist()}
        chart_data_final["Binned_Data"] = binned_data
        del chart_data_final["Chart_Data"]

        chart_data_final_str = json.dumps(chart_data_final)

        system_prompt = """Instructions:
- Examine the provided JSON data for the chart and summarize the key insights in bullet points limited to ONLY 3 concise points.
- Each point should clearly identify trends, patterns, or significant values. Focusing on the most critical data.
- When relevant, convert any time-based data into natural language (e.g., using month and year names). 
- Round decimal values appropriately.
- Avoid mentioning currency unless explicitly stated in the axis label.
- DO NOT mention the x-axis and y-axis label.
- Be concise, highlighting only the most impactful observations. Do not include sentences before the bullet points.
- Ensure the mathematic operations are done correct especially during numerical value comparison.
- Please think step by step. DO NOT Hallucinate.
- **Prioritize the analysis of overall data trends and insights while strictly avoiding any mention of specific bin details related to the histogram. This includes refraining from discussing how bins are defined, their ranges, or any numerical thresholds that pertain to binning. This focus is essential for maintaining clarity and ensuring that the insights are directly relevant to the broader data narrative. Avoid any mention of bins or related details.**"""

        user_prompt = f"""Examine the JSON chart data provided and extract the key insights to address the user intent outlined below.

JSON Chart Data:
{chart_data_final_str}

User Intent: {user_query}

"""

    elif chart_data_final["Chart_Type"] == "card_chart":
        chart_data_final_str = json.dumps(chart_data_final)

        system_prompt = """Instructions:
- Examine the provided JSON data for the chart and summarize the key insights in bullet points limited to ONLY 2 concise points.
- When relevant, convert any time-based data into natural language (e.g., using month and year names).
- Round decimal values appropriately.
- Avoid mentioning currency unless explicitly stated in the axis label.
- DO NOT mention the x-axis and y-axis label.
- Be concise, highlighting only the most impactful observations. Do not include sentences before the bullet points.
- Please think step by step. DO NOT Hallucinate.

Please verify the following:
- Each metric is correctly calculated based on the given values.
- The insights match the data provided.
- Ensure all values, trends, and calculations are accurately reflected in the description, with no discrepancies between the data points and the stated metrics.

"""

        user_prompt = f"""Examine the JSON chart data provided and extract the key insights to address the user intent outlined below.

JSON Chart Data:
{chart_data_final_str}

User Intent: {user_query}

"""

    else:
        chart_data_final_str = json.dumps(chart_data_final)

        system_prompt = """Instructions:
- Examine the provided JSON data for the chart and summarize the key insights in bullet points limited to ONLY 3 concise points.
- When relevant, convert any time-based data into natural language (e.g., using month and year names). 
- Round decimal values appropriately.
- Avoid mentioning currency unless explicitly stated in the axis label.
- DO NOT mention the x-axis and y-axis label.
- Be concise, highlighting only the most impactful observations. Do not include sentences before the bullet points.
- Ensure the mathematic operations are done correct especially during numerical value comparison.
- Please think step by step. DO NOT Hallucinate."""

        user_prompt = f"""Examine the JSON chart data provided and extract the key insights to address the user intent outlined below.

JSON Chart Data:
{chart_data_final_str}

User Intent: {user_query}

"""
    start_narrative = perf_counter()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    visual_description = llama70b_client.chat.completions.create(
        model=os.getenv("LLAMA70B_MODEL"),
        messages=messages,
        max_tokens=1000,
        temperature=0.5,
    )
    visual_description = visual_description.choices[0].message.content

    input_tokens = 0
    output_tokens = 0

    input_tokens = calculate_token_usage(system_prompt) + calculate_token_usage(
        user_prompt
    )
    output_tokens = calculate_token_usage(visual_description)

    visual_description_inference_time = perf_counter() - start_narrative

    MODULEID_GENERATE_VISUAL_DESCRIPTION = os.getenv(
        "MODULEID_GENERATE_VISUAL_DESCRIPTION", ""
    )

    if MODULEID_GENERATE_VISUAL_DESCRIPTION == "":
        code_level_logger.error("MODULEID_GENERATE_VISUAL_DESCRIPTION is invalid!")
        raise ValueError("MODULEID_GENERATE_VISUAL_DESCRIPTION is invalid!")

    formatted_data = {
        "chart_id": chart_data["Chart_ID"],
        "module_id": int(MODULEID_GENERATE_VISUAL_DESCRIPTION),
        "messages": messages,
        "output": visual_description,
        "inference_time": visual_description_inference_time,
        "llm_model": os.getenv("LLAMA70B_MODEL"),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }

    logging_llm_url = logging_url + "chart-llm-calls"
    requests.put(logging_llm_url, json=formatted_data, verify=False)

    visual_description = (
        visual_description.replace("**", "").replace("*", "").replace("•", "").strip()
    )

    log_chart_insight = {
        "chart_id": chart_data["Chart_ID"],
        "visual_description": visual_description,
    }

    logging_insights_url = logging_url + "insights"
    requests.put(logging_insights_url, json=log_chart_insight, verify=False)

    return visual_description


def generate_visual_description_chart(
    llama70b_client: Any,
    user_query: str,
    chart_data: dict,
    logging_url: str,
    session_id: str,
    code_level_logger: logging.Logger,
    chart_position: int = 2,
):
    with PerformanceLogger(session_id):
        visual_description_chart = VISUAL_INSIGHT_TEMPLATE.copy()

        visual_description_chart["Subscription_ID"] = chart_data["Subscription_ID"]
        visual_description_chart["Subscription_Name"] = chart_data["Subscription_Name"]
        visual_description_chart["Client_ID"] = chart_data["Client_ID"]
        visual_description_chart["User_ID"] = chart_data["User_ID"]
        visual_description_chart["Shared_User_ID"] = chart_data["Shared_User_ID"]
        visual_description_chart["Chart_Name"] = chart_data["Chart_Name"]
        visual_description_chart["Chart_Position"] = str(chart_position)
        visual_description_chart["Chart_Title"] = "Visual Description"
        visual_description_chart["Card_Content"] = generate_visual_description(
            llama70b_client,
            user_query,
            chart_data,
            logging_url,
            code_level_logger,
        )

        return visual_description_chart


def generate_business_recommendation(
    llama70b_client: Any,
    user_query: str,
    chart_data: dict,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    chart_data_final = chart_data.copy()

    if "Subscription_ID" in chart_data_final.keys():
        del chart_data_final["Subscription_ID"]

    if "Subscription_Name" in chart_data_final.keys():
        del chart_data_final["Subscription_Name"]

    if "User_ID" in chart_data_final.keys():
        del chart_data_final["User_ID"]

    if "Shared_User_ID" in chart_data_final.keys():
        del chart_data_final["Shared_User_ID"]

    if "Chart_Name" in chart_data_final.keys():
        del chart_data_final["Chart_Name"]

    if "Chart_Query" in chart_data_final.keys():
        del chart_data_final["Chart_Query"]

    if "Chart_SQL_Library" in chart_data_final.keys():
        del chart_data_final["Chart_SQL_Library"]

    if "Chart_Position" in chart_data_final.keys():
        del chart_data_final["Chart_Position"]

    if "Client_ID" in chart_data_final.keys():
        del chart_data_final["Client_ID"]

    if "Visual_Title" in chart_data_final.keys():
        del chart_data_final["Visual_Title"]

    if "Chart_ID" in chart_data_final.keys():
        del chart_data_final["Chart_ID"]

    if "Aggregated_Table_JSON" in chart_data_final.keys():
        del chart_data_final["Aggregated_Table_JSON"]

    if "Aggregated_Table_Column" in chart_data_final.keys():
        del chart_data_final["Aggregated_Table_Column"]

    if "Database_Identifier" in chart_data_final.keys():
        del chart_data_final["Database_Identifier"]

    if chart_data_final["Chart_Type"] == "scatterplot_chart":
        summary_report = summarize_scatterplot_data(chart_data_final["Chart_Data"])
        chart_data_final["Summary_Report"] = summary_report
        del chart_data_final["Chart_Data"]

    if chart_data_final["Chart_Type"] == "bubbleplot_chart":
        summary_report = summarize_bubbleplot_data(chart_data_final["Chart_Data"])
        chart_data_final["Summary_Report"] = summary_report
        del chart_data_final["Chart_Data"]

    if chart_data_final["Chart_Type"] == "histogram_chart":
        data_values = [item["X_Value"] for item in chart_data_final["Chart_Data"]]

        n_bins = chart_data_final["Number_of_Bins"]["sturges"]
        hist, bin_edges = np.histogram(data_values, bins=n_bins)
        binned_data = {"Bins": bin_edges.tolist(), "Counts": hist.tolist()}
        chart_data_final["Binned_Data"] = binned_data
        del chart_data_final["Chart_Data"]

        chart_data_final_str = json.dumps(chart_data_final)

        system_prompt = """Instructions:
- Craft a concise business recommendation based on the provided chart data.
- Focus on identifying key trends, patterns, and potential causes with referencing specific data points or technical chart elements. Highlight the strategic implications and suggest direct actions.
- Discuss possible causes and suggest specific actions to address these trends, with referencing numbers or chart labels. 
- Ensure the recommendation is clear, impactful, does not exceed 450 characters, and only in one paragraph.
- Avoid mentioning currency unless explicitly stated in the axis label.
- Do not include sentences before the paragraph.
- Please think step by step. DO NOT Hallucinate.
- **Prioritize the analysis of overall data trends and insights while strictly avoiding any mention of specific bin details related to the histogram. This includes refraining from discussing how bins are defined, their ranges, or any numerical thresholds that pertain to binning. This focus is essential for maintaining clarity and ensuring that the insights are directly relevant to the broader data narrative. Avoid any mention of bins or related details.**"""

        user_prompt = f"""Review the JSON chart data below and offer a business recommendation based on the insights to fulfill the user intent provided.

JSON Chart Data:
{chart_data_final_str}

User Intent: {user_query}

    """
    else:
        chart_data_final_str = json.dumps(chart_data_final)

        system_prompt = """Instructions:
    - Craft a concise business recommendation based on the provided chart data.
    - Focus on identifying key trends, patterns, and potential causes with referencing specific data points or technical chart elements. Highlight the strategic implications and suggest direct actions.
    - Discuss possible causes and suggest specific actions to address these trends, with referencing numbers or chart labels. 
    - Ensure the recommendation is clear, impactful, does not exceed 450 characters, and only in one paragraph.
    - Avoid mentioning currency unless explicitly stated in the axis label.
    - Do not include sentences before the paragraph.
    - Please think step by step. DO NOT Hallucinate."""

    user_prompt = f"""Review the JSON chart data below and offer a business recommendation based on the insights to fulfill the user intent provided.

JSON Chart Data:
{chart_data_final_str}

User Intent: {user_query}

    """
    start_narrative = perf_counter()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    business_recommendation = llama70b_client.chat.completions.create(
        model=os.getenv("LLAMA70B_MODEL"),
        messages=messages,
        max_tokens=1000,
        temperature=0.5,
    )

    business_recommendation = business_recommendation.choices[0].message.content

    input_tokens = 0
    output_tokens = 0

    input_tokens = calculate_token_usage(system_prompt) + calculate_token_usage(
        user_prompt
    )
    output_tokens = calculate_token_usage(business_recommendation)

    business_recommendation_inference_time = perf_counter() - start_narrative

    MODULEID_GENERATE_BUSINESS_RECOMMENDATION = os.getenv(
        "MODULEID_GENERATE_BUSINESS_RECOMMENDATION", ""
    )

    if MODULEID_GENERATE_BUSINESS_RECOMMENDATION == "":
        code_level_logger.error("MODULEID_GENERATE_BUSINESS_RECOMMENDATION is invalid!")
        raise ValueError("MODULEID_GENERATE_BUSINESS_RECOMMENDATION is invalid!")

    formatted_data = {
        "chart_id": chart_data["Chart_ID"],
        "module_id": int(MODULEID_GENERATE_BUSINESS_RECOMMENDATION),
        "messages": messages,
        "output": business_recommendation,
        "inference_time": business_recommendation_inference_time,
        "llm_model": os.getenv("LLAMA70B_MODEL"),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }

    logging_llm_url = logging_url + "chart-llm-calls"
    requests.put(logging_llm_url, json=formatted_data, verify=False)

    if "**" in business_recommendation:
        business_recommendation = business_recommendation.replace("**", "")

    log_chart_insight = {
        "chart_id": chart_data["Chart_ID"],
        "business_recommendation": business_recommendation,
    }

    logging_insights_url = logging_url + "insights"
    requests.put(logging_insights_url, json=log_chart_insight, verify=False)

    return business_recommendation


def generate_business_recommendation_chart(
    llama70b_client: Any,
    user_query: str,
    chart_data: dict,
    logging_url: str,
    session_id: str,
    code_level_logger: logging.Logger,
    chart_position: int = 3,
):
    with PerformanceLogger(session_id):
        business_recommendation_chart = BUSINESS_RECOMMENDATION_TEMPLATE.copy()

        business_recommendation_chart["Subscription_ID"] = chart_data["Subscription_ID"]
        business_recommendation_chart["Subscription_Name"] = chart_data[
            "Subscription_Name"
        ]
        business_recommendation_chart["Client_ID"] = chart_data["Client_ID"]
        business_recommendation_chart["User_ID"] = chart_data["User_ID"]
        business_recommendation_chart["Shared_User_ID"] = chart_data["Shared_User_ID"]
        business_recommendation_chart["Chart_Name"] = chart_data["Chart_Name"]
        business_recommendation_chart["Chart_Position"] = str(chart_position)
        business_recommendation_chart["Chart_Title"] = "Business Recommendation"
        business_recommendation_chart["Card_Content"] = (
            generate_business_recommendation(
                llama70b_client,
                user_query,
                chart_data,
                logging_url,
                code_level_logger,
            )
        )

        return business_recommendation_chart


def summarize_bubbleplot_data(data: list) -> str:
    """The function `summarize_bubbleplot_data` processes input data to generate statistical summaries and
    visual representations for bubble plot analysis.

    :param data: A list of dictionaries representing bubble plot data. Each dictionary should include
    keys like 'X_Value', 'Y_Value', 'Z_Value', and 'Group_Name'.
    :type data: list
    :return: A formatted summary report template containing statistical insights and tables based on
    the input bubble plot data. The report includes statistics for X_Value, Y_Value, and Z_Value
    (such as min, max, mean, std dev, and percentiles), and group-wise statistics.
    """
    df = pd.DataFrame(data)

    # Basic statistical insights for X, Y, and Z
    x_min, x_max, x_mean, x_std = (
        df["X_Value"].min(),
        df["X_Value"].max(),
        df["X_Value"].mean(),
        df["X_Value"].std(),
    )
    y_min, y_max, y_mean, y_std = (
        df["Y_Value"].min(),
        df["Y_Value"].max(),
        df["Y_Value"].mean(),
        df["Y_Value"].std(),
    )
    z_min, z_max, z_mean, z_std = (
        df["Z_Value"].min(),
        df["Z_Value"].max(),
        df["Z_Value"].mean(),
        df["Z_Value"].std(),
    )

    # Group-wise statistics for X_Value, Y_Value, and Z_Value
    group_stats = (
        df.groupby("Group_Name")
        .agg(
            {
                "X_Value": ["min", "max", "mean", "std"],
                "Y_Value": ["min", "max", "mean", "std"],
                "Z_Value": ["min", "max", "mean", "std"],
            },
        )
        .reset_index()
    )

    # Quantiles (25th, 50th, 75th percentiles)
    x_quantiles = df["X_Value"].quantile([0.25, 0.5, 0.75]).to_list()
    y_quantiles = df["Y_Value"].quantile([0.25, 0.5, 0.75]).to_list()
    z_quantiles = df["Z_Value"].quantile([0.25, 0.5, 0.75]).to_list()

    summary_report_template = f"""
    Summary for Bubble Plot Chart Data:
    --------------------------------------
    X_Value Statistics:
      - Min: {x_min}
      - Max: {x_max}
      - Mean: {x_mean:.2f}
      - Std Dev: {x_std:.2f}
      - 25th, 50th, 75th Percentiles: {x_quantiles}
      
    Y_Value Statistics:
      - Min: {y_min}
      - Max: {y_max}
      - Mean: {y_mean:.2f}
      - Std Dev: {y_std:.2f}
      - 25th, 50th, 75th Percentiles: {y_quantiles}

    Z_Value (Size) Statistics:
      - Min: {z_min}
      - Max: {z_max}
      - Mean: {z_mean:.2f}
      - Std Dev: {z_std:.2f}
      - 25th, 50th, 75th Percentiles: {z_quantiles}

    Group-wise Statistics:
    {group_stats.to_string(index=False)}
    """

    return summary_report_template


def summarize_scatterplot_data(data: list) -> str:
    """The function `summarize_scatterplot_data` processes input data to generate statistical summaries and
    visual representations for scatterplot analysis.

    :param data: The code you provided defines a function `summarize_scatterplot_data` that takes a list
    of data as input and generates a summary report template based on various statistical calculations
    and data manipulations. The function calculates statistics, performs dynamic binning, computes
    group-wise statistics, creates a confusion matrix-like
    :type data: list
    :return: The function `summarize_scatterplot_data` is returning a formatted summary report template
    containing various statistical insights and tables based on the input scatterplot data. The report
    includes statistics for X_Value and Y_Value (such as min, max, mean, std dev, and percentiles),
    group-wise statistics, and a confusion matrix-like table showing counts of groups in binned ranges.
    """
    df = pd.DataFrame(data)

    # Basic statistical insights
    x_min = df["X_Value"].min()
    x_max = df["X_Value"].max()
    x_mean = df["X_Value"].mean()
    x_std = df["X_Value"].std()

    y_min = df["Y_Value"].min()
    y_max = df["Y_Value"].max()
    y_mean = df["Y_Value"].mean()
    y_std = df["Y_Value"].std()

    # Dynamic binning using the square root rule
    num_bins = int(np.sqrt(len(df)))

    # Generate bins for X_Value and Y_Value
    df["X_Binned"] = pd.cut(df["X_Value"], bins=num_bins)
    df["Y_Binned"] = pd.cut(df["Y_Value"], bins=num_bins)

    # Group-wise statistics for X_Value and Y_Value
    group_stats = (
        df.groupby("Group_Name")
        .agg(
            {
                "X_Value": ["min", "max", "mean", "std"],
                "Y_Value": ["min", "max", "mean", "std"],
            },
        )
        .reset_index()
    )

    # Create confusion matrix-like table
    confusion_matrix = pd.crosstab(
        df["X_Binned"],
        df["Y_Binned"],
        df["Group_Name"],
        aggfunc="count",
    ).fillna(0)

    # Quantiles (25th, 50th, 75th percentiles)
    x_quantiles = df["X_Value"].quantile([0.25, 0.5, 0.75]).to_list()
    y_quantiles = df["Y_Value"].quantile([0.25, 0.5, 0.75]).to_list()

    summary_report_template = f"""
    Summary for Scatterplot Chart Data:
    --------------------------------------
    X_Value Statistics:
      - Min: {x_min}
      - Max: {x_max}
      - Mean: {x_mean:.2f}
      - Std Dev: {x_std:.2f}
      - 25th, 50th, 75th Percentiles: {x_quantiles}
      
    Y_Value Statistics:
      - Min: {y_min}
      - Max: {y_max}
      - Mean: {y_mean:.4f}
      - Std Dev: {y_std:.4f}
      - 25th, 50th, 75th Percentiles: {y_quantiles}

    Group-wise Statistics:
    {group_stats.to_string(index=False)}
    
    Confusion Matrix-Like Table (Counts of Groups in Binned Ranges):
    {confusion_matrix.to_string()}
    """

    return summary_report_template
