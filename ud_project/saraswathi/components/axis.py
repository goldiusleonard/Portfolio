import ast
import logging
import os
import re
import requests
import traceback
import json


from pydantic import BaseModel, Field
from enum import Enum
from time import perf_counter
from typing import Any
from pathlib import Path
from .datamodel import DataSummary
from .utils import (
    generate_column_information_prompt,
    calculate_token_usage,
    fetch_feedback,
    filter_feedback,
    filter_feedback_by_options,
)

from logging_library.performancelogger.performance_logger import PerformanceLogger

logger = logging.getLogger(__name__)

chart_data_with_feedback_path: str = str(
    Path(__file__).parent.parent / "chart_data_with_feedback.json"
)


class BarChartSchema(BaseModel):
    xAxis_title: str = Field(
        ...,
        title="xAxis_title",
        description="The title for the x-axis.",
    )
    xAxis_column: Enum = Field(
        ...,
        title="xAxis_column",
        description="The column name for the x-axis.",
    )
    yAxis_title: str = Field(
        ...,
        title="yAxis_title",
        description="The title for the y-axis.",
    )
    yAxis_column: Enum = Field(
        ...,
        title="yAxis_column",
        description="The column name for the y-axis.",
    )
    yAxis_aggregation: Enum = Field(
        ...,
        title="yAxis_aggregation",
        description="The aggregation for the y-axis.",
    )


class PyramidPieChartSchema(BaseModel):
    xAxis_title: str = Field(
        ...,
        title="xAxis_title",
        description="The title for the x-axis.",
    )
    xAxis_column: Enum = Field(
        ...,
        title="xAxis_column",
        description="The column name for the x-axis.",
    )
    yAxis_title: str = Field(
        ...,
        title="yAxis_title",
        description="The title for the y-axis.",
    )
    yAxis_column: Enum = Field(
        ...,
        title="yAxis_column",
        description="The column name for the y-axis.",
    )
    yAxis_aggregation: Enum = Field(
        ...,
        title="yAxis_aggregation",
        description="The aggregation for the y-axis.",
    )


class HistogramChartSchema(BaseModel):
    xAxis_title: str = Field(
        ...,
        title="xAxis_title",
        description="The title for the x-axis.",
    )
    xAxis_column: Enum = Field(
        ...,
        title="xAxis_column",
        description="The column name for the x-axis.",
    )


class LineGroupBarChartSchema(BaseModel):
    xAxis_title: str = Field(
        ...,
        title="xAxis_title",
        description="The title for the x-axis.",
    )
    xAxis_column: Enum = Field(
        ...,
        title="xAxis_column",
        description="The column name for the x-axis.",
    )
    yAxis_title: str = Field(
        ...,
        title="yAxis_title",
        description="The title for the y-axis.",
    )
    yAxis_column: Enum = Field(
        ...,
        title="yAxis_column",
        description="The column name for the y-axis.",
    )
    yAxis_aggregation: Enum = Field(
        ...,
        title="yAxis_aggregation",
        description="The aggregation for the y-axis.",
    )
    yAxis2_title: str = Field(
        ...,
        title="yAxis2_title",
        description="The title for the y-axis2. Set to empty string if not needed.",
    )
    yAxis2_column: Enum = Field(
        ...,
        title="yAxis2_column",
        description="The column name for the y-axis2. Set to empty string if not needed.",
    )
    yAxis2_aggregation: Enum = Field(
        ...,
        title="yAxis2_aggregation",
        description="The aggregation for the y-axis2. Set to empty string if not needed.",
    )
    yAxis3_title: str = Field(
        ...,
        title="yAxis3_title",
        description="The title for the y-axis3. Set to empty string if not needed.",
    )
    yAxis3_column: Enum = Field(
        ...,
        title="yAxis3_column",
        description="The column name for the y-axis3. Set to empty string if not needed.",
    )
    yAxis3_aggregation: Enum = Field(
        ...,
        title="yAxis3_aggregation",
        description="The aggregation for the y-axis3. Set to empty string if not needed.",
    )
    series_title: str = Field(
        ...,
        title="series_title",
        description="The title for the series. Set to empty string if not needed.",
    )
    series_column: Enum = Field(
        ...,
        title="series_column",
        description="The column name for the series. Set to empty string if not needed.",
    )


class SplineChartSchema(BaseModel):
    xAxis_title: str = Field(
        ...,
        title="xAxis_title",
        description="The title for the x-axis.",
    )
    xAxis_column: Enum = Field(
        ...,
        title="xAxis_column",
        description="The column name for the x-axis.",
    )
    yAxis_title: str = Field(
        ...,
        title="yAxis_title",
        description="The title for the y-axis.",
    )
    yAxis_column: Enum = Field(
        ...,
        title="yAxis_column",
        description="The column name for the y-axis.",
    )
    yAxis_aggregation: Enum = Field(
        ...,
        title="yAxis_aggregation",
        description="The aggregation for the y-axis.",
    )
    yAxis2_title: str = Field(
        ...,
        title="yAxis2_title",
        description="The title for the y-axis2. Set to empty string if not needed.",
    )
    yAxis2_column: Enum = Field(
        ...,
        title="yAxis2_column",
        description="The column name for the y-axis2. Set to empty string if not needed.",
    )
    yAxis2_aggregation: Enum = Field(
        ...,
        title="yAxis2_aggregation",
        description="The aggregation for the y-axis2. Set to empty string if not needed.",
    )
    series_title: str = Field(
        ...,
        title="series_title",
        description="The title for the series. Set to empty string if not needed.",
    )
    series_column: Enum = Field(
        ...,
        title="series_column",
        description="The column name for the series. Set to empty string if not needed.",
    )


class BarlineComboChartSchema(BaseModel):
    xAxis_title: str = Field(
        ...,
        title="xAxis_title",
        description="The title for the x-axis.",
    )
    xAxis_column: Enum = Field(
        ...,
        title="xAxis_column",
        description="The column name for the x-axis.",
    )
    yAxisBar_title: str = Field(
        ...,
        title="yAxisBar_title",
        description="The title for the y-axisBar.",
    )
    yAxisBar_column: Enum = Field(
        ...,
        title="yAxisBar_column",
        description="The column name for the y-axisBar.",
    )
    yAxisBar_aggregation: Enum = Field(
        ...,
        title="yAxisBar_aggregation",
        description="The aggregation for the y-axisBar.",
    )
    yAxisLine_title: str = Field(
        ...,
        title="yAxisLine_title",
        description="The title for the y-axisLine.",
    )
    yAxisLine_column: Enum = Field(
        ...,
        title="yAxisLine_column",
        description="The column name for the y-axisLine.",
    )
    yAxisLine_aggregation: Enum = Field(
        ...,
        title="yAxisLine_aggregation",
        description="The aggregation for the y-axisLine.",
    )


class ScatterplotChartSchema(BaseModel):
    xAxis_title: str = Field(
        ...,
        title="xAxis_title",
        description="The title for the x-axis.",
    )
    xAxis_column: Enum = Field(
        ...,
        title="xAxis_column",
        description="The column name for the x-axis.",
    )
    yAxis_title: str = Field(
        ...,
        title="yAxis_title",
        description="The title for the y-axis.",
    )
    yAxis_column: Enum = Field(
        ...,
        title="yAxis_column",
        description="The column name for the y-axis.",
    )
    series_title: str = Field(
        ...,
        title="series_title",
        description="The title for the series. Set to empty string if not needed.",
    )
    series_column: Enum = Field(
        ...,
        title="series_column",
        description="The column name for the series. Set to empty string if not needed.",
    )


class BubbleplotChartSchema(BaseModel):
    xAxis_title: str = Field(
        ...,
        title="xAxis_title",
        description="The title for the x-axis.",
    )
    xAxis_column: Enum = Field(
        ...,
        title="xAxis_column",
        description="The column name for the x-axis.",
    )
    yAxis_title: str = Field(
        ...,
        title="yAxis_title",
        description="The title for the y-axis.",
    )
    yAxis_column: Enum = Field(
        ...,
        title="yAxis_column",
        description="The column name for the y-axis.",
    )
    zAxis_title: str = Field(
        ...,
        title="zAxis_title",
        description="The title for the z-axis.",
    )
    zAxis_column: Enum = Field(
        ...,
        title="zAxis_column",
        description="The column name for the z-axis.",
    )
    series_title: str = Field(
        ...,
        title="series_title",
        description="The title for the series. Set to empty string if not needed.",
    )
    series_column: Enum = Field(
        ...,
        title="series_column",
        description="The column name for the series. Set to empty string if not needed.",
    )


def _select_axis_from_chart(
    llama70b_client: Any,
    chart_id: str,
    question: str,
    chart_title: str,
    chart_type: str,
    database_summary: DataSummary,
    logging_url: str,
    input_tokens: int,
    output_tokens: int,
    session_id: str,
    code_level_logger: logging.Logger,
):
    with PerformanceLogger(session_id):
        chart_feedback_data = fetch_feedback("question", question, code_level_logger)

        liked_feedbacks = filter_feedback(chart_feedback_data, filter_liked=True)

        # Filter out feedback entries where the "like" field is False, get only disliked feedbacks.
        disliked_feedbacks = filter_feedback(chart_feedback_data, filter_liked=False)

        disliked_feedbacks_based_on_axis_title = filter_feedback_by_options(
            disliked_feedbacks,
            [
                "xaxis_title",
                "yaxis_title",
                "zaxis_title",
                "xaxis_data",
                "yaxis_data",
                "zaxis_data",
                "overall_chart",
            ],
            logger,
        )

        BAD_SAMPLES = []

        if chart_type in ["pyramidfunnel_chart"]:
            x_axis_column_candidate_list = [
                column_name
                for column_name in database_summary.column_name_list
                if column_name != ""
                and database_summary.column_n_unique_value_dict[column_name] > 1
                and database_summary.column_n_unique_value_dict[column_name] <= 12
                and database_summary.column_data_tribes[column_name] in ["categorical"]
            ]

            schema_json = PyramidPieChartSchema.model_json_schema()

            schema_json["properties"]["xAxis_column"]["enum"] = (
                x_axis_column_candidate_list
            )
            schema_json["properties"]["yAxis_column"]["enum"] = (
                database_summary.column_name_list
            )
            schema_json["properties"]["yAxis_aggregation"]["enum"] = [
                "SUM",
                "AVG",
                "MEDIAN",
                "MEAN",
                "MIN",
                "MAX",
                "COUNT",
            ]

            FORMAT_INSTRUCTIONS = """{"xAxis_title": "...", "xAxis_column": "...", "yAxis_title": "...", "yAxis_column": "...", "yAxis_aggregation": "..."}"""
            KEY_LIST = [
                "xAxis_title",
                "xAxis_column",
                "yAxis_title",
                "yAxis_column",
                "yAxis_aggregation",
            ]
            TASK_INSTRUCTIONS = """Your task is to identify the appropriate axis columns and generate axis titles for 'xAxis' and 'yAxis' from the database SQL schema. Ensure each title is free from unreadable symbols or characters and is suitable for visualization as chart axis titles. Ensure each title is unique and provides clear context about the represented column data. Specify only one exact column name from the database SQL schema without any additional operator or aggregation for each 'xAxis_column' and 'yAxis_column' information. Each axis MUST have a title that provides complete context regarding the column represented (e.g., title='Total Cost Variance: Actual vs Forecast' from column='CostVariance_Actual_vs_Forecast', title='Average Revenue Variance: Actual vs Budget' from column='RevenueVariance_Actual_vs_Budget'). The 'xAxis_column' MUST be a column with STRING data type only. NEVER use constant values or any other values that are NOT in the database SQL schema for the columns. Y-axis aggregations MUST be selected from 'SUM', 'AVG', 'MEDIAN', 'MEAN', 'MIN', 'MAX', 'COUNT', etc., depending on the question. Ensure each axis title is meaningful and descriptive, using the column names directly without any additional operators or aggregation."""

            for feedback in disliked_feedbacks_based_on_axis_title:
                if feedback.get("chart_type") == "pyramidfunnel_chart":
                    BAD_SAMPLES.append(
                        {
                            "chart_type": "pyramidfunnel_chart",
                            "question": feedback.get("question", ""),
                            "chart_title": feedback.get("chart_title", ""),
                            "chart_axis": feedback.get("chart_axis", ""),
                        }
                    )

            pyramidfunnel_chart_samples = [
                {
                    "chart_type": chart["chart_type"],
                    "question": chart["question"],
                    "chart_title": chart["chart_title"],
                    "chart_axis": chart["chart_axis"],
                }
                for chart in liked_feedbacks
                if chart["chart_type"] == "pyramidfunnel_chart"
            ]

            AXIS_SAMPLES = pyramidfunnel_chart_samples or [
                {
                    "chart_type": "pyramidfunnel_chart",
                    "question": "How does the mobile product lead conversion funnel compare to broadband in terms of their percentage contribution to the overall monthly EBIT?",
                    "chart_title": "Pyramid Funnel: Lead Conversion of Mobile vs Broadband Products and Contribution to Monthly EBIT",
                    "chart_axis": """{"xAxis_title": "Product Category", "xAxis_column": "Product", "yAxis_title": "Percentage Contribution to EBIT", "yAxis_column": "EBIT", "yAxis_aggregation": "SUM"}""",
                },
                {
                    "chart_type": "pyramidfunnel_chart",
                    "question": "How do the customer acquisition funnels compare between different service categories in terms of their contribution to the overall customer base?",
                    "chart_title": "Pyramid Funnel: Customer Acquisition by Service Category and Contribution to Total Customer Base",
                    "chart_axis": """{"xAxis_title": "Service Category", "xAxis_column": "Service_Type", "yAxis_title": "Percentage Contribution to Customer Base", "yAxis_column": "Customer_Base_Contribution", "yAxis_aggregation": "SUM"}""",
                },
                {
                    "chart_type": "pyramidfunnel_chart",
                    "question": "How does cost efficiency funnel vary across different product categories?",
                    "chart_title": "Pyramid Funnel: Cost Efficiency by Product Category",
                    "chart_axis": '{"xAxis_title": "Product Category", "xAxis_column": "Product", "yAxis_title": "Cost Efficiency", "yAxis_column": "Cost_Efficiency", "yAxis_aggregation": "MAX"}',
                },
                {
                    "chart_type": "pyramidfunnel_chart",
                    "question": "How does the actual revenue variance compare to the forecasted percentage contribution across different products?",
                    "chart_title": "Revenue Variance Distribution: Actual vs Forecast Percentage Contribution (Past Two Years)",
                    "chart_axis": '{"xAxis_title": "Year", "xAxis_column": "Date", "yAxis_title": "Revenue Variance: Actual vs Forecast", "yAxis_column": "RevenueVariance_Actual_vs_Forecast", "yAxis_aggregation": "AVG"}',
                },
            ]

        elif chart_type in ["pie_chart"]:
            x_axis_column_candidate_list = [
                column_name
                for column_name in database_summary.column_name_list
                if column_name != ""
                and database_summary.column_n_unique_value_dict[column_name] > 1
                and database_summary.column_n_unique_value_dict[column_name] <= 12
                and database_summary.column_data_tribes[column_name] in ["categorical"]
            ]

            schema_json = PyramidPieChartSchema.model_json_schema()

            schema_json["properties"]["xAxis_column"]["enum"] = (
                x_axis_column_candidate_list
            )
            schema_json["properties"]["yAxis_column"]["enum"] = (
                database_summary.column_name_list
            )
            schema_json["properties"]["yAxis_aggregation"]["enum"] = [
                "SUM",
                "AVG",
                "MEDIAN",
                "MEAN",
                "MIN",
                "MAX",
                "COUNT",
            ]

            FORMAT_INSTRUCTIONS = """{"xAxis_title": "...", "xAxis_column": "...", "yAxis_title": "...", "yAxis_column": "...", "yAxis_aggregation": "..."}"""
            KEY_LIST = [
                "xAxis_title",
                "xAxis_column",
                "yAxis_title",
                "yAxis_column",
                "yAxis_aggregation",
            ]
            TASK_INSTRUCTIONS = """Your task is to identify the appropriate axis columns and generate axis titles for 'xAxis' and 'yAxis' from the database SQL schema. Ensure each title is free from unreadable symbols or characters and is suitable for visualization as chart axis titles. Ensure each title is unique and provides clear context about the represented column data. Specify only one exact column name from the database SQL schema without any additional operator or aggregation for each 'xAxis_column' and 'yAxis_column' information. Each axis MUST have a title that provides complete context regarding the column represented (e.g., title='Total Cost Variance: Actual vs Forecast' from column='CostVariance_Actual_vs_Forecast', title='Average Revenue Variance: Actual vs Budget' from column='RevenueVariance_Actual_vs_Budget'). The 'xAxis_column' MUST be a column with STRING data type only. NEVER use constant values or any other values that are NOT in the database SQL schema for the columns. Y-axis aggregations MUST be selected from 'SUM', 'AVG', 'MEDIAN', 'MEAN', 'MIN', 'MAX', 'COUNT', etc., depending on the question. Ensure each axis title is meaningful and descriptive, using the column names directly without any additional operators or aggregation."""

            # Check if there are any disliked feedbacks for pie chart title
            for feedback in disliked_feedbacks_based_on_axis_title:
                if feedback.get("chart_type") == "pie_chart":
                    BAD_SAMPLES.append(
                        {
                            "chart_type": "pie_chart",
                            "question": feedback.get("question", ""),
                            "chart_title": feedback.get("chart_title", ""),
                            "chart_axis": feedback.get("chart_axis", ""),
                        }
                    )

            pie_chart_samples = [
                {
                    "chart_type": chart["chart_type"],
                    "question": chart["question"],
                    "chart_title": chart["chart_title"],
                    "chart_axis": json.dumps(chart["chart_axis"]),
                }
                for chart in liked_feedbacks
                if chart["chart_type"] == "pie_chart"
            ]

            AXIS_SAMPLES = pie_chart_samples or [
                {
                    "chart_type": "pie_chart",
                    "question": "What proportion of costs is attributed to entertainment and broadband products in 2022?",
                    "chart_title": "Cost Distribution of Entertainment and Broadband Products (2022)",
                    "chart_axis": """{"xAxis_title": "Product Category", "xAxis_column": "Product", "yAxis_title": "Total Cost", "yAxis_column": "Cost", "yAxis_aggregation": "SUM"}""",
                },
                {
                    "chart_type": "pie_chart",
                    "question": "How does the actual revenue variance compare to the forecasted percentage contribution across different products?",
                    "chart_title": "Revenue Variance Distribution: Actual vs Forecast Percentage Contribution (Past Two Years)",
                    "chart_axis": '{"xAxis_title": "Year", "xAxis_column": "Date", "yAxis_title": "Revenue Variance: Actual vs Forecast", "yAxis_column": "RevenueVariance_Actual_vs_Forecast", "yAxis_aggregation": "AVG"}',
                },
                {
                    "chart_type": "pie_chart",
                    "question": "What is the percentage breakdown of sales revenue across different regions for 2023?",
                    "chart_title": "Sales Revenue Distribution by Region (2023)",
                    "chart_axis": '{"xAxis_title": "Region", "xAxis_column": "Region", "yAxis_title": "Total Revenue", "yAxis_column": "Revenue", "yAxis_aggregation": "SUM"}',
                },
                {
                    "chart_type": "pie_chart",
                    "question": "How is the marketing budget allocated across various campaigns in the last quarter?",
                    "chart_title": "Marketing Budget Allocation by Campaign (Last Quarter)",
                    "chart_axis": '{"xAxis_title": "Campaign", "xAxis_column": "Campaign", "yAxis_title": "Budget Allocation", "yAxis_column": "MarketingBudget", "yAxis_aggregation": "SUM"}',
                },
            ]

        elif chart_type in ["histogram_chart"]:
            x_axis_column_candidate_list = [
                column_name
                for column_name in database_summary.column_name_list
                if column_name != ""
                and database_summary.column_data_tribes[column_name] in ["numerical"]
            ]

            schema_json = HistogramChartSchema.model_json_schema()

            schema_json["properties"]["xAxis_column"]["enum"] = (
                x_axis_column_candidate_list
            )

            FORMAT_INSTRUCTIONS = """{"xAxis_title": "...", "xAxis_column": "..."}"""
            KEY_LIST = ["xAxis_title", "xAxis_column"]
            TASK_INSTRUCTIONS = """Your task is to get the appropriate axis columns and generate an axis title for 'xAxis' only from the database SQL schema. Ensure the title is free from unreadable symbols or characters, and suitable for visualization as a chart axis title. Specify only one exact column name from the database SQL schema without any additional operator or aggregation for 'xAxis_column' information only. You MUST ALWAYS INCLUDE an aggregation in 'xAxis_title' where the 'xAxis_column' MUST be a column with NUMERICAL data type. The 'xAxis_column' is intended to be the numerical metric for calculating the frequency of metric range distribution, and no 'yAxis' or 'series' needed. 'xAxis_title' MUST provides complete context of 'xAxis_column' (e.g., title='Total Cost Variance: Actual vs Forecast' from column='CostVariance_Actual_vs_Forecast', title='Average Revenue Variance: Actual vs Budget' from column='RevenueVariance_Actual_vs_Budget'). NEVER USE constant value or any other values which are NOT in the database SQL schema for the column. NEVER USE column with DATE or TEXT data type for xAxis. ENSURE 'xAxis_column' IS A COLUMN WITH NUMERICAL DATA TYPE for calculation, as non-numerical columns cannot be used to calculate distribution frequency. The 'xAxis_column' must only contain one column from the database SQL schema."""

            for feedback in disliked_feedbacks_based_on_axis_title:
                if feedback.get("chart_type") == "histogram_chart":
                    BAD_SAMPLES.append(
                        {
                            "chart_type": "histogram_chart",
                            "question": feedback.get("question", ""),
                            "chart_title": feedback.get("chart_title", ""),
                            "chart_axis": feedback.get("chart_axis", ""),
                        }
                    )

            histogram_chart_samples = [
                {
                    "chart_type": chart["chart_type"],
                    "question": chart["question"],
                    "chart_title": chart["chart_title"],
                    "chart_axis": json.dumps(chart["chart_axis"]),
                    "chart_duration": chart["time_duration"],
                }
                for chart in liked_feedbacks
                if chart["chart_type"] == "histogram_chart"
            ]
            AXIS_SAMPLES = histogram_chart_samples or [
                {
                    "chart_type": "histogram_chart",
                    "question": "What is the distribution of cost efficiency for all products in the current year?",
                    "chart_title": "Distribution of Cost Efficiency for All Products (Current Year)",
                    "chart_axis": """{"xAxis_title": "Cost Efficiency", "xAxis_column": "Cost_Efficiency"}""",
                },
                {
                    "chart_type": "histogram_chart",
                    "question": "How does the distribution of cost variance compare between actual and budget figures?",
                    "chart_title": "Distribution of Cost Variance: Actual vs. Budget for All Products",
                    "chart_axis": """{"xAxis_title": "Cost Variance: Actual vs Budget", "xAxis_column": "CostVariance_Actual_vs_Budget"}""",
                },
                {
                    "chart_type": "histogram_chart",
                    "question": "What does the distribution of product profitability reveal about products with above-average profitability in the past year?",
                    "chart_title": "Distribution of Product Profitability for Products with Above-Average Profitability (Past Year)",
                    "chart_axis": """{"xAxis_title": "Above Average Product Profitability Distribution", "xAxis_column": "Product_Profitability"}""",
                    "chart_duration": "Past Year",
                },
            ]

        elif chart_type in ["grouped_bar_chart"]:
            schema_json = LineGroupBarChartSchema.model_json_schema()

            # Generating series column candidate list where the column has number of unique value more than 1 and less than equal to 4.
            series_column_candidate_list = [
                column_name
                for column_name in database_summary.column_name_list
                if column_name != ""
                and database_summary.column_n_unique_value_dict[column_name] > 1
                and database_summary.column_n_unique_value_dict[column_name] <= 4
                and database_summary.column_data_tribes[column_name] in ["categorical"]
            ]

            schema_json["properties"]["xAxis_column"]["enum"] = (
                database_summary.column_name_list
            )
            schema_json["properties"]["yAxis_column"]["enum"] = (
                database_summary.column_name_list
            )
            schema_json["properties"]["yAxis_aggregation"]["enum"] = [
                "SUM",
                "AVG",
                "MEDIAN",
                "MEAN",
                "MIN",
                "MAX",
                "COUNT",
            ]
            schema_json["properties"]["yAxis2_column"]["enum"] = (
                database_summary.column_name_list
            )
            schema_json["properties"]["yAxis2_column"]["enum"].append("")
            schema_json["properties"]["yAxis2_aggregation"]["enum"] = [
                "SUM",
                "AVG",
                "MEDIAN",
                "MEAN",
                "MIN",
                "MAX",
                "COUNT",
                "",
            ]
            schema_json["properties"]["yAxis3_column"]["enum"] = (
                database_summary.column_name_list
            )
            schema_json["properties"]["yAxis3_column"]["enum"].append("")
            schema_json["properties"]["yAxis3_aggregation"]["enum"] = [
                "SUM",
                "AVG",
                "MEDIAN",
                "MEAN",
                "MIN",
                "MAX",
                "COUNT",
                "",
            ]
            schema_json["properties"]["series_column"]["enum"] = (
                series_column_candidate_list
            )
            schema_json["properties"]["series_column"]["enum"].append("")

            FORMAT_INSTRUCTIONS = """{"xAxis_title": "...", "xAxis_column": "...", "yAxis_title": "...", "yAxis_column": "...", "yAxis_aggregation": "...", "yAxis2_title": "...", "yAxis2_column": "...", "yAxis2_aggregation": "...", "yAxis3_title": "...", "yAxis3_column": "...", "yAxis3_aggregation": "...", "series_title": "...", "series_column": "..."}"""

            KEY_LIST = [
                "xAxis_title",
                "xAxis_column",
                "yAxis_title",
                "yAxis_column",
                "yAxis_aggregation",
                "yAxis2_title",
                "yAxis2_column",
                "yAxis2_aggregation",
                "yAxis3_title",
                "yAxis3_column",
                "yAxis3_aggregation",
                "series_title",
                "series_column",
            ]

            TASK_INSTRUCTIONS = "Your task is to identify the appropriate axis columns and generate axis titles for 'xAxis', 'yAxis', 'yAxis2', 'yAxis3', and 'series' from the database SQL schema. The 'series' axis is used for splitting the data into several categories. Ensure each title is free from unreadable symbols or characters and is suitable for visualization as chart axis titles and legends. Ensure each title is unique and provides clear context about the represented column data. Specify only one exact column name from the database SQL schema without any additional operator or aggregation for each 'xAxis_column', 'yAxis_column', 'yAxis2_column', 'yAxis3_column', and 'series_column' information. Each axis must have a title that provides complete context regarding the column represented (e.g., title='Total Cost Variance: Actual vs Forecast' from column='CostVariance_Actual_vs_Forecast', title='Average Revenue Variance: Actual vs Budget' from column='RevenueVariance_Actual_vs_Budget'). Ensure 'xAxis_column' is a column with STRING, NUMERICAL, or DATE data type only. 'yAxis_column', 'yAxis2_column', and 'yAxis3_column' must be columns with NUMERICAL data type only. Never choose a DATE column or TEXT/STRING column for 'yAxis_column', 'yAxis2_column', and 'yAxis3_column'. Ensure 'yAxis_column', 'yAxis2_column', and 'yAxis3_column' are column with NUMERICAL data type. Ensure 'series_column' is a column with TEXT/STRING data type that represents categorical data only. IF there is no column related to the axis or series, generate the title, column, and aggregation key related to the axis or series as empty text only and do not remove the axis or series key(s). Never use constant values or any other values that are not in the database SQL schema for the columns. Never use a column with TEXT or DATE data type for 'yAxis_column', 'yAxis2_column', and 'yAxis3_column'. Y-axis aggregations must be selected from 'SUM', 'AVG', 'MEDIAN', 'MEAN', 'MIN', 'MAX', 'COUNT', etc., depending on the question. ENSURE 'xAxis_column' and 'series_column' are not using the same column!"

            for feedback in disliked_feedbacks_based_on_axis_title:
                if feedback.get("chart_type") == "grouped_bar_chart":
                    BAD_SAMPLES.append(
                        {
                            "chart_type": "grouped_bar_chart",
                            "question": feedback.get("question", ""),
                            "chart_title": feedback.get("chart_title", ""),
                            "chart_axis": feedback.get("chart_axis", ""),
                        }
                    )

            grouped_bar_chart_samples = [
                {
                    "chart_type": chart["chart_type"],
                    "question": chart["question"],
                    "chart_title": chart["chart_title"],
                    "chart_axis": chart["chart_axis"],
                }
                for chart in liked_feedbacks
                if chart["chart_type"] == "grouped_bar_chart"
            ]

            AXIS_SAMPLES = grouped_bar_chart_samples or [
                {
                    "chart_type": "grouped_bar_chart",
                    "question": "How do the actual versus forecast variances in cost, revenue, and EBIT compare across different product categories?",
                    "chart_title": "Actual vs Forecast Variances for Cost, Revenue, and EBIT by Product",
                    "chart_axis": '{"xAxis_title": "Product Category", "xAxis_column": "Product", "yAxis_title": "Total Variance", "yAxis_column": "Variance_Value", "yAxis_aggregation": "SUM", "yAxis2_title": "Cost Variance", "yAxis2_column": "CostVariance", "yAxis2_aggregation": "SUM", "yAxis3_title": "Revenue Variance", "yAxis3_column": "RevenueVariance", "yAxis3_aggregation": "SUM", "series_title": "Variance Type", "series_column": "variance"}',
                },
                {
                    "chart_type": "grouped_bar_chart",
                    "question": "How do the actual versus forecast variances in cost, revenue, and EBIT compare across different product categories?",
                    "chart_title": "Actual vs Forecast Variances for Cost, Revenue, and EBIT by Product",
                    "chart_axis": '{"xAxis_title": "Product Category", "xAxis_column": "Product", "yAxis_title": "Total Cost Variance Actual vs Forecast", "yAxis_column": "CostVariance_Actual_vs_Forecast", "yAxis_aggregation": "SUM", "yAxis2_title": "Total Revenue Variance Actual vs Forecast", "yAxis2_column": "RevenueVariance_Actual_vs_Forecast", "yAxis2_aggregation": "SUM", "yAxis3_title": "Total EBIT Variance Actual vs Forecast", "yAxis3_column": "EBITVariance_Actual_vs_Forecast", "yAxis3_aggregation": "SUM", "series_title": "", "series_column": ""}',
                },
                {
                    "chart_type": "grouped_bar_chart",
                    "question": "How do quarterly profit margins for each product line compare over the last year?",
                    "chart_title": "Quarterly Profit Margins by Product Line (Last Year)",
                    "chart_axis": '{"xAxis_title": "Quarter", "xAxis_column": "Quarter", "yAxis_title": "Profit Margin", "yAxis_column": "ProfitMargin", "yAxis_aggregation": "AVG", "yAxis2_title": "Revenue", "yAxis2_column": "Revenue", "yAxis2_aggregation": "SUM", "yAxis3_title": "Cost", "yAxis3_column": "Cost", "yAxis3_aggregation": "SUM", "series_title": "Product Line", "series_column": "ProductLine"}',
                },
                {
                    "chart_type": "grouped_bar_chart",
                    "question": "What are the year-over-year changes in sales and operating expenses for key regions?",
                    "chart_title": "Year-over-Year Sales and Operating Expenses by Region",
                    "chart_axis": '{"xAxis_title": "Region", "xAxis_column": "Region", "yAxis_title": "Sales", "yAxis_column": "Sales", "yAxis_aggregation": "SUM", "yAxis2_title": "Operating Expenses", "yAxis2_column": "OperatingExpenses", "yAxis2_aggregation": "SUM", "yAxis3_title": "", "yAxis3_column": "", "yAxis3_aggregation": "", "series_title": "Year", "series_column": "Year"}',
                },
            ]

        elif chart_type in ["line_chart"]:
            schema_json = LineGroupBarChartSchema.model_json_schema()

            # Generating series column candidate list where the column has number of unique value more than 1 and less than equal to 4.
            series_column_candidate_list = [
                column_name
                for column_name in database_summary.column_name_list
                if column_name != ""
                and database_summary.column_n_unique_value_dict[column_name] > 1
                and database_summary.column_n_unique_value_dict[column_name] <= 4
                and database_summary.column_data_tribes[column_name] in ["categorical"]
            ]

            schema_json["properties"]["xAxis_column"]["enum"] = (
                database_summary.column_name_list
            )
            schema_json["properties"]["yAxis_column"]["enum"] = (
                database_summary.column_name_list
            )
            schema_json["properties"]["yAxis_aggregation"]["enum"] = [
                "SUM",
                "AVG",
                "MEDIAN",
                "MEAN",
                "MIN",
                "MAX",
                "COUNT",
            ]
            schema_json["properties"]["yAxis2_column"]["enum"] = (
                database_summary.column_name_list
            )
            schema_json["properties"]["yAxis2_column"]["enum"].append("")
            schema_json["properties"]["yAxis2_aggregation"]["enum"] = [
                "SUM",
                "AVG",
                "MEDIAN",
                "MEAN",
                "MIN",
                "MAX",
                "COUNT",
                "",
            ]
            schema_json["properties"]["yAxis3_column"]["enum"] = (
                database_summary.column_name_list
            )
            schema_json["properties"]["yAxis3_column"]["enum"].append("")
            schema_json["properties"]["yAxis3_aggregation"]["enum"] = [
                "SUM",
                "AVG",
                "MEDIAN",
                "MEAN",
                "MIN",
                "MAX",
                "COUNT",
                "",
            ]
            schema_json["properties"]["series_column"]["enum"] = (
                series_column_candidate_list
            )
            schema_json["properties"]["series_column"]["enum"].append("")

            FORMAT_INSTRUCTIONS = """{"xAxis_title": "...", "xAxis_column": "...", "yAxis_title": "...", "yAxis_column": "...", "yAxis_aggregation": "...", "yAxis2_title": "...", "yAxis2_column": "...", "yAxis2_aggregation": "...", "yAxis3_title": "...", "yAxis3_column": "...", "yAxis3_aggregation": "...", "series_title": "...", "series_column": "..."}"""

            KEY_LIST = [
                "xAxis_title",
                "xAxis_column",
                "yAxis_title",
                "yAxis_column",
                "yAxis_aggregation",
                "yAxis2_title",
                "yAxis2_column",
                "yAxis2_aggregation",
                "yAxis3_title",
                "yAxis3_column",
                "yAxis3_aggregation",
                "series_title",
                "series_column",
            ]

            TASK_INSTRUCTIONS = "Your task is to identify the appropriate axis columns and generate axis titles for 'xAxis', 'yAxis', 'yAxis2', 'yAxis3', and 'series' from the database SQL schema. The 'series' axis is used for splitting the data into several categories. Ensure each title is free from unreadable symbols or characters and is suitable for visualization as chart axis titles and legends. Ensure each title is unique and provides clear context about the represented column data. Specify only one exact column name from the database SQL schema without any additional operator or aggregation for each 'xAxis_column', 'yAxis_column', 'yAxis2_column', 'yAxis3_column', and 'series_column' information. Each axis must have a title that provides complete context regarding the column represented (e.g., title='Total Cost Variance: Actual vs Forecast' from column='CostVariance_Actual_vs_Forecast', title='Average Revenue Variance: Actual vs Budget' from column='RevenueVariance_Actual_vs_Budget'). Ensure 'xAxis_column' is a column with STRING, NUMERICAL, or DATE data type only. 'yAxis_column', 'yAxis2_column', and 'yAxis3_column' must be columns with NUMERICAL data type only. Never choose a DATE column or TEXT/STRING column for 'yAxis_column', 'yAxis2_column', and 'yAxis3_column'. Ensure 'yAxis_column', 'yAxis2_column', and 'yAxis3_column' are column with NUMERICAL data type. Ensure 'series_column' is a column with TEXT/STRING data type that represents categorical data only. IF there is no column related to the axis or series, generate the title, column, and aggregation key related to the axis or series as empty text only and do not remove the axis or series key(s). Never use constant values or any other values that are not in the database SQL schema for the columns. Never use a column with TEXT or DATE data type for 'yAxis_column', 'yAxis2_column', and 'yAxis3_column'. Y-axis aggregations must be selected from 'SUM', 'AVG', 'MEDIAN', 'MEAN', 'MIN', 'MAX', 'COUNT', etc., depending on the question. ENSURE 'xAxis_column' and 'series_column' are not using the same column!"

            for feedback in disliked_feedbacks_based_on_axis_title:
                if feedback.get("chart_type") == "line_chart":
                    BAD_SAMPLES.append(
                        {
                            "chart_type": "line_chart",
                            "question": feedback.get("question", ""),
                            "chart_title": feedback.get("chart_title", ""),
                            "chart_axis": feedback.get("chart_axis", ""),
                        }
                    )

            line_chart_samples = [
                {
                    "chart_type": chart["chart_type"],
                    "question": chart["question"],
                    "chart_title": chart["chart_title"],
                    "chart_axis": chart["chart_axis"],
                }
                for chart in liked_feedbacks
                if chart["chart_type"] == "line_chart"
            ]

            AXIS_SAMPLES = line_chart_samples or [
                {
                    "chart_type": "line_chart",
                    "question": "What trends or patterns can be observed in the overall earnings per cost across the quarters?",
                    "chart_title": "Quarterly Average Earnings per Cost (Past Year)",
                    "chart_axis": '{"xAxis_title": "Quarter", "xAxis_column": "Date", "yAxis_title": "Average Earnings per Cost", "yAxis_column": "Earning_per_Cost", "yAxis_aggregation": "AVG", "yAxis2_title": "", "yAxis2_column": "", "yAxis2_aggregation": "", "yAxis3_title": "", "yAxis3_column": "", "yAxis3_aggregation": "", "series_title": "", "series_column": ""}',
                },
                {
                    "chart_type": "line_chart",
                    "question": "How do earnings per cost vary across different sales channels over the quarters?",
                    "chart_title": "Quarterly Average Earnings per Cost for Each Sales Channel (Past Year)",
                    "chart_axis": '{"xAxis_title": "Quarter", "xAxis_column": "Date", "yAxis_title": "Average Earnings per Cost", "yAxis_column": "Earning_per_Cost", "yAxis_aggregation": "AVG", "yAxis2_title": "", "yAxis2_column": "", "yAxis2_aggregation": "", "yAxis3_title": "", "yAxis3_column": "", "yAxis3_aggregation": "", "series_title": "Sales Channel", "series_column": "sales_channel"}',
                },
                {
                    "chart_type": "line_chart",
                    "question": "What are the trends in monthly customer retention rates over the past year?",
                    "chart_title": "Monthly Customer Retention Trends (Past Year)",
                    "chart_axis": '{"xAxis_title": "Month", "xAxis_column": "Month", "yAxis_title": "Retention Rate", "yAxis_column": "RetentionRate", "yAxis_aggregation": "AVG", "yAxis2_title": "", "yAxis2_column": "", "yAxis2_aggregation": "", "yAxis3_title": "", "yAxis3_column": "", "yAxis3_aggregation": "", "series_title": "", "series_column": ""}',
                },
                {
                    "chart_type": "line_chart",
                    "question": "How has the revenue growth rate changed across different regions over the past two years?",
                    "chart_title": "Regional Revenue Growth Trends (Last Two Years)",
                    "chart_axis": '{"xAxis_title": "Time Period", "xAxis_column": "Time", "yAxis_title": "Revenue Growth Rate", "yAxis_column": "RevenueGrowthRate", "yAxis_aggregation": "AVG", "yAxis2_title": "", "yAxis2_column": "", "yAxis2_aggregation": "", "yAxis3_title": "", "yAxis3_column": "", "yAxis3_aggregation": "", "series_title": "Region", "series_column": "Region"}',
                },
            ]

        elif chart_type in ["barlinecombo_chart"]:
            schema_json = BarlineComboChartSchema.model_json_schema()

            schema_json["properties"]["xAxis_column"]["enum"] = (
                database_summary.column_name_list
            )
            schema_json["properties"]["yAxisBar_column"]["enum"] = (
                database_summary.column_name_list
            )
            schema_json["properties"]["yAxisBar_aggregation"]["enum"] = [
                "SUM",
                "AVG",
                "MEDIAN",
                "MEAN",
                "MIN",
                "MAX",
                "COUNT",
            ]
            schema_json["properties"]["yAxisLine_column"]["enum"] = (
                database_summary.column_name_list
            )
            schema_json["properties"]["yAxisLine_aggregation"]["enum"] = [
                "SUM",
                "AVG",
                "MEDIAN",
                "MEAN",
                "MIN",
                "MAX",
                "COUNT",
            ]

            FORMAT_INSTRUCTIONS = """{"xAxis_title": "...", "xAxis_column": "...", "yAxisBar_title": "...", "yAxisBar_column": "...", "yAxisBar_aggregation": "...", "yAxisLine_title": "...", "yAxisLine_column": "...", "yAxisLine_aggregation": "..."}"""
            KEY_LIST = [
                "xAxis_title",
                "xAxis_column",
                "yAxisBar_title",
                "yAxisBar_column",
                "yAxisBar_aggregation",
                "yAxisLine_title",
                "yAxisLine_column",
                "yAxisLine_aggregation",
            ]
            TASK_INSTRUCTIONS = "Your task is to get the appropriate axis columns and generate axis titles for 'xAxis', 'yAxisBar', and 'yAxisLine' from the database SQL schema. Ensure each title is free from unreadable symbols or characters and suitable for visualization as chart axis titles. Ensure each title is unique and provides clear context about the represented column data. Specify only one exact column name from the database SQL schema without any additional operator or aggregation for each 'xAxis_column', 'yAxisBar_column', and 'yAxisLine_column'. The 'xAxis_column' must be a column with a NUMERICAL or DATE-related data type only. Both 'yAxisBar_column' and 'yAxisLine_column' must be columns with a NUMERICAL data type only. Each axis must have a title that provides complete context regarding the column represented (e.g., title='Total Cost Variance: Actual vs Forecast' from column='CostVariance_Actual_vs_Forecast', title='Average Revenue Variance: Actual vs Budget' from column='RevenueVariance_Actual_vs_Budget'). Never use a constant value or any other values that are not in the database SQL schema for the columns. Select only columns with a NUMERICAL data type for 'yAxisBar' and 'yAxisLine'. Y-axis aggregations must be selected from 'SUM', 'AVG', 'MEDIAN', 'MEAN', 'MIN', 'MAX', 'COUNT', etc., depending on the question."

            for feedback in disliked_feedbacks_based_on_axis_title:
                if feedback.get("chart_type") == "barlinecombo_chart":
                    BAD_SAMPLES.append(
                        {
                            "chart_type": "barlinecombo_chart",
                            "question": feedback.get("question", ""),
                            "chart_title": feedback.get("chart_title", ""),
                            "chart_axis": feedback.get("chart_axis", ""),
                        }
                    )

            barlinecombo_chart_samples = [
                {
                    "chart_type": chart["chart_type"],
                    "question": chart["question"],
                    "chart_title": chart["chart_title"],
                    "chart_axis": chart["chart_axis"],
                }
                for chart in liked_feedbacks
                if chart["chart_type"] == "barlinecombo_chart"
            ]

            AXIS_SAMPLES = barlinecombo_chart_samples or [
                {
                    "chart_type": "barlinecombo_chart",
                    "question": "How does the total cost variance between actual and budget compare across different quarters for each product?",
                    "chart_title": "Product-wise Cost Variance: Actual vs Budget per Quarter (Past Year)",
                    "chart_axis": """{"xAxis_title": "Quarter", "xAxis_column": "Date", "yAxisBar_title": "Total Cost Variance: Actual vs Budget", "yAxisBar_column": "CostVariance_Actual_vs_Budget", "yAxisBar_aggregation": "SUM", "yAxisLine_title": "Average Cost Variance: Actual vs Budget", "yAxisLine_column": "CostVariance_Actual_vs_Budget", "yAxisLine_aggregation": "AVG"}""",
                },
                {
                    "chart_type": "barlinecombo_chart",
                    "question": "Which months show the highest revenue generation and cost efficiency for the products?",
                    "chart_title": "Product Monthly Revenue Generation vs Cost Efficiency Comparison (Past Year)",
                    "chart_axis": """{"xAxis_title": "Month", "xAxis_column": "Date", "yAxisBar_title": "Total Revenue Generation", "yAxisBar_column": "Revenue_Generation", "yAxisBar_aggregation": "SUM", "yAxisLine_title": "Total Cost Efficiency", "yAxisLine_column": "Cost_Efficiency", "yAxisLine_aggregation": "SUM"}""",
                },
                {
                    "chart_type": "barlinecombo_chart",
                    "question": "How does the EBIT contribution of the top 5 products compare to the overall EBIT on a monthly basis?",
                    "chart_title": "Monthly EBIT Contribution of Top 5 Products vs Overall EBIT (Past Year)",
                    "chart_axis": """{"xAxis_title": "Month", "xAxis_column": "Date", "yAxisBar_title": "EBIT Contribution of Top 5 Products", "yAxisBar_column": "EBIT", "yAxisBar_aggregation": "SUM", "yAxisLine_title": "Overall EBIT", "yAxisLine_column": "EBIT", "yAxisLine_aggregation": "SUM"}""",
                },
            ]

        elif chart_type in ["scatterplot_chart"]:
            schema_json = ScatterplotChartSchema.model_json_schema()

            # Generating series column candidate list where the column has number of unique value more than 1 and less than equal to 4.
            series_column_candidate_list = [
                column_name
                for column_name in database_summary.column_name_list
                if column_name != ""
                and database_summary.column_n_unique_value_dict[column_name] > 1
                and database_summary.column_n_unique_value_dict[column_name] <= 4
                and database_summary.column_data_tribes[column_name] in ["categorical"]
            ]

            numerical_column_candidate_list = [
                column_name
                for column_name in database_summary.column_name_list
                if column_name != ""
                and database_summary.column_data_tribes[column_name] in ["numerical"]
            ]

            schema_json["properties"]["xAxis_column"]["enum"] = (
                numerical_column_candidate_list
            )
            schema_json["properties"]["yAxis_column"]["enum"] = (
                numerical_column_candidate_list
            )
            schema_json["properties"]["series_column"]["enum"] = (
                series_column_candidate_list
            )
            schema_json["properties"]["series_column"]["enum"].append("")

            FORMAT_INSTRUCTIONS = """{"xAxis_title": "...", "xAxis_column": "...", "yAxis_title": "...", "yAxis_column": "...", "series_title": "...", "series_column": "..."}"""

            KEY_LIST = [
                "xAxis_title",
                "xAxis_column",
                "yAxis_title",
                "yAxis_column",
                "series_title",
                "series_column",
            ]

            TASK_INSTRUCTIONS = "Your task is to identify the appropriate axis columns and generate axis titles for 'xAxis', 'yAxis', and 'series' from the database SQL schema. The 'series' axis is used for splitting the data into several categories. Ensure each title is free from unreadable symbols or characters and is suitable for visualization as chart axis titles and legends. Ensure each title is unique and provides clear context about the represented column data. Specify only one exact column name from the database SQL schema without any additional operator or aggregation for each 'xAxis_column', 'yAxis_column', and 'series_column' information. Each axis must have a title that provides complete context regarding the column represented (e.g., title='Total Cost Variance: Actual vs Forecast' from column='CostVariance_Actual_vs_Forecast', title='Average Revenue Variance: Actual vs Budget' from column='RevenueVariance_Actual_vs_Budget'). Ensure 'xAxis_column' and 'yAxis_column' are using columns with NUMERICAL data type only. Ensure 'series_column' is a column with TEXT/STRING data type that represents categorical data only. IF there is no column related to the series, generate the series title and column key as empty text only and do not remove the key(s). Never use constant values or any other values that are not in the database SQL schema for the columns. Never use a column with TEXT or DATE data type for 'xAxis_column' and 'yAxis_column'."

            for feedback in disliked_feedbacks_based_on_axis_title:
                if feedback.get("chart_type") == "scatterplot_chart":
                    BAD_SAMPLES.append(
                        {
                            "chart_type": "scatterplot_chart",
                            "question": feedback.get("question", ""),
                            "chart_title": feedback.get("chart_title", ""),
                            "chart_axis": feedback.get("chart_axis", ""),
                        }
                    )

            scatterplot_chart_samples = [
                {
                    "chart_type": chart["chart_type"],
                    "question": chart["question"],
                    "chart_title": chart["chart_title"],
                    "chart_axis": chart["chart_axis"],
                }
                for chart in liked_feedbacks
                if chart["chart_type"] == "scatterplot_chart"
            ]

            AXIS_SAMPLES = scatterplot_chart_samples or [
                {
                    "chart_type": "scatterplot_chart",
                    "question": "What is the relationship between product price and customer ratings across various products?",
                    "chart_title": "Product Price vs Customer Ratings by Brand",
                    "chart_axis": '{"xAxis_title": "Product Price", "xAxis_column": "Product_Price", "yAxis_title": "Customer Ratings", "yAxis_column": "Customer_Ratings", "series_title": "Brand", "series_column": "brand"}',
                },
                {
                    "chart_type": "scatterplot_chart",
                    "question": "How do marketing spend and revenue generation compare across different campaigns?",
                    "chart_title": "Marketing Spend vs Revenue Generation",
                    "chart_axis": '{"xAxis_title": "Marketing Spend", "xAxis_column": "Marketing_Spend", "yAxis_title": "Revenue Generation", "yAxis_column": "Revenue_Generation", "series_title": "", "series_column": ""}',
                },
                {
                    "chart_type": "scatterplot_chart",
                    "question": "How do website traffic and conversion rates correlate across different regions?",
                    "chart_title": "Website Traffic vs Conversion Rates (By Region)",
                    "chart_axis": '{"xAxis_title": "Website Traffic", "xAxis_column": "Website_Traffic", "yAxis_title": "Conversion Rates", "yAxis_column": "Conversion_Rates", "series_title": "", "series_column": ""}',
                },
                {
                    "chart_type": "scatterplot_chart",
                    "question": "What is the correlation between advertising budget and sales performance across different product categories?",
                    "chart_title": "Advertising Budget vs Sales Performance by Product Category",
                    "chart_axis": '{"xAxis_title": "Advertising Budget", "xAxis_column": "Advertising_Budget", "yAxis_title": "Sales Performance", "yAxis_column": "Sales_Performance", "series_title": "Product Category", "series_column": "product_category"}',
                },
                {
                    "chart_type": "scatterplot_chart",
                    "question": "What is the relationship between employee satisfaction and productivity levels across departments?",
                    "chart_title": "Employee Satisfaction vs Productivity (By Department)",
                    "chart_axis": '{"xAxis_title": "Employee Satisfaction", "xAxis_column": "Employee_Satisfaction", "yAxis_title": "Productivity Levels", "yAxis_column": "Productivity_Levels", "series_title": "Department", "series_column": "department"}',
                },
            ]

        elif chart_type in ["bubbleplot_chart"]:
            schema_json = BubbleplotChartSchema.model_json_schema()

            # Generating series column candidate list where the column has number of unique value more than 1 and less than equal to 4.
            series_column_candidate_list = [
                column_name
                for column_name in database_summary.column_name_list
                if column_name != ""
                and database_summary.column_n_unique_value_dict[column_name] > 1
                and database_summary.column_n_unique_value_dict[column_name] <= 4
                and database_summary.column_data_tribes[column_name] in ["categorical"]
            ]

            numerical_column_candidate_list = [
                column_name
                for column_name in database_summary.column_name_list
                if column_name != ""
                and database_summary.column_data_tribes[column_name] in ["numerical"]
            ]

            schema_json["properties"]["xAxis_column"]["enum"] = (
                numerical_column_candidate_list
            )
            schema_json["properties"]["yAxis_column"]["enum"] = (
                numerical_column_candidate_list
            )
            schema_json["properties"]["zAxis_column"]["enum"] = (
                numerical_column_candidate_list
            )
            schema_json["properties"]["series_column"]["enum"] = (
                series_column_candidate_list
            )
            schema_json["properties"]["series_column"]["enum"].append("")

            FORMAT_INSTRUCTIONS = """{"xAxis_title": "...", "xAxis_column": "...", "yAxis_title": "...", "yAxis_column": "...", "zAxis_title": "...", "zAxis_column": "...", "series_title": "...", "series_column": "..."}"""

            KEY_LIST = [
                "xAxis_title",
                "xAxis_column",
                "yAxis_title",
                "yAxis_column",
                "zAxis_title",
                "zAxis_column",
                "series_title",
                "series_column",
            ]

            TASK_INSTRUCTIONS = """Your task is to identify the appropriate axis columns and generate axis titles for 'xAxis', 'yAxis', 'zAxis', and 'series' from the database SQL schema. 
    - zAxis-title cannot be empty string.
    - The 'series' axis is used for splitting the data into several categories. 
    - Ensure each title is free from unreadable symbols or characters and is suitable for visualization as chart axis titles and legends. Ensure each title is unique and provides clear context about the represented column data. 
    - Specify only one exact column name from the database SQL schema without any additional operator or aggregation for each 'xAxis_column', 'yAxis_column', 'zAxis_column', and 'series_column' information. 
    - Each axis must have a title that provides complete context regarding the column represented (e.g., title='Total Cost Variance: Actual vs Forecast' from column='CostVariance_Actual_vs_Forecast', title='Average Revenue Variance: Actual vs Budget' from column='RevenueVariance_Actual_vs_Budget'). 
    - Ensure 'xAxis_column' and 'yAxis_column' are using a column with NUMERICAL data type only. 
    - Ensure 'series_column' is a column with TEXT/STRING data type that represents categorical data only. 
    - IF there is no column related to the series, generate the series title and column key as empty text only and do not remove the key(s).
    - Never use constant values or any other values that are not in the database SQL schema for the columns. 
    - Never use a column with TEXT or DATE data type for 'xAxis_column', 'yAxis_column', and 'zAxis_column'. 
    - Ensure 'z-axis' or 'zAxis-titles' is not Empty. 
    - Ensure 'zAxis-title' is not an empty string."""

            for feedback in disliked_feedbacks_based_on_axis_title:
                if feedback.get("chart_type") == "bubbleplot_chart":
                    BAD_SAMPLES.append(
                        {
                            "chart_type": "bubbleplot_chart",
                            "question": feedback.get("question", ""),
                            "chart_title": feedback.get("chart_title", ""),
                            "chart_axis": feedback.get("chart_axis", ""),
                        }
                    )

            bubbleplot_chart_samples = [
                {
                    "chart_type": chart["chart_type"],
                    "question": chart["question"],
                    "chart_title": chart["chart_title"],
                    "chart_axis": chart["chart_axis"],
                }
                for chart in liked_feedbacks
                if chart["chart_type"] == "bubbleplot_chart"
            ]

            AXIS_SAMPLES = bubbleplot_chart_samples or [
                {
                    "chart_type": "bubbleplot_chart",
                    "question": "How do employee satisfaction, productivity levels, and team size relate across different departments?",
                    "chart_title": "Employee Satisfaction vs Productivity vs Team Size by Department",
                    "chart_axis": '{"xAxis_title": "Employee Satisfaction", "xAxis_column": "Employee_Satisfaction", "yAxis_title": "Productivity Level", "yAxis_column": "Productivity_Level", "zAxis_title": "Team Size", "zAxis_column": "Team_Size", "series_title": "Department Name", "series_column": "department_name"}',
                },
                {
                    "chart_type": "bubbleplot_chart",
                    "question": "What is the relationship between project duration, team size, and budget for various projects?",
                    "chart_title": "Project Duration vs Team Size vs Budget",
                    "chart_axis": '{"xAxis_title": "Project Duration (months)", "xAxis_column": "Project_Duration", "yAxis_title": "Team Size", "yAxis_column": "Team_Size", "zAxis_title": "Budget", "zAxis_column": "Project_Budget", "series_title": "", "series_column": ""}',
                },
                {
                    "chart_type": "bubbleplot_chart",
                    "question": "How do sales volume, customer acquisition cost, and customer lifetime value vary across different regions?",
                    "chart_title": "Sales Volume vs Customer Acquisition Cost vs Customer Lifetime Value by Region",
                    "chart_axis": '{"xAxis_title": "Sales Volume", "xAxis_column": "Sales_Volume", "yAxis_title": "Customer Acquisition Cost", "yAxis_column": "Customer_Acquisition_Cost", "zAxis_title": "Customer Lifetime Value", "zAxis_column": "Customer_Lifetime_Value", "series_title": "Region", "series_column": "region"}',
                },
                {
                    "chart_type": "bubbleplot_chart",
                    "question": "What is the relationship between marketing spend, number of leads, and conversion rate across different campaigns?",
                    "chart_title": "Marketing Spend vs Leads vs Conversion Rate by Campaign",
                    "chart_axis": '{"xAxis_title": "Marketing Spend", "xAxis_column": "Marketing_Spend", "yAxis_title": "Number of Leads", "yAxis_column": "Leads", "zAxis_title": "Conversion Rate", "zAxis_column": "Conversion_Rate", "series_title": "Campaign Name", "series_column": "campaign_name"}',
                },
                {
                    "chart_type": "bubbleplot_chart",
                    "question": "How do product pricing, sales volume, and profit margins vary across different product categories?",
                    "chart_title": "Product Pricing vs Sales Volume vs Profit Margin by Product Category",
                    "chart_axis": '{"xAxis_title": "Product Pricing", "xAxis_column": "Product_Pricing", "yAxis_title": "Sales Volume", "yAxis_column": "Sales_Volume", "zAxis_title": "Profit Margin", "zAxis_column": "Profit_Margin", "series_title": "Product Category", "series_column": "product_category"}',
                },
            ]

        elif chart_type in ["table_chart"]:
            return (
                {
                    "xAxis_title": "all",
                    "xAxis_column": "all",
                    "yAxis_title": "all",
                    "yAxis_column": "all",
                },
                input_tokens,
                output_tokens,
            )
        else:
            print(
                f"'{chart_type}' Chart Type is not supported in Chart Axis Generator!"
            )
            code_level_logger.error(
                f"'{chart_type}' Chart Type is not supported in Chart Axis Generator!"
            )
            return None, input_tokens, output_tokens

        if chart_type in ["histogram_chart"]:
            yaxis_numerical_instruction = "NEVER INCLUDE columns and titles for other axis or series except for x-axis."
        else:
            yaxis_numerical_instruction = "ENSURE the columns related to y-axis are column with 'numerical' data type, not column with 'date' data type, and can be pivoted."

        BAD_SAMPLES_INSTRUCTION = ""
        if BAD_SAMPLES:
            BAD_SAMPLES_INSTRUCTION = f"""
    Strictly Avoid Repeating These Patterns:
    - The following examples represent axis titles or chart-related responses that were deemed unsatisfactory by users. These responses failed to meet key expectations such as clarity, relevance, and specificity. You must avoid generating any responses that resemble these examples in structure, wording, or intent:

    {BAD_SAMPLES}

    Reasons to Avoid These Patterns:
    - The above samples indicates issues with lack of clarity, overly broad descriptions, and failure to provide detailed context that accurately reflects the data being presented. These axis titles do not sufficiently explain the data, making them ineffective for analysis or decision-making.
    
    Instructions:
    - Please ensure your generated axis titles are precise, meaningful, and directly tied to the data in question. The axis titles should provide clear context and aid in the understanding of the data, without being vague or generic. Do not replicate the problematic patterns seen in the bad examples above.

    Focus on:
    - Specificity: Use concrete, relevant column names and avoid vague or generic titles.
    - Clarity: Provide detailed, unambiguous titles that clearly describe the data represented.
    - Context: Ensure the titles fully reflect the context of the data without being overly simplistic or uninformative."""

        system_prompt = f"""You are an experienced data analyst in {os.getenv("INDUSTRY_DOMAIN")} industry. {TASK_INSTRUCTIONS}

    Ensure axis informations generated meet these criterias:
    - ENSURE every axis or series information consist of title and its respective column name.
    - ENSURE every axis or series respective column name only contain ONE EXACT column name from the given database without any aggregation or operator.
    - {yaxis_numerical_instruction}
    - Ensure every axis and series title should be concise, clear, and derived directly from the respective column name.
    - Ensure to include sufficient context in every axis and series title to convey their meaning clearly.
    - Ensure each axis and series title is descriptive and meaningful, and AVOID axis and series title contain vague terms like "Amount", "Value", "Total Amount", "Sum Value", "Average Value", "Time", "Date", etc.
    - Each axis and series title should avoid ambiguity by being specific about the data they represent. For example, instead of 'Value' or 'Aggregated Amount', use 'Sales'.
    - Ensure that the axis and series title remain readable and use full descriptive names. For example, if the column name is 'CostVariance_Actual_vs_Forecast', the axis title should be 'Cost Variance: Actual vs Forecast' rather than abbreviated or partial title like 'Cost Variance', 'Variance', or 'Cost'.
    - ALWAYS GENERATE ONLY a VALID and COMPLETE JSON response.
    - ENSURE date related title match the time frame (e.g., 'Monthly', 'Weekly', 'Daily', 'Anually', 'Yearly', etc) from the question or chart title given IF exist.
    - IF x-axis is related to date, ensure x-axis title uses time frame phrase (e.g., 'Month', 'Quarter', 'Week', 'Day', 'Year', etc.) and avoid including time duration phrase (e.g., 'Past Two Years', 'Last Six Months', '2022 - 2023', etc.).
    - ENSURE that the chart axis and series title do not include the term "Time". Title should STRICTLY USE SPECIFIC TIME UNITS like "Day", "Week", "Month", "Quarter", or "Year".
    - For y-axis with numerical columns, include the specified aggregation in the title. For example, use 'Average Revenue', 'Total Cost', 'Median Profit', 'Total Count' etc.
    - For aggregations, always generate it in a string format consisting of single aggregation term.
    - ENSURE axis or series title is not empty text only if the respective column is not empty text.
    - ENSURE to include all axis and/or series keys in the JSON format given even when the respective value is empty text.
    - STRICTLY AVOID including time duration (e.g., 'Past Two Years', 'Last Six Months', etc.) in the axis and series title.
    - Use 'Monthly' as a default time frame when time frame is required in that specific chart and no time frame request from the user intent.
    - Use 'Past One Year' as a default time duration when time duration is required in that specific chart and no time frame specified in the user intent.
    - Use 'Total' as a default aggregation term when numerical metric must be shown and no aggregation term specified in the user intent.
    - ENSURE no identical y-axis title, y-axis column, and y-axis aggregation.
    - ENSURE x-axis title is not empty.
    - ENSURE each y-axis title is unique and clear.
    - ENSURE series column is a TEXT or STRING column.
    - ENSURE that series column use a column that has more than 1 and less than equal to 4 number of unique values, to maintain chart clarity and avoid clutter. If the column doesn't meet this criterion, do not use it.
    - ENSURE title and column of each axis and series aligns with each other.
    - ENSURE x-axis and series are not identical.
    - ENSURE the axis title explicitly and accurately represent the corresponding axis column, guaranteeing clarity and a direct connection between each title and the data displayed on that axis.

    You must include all keys from this key list in your response: {KEY_LIST}

    For more context, you are provided a database SQL schema, database table description, and database column description to support the chart axis generation.

    Database SQL Schema:
    {database_summary.database_schema_sql}

    Database Table Description:
    {database_summary.table_description}

    {generate_column_information_prompt(database_summary.column_description_dict,database_summary.column_sample_dict,database_summary.column_display_name_dict,database_summary.column_n_unique_value_dict,database_summary.column_data_tribes)}

    Please ensure that each axis title directly reflects its respective column display name. Avoid creating generic or combined titles that do not directly relate to the specific columns; instead, use titles that accurately represent each respective individual column. DO NOT LEAVE THE CHART AXIS TITLE EMPTY IF THE CHART AXIS IS NOT EMPTY. PLEASE DO NOT HALLUCINATE!!

    ENSURE your response is COMPLETE and NEVER ENDS abruptly. NEVER INCLUDE ANY EXPLANATIONS or NOTES on your response. ENSURE the axis title and its respective column generated in a VALID JSON dictionary format given below.

    {FORMAT_INSTRUCTIONS}

    """

        user_prompt = f"""Generate the axis title and its respective column required for the {chart_type} chart based on the question with its respective chart title below.

    Question: {question}

    Chart title: {chart_title}

    """

        SAMPLE_USER_PROMPT = """Generate the axis title and its respective column required for the {chart_type} chart based on the question with its respective chart title below.

    Question: {question}

    Chart title: {chart_title}"""

        TARGET_TOKEN_LIMIT = int(os.getenv("QUESTION_TOTAL_INPUT_TOKEN_LIMIT", "0"))

        if TARGET_TOKEN_LIMIT == 0:
            raise ValueError("TARGET_TOKEN_LIMIT is invalid!")

        # Start with the system prompt (without bad samples instruction for now)
        total_num_tokens = calculate_token_usage(user_prompt, system_prompt)

        messages = [
            {"role": "system", "content": system_prompt},
        ]

        for SAMPLE in AXIS_SAMPLES:
            user_prompt_message = {
                "role": "user",
                "content": SAMPLE_USER_PROMPT.format(
                    chart_type=SAMPLE["chart_type"],
                    question=SAMPLE["question"],
                    chart_title=SAMPLE["chart_title"],
                ),
            }
            user_prompt_tokens = calculate_token_usage(user_prompt_message["content"])

            assistant_message = {
                "role": "assistant",
                "content": json.dumps(SAMPLE["chart_axis"]),
            }
            assistant_tokens = calculate_token_usage(assistant_message["content"])

            # Check if adding this SAMPLE would exceed the token limit
            if (
                total_num_tokens + user_prompt_tokens + assistant_tokens
                > TARGET_TOKEN_LIMIT
            ):
                break  # Stop if adding this SAMPLE would exceed the limit

            # Append the SAMPLE's messages and update the total token count
            messages.append(user_prompt_message)
            messages.append(assistant_message)
            total_num_tokens += user_prompt_tokens + assistant_tokens

        # Try to add the bad samples instruction if there's still room and it's not empty
        if BAD_SAMPLES_INSTRUCTION.strip():
            bad_samples_tokens = calculate_token_usage(BAD_SAMPLES_INSTRUCTION)
            if total_num_tokens + bad_samples_tokens <= TARGET_TOKEN_LIMIT:
                # Update the system prompt to include the bad samples instruction
                system_prompt_with_bad_samples = (
                    system_prompt + "\n\n" + BAD_SAMPLES_INSTRUCTION
                )
                # Replace the original system message with the updated one
                messages[0] = {
                    "role": "system",
                    "content": system_prompt_with_bad_samples,
                }

        # Append the user query as the last message
        messages.append({"role": "user", "content": user_prompt})

        start_narrative = perf_counter()

        for trial in range(3):
            response = (
                llama70b_client.chat.completions.create(
                    messages=messages,
                    model=os.getenv("LLAMA70B_MODEL"),
                    max_tokens=2000,
                    temperature=0.0,
                    extra_body={
                        "guided_json": schema_json,
                    },
                )
                .choices[0]
                .message.content
            )

            for message in messages:
                if "content" in message:
                    tokens = calculate_token_usage(message["content"])
                    input_tokens += tokens
            for message in messages:
                if "content" in message:
                    tokens = calculate_token_usage(message["content"])
                    input_tokens += tokens

            output_tokens += calculate_token_usage(response)
            output_tokens += calculate_token_usage(response)

            chart_axis_inference_time = perf_counter() - start_narrative
            chart_axis_inference_time = perf_counter() - start_narrative

            MODULEID_SELECT_AXIS_FROM_CHART = os.getenv(
                "MODULEID_SELECT_AXIS_FROM_CHART", ""
            )
            MODULEID_SELECT_AXIS_FROM_CHART = os.getenv(
                "MODULEID_SELECT_AXIS_FROM_CHART", ""
            )

            if MODULEID_SELECT_AXIS_FROM_CHART == "":
                raise ValueError("MODULEID_SELECT_AXIS_FROM_CHART is invalid!")
            if MODULEID_SELECT_AXIS_FROM_CHART == "":
                raise ValueError("MODULEID_SELECT_AXIS_FROM_CHART is invalid!")

            log_chart_data = {
                "chart_id": chart_id,
                "chart_axis": response,
            }
            log_chart_data = {
                "chart_id": chart_id,
                "chart_axis": response,
            }

            logging_url_chart = logging_url + "chart"
            log_responds = requests.post(
                logging_url_chart, json=log_chart_data, verify=False
            ).json()
            logging_url_chart = logging_url + "chart"
            log_responds = requests.post(
                logging_url_chart, json=log_chart_data, verify=False
            ).json()

            chart_id = log_responds["chart_id"]
            chart_id = log_responds["chart_id"]

            formatted_data = {
                "chart_id": chart_id,
                "module_id": int(MODULEID_SELECT_AXIS_FROM_CHART),
                "messages": messages,
                "output": response,
                "inference_time": chart_axis_inference_time,
                "llm_model": os.getenv("LLAMA70B_MODEL"),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }
            formatted_data = {
                "chart_id": chart_id,
                "module_id": int(MODULEID_SELECT_AXIS_FROM_CHART),
                "messages": messages,
                "output": response,
                "inference_time": chart_axis_inference_time,
                "llm_model": os.getenv("LLAMA70B_MODEL"),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }

            logging_url_llm_calls = logging_url + "chart-llm-calls"
            requests.put(logging_url_llm_calls, json=formatted_data, verify=False)

            # Replace colon followed by nothing with colon followed by empty string
            response = re.sub(r":\s*(?=[,}])", ": ''", response)
            response = re.sub(r"null", r"None", response)

            try:
                pattern = r"\{[^{}]*\}"
                match = re.search(pattern, response)

                if match:
                    json_string = match.group()
                else:
                    json_string = response

                json_string = json_string.replace("None", '""')
                json_string = json_string.replace("NONE", '""')
                json_string = json_string.replace("N/A", "")
                json_string = json_string.replace("NaN", '""')
                json_string = json_string.replace(": null", ': ""')
                json_string = json_string.replace(": NULL", ': ""')
                json_string = json_string.replace('"null"', '""')
                json_string = json_string.replace("<not used>", "")
                json_string = json_string.replace("<blank>", "")
                json_string = json_string.replace("(blank)", "")
                json_string = json_string.replace('" "', '""')
                json_string = json_string.replace("null", "")
                json_string = json_string.replace(r"\_", "_")
                json_string = json_string.replace("\\\\_", "_")
                json_string = json_string.replace("’", "'")
                json_string = json_string.replace('" "', '""')
                json_string = json_string.replace('""""', '""')
                json_string = json_string.replace("...", "")
                json_string = json_string.strip()
                result = ast.literal_eval(json_string)
            except Exception:
                print("Error Chart Axis Response")
                print(response)
                return None, input_tokens, output_tokens

            result_KEY_LIST = list(result.keys())

            try:
                # Validate all keys are in the generated axis
                for key in KEY_LIST:
                    if key not in result_KEY_LIST:
                        print("Incomplete Chart Axis Response")
                        print(response)
                        print(f"Required Chart Axis Keys: {KEY_LIST}")
                        print(f"Chart Question: {question}")
                        print(f"Chart Title: {chart_title}")
                        code_level_logger.error(
                            "Chart Axis is not generated correctly!"
                        )
                        raise RuntimeError("Chart Axis is not generated correctly!")

                result_KEY_LIST = list(result.keys())

                for key in result_KEY_LIST:
                    if key not in KEY_LIST:
                        print("Incomplete Chart Axis Response")
                        print(response)
                        print(f"Required Chart Axis Keys: {KEY_LIST}")
                        print(f"Chart Question: {question}")
                        print(f"Chart Title: {chart_title}")
                        code_level_logger.error(
                            "Chart Axis is not generated correctly!"
                        )
                        raise RuntimeError("Chart Axis is not generated correctly!")

                # Validate X-axis title is not empty
                if "xAxis_title" in result_KEY_LIST and result["xAxis_title"] == "":
                    code_level_logger.error("Chart Axis is not generated correctly!")
                    raise RuntimeError("Chart Axis is not generated correctly!")

                # Validate X-axis column is not empty
                if "xAxis_column" in result_KEY_LIST and result["xAxis_column"] == "":
                    code_level_logger.error("Chart Axis is not generated correctly!")
                    raise RuntimeError("Chart Axis is not generated correctly!")

                # Validate Y-axis title is not empty
                if "yAxis_title" in result_KEY_LIST and result["yAxis_title"] == "":
                    code_level_logger.error("Chart Axis is not generated correctly!")
                    raise RuntimeError("Chart Axis is not generated correctly!")

                # Validate Y-axis column is not empty
                if "yAxis_column" in result_KEY_LIST and result["yAxis_column"] == "":
                    code_level_logger.error("Chart Axis is not generated correctly!")
                    raise RuntimeError("Chart Axis is not generated correctly!")

                # Validate Y-axis aggregation is not empty
                if (
                    "yAxis_aggregation" in result_KEY_LIST
                    and result["yAxis_aggregation"] == ""
                ):
                    code_level_logger.error("Chart Axis is not generated correctly!")
                    raise RuntimeError("Chart Axis is not generated correctly!")

                # Validate no improper empty keys are in the generated axis
                for key in result_KEY_LIST:
                    # Aggregation
                    if "aggregation" in key.lower() and isinstance(result[key], str):
                        if result[key] == "" and (
                            result[key.replace("aggregation", "title")] != ""
                            or (
                                result[key.replace("aggregation", "column")] != ""
                                and result[key.replace("aggregation", "column")] != []
                            )
                        ):
                            print("Incomplete Chart Axis Response")
                            print(response)
                            print(f"Required Chart Axis Keys: {KEY_LIST}")
                            print(f"Chart Question: {question}")
                            print(f"Chart Title: {chart_title}")
                            code_level_logger.error(
                                "Chart Axis is not generated correctly!"
                            )
                            raise RuntimeError("Chart Axis is not generated correctly!")

                        result[key] = result[key].upper()
                        continue

                    # Title
                    if "title" in key.lower():
                        if (
                            result[key.replace("title", "column")] != ""
                            and result[key.replace("title", "column")] != []
                        ) and result[key] == "":
                            print("Incomplete Chart Axis Response")
                            print(response)
                            print(f"Required Chart Axis Keys: {KEY_LIST}")
                            print(f"Chart Question: {question}")
                            print(f"Chart Title: {chart_title}")
                            code_level_logger.error(
                                "Chart Axis Title is not generated correctly!"
                            )
                            raise RuntimeError("Chart Axis is not generated correctly!")

                        if "aggregated value" in result[key].lower():
                            print("Incomplete Chart Axis Response")
                            print(response)
                            print(f"Required Chart Axis Keys: {KEY_LIST}")
                            print(f"Chart Question: {question}")
                            print(f"Chart Title: {chart_title}")
                            code_level_logger.error(
                                "Chart Axis Title is not generated correctly!"
                            )
                            raise RuntimeError("Chart Axis is not generated correctly!")

                        if isinstance(result[key], str) and result[key].lower() in [
                            "amount",
                            "value",
                            "null",
                            "total value",
                            "total amount",
                        ]:
                            print("Invalid Chart Axis Title")
                            print(response)
                            print(f"Required Chart Axis Keys: {KEY_LIST}")
                            print(f"Chart Question: {question}")
                            print(f"Chart Title: {chart_title}")
                            code_level_logger.error(
                                "Chart Axis Title contains only 'amount'/'value'/'null'/'total value', 'total amount'!"
                            )
                            raise RuntimeError(
                                "Chart Axis title contains only 'amount'/'value'/'null'/'total value', 'total amount'!",
                            )

                        if (result[key] != "") and (
                            key.replace("title", "column") in result_KEY_LIST
                            and result[key.replace("title", "column")] == ""
                        ):
                            print("Incomplete Chart Axis Response")
                            print(response)
                            print(f"Required Chart Axis Keys: {KEY_LIST}")
                            print(f"Chart Question: {question}")
                            print(f"Chart Title: {chart_title}")
                            code_level_logger.error(
                                "Chart Axis Title is not generated correctly!"
                            )
                            raise RuntimeError(
                                "Chart Axis Column is not generated correctly!"
                            )
                        continue

                    # Column
                    if (result[key] != "" and result[key] != []) and (
                        key.replace("column", "title") in result_KEY_LIST
                        and result[key.replace("column", "title")] == ""
                    ):
                        print("Incomplete Chart Axis Response")
                        print(response)
                        print(f"Required Chart Axis Keys: {KEY_LIST}")
                        print(f"Chart Question: {question}")
                        print(f"Chart Title: {chart_title}")
                        code_level_logger.error(
                            "Chart Axis Column is not generated correctly!"
                        )
                        raise RuntimeError(
                            "Chart Axis Title is not generated correctly!"
                        )

                    if isinstance(result[key], str) and "," in result[key]:
                        result[key] = result[key].split(",")
                        for result_idx, result_value in enumerate(result[key]):
                            result[key][result_idx] = result_value.strip()

                    if isinstance(result[key], str) and "|" in result[key]:
                        result[key] = result[key].split("|")
                        for result_idx, result_value in enumerate(result[key]):
                            result[key][result_idx] = result_value.strip()

                    if isinstance(result[key], str) and result[key] != "":
                        if result[key] not in database_summary.column_name_list:
                            print("Invalid Chart Axis Response")
                            print(response)
                            print(f"Required Chart Axis Keys: {KEY_LIST}")
                            print(f"Chart Question: {question}")
                            print(f"Chart Title: {chart_title}")
                            code_level_logger.error(
                                "Invalid Chart Axis Response: Column name not in the database!"
                            )
                            raise RuntimeError("Chart Axis is not generated correctly!")

                    if isinstance(result[key], list) and result[key] != []:
                        for result_column_name in result[key]:
                            if (
                                result_column_name
                                not in database_summary.column_name_list
                            ):
                                print("Invalid Chart Axis Response")
                                print(response)
                                print(f"Required Chart Axis Keys: {KEY_LIST}")
                                print(f"Chart Question: {question}")
                                print(f"Chart Title: {chart_title}")
                                code_level_logger.error(
                                    "Invalid Chart Axis Response: Column name not in the database!"
                                )
                                raise RuntimeError(
                                    "Chart Axis is not generated correctly!"
                                )

                if "series_column" in result_KEY_LIST:
                    if (
                        isinstance(result["series_column"], str)
                        and result["series_column"]
                        in database_summary.column_data_tribes.keys()
                        and database_summary.column_data_tribes[result["series_column"]]
                        in ["numerical", "date_related", "id"]
                    ):
                        print(
                            "Invalid Chart Axis Response: Series column is numerical/date/id!"
                        )
                        print(response)
                        code_level_logger.error(
                            "Invalid Chart Axis Response: Series column is numerical/date/id!"
                        )
                        raise RuntimeError(
                            "Invalid Chart Axis Response: Series column is numerical/date/id!",
                        )
                    if (
                        isinstance(result["series_column"], list)
                        and result["series_column"] != []
                    ):
                        for series_column_name in result["series_column"]:
                            if (
                                series_column_name
                                in database_summary.column_data_tribes.keys()
                                and database_summary.column_data_tribes[
                                    series_column_name
                                ]
                                in ["numerical", "date_related", "id"]
                            ):
                                print(
                                    "Invalid Chart Axis Response: Series column is numerical/date/id!",
                                )
                                print(response)
                                code_level_logger.error(
                                    "Invalid Chart Axis Response: Series column is numerical/date/id!"
                                )
                                raise RuntimeError(
                                    "Invalid Chart Axis Response: Series column is numerical/date/id!",
                                )

                    if (
                        "xAxis_column" in result_KEY_LIST
                        and "series_column" in result_KEY_LIST
                    ):
                        if result["xAxis_column"] == result["series_column"]:
                            print("Invalid Chart Axis")
                            print(response)
                            print(f"Required Chart Axis Keys: {KEY_LIST}")
                            code_level_logger.error(
                                "xAxis and series have the same value!"
                            )
                            raise RuntimeError(
                                "xAxis_column and series_column have the same values!",
                            )

                if (
                    "yAxis_column" in result_KEY_LIST
                    and result["yAxis_column"] != ""
                    and result["yAxis_column"] != []
                    and "yAxis2_column" in result_KEY_LIST
                    and result["yAxis2_column"] != ""
                    and result["yAxis2_column"] != []
                    and "yAxis_aggregation" in result_KEY_LIST
                    and result["yAxis_aggregation"] != ""
                    and "yAxis2_aggregation" in result_KEY_LIST
                    and result["yAxis2_aggregation"] != ""
                ):
                    if (
                        result["yAxis_column"] == result["yAxis2_column"]
                        and result["yAxis_aggregation"] == result["yAxis2_aggregation"]
                    ):
                        print(
                            "Both yAxis and yAxis2 is having the same value for column and aggregation!",
                        )
                        code_level_logger.error("yAxis and yAxis2 have the same value!")
                        raise RuntimeError("yAxis and yAxis2 have the same value!")

                if (
                    "yAxis2_column" in result_KEY_LIST
                    and result["yAxis2_column"] != ""
                    and result["yAxis2_column"] != []
                    and "yAxis3_column" in result_KEY_LIST
                    and result["yAxis3_column"] != ""
                    and result["yAxis3_column"] != []
                    and "yAxis2_aggregation" in result_KEY_LIST
                    and result["yAxis2_aggregation"] != ""
                    and "yAxis3_aggregation" in result_KEY_LIST
                    and result["yAxis3_aggregation"] != ""
                ):
                    if (
                        result["yAxis2_column"] == result["yAxis3_column"]
                        and result["yAxis2_aggregation"] == result["yAxis3_aggregation"]
                    ):
                        print(
                            "Both yAxis2 and yAxis3 is having the same value for column and aggregation!",
                        )
                        code_level_logger.error(
                            "yAxis2 and yAxis3 have the same value!"
                        )
                        raise RuntimeError("yAxis2 and yAxis3 have the same value!")

                if (
                    "yAxis_column" in result_KEY_LIST
                    and result["yAxis_column"] != ""
                    and result["yAxis_column"] != []
                    and "yAxis3_column" in result_KEY_LIST
                    and result["yAxis3_column"] != ""
                    and result["yAxis3_column"] != []
                    and "yAxis_aggregation" in result_KEY_LIST
                    and result["yAxis_aggregation"] != ""
                    and "yAxis3_aggregation" in result_KEY_LIST
                    and result["yAxis3_aggregation"] != ""
                ):
                    if (
                        result["yAxis_column"] == result["yAxis3_column"]
                        and result["yAxis_aggregation"] == result["yAxis3_aggregation"]
                    ):
                        print(
                            "Both yAxis and yAxis3 is having the same value for column and aggregation!",
                        )
                        code_level_logger.error("yAxis and yAxis3 have the same value!")
                        raise RuntimeError("yAxis and yAxis3 have the same value!")

                if (
                    "yAxisBar_column" in result_KEY_LIST
                    and result["yAxisBar_column"] != ""
                    and result["yAxisBar_column"] != []
                    and "yAxisLine_column" in result_KEY_LIST
                    and result["yAxisLine_column"] != ""
                    and result["yAxisLine_column"] != []
                    and "yAxisBar_aggregation" in result_KEY_LIST
                    and result["yAxisBar_aggregation"] != ""
                    and "yAxisLine_aggregation" in result_KEY_LIST
                    and result["yAxisLine_aggregation"] != ""
                ):
                    if (
                        result["yAxisBar_column"] == result["yAxisLine_column"]
                        and result["yAxisBar_aggregation"]
                        == result["yAxisLine_aggregation"]
                    ):
                        print(
                            "Both yAxisBar and yAxisLine is having the same value for column and aggregation!",
                        )
                        code_level_logger.error(
                            "yAxisBar and yAxisLine have the same value!"
                        )
                        raise RuntimeError(
                            "yAxisBar and yAxisLine have the same value!"
                        )

                if (
                    "yAxis_title" in result_KEY_LIST
                    and result["yAxis_title"] != ""
                    and "yAxis2_title" in result_KEY_LIST
                    and result["yAxis2_title"] != ""
                ):
                    if result["yAxis_title"] == result["yAxis2_title"]:
                        print(
                            "Both yAxis and yAxis2 is having the same value for title!"
                        )
                        code_level_logger.error("yAxis and yAxis2 have the same title!")
                        raise RuntimeError("yAxis and yAxis2 have the same title!")

                if (
                    "yAxis2_title" in result_KEY_LIST
                    and result["yAxis2_title"] != ""
                    and "yAxis3_title" in result_KEY_LIST
                    and result["yAxis3_title"] != ""
                ):
                    if result["yAxis2_title"] == result["yAxis3_title"]:
                        print(
                            "Both yAxis2 and yAxis3 is having the same value for title!"
                        )
                        code_level_logger.error(
                            "yAxis2 and yAxis3 have the same title!"
                        )
                        raise RuntimeError("yAxis2 and yAxis3 have the same title!")

                if (
                    "yAxis_title" in result_KEY_LIST
                    and result["yAxis_title"] != ""
                    and "yAxis3_title" in result_KEY_LIST
                    and result["yAxis3_title"] != ""
                ):
                    if result["yAxis_title"] == result["yAxis3_title"]:
                        print(
                            "Both yAxis and yAxis3 is having the same value for title!"
                        )
                        code_level_logger.error("yAxis and yAxis3 have the same title!")
                        raise RuntimeError("yAxis and yAxis3 have the same title!")

                if (
                    "yAxisBar_title" in result_KEY_LIST
                    and result["yAxisBar_title"] != ""
                    and "yAxisLine_title" in result_KEY_LIST
                    and result["yAxisLine_title"] != ""
                ):
                    if result["yAxisBar_title"] == result["yAxisLine_title"]:
                        print(
                            "Both yAxisBar and yAxisLine is having the same value for title!"
                        )
                        code_level_logger.error(
                            "yAxisBar and yAxisLine have the same title!"
                        )
                        raise RuntimeError(
                            "yAxisBar and yAxisLine have the same title!"
                        )

                if "xAxis_title" in result and re.match(
                    r"^Time$", result["xAxis_title"]
                ):
                    result["xAxis_title"] = "Date"
                    print("condition xaxis title met")

                return result, input_tokens, output_tokens

            except Exception:
                continue

        return None, input_tokens, output_tokens


def generate_axis_names(
    llama70b_client: Any,
    chart_question_data: dict,
    database_summary: DataSummary,
    logging_url: str,
    session_id: str,
    code_level_logger: logging.Logger,
):
    main_question = chart_question_data["main_question"]
    main_chart_title = chart_question_data["main_title"]
    main_chart_type = chart_question_data["main_chart_type"]
    main_chart_id = chart_question_data["chart_id"]

    input_tokens = 0
    output_tokens = 0

    try:
        axis_data, input_tokens, output_tokens = _select_axis_from_chart(
            llama70b_client,
            main_chart_id,
            main_question,
            main_chart_title,
            main_chart_type,
            database_summary,
            logging_url,
            input_tokens,
            output_tokens,
            session_id,
            code_level_logger,
        )
        if axis_data is None:
            code_level_logger.error("Chart Axis is not generated correctly!")
            raise RuntimeError("Chart Axis is not generated correctly!")

    except Exception:
        print(traceback.format_exc())

    chart_question_data["main_chart_axis"] = axis_data

    sub_questions_datas = chart_question_data["sub_questions"]

    for sub_questions_data_idx, sub_questions_data in enumerate(sub_questions_datas):
        sub_question = sub_questions_data["question"]
        sub_chart_title = sub_questions_data["chart_title"]
        sub_chart_type = sub_questions_data["chart_type"]
        sub_chart_id = sub_questions_data["chart_id"]

        input_tokens = 0
        output_tokens = 0
        try:
            axis_data, input_tokens, output_tokens = _select_axis_from_chart(
                llama70b_client,
                sub_chart_id,
                sub_question,
                sub_chart_title,
                sub_chart_type,
                database_summary,
                logging_url,
                input_tokens,
                output_tokens,
                session_id,
                code_level_logger,
            )
            if axis_data is None:
                code_level_logger.error("Chart Axis is not generated correctly!")
                raise RuntimeError("Chart Axis is not generated correctly!")
            break
        except Exception:
            print(traceback.format_exc())

        sub_questions_datas[sub_questions_data_idx]["chart_axis"] = axis_data

    chart_question_data["sub_questions"] = sub_questions_datas

    return chart_question_data
