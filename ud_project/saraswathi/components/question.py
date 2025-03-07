import ast
import logging
import os
import json
import re
import requests
import traceback

from vers import version
from time import perf_counter
from datetime import datetime
from enum import Enum
from typing import Any, List, Tuple, Union
from .datamodel import DataSummary, StoryNarrative
from .utils import (
    validate_and_add_time_info,
    generate_column_information_prompt,
    calculate_token_usage,
    fetch_feedback,
    filter_feedback,
    filter_by_chart_duration,
    filter_feedback_by_options,
)

from pydantic import BaseModel, Field, RootModel

from logging_library.performancelogger.performance_logger import PerformanceLogger

logger = logging.getLogger(__name__)


class SubQuestionModel(BaseModel):
    question: str = Field(..., description="The sub-question text.")
    chart_title: str = Field(
        ...,
        description="The title of the chart associated with the sub-question.",
    )
    chart_type: Enum = Field(
        ...,
        description="The type of the chart for the sub-question.",
    )
    chart_category: Enum = Field(
        ...,
        description="The category type of the chart for the sub-question.",
    )
    chart_timeframe: Enum = Field(
        ...,
        description="The time frame of the chart for the sub-question.",
    )
    chart_duration: str = Field(
        ...,
        description="The time duration of the chart for the sub-question.",
    )


class ResponseSchema_SubQuestion(RootModel[List[SubQuestionModel]]):
    pass


class MainQuestionModel(BaseModel):
    main_question: str = Field(
        ...,
        description="The primary question or query related to the data being visualized.",
    )
    main_title: str = Field(
        ...,
        description="The descriptive title of the chart that reflects the key insight or data representation for the main question.",
    )
    main_chart_type: Enum = Field(
        ...,
        description="The specific type of chart used to represent the data.",
    )
    main_chart_category: Enum = Field(
        ...,
        description="The chart's category based on its analytical purpose.",
    )
    main_chart_timeframe: Enum = Field(
        ...,
        description="The specific time frame that the chart data covers.",
    )
    main_chart_duration: str = Field(
        ...,
        description="The specific time duration for which the data is presented, indicating the range or span of time.",
    )


class ResponseSchema_MainQuestion(RootModel[List[MainQuestionModel]]):
    pass


class ResponseSchema_NarrativeQuestion(BaseModel):
    narrative: str = Field(..., description="The narrative flow of the charts.")
    main_questions: List[MainQuestionModel]


class OverallTitleModel(BaseModel):
    overarching_title: str = Field(
        ...,
        description="The overarching title for the entire visualization.",
    )


def generate_filter_and_dimension_instructions_d3(
    filters: dict,
) -> Tuple[str, str]:
    """The function generates filter and dimension instructions based on the provided filters dictionary.

    :param filters: filter intended by the user.
    :type filters: dict
    :return: A tuple containing the filter instructions and dimension instructions is being returned.
    """
    if filters == {}:
        FILTER_INSTRUCTIONS: str = ""
        DIMENSION_INSTRUCTIONS: str = ""
    else:
        FILTER_COLUMNS: list = []
        DIMENSION_COLUMNS: list = []

        for filter_key in filters:
            if filters[filter_key] == [] or filters[filter_key] == [""]:
                DIMENSION_COLUMNS.append(filter_key)
            else:
                FILTER_COLUMNS.append(filter_key)

        if FILTER_COLUMNS == []:
            FILTER_INSTRUCTIONS = ""
        else:
            FILTER_INSTRUCTIONS = "Limit the scope of the narrative and main questions to the filter below with other possible scope not removed.\n"

            for filter_column in FILTER_COLUMNS:
                FILTER_INSTRUCTIONS += f"'{filter_column}' = {filters[filter_column]}\n"

        if DIMENSION_COLUMNS == []:
            DIMENSION_INSTRUCTIONS = ""
        else:
            DIMENSION_INSTRUCTIONS = "Always use the database columns below in the narrative.\n\n. Always use the database columns below in each main question.\n\n"

            for dimension_column in DIMENSION_COLUMNS:
                DIMENSION_INSTRUCTIONS += f"- '{dimension_column}'\n"

    return FILTER_INSTRUCTIONS, DIMENSION_INSTRUCTIONS


def generate_aggregation_instructions_d3(
    aggregations: list,
    data_summary: DataSummary,
) -> str:
    """Generates a string of aggregation instructions based on the list of columns provided.

    Parameters
    ----------
    aggregations (list of str): A list of column names to group or aggregate by. If empty, no instructions are returned.

    Returns
    -------
    str: A formatted string with aggregation instructions. If the list is empty, an empty string is returned.

    Example Usage:
    ---------------
    # Example 1: With aggregation columns
    columns = ['region', 'category']
    instructions = generate_aggregation_instructions(columns)
    print(instructions)  # Output: "Group or aggregate the charts planned in the narrative by region, category columns."

    # Example 2: Without aggregation columns (empty list)
    columns = []
    instructions = generate_aggregation_instructions(columns)
    print(instructions)  # Output: ""

    Edge Cases:
    ---------------
    - If `aggregations` is an empty list ([]), the function returns an empty string, as no aggregation instructions are necessary.

    """
    for column in aggregations:
        if data_summary.column_n_unique_value_dict[column] > 12:
            aggregations.remove(column)

    if aggregations == []:
        AGGREGATION_INSTRUCTIONS: str = ""
    else:
        AGGREGATION_INSTRUCTIONS = f"Group or aggregate the charts planned (excluding the histogram chart) in the narrative by {', '.join(aggregations)} columns, and do not limit the charts within the group by or aggregation."

    return AGGREGATION_INSTRUCTIONS


def generate_date_instruction_timeframe_samples_d3(
    data_summary: DataSummary,
    user_query: str,
    code_level_logger: logging.Logger,
) -> Tuple[str, str, list, list]:
    # Date instruction depends on the table contains date-related column
    column_data_tribe_variation = [
        data_summary.column_data_tribes[key].lower()
        for key in data_summary.column_data_tribes.keys()
    ]

    column_data_tribe_variation = list(set(column_data_tribe_variation))

    chart_feedback_data = fetch_feedback("user_query", user_query, code_level_logger)

    liked_feedbacks = filter_feedback(chart_feedback_data, filter_liked=True)

    duration_related_samples, non_duration_related_samples = filter_by_chart_duration(
        liked_feedbacks
    )

    if "date_related" in column_data_tribe_variation:
        DATE_INSTRUCTIONS = """- Ensure that the time frame and time duration are included in both the main question and chart title for charts with a date-related x-axis (e.g., 'Day', 'Week', 'Month', 'Quarter', 'Year', etc.), specifically for time series data, excluding cases related to date of birth, account opening date, or similar fields.
- Ensure chart titles accurately reflect the content and focus of the chart, specifically addressing the main metric, the time frame, and the time duration involved.
- Ensure that the chosen time frame is shorter than the specified time duration.
- Avoid general terms in chart titles; instead, be specific about the metric, time duration, and any relevant dimensions or series in the chart.
- Ensure the time duration is clearly defined and included in both the chart title and the question, specifying the period of data analysis or presentation when a date field is available, except for fields such as date of birth, account opening date, or similar.
- Default time frame: 'Monthly'.
- Default time duration: 'Past One Year'."""

        DATE_INSTRUCTIONS2 = """Consider the following time frames based on the chart type and the insights required:

Daily: Use when analyzing real-time or very short-term data. This is ideal for detecting immediate changes, fluctuations, or behaviors on a day-to-day basis, especially for monitoring dynamic environments like sales or web traffic.
Weekly: Use when analyzing short-term trends or patterns that occur within a single week. This is useful for data that fluctuates frequently or needs close monitoring over a short period.
Monthly: Ideal for observing medium-term trends and changes. Monthly data is suitable for understanding performance, behaviors, or other metrics on a slightly longer timescale.
Quarterly: Choose this time frame for analyzing data in three-month intervals. It's useful for assessing performance or trends over a more extended period, often used in business reporting.
Half-Yearly: Suitable for medium-to-long-term analysis, spanning six months. This time frame is often used for mid-year reviews, capturing trends that need a larger window than quarterly data but still short of an annual overview.
Yearly: Use this time frame for long-term trends and yearly comparisons. It's suitable for annual summaries or understanding data across an entire year."""

        CHART_TIMEFRAME = [
            "Daily",
            "Weekly",
            "Monthly",
            "Half-Yearly",
            "Yearly",
            "Quarterly",
            "",
        ]
        if liked_feedbacks and duration_related_samples:
            # Initialize a list to store the samples
            SAMPLES = []

            # Loop through each entry in liked_feedbacks
            for chart in duration_related_samples:
                # Construct the sample dictionary for each liked feedback item
                sample = {
                    "user_intent": chart.get("user_query", ""),
                    "narrative": chart.get("narrative", ""),
                    "main_questions": [
                        {
                            "main_question": chart.get("question", ""),
                            "main_title": chart.get("chart_title", ""),
                            "main_chart_type": chart.get("chart_type", ""),
                            "main_chart_category": chart.get("chart_category", ""),
                            "main_chart_timeframe": chart.get("time_frame", ""),
                            "main_chart_duration": chart.get("time_duration", ""),
                        }
                    ],
                }

                # Append the constructed sample to the samples list
                SAMPLES.append(sample)
        else:
            SAMPLES = [
                # Line Charts
                {
                    "user_intent": "Analyze the evolution of monthly total cost variance (actual vs budget and actual vs forecast) for the broadband product over the past six months.",
                    "narrative": "Over the past six months, the monthly total cost variance for the broadband product has shown distinct patterns when comparing actual vs budget and actual vs forecast. The line chart visualizes these trends, highlighting periods of alignment or deviation. Key insights from the data reveal fluctuations in cost management, with certain months showing significant variances between the planned and actual expenditures, while others maintain closer adherence to forecasts. This analysis helps identify the effectiveness of budgeting and forecasting strategies in the broadband product's cost management.",
                    "main_questions": [
                        {
                            "main_question": "How have the monthly total cost variance (actual vs budget) and monthly total cost variance (actual vs forecast) for the broadband product evolved over the past six months?",
                            "main_title": "Monthly Total Cost Variance: Actual vs. Budget and Actual vs. Forecast for Broadband Product (Past Six Months)",
                            "main_chart_type": "line_chart",
                            "main_chart_category": "comparison",
                            "main_chart_timeframe": "Monthly",
                            "main_chart_duration": "Past Six Months",
                        }
                    ],
                },
                {
                    "user_intent": "Track the trend in monthly total revenue from premium services over the past 18 months.",
                    "narrative": "The line chart tracks the trend in monthly total revenue from premium services over the past 18 months, showcasing fluctuations and key growth periods.",
                    "main_questions": [
                        {
                            "main_question": "What is the trend in monthly total revenue from premium services over the past 18 months?",
                            "main_title": "Monthly Total Revenue from Premium Services (Past 18 Months)",
                            "main_chart_type": "line_chart",
                            "main_chart_category": "comparison",
                            "main_chart_timeframe": "Monthly",
                            "main_chart_duration": "Past 18 Months",
                        }
                    ],
                },
                # Grouped Bar Charts
                {
                    "user_intent": "Compare the median cost variance (actual vs budget) for entertainment services between the current and previous quarters.",
                    "narrative": "By comparing the median entertainment services' cost variance between the current and previous quarters, the grouped bar chart highlights significant differences in budgeting accuracy. This analysis allows for a deeper understanding of cost management trends and helps identify areas where financial planning has either succeeded or requires improvement.",
                    "main_questions": [
                        {
                            "main_question": "How does the median cost variance (actual vs budget) for entertainment services compare between the current and previous quarters?",
                            "main_title": "Median Cost Variance (Actual vs Budget) for Entertainment Services: Current vs Previous Quarter",
                            "main_chart_type": "grouped_bar_chart",
                            "main_chart_category": "comparison",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "Current and Previous Quarter",
                        }
                    ],
                },
                {
                    "user_intent": "Compare the average revenue per user (ARPU) for the mobile app to the overall ARPU from Q2 2022 to Q2 2023.",
                    "narrative": "The grouped bar chart compares the average revenue per user (ARPU) for the mobile app with the overall ARPU from Q2 2022 to Q2 2023, highlighting differences in revenue generation.",
                    "main_questions": [
                        {
                            "main_question": "How does the average revenue per user (ARPU) for the mobile app compare to the overall ARPU from Q2 2022 to Q2 2023?",
                            "main_title": "ARPU Comparison: Mobile App vs Overall (Q2 2022 - Q2 2023)",
                            "main_chart_type": "grouped_bar_chart",
                            "main_chart_category": "comparison",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "Q2 2022 - Q2 2023",
                        }
                    ],
                },
                # Pie Charts
                {
                    "user_intent": "Determine the percentage contribution of each service to the overall revenue forecast for the next six months.",
                    "narrative": "The pie chart illustrates the percentage contribution of each service to the overall revenue forecast over the next six months. This visualization provides a clear breakdown of which services are expected to drive the majority of revenue, offering insights into potential areas of focus and strategic importance for optimizing revenue streams.",
                    "main_questions": [
                        {
                            "main_question": "What is the percentage contribution of each service to the overall revenue forecast for the next six months?",
                            "main_title": "Percentage Contribution of Services to Overall Revenue Forecast (Next Six Months)",
                            "main_chart_type": "pie_chart",
                            "main_chart_category": "composition",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "Next Six Months",
                        }
                    ],
                },
                {
                    "user_intent": "Analyze the market share of different product lines in the current quarter.",
                    "narrative": "The pie chart illustrates the market share of different product lines in the current quarter. This visualization provides a clear breakdown of how each product line contributes to the overall market presence, helping identify dominant products and potential areas for growth or improvement.",
                    "main_questions": [
                        {
                            "main_question": "What is the current market share distribution of different product lines?",
                            "main_title": "Market Share Distribution of Product Lines (Current Quarter)",
                            "main_chart_type": "pie_chart",
                            "main_chart_category": "composition",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "Current Quarter",
                        }
                    ],
                },
                # Bubble Plot Charts
                {
                    "user_intent": "Analyze the relationship between marketing spend, sales revenue, and market share for five leading products.",
                    "narrative": "The bubble chart visualizes the relationship between marketing spend, sales revenue, and market share for five leading products. This analysis helps identify which products are most efficient in converting marketing investments into sales and market share, providing insights for optimizing marketing strategies.",
                    "main_questions": [
                        {
                            "main_question": "What is the relationship between marketing spend, sales revenue, and market share for five leading products?",
                            "main_title": "Marketing Spend vs Sales Revenue vs Market Share for Five Leading Products",
                            "main_chart_type": "bubbleplot_chart",
                            "main_chart_category": "relationship",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "Current Year",
                        }
                    ],
                },
                {
                    "user_intent": "Compare the relationship between customer acquisition costs, customer lifetime value, and retention rates across three key regions.",
                    "narrative": "The bubble chart illustrates the relationship between customer acquisition costs, customer lifetime value, and retention rates for three key regions. This analysis helps identify which regions are most efficient in acquiring and retaining high-value customers, offering insights into regional customer strategies.",
                    "main_questions": [
                        {
                            "main_question": "How do customer acquisition costs, customer lifetime value, and retention rates relate across three key regions?",
                            "main_title": "Customer Acquisition Cost vs Lifetime Value vs Retention Rate for Three Key Regions",
                            "main_chart_type": "bubbleplot_chart",
                            "main_chart_category": "relationship",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "Past Six Months",
                        }
                    ],
                },
                # Scatterplot Charts
                {
                    "user_intent": "Analyze the relationship between customer satisfaction scores and customer retention rates for different product categories.",
                    "narrative": "The scatterplot chart visualizes the relationship between customer satisfaction scores and customer retention rates across different product categories. This analysis helps identify patterns and correlations between customer satisfaction and loyalty, providing insights into which product categories may need improvement or which are performing well in terms of customer retention.",
                    "main_questions": [
                        {
                            "main_question": "What is the relationship between customer satisfaction scores and customer retention rates for different product categories?",
                            "main_title": "Customer Satisfaction vs. Retention Rates by Product Category",
                            "main_chart_type": "scatterplot_chart",
                            "main_chart_category": "relationship",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "Last Year",
                        }
                    ],
                },
                {
                    "user_intent": "Analyze the correlation between marketing spend and sales revenue for different product categories.",
                    "narrative": "The scatterplot chart visualizes the relationship between marketing spend and sales revenue across different product categories. This analysis helps identify which product categories show a strong positive correlation between marketing investments and sales outcomes, providing insights for optimizing marketing strategies.",
                    "main_questions": [
                        {
                            "main_question": "What is the correlation between marketing spend and sales revenue for different product categories?",
                            "main_title": "Marketing Spend vs. Sales Revenue by Product Category",
                            "main_chart_type": "scatterplot_chart",
                            "main_chart_category": "relationship",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "Current Quarter",
                        }
                    ],
                },
                # Histogram Charts
                {
                    "user_intent": "Evaluate the distribution of customer lifetime value across all customers.",
                    "narrative": "The histogram chart displays the distribution of customer lifetime value across all customers. This visualization helps identify the most common value ranges and any outliers, providing insights into customer segmentation and potential high-value customer groups.",
                    "main_questions": [
                        {
                            "main_question": "What is the distribution of customer lifetime value across all customers?",
                            "main_title": "Distribution of Customer Lifetime Value",
                            "main_chart_type": "histogram_chart",
                            "main_chart_category": "distribution",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "Over the Last Year",
                        }
                    ],
                },
                {
                    "user_intent": "Examine the distribution of customer support response times over the past month.",
                    "narrative": "The histogram chart displays the distribution of customer support response times over the past month. This visualization helps identify the most common response time ranges and any outliers, providing insights into support team performance and areas for potential improvement in customer service efficiency.",
                    "main_questions": [
                        {
                            "main_question": "What is the distribution of customer support response times over the past month?",
                            "main_title": "Distribution of Customer Support Response Times",
                            "main_chart_type": "histogram_chart",
                            "main_chart_category": "distribution",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "Within the Past 30 Days",
                        }
                    ],
                },
                # Table Charts
                {
                    "user_intent": "Compare key performance indicators (KPIs) across different departments for the past quarter.",
                    "narrative": "The table chart presents a comparison of key performance indicators (KPIs) across different departments for the past quarter. This structured view allows for easy comparison of various metrics, helping identify high-performing departments and areas that may need improvement.",
                    "main_questions": [
                        {
                            "main_question": "How do key performance indicators (KPIs) compare across different departments in the past quarter?",
                            "main_title": "KPI Comparison Across Departments (Past Quarter)",
                            "main_chart_type": "table_chart",
                            "main_chart_category": "comparison",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "Past Quarter",
                        }
                    ],
                },
                {
                    "user_intent": "Compare product performance metrics across different regions for the current year.",
                    "narrative": "The table chart presents a comparison of product performance metrics across different regions for the current year. This structured view allows for easy comparison of various indicators such as sales, market share, and growth rates, helping identify regional strengths and areas for improvement in product strategy.",
                    "main_questions": [
                        {
                            "main_question": "How do product performance metrics compare across different regions for the current year?",
                            "main_title": "Regional Product Performance Comparison (Current Year)",
                            "main_chart_type": "table_chart",
                            "main_chart_category": "comparison",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "Current Year",
                        }
                    ],
                },
            ]

    else:
        DATE_INSTRUCTIONS = (
            "- ENSURE no time frame and time duration generated for each chart."
        )
        DATE_INSTRUCTIONS2 = ""

        CHART_TIMEFRAME = [""]

        if liked_feedbacks and non_duration_related_samples:
            # Initialize a list to store the samples
            SAMPLES = []

            # Loop through each entry in liked_feedbacks
            for chart in non_duration_related_samples:
                # Construct the sample dictionary for each liked feedback item
                sample = {
                    "user_intent": chart.get("user_query", ""),
                    "narrative": chart.get("narrative", ""),
                    "main_questions": [
                        {
                            "main_question": chart.get("question", ""),
                            "main_title": chart.get("chart_title", ""),
                            "main_chart_type": chart.get("chart_type", ""),
                            "main_chart_category": chart.get("chart_category", ""),
                            "main_chart_timeframe": chart.get("time_frame", ""),
                            "main_chart_duration": chart.get("time_duration", ""),
                        }
                    ],
                }

                # Append the constructed sample to the samples list
                SAMPLES.append(sample)
        else:
            SAMPLES = [
                # Line Charts
                {
                    "user_intent": "Analyze the evolution of total cost variance (actual vs budget and actual vs forecast) for the broadband product.",
                    "narrative": "The total cost variance for the broadband product shows distinct patterns when comparing actual vs budget and actual vs forecast. The line chart visualizes these trends, highlighting periods of alignment or deviation. Key insights from the data reveal fluctuations in cost management, with certain periods showing significant variances between the planned and actual expenditures, while others maintain closer adherence to forecasts. This analysis helps identify the effectiveness of budgeting and forecasting strategies in the broadband product's cost management.",
                    "main_questions": [
                        {
                            "main_question": "How have the total cost variance (actual vs budget) and total cost variance (actual vs forecast) for the broadband product evolved?",
                            "main_title": "Total Cost Variance: Actual vs. Budget and Actual vs. Forecast for Broadband Product",
                            "main_chart_type": "line_chart",
                            "main_chart_category": "comparison",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "",
                        }
                    ],
                },
                {
                    "user_intent": "Track the trend in total revenue from premium services.",
                    "narrative": "The line chart tracks the trend in total revenue from premium services, showcasing fluctuations and key growth periods. This analysis provides insights into revenue performance and growth opportunities.",
                    "main_questions": [
                        {
                            "main_question": "What is the trend in total revenue from premium services?",
                            "main_title": "Total Revenue from Premium Services",
                            "main_chart_type": "line_chart",
                            "main_chart_category": "comparison",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "",
                        }
                    ],
                },
                # Grouped Bar Charts
                {
                    "user_intent": "Compare the median cost variance (actual vs budget) for entertainment services between different periods.",
                    "narrative": "By comparing the median entertainment services' cost variance between different periods, the grouped bar chart highlights significant differences in budgeting accuracy. This analysis allows for a deeper understanding of cost management trends and helps identify areas where financial planning has either succeeded or requires improvement.",
                    "main_questions": [
                        {
                            "main_question": "How does the median cost variance (actual vs budget) for entertainment services compare between different periods?",
                            "main_title": "Median Cost Variance (Actual vs Budget) for Entertainment Services: Period Comparison",
                            "main_chart_type": "grouped_bar_chart",
                            "main_chart_category": "comparison",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "",
                        }
                    ],
                },
                {
                    "user_intent": "Compare the average revenue per user (ARPU) for the mobile app to the overall ARPU.",
                    "narrative": "The grouped bar chart compares the average revenue per user (ARPU) for the mobile app with the overall ARPU, highlighting differences in revenue generation.",
                    "main_questions": [
                        {
                            "main_question": "How does the average revenue per user (ARPU) for the mobile app compare to the overall ARPU?",
                            "main_title": "ARPU Comparison: Mobile App vs Overall",
                            "main_chart_type": "grouped_bar_chart",
                            "main_chart_category": "comparison",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "",
                        }
                    ],
                },
                # Pie Charts
                {
                    "user_intent": "Determine the percentage contribution of each service to the overall revenue forecast.",
                    "narrative": "The pie chart illustrates the percentage contribution of each service to the overall revenue forecast. This visualization provides a clear breakdown of which services are expected to drive the majority of revenue, offering insights into potential areas of focus and strategic importance for optimizing revenue streams.",
                    "main_questions": [
                        {
                            "main_question": "What is the percentage contribution of each service to the overall revenue forecast?",
                            "main_title": "Percentage Contribution of Services to Overall Revenue Forecast",
                            "main_chart_type": "pie_chart",
                            "main_chart_category": "composition",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "",
                        }
                    ],
                },
                {
                    "user_intent": "Analyze the market share of different product lines.",
                    "narrative": "The pie chart illustrates the market share of different product lines. This visualization provides a clear breakdown of how each product line contributes to the overall market presence, helping identify dominant products and potential areas for growth or improvement.",
                    "main_questions": [
                        {
                            "main_question": "What is the current market share distribution of different product lines?",
                            "main_title": "Market Share Distribution of Product Lines",
                            "main_chart_type": "pie_chart",
                            "main_chart_category": "composition",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "",
                        }
                    ],
                },
                # Bubble Charts
                {
                    "user_intent": "Analyze the relationship between marketing spend, sales revenue, and market share for five leading products.",
                    "narrative": "The bubble chart visualizes the relationship between marketing spend, sales revenue, and market share for five leading products. This analysis helps identify which products are most efficient in converting marketing investments into sales and market share, providing insights for optimizing marketing strategies.",
                    "main_questions": [
                        {
                            "main_question": "What is the relationship between marketing spend, sales revenue, and market share for five leading products?",
                            "main_title": "Marketing Spend vs Sales Revenue vs Market Share for Five Leading Products",
                            "main_chart_type": "bubbleplot_chart",
                            "main_chart_category": "relationship",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "",
                        }
                    ],
                },
                {
                    "user_intent": "Compare the relationship between customer acquisition costs, customer lifetime value, and retention rates across three key regions.",
                    "narrative": "The bubble chart illustrates the relationship between customer acquisition costs, customer lifetime value, and retention rates for three key regions. This analysis helps identify which regions are most efficient in acquiring and retaining high-value customers, offering insights into regional customer strategies.",
                    "main_questions": [
                        {
                            "main_question": "How do customer acquisition costs, customer lifetime value, and retention rates relate across three key regions?",
                            "main_title": "Customer Acquisition Cost vs Lifetime Value vs Retention Rate for Three Key Regions",
                            "main_chart_type": "bubbleplot_chart",
                            "main_chart_category": "relationship",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "",
                        }
                    ],
                },
                # Scatterplot Charts
                {
                    "user_intent": "Analyze the relationship between customer satisfaction scores and customer retention rates for different product categories.",
                    "narrative": "The scatterplot chart visualizes the relationship between customer satisfaction scores and customer retention rates across different product categories. This analysis helps identify patterns and correlations between customer satisfaction and loyalty, providing insights into which product categories may need improvement or which are performing well in terms of customer retention.",
                    "main_questions": [
                        {
                            "main_question": "What is the relationship between customer satisfaction scores and customer retention rates for different product categories?",
                            "main_title": "Customer Satisfaction vs. Retention Rates by Product Category",
                            "main_chart_type": "scatterplot_chart",
                            "main_chart_category": "relationship",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "",
                        }
                    ],
                },
                {
                    "user_intent": "Analyze the correlation between marketing spend and sales revenue for different product categories.",
                    "narrative": "The scatterplot chart visualizes the relationship between marketing spend and sales revenue across different product categories. This analysis helps identify which product categories show a strong positive correlation between marketing investments and sales outcomes, providing insights for optimizing marketing strategies.",
                    "main_questions": [
                        {
                            "main_question": "What is the correlation between marketing spend and sales revenue for different product categories?",
                            "main_title": "Marketing Spend vs. Sales Revenue by Product Category",
                            "main_chart_type": "scatterplot_chart",
                            "main_chart_category": "relationship",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "",
                        }
                    ],
                },
                # Histogram Charts
                {
                    "user_intent": "Evaluate the distribution of customer lifetime value across all customers.",
                    "narrative": "The histogram chart displays the distribution of customer lifetime value across all customers. This visualization helps identify the most common value ranges and any outliers, providing insights into customer segmentation and potential high-value customer groups.",
                    "main_questions": [
                        {
                            "main_question": "What is the distribution of customer lifetime value across all customers?",
                            "main_title": "Distribution of Customer Lifetime Value",
                            "main_chart_type": "histogram_chart",
                            "main_chart_category": "distribution",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "",
                        }
                    ],
                },
                {
                    "user_intent": "Examine the distribution of customer support response times.",
                    "narrative": "The histogram chart displays the distribution of customer support response times. This visualization helps identify the most common response time ranges and any outliers, providing insights into support team performance and areas for potential improvement in customer service efficiency.",
                    "main_questions": [
                        {
                            "main_question": "What is the distribution of customer support response times?",
                            "main_title": "Distribution of Customer Support Response Times",
                            "main_chart_type": "histogram_chart",
                            "main_chart_category": "distribution",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "",
                        }
                    ],
                },
                # Table Charts
                {
                    "user_intent": "Compare key performance indicators (KPIs) across different departments.",
                    "narrative": "The table chart presents a comparison of key performance indicators (KPIs) across different departments. This structured view allows for easy comparison of various metrics, helping identify high-performing departments and areas that may need improvement.",
                    "main_questions": [
                        {
                            "main_question": "How do key performance indicators (KPIs) compare across different departments?",
                            "main_title": "Departmental KPI Comparison",
                            "main_chart_type": "table_chart",
                            "main_chart_category": "comparison",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "",
                        }
                    ],
                },
                {
                    "user_intent": "Compare product performance metrics across different regions.",
                    "narrative": "The table chart presents a comparison of product performance metrics across different regions. This structured view allows for easy comparison of various indicators such as sales, market share, and growth rates, helping identify regional strengths and areas for improvement in product strategy.",
                    "main_questions": [
                        {
                            "main_question": "How do product performance metrics compare across different regions?",
                            "main_title": "Regional Product Performance Comparison",
                            "main_chart_type": "table_chart",
                            "main_chart_category": "comparison",
                            "main_chart_timeframe": "",
                            "main_chart_duration": "",
                        }
                    ],
                },
            ]

    return DATE_INSTRUCTIONS, DATE_INSTRUCTIONS2, CHART_TIMEFRAME, SAMPLES


def generate_narrative_question_d3(
    llama70b_client: Any,
    user_query: str,
    filters: dict,
    aggregations: list,
    data_summary: DataSummary,
    logging_url: str,
    session_id: str,
    user_id: str,
    input_tokens: int,
    output_tokens: int,
    table_name: str,
    code_level_logger: logging.Logger,
) -> Tuple[Union[StoryNarrative, None], int, int]:
    with PerformanceLogger(session_id):
        REQUIRED_KEY_LIST = ["narrative", "main_questions"]
        FORMAT_INSTRUCTIONS = """{"narrative": "...", "main_questions": 
        [{"main_question": "...", "main_title": "...", "main_chart_type": "...", "main_chart_category": "...", "main_chart_timeframe": "...",  "main_chart_duration": "..."}, 
        {"main_question": "...", "main_title": "...", "main_chart_type": "...", "main_chart_category": "...", "main_chart_timeframe": "...", "main_chart_duration": "..."}, ..]}"""

        TARGET_TOKEN_LIMIT = int(os.getenv("QUESTION_TOTAL_INPUT_TOKEN_LIMIT", "0"))

        if TARGET_TOKEN_LIMIT == 0:
            code_level_logger.error("Target Token Limit is not valid!")
            raise ValueError("Target Token Limit is not valid!")

        CHART_TYPE_LIST = [
            "line_chart",
            "grouped_bar_chart",
            "histogram_chart",
            "pie_chart",
            "scatterplot_chart",
            "table_chart",
            "bubbleplot_chart",
        ]

        CHART_CATEGORY_MAP = {
            "relationship": [
                "scatterplot_chart",
                "bubbleplot_chart",
            ],
            "comparison": [
                "grouped_bar_chart",
                "line_chart",
                "table_chart",
            ],
            "distribution": ["histogram_chart"],
            "composition": ["pie_chart"],
        }

        FILTER_INSTRUCTIONS, DIMENSION_INSTRUCTIONS = (
            generate_filter_and_dimension_instructions_d3(
                filters,
            )
        )

        AGGREGATION_INSTRUCTIONS = generate_aggregation_instructions_d3(
            aggregations,
            data_summary,
        )

        DATE_INSTRUCTIONS, DATE_INSTRUCTIONS2, CHART_TIMEFRAME, SAMPLES = (
            generate_date_instruction_timeframe_samples_d3(
                data_summary,
                user_query,
                code_level_logger,
            )
        )

        schema_json_narrative = ResponseSchema_NarrativeQuestion.model_json_schema()

        schema_json_narrative["$defs"]["MainQuestionModel"]["properties"][
            "main_chart_type"
        ]["enum"] = CHART_TYPE_LIST

        schema_json_narrative["$defs"]["MainQuestionModel"]["properties"][
            "main_chart_category"
        ]["enum"] = list(CHART_CATEGORY_MAP.keys())

        schema_json_narrative["$defs"]["MainQuestionModel"]["properties"][
            "main_chart_timeframe"
        ]["enum"] = CHART_TIMEFRAME

        chart_feedback_data = fetch_feedback(
            "user_query",
            user_query,
            code_level_logger,
        )

        # Filter out feedback entries where the "like" field is False, get only disliked feedbacks.
        disliked_feedbacks = filter_feedback(chart_feedback_data, filter_liked=False)

        # Further filter the disliked feedback entries to include only those with selected options or "other" text in feedback fields.
        disliked_feedbacks = filter_feedback_by_options(
            disliked_feedbacks,
            ["chart_title", "overall_chart"],
            code_level_logger,
        )

        BAD_SAMPLES = []

        if disliked_feedbacks:
            for chart in disliked_feedbacks:
                sample = {
                    "user_intent": chart.get("user_query", ""),
                    "narrative": chart.get("narrative", ""),
                    "main_questions": [
                        {
                            "main_question": chart.get("question", ""),
                            "main_title": chart.get("chart_title", ""),
                            "main_chart_type": chart.get("chart_type", ""),
                            "main_chart_category": chart.get("chart_category", ""),
                            "main_chart_timeframe": chart.get("time_frame", ""),
                            "main_chart_duration": chart.get("time_duration", ""),
                        }
                    ],
                }
                BAD_SAMPLES.append(sample)

        # Create the disallowed samples instruction if there are any
        BAD_SAMPLES_INSTRUCTION = ""
        if BAD_SAMPLES:
            BAD_SAMPLES_INSTRUCTION = f"""
    Disallowed Narrative Patterns:
    - Please avoid generating responses that resemble any of the following examples, as these have been marked as unsatisfactory by users:
    {BAD_SAMPLES}

    Take special care to avoid generating responses similar to those listed in the feedback. 
    These examples were marked as inadequate because they do not fully align with user intent, lack specificity, 
    or fail to provide meaningful information for business decisions."""

        system_prompt_beginning = """Current datetime is {current_datetime}. You are a professional data analyst who can help in crafting a business analytics report plan. Your task is to generate a SINGLE cohesive narrative that answers up to 6 main questions focusing more to key performance indicator related to the {industry_domain} industry domain to help business decisions, along with the corresponding chart titles and chart types, based on the provided SQL schema and user query. Please output the best narrative flow, including main questions + chart titles + chart types (not more than 6).

    General Narrative Flow Requirements:
    - Develop a SINGLE narrative that logically covers all key aspects of the user intent, integrating at least six relevant key performance indicators/metrics and dimensions from the SQL schema.
    - The narrative must be coherent, complete, and avoid any numbering or lists.
    - Refer to the database SQL schema, table descriptions, and column details to ensure accuracy and data availability.
    - Ensure each part of the narrative shows high value for the business impact.
    - Ensure to visualize the user's intent first before proceeding with further analysis or actions.
    - Ensure that the narrative conveys a compelling story to the user, illustrating insights derived from the charts and enhancing the overall understanding of the data.

    Main Questions, Chart Titles, and Chart Types Requirements:
    - Generate up to 6 distinct charts (question, chart title, and chart type) that align seamlessly with the narrative flow.
    - Ensure charts (question, chart title, and chart type) are unique, non-repetitive, and free of unnecessary filters. Do not generate another chart if there is no additional non-identical chart available to be generated.
    - Avoid identical charts which are showing identical data.
    - Ensure each chart shows high value for the business impact.
    - Avoid questions starting with 'which'.
    - Limit frequency distribution question to one category per question.
    - Ensure chart titles are clear and aligned with the questions.
    - Ensure questions and chart titles include aggregation keywords (e.g., 'Total', 'Average', 'Median', etc) for numerical metrics.
    - Avoid simplistic questions, or titles.
    - ENSURE no redundant charts which project similar data.
    - Ensure charts are not duplicated.
    - Default aggregation term: 'Total'.
    - Ensure chart types are correctly matched to the data they represent.
    - Avoid question that shows 'the highest and the lowest' in one question, such as 'Monthly Revenue Percent Change Trend for Top and Bottom Products (Last Year)'. Instead, split the question into two separate questions where first question shows the highest and second question shows the lowest.
    - Always use 'top' or 'bottom' (e.g., 'top 3 products with highest revenue', 'top 5 products with lowest cost') keyword in the question and chart title for chart related to lowest or highest data.
    - Ensure that the date unit is appropriate for the context of the chart (e.g., 'days', 'weeks', 'months', 'quarters', 'years').
    - Ensure to use 'line_chart' chart type when x-axis is date-related (e.g., 'Month', 'Day', 'Quarter').
    - Ensure 'pie_chart' chart type is always paired exclusively with 'composition' chart category.
    - Ensure 'line_chart' chart type is always paired exclusively with 'comparison' chart category.
    - Ensure that question and chart title which uses the 'histogram_chart' chart type does not include aggregation or grouping, while still allowing filtering options.
    - Ensure that question and chart title which uses the 'scatterplot_chart' chart type always utilize numerical columns for x-axis and y-axis.
    - Ensure that question and chart title which uses the 'bubbleplot_chart' chart type always utilize numerical columns for x-axis, y-axis, and z-axis.
    - Avoid using “group by” or aggregation on columns that have more than 12 unique values.
    - Visualize the key performance indicator or metric using its corresponding formula where necessary data column(s) is/are sufficient for calculation.
    - ENSURE that any question using a series column selects one with more than 1 and up to 4 unique values as the series column to maintain chart clarity and avoid clutter. If the column doesn't meet this criterion, exclude it.
    - ENSURE to utilize column with number of unique values more than 1 and less than 13 for x-axis in pie chart.
    {DATE_INSTRUCTIONS}

    Please check **Column Information** below or context to confirm whether the data is categorical or numerical before selecting a chart type.
    Column Information:
    {column_information}

    Follow the suitable chart category below to select the most suitable chart category based on the type of data and the insights required:

    - 'comparison': Choose this category when comparing different groups, categories, or items to highlight differences.
    - 'distribution': Use this category when you want to show how data is spread out or distributed across a range of values. It's helpful for understanding the shape, central tendency, and variability of a dataset.
    - 'composition': Choose this category when you want to show how a whole is divided into its constituent parts. It's useful for displaying the relative proportions of different components that make up a total.
    - 'relationship': Use when analyzing the relationship or correlation between two or more numerical variables to understand how they interact with each other.

    Ensure to select the most suitable chart type based on the following criteria from each chart category:

    Comparison:
    - 'grouped_bar_chart':
        - Description: Used to compare discrete data across different categories. Suitable for comparing a single metric without any series or sub-categories, or for comparing multiple metrics or series side by side. Ideal for visualizing changes over time or comparisons between distinct groups.
        - Conditions:
            - Use when working with categorical variables and numerical metrics.
            - Avoid if there are too many categories or metrics, which may lead to overcrowding.
        - Fallback: If there are too many categories or metrics, causing overcrowding, default to a 'table_chart'. A table can handle a high number of categories and offers a structured view without visual clutter.
    - 'line_chart':
        - Description: Used to track changes in data over equal intervals, like time, and to show continuous data trends. Suitable for time series analysis where continuity of data is key, such as tracking metrics over time.
        - Conditions:
            - Use for continuous numerical data on the y-axis and time-based data on the x-axis.
            - Ensure intervals are uniform to capture trends effectively.
        - Fallback: If data intervals are not uniform or don't effectively show trends, use a 'grouped_bar_chart' to display discrete time comparisons instead.
    - 'table_chart':
        - Description: Used for displaying and comparing data in a structured grid format with high precision. Allows comparison of multiple metrics across categories directly.
        - Conditions:
            - Use when exact numerical values are important or when comparing categories, metrics, or time periods side-by-side.
            - Prefer this over other charts when textual or highly granular data is involved.

    Distribution:
    - 'histogram_chart':
        - Description: Used to show the distribution of a single numerical variable by grouping data into bins or intervals. This chart focuses on displaying continuous data distribution patterns.
        - Conditions:
            - Best suited for numerical metrics with a wide range and a large amount of data.
            - Avoid using categorical data or metrics with limited unique values.
            - Ensure bins or intervals are appropriately sized to capture distribution details accurately.
            - Do not use with GROUP BY as histogram charts rely on continuous data and binning instead of discrete grouping.
            - For questions requiring GROUP BY, use alternative chart types.
        - Fallback: If the data is categorical or lacks sufficient unique values for binning, default to a table chart to display discrete counts or grouped data instead.

    Composition:
    - 'pie_chart':
        - Description: Displays parts of a whole by dividing a circle into proportional segments. Each segment represents a percentage, with all segments totaling 100%.
        - Conditions:
            - Use for limited categories (typically fewer than five).
            - Prefer this for comparing proportions rather than exact values.
        - Fallback: If the pie chart becomes crowded due to more than five categories, switch to a grouped bar chart to display proportional data across multiple categories.

    relationship:
    - 'scatterplot_chart': 
        - Description: Displays relationships between TWO continuous numerical variables by plotting them on the x and y axes.
        - Conditions:
            - Both variables (x and y) must be confirmed as continuous numerical data in the Column Data Tribes list.
            - If either variable is identified as "categorical," exclude scatterplot from consideration.
        - Fallback: If either variable is categorical, use a grouped bar chart to represent relationships across categories.
    - 'bubbleplot_chart': 
        - Description: Visualizes relationships among THREE dimensions: two continuous numerical variables on the x and y axes, and a third numerical variable represented by bubble size.
        - Conditions:
            - All three variables (x, y, and z) must be confirmed as continuous numerical data in Column Data Tribes.
            - If any variable is identified as "categorical," exclude bubbleplot from selection.
        - Fallback: If any of the three dimensions is categorical, consider reverting to a scatterplot chart (if reduced to two continuous variables). If neither a scatterplot nor a bubbleplot meets conditions, use a grouped bar chart to represent categorical relationships.

    Additional Guidelines:
    - Categorical Data Indicators: Treat columns as categorical if they represent classes, levels, categories, groups, stages, or types.
    - Avoid Substituting Categorical Data with Numerical Proxies: Do not use numerical proxies solely to use scatterplot or bubbleplot.

    {DATE_INSTRUCTIONS2}

    For more context, you are provided a database SQL schema, database table description, and database column description to support the narrative and chart generation.

    Database SQL Schema:
    {database_schema_sql}

    Database Table Description:
    {table_description}

    {DIMENSION_INSTRUCTIONS}

    {AGGREGATION_INSTRUCTIONS}

    {FILTER_INSTRUCTIONS}

    {FORMAT_INSTRUCTIONS}

    Include all keys from this key list: {REQUIRED_KEY_LIST}""".format(
            current_datetime=datetime.now(),
            industry_domain=os.getenv("INDUSTRY_DOMAIN"),
            REQUIRED_KEY_LIST=REQUIRED_KEY_LIST,
            database_schema_sql=data_summary.database_schema_sql,
            table_description=data_summary.table_description,
            column_information=generate_column_information_prompt(
                data_summary.column_description_dict,
                data_summary.column_sample_dict,
                data_summary.column_display_name_dict,
                data_summary.column_n_unique_value_dict,
                data_summary.column_data_tribes,
            ),
            DIMENSION_INSTRUCTIONS=DIMENSION_INSTRUCTIONS,
            AGGREGATION_INSTRUCTIONS=AGGREGATION_INSTRUCTIONS,
            FILTER_INSTRUCTIONS=FILTER_INSTRUCTIONS,
            FORMAT_INSTRUCTIONS=FORMAT_INSTRUCTIONS,
            DATE_INSTRUCTIONS=DATE_INSTRUCTIONS,
            DATE_INSTRUCTIONS2=DATE_INSTRUCTIONS2,
        )

        system_prompt_ending = """ENSURE that your response is COMPLETE, LOGICAL, and NEVER ENDS abruptly.
    DO NOT INCLUDE ANY EXPLANATIONS or NOTES in your response.
    ENSURE your answer is in a VALID LIST format as instructed.
    PLEASE DO NOT HALLUCINATE!

    """.format()

        user_prompt = """Please process and output the results step-by-step. Generate a (ONE) narrative flow including main questions, main titles, main chart types, main chart categories, main chart timeframe, and main chart duration (up to 6) based on the user intent, user query, filter, database SQL schema to get all the informations needed to answer every part of the narrative flow while also following the criterias specified before.

    User intent: {user_query}

    """

        SAMPLE_USER_PROMPT = """Please process and output the results step-by-step. Generate a (ONE) narrative flow including main questions, main titles, main chart types, main chart categories, main chart timeframe, and main chart duration (up to 6) based on the user intent, user query, filter, database SQL schema to get all the informations needed to answer every part of the narrative flow while also following the criterias specified before.

    User intent: {user_query}"""

        messages = []

        # Start with the system prompt (without bad samples instruction for now)
        system_prompt = system_prompt_beginning + "\n\n" + system_prompt_ending
        total_num_tokens = calculate_token_usage(user_prompt, system_prompt)

        # Add system message as the first item in the array
        messages.append({"role": "system", "content": system_prompt})

        for SAMPLE in SAMPLES:
            user_prompt_message = {
                "role": "user",
                "content": SAMPLE_USER_PROMPT.format(user_query=SAMPLE["user_intent"]),
            }
            user_prompt_tokens = calculate_token_usage(user_prompt_message["content"])

            # Calculate tokens for all assistant messages in this sample
            assistant_messages = []
            assistant_tokens_total = 0
            for main_question in SAMPLE["main_questions"]:
                assistant_message = {
                    "role": "assistant",
                    "content": """[{
                        "main_question": """
                    + f'"{main_question["main_question"]}"'
                    + """, "main_title": """
                    + f'"{main_question["main_title"]}"'
                    + """, "main_chart_type": """
                    + f'"{main_question["main_chart_type"]}"'
                    + """, "main_chart_category: """
                    + f'"{main_question["main_chart_category"]}"'
                    + """, "main_chart_timeframe: """
                    + f'"{main_question["main_chart_timeframe"]}"'
                    + """, "main_chart_duration: """
                    + f'"{main_question["main_chart_duration"]}"'
                    + """,}]""",
                }
                assistant_tokens = calculate_token_usage(assistant_message["content"])
                assistant_tokens_total += assistant_tokens
                assistant_messages.append(assistant_message)

            # Check if adding the user and all assistant messages would exceed the token limit
            if (
                total_num_tokens + user_prompt_tokens + assistant_tokens_total
                > TARGET_TOKEN_LIMIT
            ):
                break  # Stop processing further if limit would be exceeded

            # Append the user and assistant messages, and update the token count
            messages.append(user_prompt_message)
            messages.extend(assistant_messages)
            total_num_tokens += user_prompt_tokens + assistant_tokens_total

        # Now try to add the bad samples instruction if there's still room
        bad_samples_token = calculate_token_usage(BAD_SAMPLES_INSTRUCTION)

        if total_num_tokens + bad_samples_token <= TARGET_TOKEN_LIMIT:
            # Update the system prompt to include the bad samples instruction
            system_prompt_with_bad_samples = (
                system_prompt_beginning
                + "\n\n"
                + BAD_SAMPLES_INSTRUCTION
                + "\n\n"
                + system_prompt_ending
            )
            # Replace the original system message with the updated one that includes bad samples instruction
            messages[0] = {"role": "system", "content": system_prompt_with_bad_samples}

        messages.append(
            {"role": "user", "content": user_prompt},
        )

        start_narrative = perf_counter()

        for trial in range(3):
            response = (
                llama70b_client.chat.completions.create(
                    messages=messages,
                    model=os.getenv("LLAMA70B_MODEL"),
                    max_tokens=2000,
                    temperature=0.5,
                    extra_body={
                        "guided_json": schema_json_narrative,
                    },
                )
                .choices[0]
                .message.content
            )

            for message in messages:
                if "content" in message:
                    tokens = calculate_token_usage(message["content"])
                    input_tokens += tokens

            output_tokens += calculate_token_usage(response)

            response_json = json.loads(response)
            narrative = response_json["narrative"]

            narrative_inference_time = perf_counter() - start_narrative

            try:
                match = re.search(r"\{.*\}", response, re.DOTALL)
                if match:
                    json_string = match.group().strip()
                else:
                    json_string = response

                json_string = json_string.replace("None", "null")
                json_string = json_string.replace("NaN", "null")
                json_string = json_string.replace(r"\_", "_")
                json_string = json_string.replace("\\\\_", "_")
                json_string = json_string.replace("grouped_line_chart", "line_chart")
                json_string = json_string.replace("grouped_pie_chart", "pie_chart")
                json_string = json_string.replace(
                    "grouped_barchart_chart", "grouped_bar_chart"
                )
                json_string = json_string.replace(
                    "grouped_barchart", "grouped_bar_chart"
                )
                json_string = json_string.replace(
                    "bar_chartcombo_chart", "barlinecombo_chart"
                )
                json_string = json_string.replace(
                    "blinecombo_chart", "barlinecombo_chart"
                )
                json_string = json_string.replace("groupedbar", "grouped_bar_chart")
                json_string = json_string.replace(
                    "treemapmultichart", "TreemapMulti_chart"
                )
                json_string = json_string.replace(
                    "treemapmulti_chart", "TreemapMulti_chart"
                )
                json_string = json_string.replace("treemap_multi", "TreemapMulti_chart")
                json_string = json_string.replace("treemap_chart", "TreemapMulti_chart")
                json_string = json_string.replace("linechart", "line_chart")
                json_string = json_string.replace(
                    "bar_chart_combo_chart", "barlinecombo_chart"
                )
                json_string = json_string.replace("Radar_chart", "radar_chart")
                json_string = json_string.strip()
                result = ast.literal_eval(json_string)

                MAIN_QUESTION_REQUIRE_KEY = [
                    "main_question",
                    "main_title",
                    "main_chart_type",
                    "main_chart_category",
                    "main_chart_timeframe",
                    "main_chart_duration",
                ]

                for result_idx, question_data in enumerate(result["main_questions"]):
                    for key in question_data:
                        if key not in MAIN_QUESTION_REQUIRE_KEY:
                            raise RuntimeError(
                                "Error: Incomplete main question response generated",
                            )

                    result["main_questions"][result_idx]["main_title"] = question_data[
                        "main_title"
                    ].replace("_", " ")

                    if question_data["main_chart_type"] not in CHART_TYPE_LIST:
                        new_chart_type = (
                            question_data["main_chart_type"]
                            .replace("stacked_", "")
                            .replace("grouped_", "")
                        )
                        if "_chart" not in new_chart_type:
                            new_chart_type = new_chart_type.replace("chart", "_chart")
                        if "_chart_chart" in new_chart_type:
                            new_chart_type = new_chart_type.replace(
                                "_chart_chart", "_chart"
                            )

                        if "bar_chart" in new_chart_type:
                            new_chart_type = "grouped_bar_chart"

                        new_chart_type = new_chart_type.strip()

                        if new_chart_type not in CHART_TYPE_LIST:
                            raise RuntimeError(
                                f"Chart type generated {new_chart_type} is not supported!",
                            )

                        result["main_questions"][result_idx]["main_chart_type"] = (
                            new_chart_type
                        )

                    if question_data["main_chart_type"] not in CHART_CATEGORY_MAP.get(
                        question_data["main_chart_category"],
                        [],
                    ):
                        code_level_logger.error(f"""Chart category generated {question_data["main_chart_type"]} does not falls under
                                {question_data["main_chart_category"]} !""")
                        raise RuntimeError(
                            f"""Chart category generated {question_data["main_chart_type"]} does not falls under
                                {question_data["main_chart_category"]} !""",
                        )

                    if question_data["main_chart_timeframe"] not in CHART_TIMEFRAME:
                        raise RuntimeError(
                            f"""Chart Timeframe {question_data["main_chart_timeframe"]} is not supported!""",
                        )
                    current_version = version
                    log_entry_data = {
                        "chart_id": None,
                        "user_id": user_id,
                        "session_id": session_id,
                        "user_query": user_query,
                        "narrative": narrative,
                        "question": question_data["main_question"],
                        "time_frame": question_data["main_chart_timeframe"],
                        "time_duration": question_data["main_chart_duration"],
                        "chart_title": question_data["main_title"],
                        "chart_category": question_data["main_chart_category"],
                        "chart_type": question_data["main_chart_type"],
                        "table_name": table_name,
                        "module_version": current_version,
                        "db_tag": data_summary.database_properties["db_tag"],
                    }

                    logging_url_chart = logging_url + "chart"
                    log_responds = requests.post(
                        logging_url_chart, json=log_entry_data, verify=False
                    ).json()

                    question_data["chart_id"] = log_responds["chart_id"]

                    result["main_questions"][result_idx]["main_title"] = (
                        validate_and_add_time_info(
                            result["main_questions"][result_idx]["main_title"],
                            question_data["main_chart_timeframe"],
                            question_data["main_chart_duration"],
                        )
                    )

                    MODULEID_GENERATE_NARRATIVE_QUESTION_D3 = os.getenv(
                        "MODULEID_GENERATE_NARRATIVE_QUESTION_D3", ""
                    )

                    if MODULEID_GENERATE_NARRATIVE_QUESTION_D3 == "":
                        raise RuntimeError(
                            "MODULEID_GENERATE_NARRATIVE_QUESTION_D3 is invalid!"
                        )

                    formatted_data = {
                        "chart_id": question_data["chart_id"],
                        "module_id": int(MODULEID_GENERATE_NARRATIVE_QUESTION_D3),
                        "messages": messages,
                        "output": response,
                        "inference_time": narrative_inference_time,
                        "llm_model": os.getenv("MIXTRAL_MODEL"),
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                    }

                    logging_url_llm_calls = logging_url + "chart-llm-calls"
                    requests.put(
                        logging_url_llm_calls, json=formatted_data, verify=False
                    )

                    if question_data["main_chart_timeframe"] not in CHART_TIMEFRAME:
                        raise RuntimeError(
                            f"""Chart Timeframe {question_data["main_chart_timeframe"]} is not supported!""",
                        )
                    current_version = version
                    log_entry_data = {
                        "chart_id": None,
                        "user_id": user_id,
                        "session_id": session_id,
                        "user_query": user_query,
                        "narrative": narrative,
                        "question": question_data["main_question"],
                        "time_frame": question_data["main_chart_timeframe"],
                        "time_duration": question_data["main_chart_duration"],
                        "chart_title": question_data["main_title"],
                        "chart_category": question_data["main_chart_category"],
                        "chart_type": question_data["main_chart_type"],
                        "table_name": table_name,
                        "module_version": current_version,
                        "db_tag": data_summary.database_properties["db_tag"],
                    }

                    logging_url_chart = logging_url + "chart"
                    log_responds = requests.post(
                        logging_url_chart, json=log_entry_data, verify=False
                    ).json()

                    question_data["chart_id"] = log_responds["chart_id"]

                    result["main_questions"][result_idx]["main_title"] = (
                        validate_and_add_time_info(
                            result["main_questions"][result_idx]["main_title"],
                            question_data["main_chart_timeframe"],
                            question_data["main_chart_duration"],
                        )
                    )

                    MODULEID_GENERATE_NARRATIVE_QUESTION_D3 = os.getenv(
                        "MODULEID_GENERATE_NARRATIVE_QUESTION_D3", ""
                    )

                    if MODULEID_GENERATE_NARRATIVE_QUESTION_D3 == "":
                        code_level_logger.error(
                            "MODULEID_GENERATE_NARRATIVE_QUESTION_D3 is invalid!"
                        )
                        raise RuntimeError(
                            "MODULEID_GENERATE_NARRATIVE_QUESTION_D3 is invalid!"
                        )

                    formatted_data = {
                        "chart_id": question_data["chart_id"],
                        "module_id": int(MODULEID_GENERATE_NARRATIVE_QUESTION_D3),
                        "messages": messages,
                        "output": response,
                        "inference_time": narrative_inference_time,
                        "llm_model": os.getenv("LLAMA70B_MODEL"),
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                    }

                    logging_url_llm_calls = logging_url + "chart-llm-calls"
                    requests.put(
                        logging_url_llm_calls, json=formatted_data, verify=False
                    )

                return StoryNarrative(**result), input_tokens, output_tokens
            except Exception:
                code_level_logger.error(traceback.format_exc())
                print(traceback.format_exc())

        return None, input_tokens, output_tokens
