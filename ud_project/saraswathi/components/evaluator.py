import ast
import logging
import traceback
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def _evaluate(
    openai_client: Any,
    user_query: str,
    question: str,
    chart_title: str,
    chart_type: str,
    chart_axis: dict,
    sql_query: str,
    chart_data: pd.DataFrame,
    chart_json: dict,
):
    REQUIRED_KEY_LIST = [
        "chart_type_appropriate_score",
        "reason_cta",
        "sql_validity_score",
        "reason_sv",
        "chart_axis_relevancy_score",
        "reason_car",
        "chart_title_relevancy_score",
        "reason_ctr",
        "overall_reasoning",
        "overall_recommendations",
    ]
    FORMAT_INSTRUCTIONS = """{"chart_type_appropriate_score": "...", "reason_cta": "...", "sql_validity_score": "...", "reason_sv": "...", "chart_axis_relevancy_score": "...", "reason_car": "...","chart_title_relevancy_score": "...", "reason_ctr": "...", "overall_reasoning": "...", "overall_recommendations": "..."}"""

    system_prompt = f"""You are an experienced data analyst. You are tasked with evaluating visualizations generated from data across four dimensions. Your evaluation should provide scores on a scale from 1 to 10 for each dimension, with 1 being poor and 10 being good. The score MUST BE AN INTEGER DATA TYPE. 

1. Chart Type Appropriate Score: Assess how well the chosen chart type aligns with the chart data and the story question, considering potential issues such as inappropriate chart types selected. Evaluate whether the chart accurately represents the data relationships and effectively communicates the main message despite any discrepancies. For example, a bar chart might be more appropriate for comparing categories, but if a pie chart is selected instead, it could indicate a mismatch between the chosen chart type and the data.

2. SQL Validity Score: Determine the validity of the SQL query used to generate the chart data for the visualization, considering potential issues such as syntax errors or logical flaws in the query. Evaluate whether the query accurately retrieves the required chart data despite any discrepancies in the visualization. For example, if the chart data displays all table values as 0 due to an error in the SQL query, it could indicate a validity issue.

3. Chart Axis Relevancy with the Chart Data: Evaluate how relevant the chart axes are to the chart data being visualized and the chart type, considering issues such as incorrect axis titles or inappropriate data mappings except for table_chart which should contain "all". For example, if the x-axis title is labeled as "date" but actually represents "month," it could indicate an axis relevancy issue.

4. Chart Title Relevancy with the Chart Data: Assess the relevance of the chart title to the chart data and the story question, considering issues such as misleading titles. Evaluate whether the chart title effectively communicates the main message and summarizes the key insights derived from the chart data and the story question. For example, if the chart title contains symbols or characters that hinder readability, it could indicate a relevancy issue.

Please provide a score from 1 to 10 for each dimension based on the provided visualization JSON Data, User Intent, Story Question, Chart Title, Chart Type, Chart Axis, SQL Query, and Chart Data below.

Visualization JSON: {chart_json}

User intent: {user_query}

Story Question: {question}

Chart Title: {chart_title}

Chart Type: {chart_type}

Chart Axis: {chart_axis}

SQL Query: {sql_query}

Chart Data: {chart_data}

INCLUDE THE REASON FOR ALL 4 DIMENSIONS. GIVE THE OVERALL SUMMARY FOR THE REASONING AS WHY IT IS IRRELEVANT AND RECOMMENDATIONS TO ADDRESS THE ISSUES FOR THE POOR SCORES.
Ensure that your evaluation is objective, without bias, and strictly adheres to the provided scoring criteria. Be critical and avoid introducing personal opinions or subjective judgments into your assessment. Provide your response ONLY in a VALID JSON format given below.

{FORMAT_INSTRUCTIONS}

"""

    user_prompt = f"""Evaluate visualizations generated from data for each dimension based on the provided visualization JSON, Story Question, Chart Title, Chart Type, Chart Axis, SQL Query, and Chart Data below. The evaluation should provide scores on a scale from 1 to 10 for each dimension, with 1 being poor and 10 being good. The score MUST BE AN INTEGER DATA TYPE.

Dimensions:
1. Chart Type Appropriate Score

2. SQL Validity Score

3. Chart Axis Relevancy with the Chart Data

4. Chart Title Relevancy with the Chart Data

Please provide a score from 1 to 10 for each dimension based on the provided visualization JSON, User Intent, Story Question, Chart Title, Chart Type, Chart Axis, Sql Query and Chart Data below.

Visualization JSON:{chart_json}
User intent:{user_query}
Story Question:{question}
Chart Title: {chart_title}
Chart Type: {chart_type}
Chart Axis: {chart_axis}
Sql Query: {sql_query}
Chart Data: {chart_data}

INCLUDE THE REASON FOR EACH SCORES DIMENSIONS. INCLUDE THE SUMMARY FOR THE REASONING AS WHY IT IS IRRELEVANT. GIVE RECOMMENDATIONS TO ADDRESS THE ISSUES FOR THE POOR SCORES. Provide your response ONLY in a VALID JSON format given below.

{FORMAT_INSTRUCTIONS}

"""

    response = (
        openai_client.chat.completions.create(
            model="got-35-turbo-16k",  # model = "deployment_name".
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1000,
            # stream = True
        )
        .choices[0]
        .message.content
    )

    result = ast.literal_eval(response)

    # Verify evaluator response
    for required_key in REQUIRED_KEY_LIST:
        if required_key not in result.keys():
            print("Error Evaluator Response")
            print(response)
            raise RuntimeError("Error: Incomplete evaluation response")

    return result


def _eval_chart_completeness(
    openai_client: Any,
    user_query: str,
    chart_json: dict,
    questions: list,
):
    REQUIRED_KEY_LIST = [
        "chart_relevancy_score",
        "reason_cr",
        "questions_relevancy_score",
        "reason_qr",
        "chart_perspective_completeness_score",
        "reason_car",
        "chart_title_relevancy_score",
        "reason_ctr",
        "overall_reasoning",
        "overall_recommendations",
    ]
    FORMAT_INSTRUCTIONS = """{"chart_relevancy_score": "...", "reason_cr": "...", "questions_relevancy_score": "...", "reason_qr": "...", "chart_perspective_completeness_score": "...", "reason_cpc": "...",  "overall_reasoning": "...", "overall_recommendations": "..."}"""

    system_prompt = f"""
    You are tasked with evaluating visualizations generated from data across three dimensions. Your evaluation should provide scores on a scale from 1 to 10 for each dimension, with 1 being poor and 10 being good. The score MUST BE AN INTEGER DATA TYPE. 

1. Chart Relevancy Score: Evaluate the relevance of the visualization JSON to the specified story question, taking into account any discrepancies between the chart and the intended visualization. Consider whether the chart addresses the user query and story questions despite potential issues like incorrect filtering. For example, if the user query asks about revenue trends over time, but the charts display data for multiple dates instead of the specified date, it could indicate a relevancy issue. Additionally, assess whether the data displayed aligns with the expected patterns of the chart type. In cases where the data contains many zeros or does not reflect the characteristics expected for the chosen chart type, it may indicate a relevancy issue that could impact the overall score.

2. Questions Relevancy to the User Intent: Evaluate the relevance of the story questions asked to the user intent, considering potential issues like ambiguous or unrelated questions. Assess whether the story questions directly relates to the user's intent and align with the goals of the visualization. For example, if the questions fail to relate to the user's intent, it could indicate a relevancy issue.

3. Chart Perspective Completeness Score: Assess the completeness of perspectives provided by the set of visualizations (Visualization JSON) generated in response to the user query. Evaluate whether the collective visualizations offer a comprehensive view of the user intent, considering various angles or dimensions. For example, a series of charts that only show total revenue over time might lack completeness compared to those that also break down revenue by product or region.

Please provide a score from 1 to 10 for each dimension based on the provided visualization JSON Data, User Intent, and Story Questions below.

Visualization JSON: {chart_json}
User intent: {user_query}
Story questions: {questions}

Ensure that your evaluation is objective, without bias, and strictly adheres to the provided scoring criteria. Be critical and avoid introducing personal opinions or subjective judgments into your assessment. INCLUDE THE SUMMARY FOR THE REASONING AS WHY IT IS IRRELEVANT. GIVE RECOMMENDATIONS TO ADDRESS THE ISSUES FOR THE POOR SCORES. Provide your response ONLY in a VALID JSON format given below.

{FORMAT_INSTRUCTIONS}

"""

    user_prompt = f"""Evaluate visualizations generated from data for Chart Perspective Completeness Score based on the provided visualization JSON, user query. The evaluation should provide scores on a scale from 1 to 10 for each dimension, with 1 being poor and 10 being good. The score MUST BE AN INTEGER DATA TYPE.

Dimensions:

1. Chart Relevancy Score

2. Questions Relevancy to the User Intent

3. Chart Perspective Completeness Score

4. Overall Reasoning

5. Overall Recommendations

Please provide a score from 1 to 10 for each dimension based on the provided visualization JSON Data, User Intent, and Story Questions below.

Visualization JSON: {chart_json}
User intent: {user_query}
Story questions: {questions}

INCLUDE THE REASON FOR ALL 2 DIMENSIONS. GIVE THE OVERALL SUMMARY FOR THE REASONING AS WHY IT IS IRRELEVANT AND RECOMMENDATIONS TO ADDRESS THE ISSUES FOR THE POOR SCORES.
Provide your response ONLY in a VALID JSON format given below.

{FORMAT_INSTRUCTIONS}

"""

    response = (
        openai_client.chat.completions.create(
            model="got-35-turbo-16k",  # model = "deployment_name".
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1000,
            # stream = True
        )
        .choices[0]
        .message.content
    )

    result = ast.literal_eval(response)

    # Verify evaluator response
    for required_key in REQUIRED_KEY_LIST:
        if required_key not in result.keys():
            print("Error Chart Completeness Evaluator Response")
            print(response)
            raise RuntimeError(
                "Error: Incomplete chart completeness evaluation response",
            )

    return result


def evaluate(
    openai_client: Any,
    user_query: str,
    chart_data: dict,
    chart_json: dict,
):
    main_chart_question = chart_data["main_question"]
    main_chart_title = chart_data["main_title"]
    main_chart_type = chart_data["main_chart_type"]
    main_chart_axis = chart_data["main_chart_axis"]
    main_chart_sql = chart_data["main_chart_sql"]
    main_chart_data = chart_data["chart_data"]
    sub_chart_data_list = chart_data["sub_questions"]

    filtered_chart_axis = main_chart_axis.copy()
    filtered_chart_axis = {
        key: value for key, value in filtered_chart_axis.items() if value != ""
    }

    if (
        not isinstance(main_chart_data, pd.DataFrame)
        or main_chart_data.empty
        or "main_chart_json" not in chart_data
    ):
        return chart_data
    main_chart_json = chart_data["main_chart_json"]

    filtered_chart_json = main_chart_json.copy()
    json_chart_axis = filtered_chart_json["Chart_Axis"]
    filtered_chart_json["Chart_Axis"] = json_chart_axis

    for trial in range(3):
        try:
            main_eval_score = _evaluate(
                openai_client,
                user_query,
                main_chart_question,
                main_chart_title,
                main_chart_type,
                filtered_chart_axis,
                main_chart_sql,
                main_chart_data,
                filtered_chart_json,
            )

            story_questions = [main_chart_question]
            for sub_chart_data in sub_chart_data_list:
                story_questions.append(sub_chart_data["question"])

            chart_completeness_score = _eval_chart_completeness(
                openai_client,
                user_query,
                chart_json,
                story_questions,
            )

            main_eval_score["chart_relevancy_score"] = chart_completeness_score[
                "chart_relevancy_score"
            ]
            main_eval_score["questions_relevancy_score"] = chart_completeness_score[
                "questions_relevancy_score"
            ]
            main_eval_score["chart_perspective_completeness_score"] = (
                chart_completeness_score["chart_perspective_completeness_score"]
            )
            main_eval_score["reason"] = chart_completeness_score["overall_reasoning"]
            main_eval_score["recommendation"] = chart_completeness_score[
                "overall_recommendations"
            ]
            break
        except Exception:
            print("Error evaluate main visualization")
            print(traceback.format_exc())
            # logger.error(traceback.format_exc())

            main_eval_score = {}

    chart_data["eval_score"] = main_eval_score

    for sub_chart_idx, sub_chart_data in enumerate(sub_chart_data_list):
        sub_chart_question = sub_chart_data["question"]
        sub_chart_title = sub_chart_data["chart_title"]
        sub_chart_type = sub_chart_data["chart_type"]
        sub_chart_axis = sub_chart_data["chart_axis"]
        sub_chart_sql = sub_chart_data["chart_sql"]
        sub_chart_datas = sub_chart_data["chart_data"]

        filtered_sub_chart_axis = sub_chart_axis.copy()
        filtered_sub_chart_axis = {
            key: value for key, value in filtered_sub_chart_axis.items() if value != ""
        }

        if not isinstance(sub_chart_datas, pd.DataFrame) or sub_chart_datas.empty:
            sub_eval_score: dict = {}
        elif "chart_json" not in sub_chart_data.keys():
            sub_eval_score = {}
        else:
            sub_chart_json = sub_chart_data["chart_json"]

            filtered_sub_chart_json = sub_chart_json.copy()
            json_sub_chart_axis = filtered_sub_chart_json["Chart_Axis"]
            filtered_sub_chart_json["Chart_Axis"] = json_sub_chart_axis

            for trial in range(3):
                try:
                    sub_eval_score = _evaluate(
                        openai_client,
                        user_query,
                        sub_chart_question,
                        sub_chart_title,
                        sub_chart_type,
                        filtered_sub_chart_axis,
                        sub_chart_sql,
                        sub_chart_datas,
                        filtered_sub_chart_json,
                    )
                    break
                except Exception:
                    print("Error evaluate visualization")
                    print(traceback.format_exc())
                    sub_eval_score = {}

        sub_chart_data_list[sub_chart_idx]["eval_score"] = sub_eval_score

    chart_data["sub_questions"] = sub_chart_data_list

    return chart_data
