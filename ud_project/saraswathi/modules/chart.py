import ast
import json
import random
import requests
import time
import traceback
import logging

from typing import List
from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse, Response, JSONResponse
from time import perf_counter
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient

from components.axis import (
    generate_axis_names,
)
from components.datamodel import DataSummary
from components.executor import execute_sql_query, execute_beautiful_table_sql_query
from components.extractor import (
    extract_chart_data_d3,
    extract_beautiful_table_data,
)
from components.insights import (
    generate_visual_description_chart,
    generate_business_recommendation_chart,
    generate_visual_description,
    generate_business_recommendation,
)
from components.postprocess import postprocess_chart_data
from components.progress_messages import (
    METADATA_RETRIEVAL_MESSAGE_TEMPLATES,
    NARRATIVE_GENERATION_MESSAGE_TEMPLATES,
    START_CHART_GENERATION_MESSAGE_TEMPLATES,
)
from components.summarizer import (
    summarize,
    summarize_joined_table,
)
from components.updater import update_chart_data_d3
from components.utils import (
    get_env_variable,
    remove_duplicate_charts,
    change_main_chart,
    remove_unused_keys_UPS,
    get_blue_river_output_from_sql,
)
from components.sql_query import (
    generate_sql_query,
    generate_beautiful_table_sql_query,
)
from components.question import generate_narrative_question_d3

from logging_library.applogger.log_manager import LogManager

from vers import version

load_dotenv()

router = APIRouter()

# Fetch and validate environment variables
mixtral_8x7b_llm_url: str = get_env_variable(
    "LLAMA70B_LLM_BASE_URL", "LLM URL is not provided!"
)
mixtral_8x7b_llm_api_key: str = get_env_variable(
    "LLAMA70B_LLM_API_KEY", "LLM API is not provided!"
)
embedding_model_url: str = get_env_variable(
    "EMBEDDING_BASE_URL", "EMBEDDING API is not provided!"
)
qdrant_host: str = get_env_variable("QDRANT_HOST", "Qdrant host is not provided!")
qdrant_api_key: str = get_env_variable(
    "QDRANT_API_KEY", "Qdrant API key is not provided!"
)
table_collection: str = get_env_variable(
    "QDRANT_TABLE_COLLECTION", "Table collection is not provided!"
)
column_collection: str = get_env_variable(
    "QDRANT_COLUMN_COLLECTION", "Column collection is not provided!"
)
logging_url: str = get_env_variable("LOGGING_URL", "Logging URL is not provided!")
code_level_logger_name: str = get_env_variable(
    "CODE_LEVEL_LOGGER_NAME", "CODE LEVEL LOGGER NAME is not provided!"
)

llama70b_client = OpenAI(
    base_url=mixtral_8x7b_llm_url, api_key=mixtral_8x7b_llm_api_key
)

qdrant_client = QdrantClient(
    url=qdrant_host,
    api_key=qdrant_api_key,
)


@router.get("/")
def root(response: Response):
    """The function sets response headers for cache control and CORS, and returns a message indicating that
    the Saraswati Agent is ready.

    :param response: The `response` parameter in the `root` function is an object that represents the
    HTTP response that will be sent back to the client. In this case, the code is setting various
    headers on the response object before returning a JSON response with the message "Saraswati Agent is
    Ready!"
    :type response: Response
    :return: a dictionary with the key "saraswati" and the value "Saraswati Agent is Ready!".
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = "0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"

    return {"saraswati": "Saraswati Agent is Ready!"}


def generate_single_up_SSE_d3(
    user_query: str,
    story_question: dict,
    data_summary: DataSummary,
    filters: dict,
    aggregations: list,
    database_properties: dict,
    ups_idx: int,
    client_id: str,
    user_id: str,
    database_name: str,
    table_name: str,
    logging_url: str,
    session_id: str,
    code_level_logger: logging.Logger,
) -> list:
    """This Python function generates and processes chart data for a given user query and story question to
    be displayed visually.

    :param user_query: The `user_query` parameter in the `generate_single_up_SSE_d3` function represents
    the query input provided by the user. This query is used as part of the process to generate a single
    visualization for a story or report. It is utilized in conjunction with other parameters and
    functions within the code to create
    :type user_query: str
    :param story_question: The `story_question` parameter in the `generate_single_up_SSE_d3` function is a
    dictionary containing information about a specific story question. It likely includes details such
    as the question text, filters, aggregations, and other relevant information needed to generate
    visualizations or charts for that particular question. This dictionary
    :type story_question: dict
    :param data_summary: `DataSummary` is a class or data structure that likely contains summarized
    information about the data being used in the story or visualization. It may include details such as
    the data schema, column names, data types, and possibly some statistical summaries or metadata about
    the dataset. In the function `generate_single_up
    :type data_summary: DataSummary
    :param filters: Filters are used to narrow down the data that will be included in the analysis or
    visualization. They are conditions that are applied to the data to select only the relevant
    information. Filters can be based on various criteria such as time period, categories, numerical
    ranges, etc. In the context of the `generate
    :type filters: dict
    :param aggregations: Aggregations are functions that perform a calculation on a set of values and
    return a single aggregated value. In the context of the `generate_single_up_SSE_d3` function you
    provided, aggregations are used to specify the types of calculations or operations to be performed
    on the data during the generation of the
    :type aggregations: list
    :param database_properties: The `database_properties` parameter in the `generate_single_up_SSE_d3`
    function is a dictionary that likely contains properties or configurations related to the database
    being used. These properties could include information such as database connection details,
    authentication credentials, database type (e.g., MySQL, PostgreSQL), and any other settings
    :type database_properties: dict
    :param ups_idx: The `ups_idx` parameter in the `generate_single_up_SSE_d3` function is an integer that
    represents the index of the visual being generated. It is used to keep track of and identify the
    specific visual being processed within the function
    :type ups_idx: int
    :param client_id: The `client_id` parameter in the function `generate_single_up_SSE_d3` is a string
    that represents the unique identifier of the client for whom the chart data is being generated. It
    is used as part of the process to extract chart data for a specific client from the database
    :type client_id: str
    :param user_id: The `user_id` parameter in the `generate_single_up_SSE_d3` function represents the
    unique identifier of the user for whom the single up SSE (Story Sub Element) is being generated.
    This identifier is used within the function to perform various operations related to generating
    sub-questions, overall titles, chart
    :type user_id: str
    :param database_name: The `database_name` parameter in the `generate_single_up_SSE_d3` function refers
    to the name of the database from which data will be queried and analyzed. This parameter is used to
    specify the database where the table containing the relevant data is located. It is essential for
    constructing the SQL queries and accessing
    :type database_name: str
    :param table_name: The `table_name` parameter in the `generate_single_up_SSE_d3` function refers to the
    name of the table in the database from which data will be queried and used to generate
    visualizations. It is a string parameter that specifies the specific table within the
    `database_name` where the data is stored
    :type table_name: str
    :return: The function `generate_single_up_SSE_d3` returns a list of chart data in JSON format.
    """
    start_sub_question = perf_counter()

    # Questions Loop
    # for trial in range(3):
    #     try:
    #         sub_questions: list = generate_sub_questions(
    #             llama70b_client,
    #             story_question,
    #             user_query,
    #             filters,
    #             aggregations,
    #             data_summary,
    #         )
    #         break
    #     except Exception:
    #         print(traceback.format_exc())
    #         logger.error(traceback.format_exc())

    # No Sub Questions
    sub_questions: list = []
    story_question["sub_questions"] = sub_questions

    sub_question_inference_time = perf_counter() - start_sub_question
    print(f"Sub Story Questions Inference Time: {sub_question_inference_time}")

    start_overall_title = perf_counter()
    story_question["overall_title"] = story_question["main_title"]
    overall_title_inference_time = perf_counter() - start_overall_title
    print(
        f"Overall Title Story Questions Inference Time: {overall_title_inference_time}",
    )

    start_sql_axis = perf_counter()
    # Generate Chart Axes
    chart_axis = generate_axis_names(
        llama70b_client,
        story_question,
        data_summary,
        logging_url,
        session_id,
        code_level_logger,
    )
    chart_sql_axis_inference_time = perf_counter() - start_sql_axis
    print(f"Story Chart Axes Inference Time: {chart_sql_axis_inference_time}")

    start_sql = perf_counter()
    # Generate Chart SQL
    chart_sql = generate_sql_query(
        llama70b_client,
        data_summary,
        chart_axis,
        filters,
        aggregations,
        database_name,
        table_name,
        logging_url,
        session_id,
        code_level_logger,
    )
    chart_sql_inference_time = perf_counter() - start_sql
    print(f"Story Chart SQLs Inference Time: {chart_sql_inference_time}")

    start_sql_exec = perf_counter()
    # Execute Chart SQL
    chart_data = execute_sql_query(
        llama70b_client,
        data_summary,
        filters,
        aggregations,
        database_name,
        table_name,
        chart_sql,
        data_summary.sql_library,
        database_properties,
        chart_axis,
        logging_url,
        session_id,
        code_level_logger,
    )

    chart_sql_execution_time = perf_counter() - start_sql_exec
    print(f"Story Chart SQLs Execution Time: {chart_sql_execution_time}")

    start_postprocess_data = perf_counter()
    # Execute Chart SQL
    chart_data = postprocess_chart_data(
        chart_data,
        session_id,
        code_level_logger,
    )
    chart_postprocess_data_time = perf_counter() - start_postprocess_data
    print(f"Story Chart Data Postprocess Time: {chart_postprocess_data_time}")

    # print("Postprocessed Chart Data")
    # print(chart_data)
    # print()

    start_sql_extract = perf_counter()
    # Extract Chart Data
    chart_json = extract_chart_data_d3(
        llama70b_client,
        user_query,
        data_summary,
        chart_data,
        data_summary.sql_library,
        database_properties,
        ups_idx,
        client_id,
        user_id,
        database_name,
        logging_url,
        session_id,
        code_level_logger,
    )
    chart_data_extraction_time = perf_counter() - start_sql_extract
    print(f"Story Chart Data Extraction Time: {chart_data_extraction_time}")

    chart_json = remove_duplicate_charts(chart_json)

    # Change main chart if main chart is card chart
    if len(chart_json) >= 1 and chart_json[0]["Chart_Type"] == "card_chart":
        chart_json = change_main_chart(chart_json)

    # Add Visual Description Chart & Add Business Recommendation Chart
    if len(chart_json) > 0:
        try:
            chart_json.append(
                generate_visual_description_chart(
                    llama70b_client,
                    user_query,
                    chart_json[0],
                    logging_url,
                    session_id,
                    code_level_logger,
                    len(chart_json) + 1,
                )
            )
        except Exception:
            print(chart_json[0])
            print(traceback.format_exc())
            # logger.error(traceback.format_exc())

        try:
            chart_json.append(
                generate_business_recommendation_chart(
                    llama70b_client,
                    user_query,
                    chart_json[0],
                    logging_url,
                    session_id,
                    code_level_logger,
                    len(chart_json) + 1,
                )
            )
        except Exception:
            print(chart_json[0])
            print(traceback.format_exc())

    return chart_json


def generate_insight(
    user_query: str,
    chart_json: List[dict],
    logging_url: str,
    session_id: str,
):
    code_level_logger: logging.Logger = LogManager(session_id).get_logger_by_name(
        code_level_logger_name
    )

    for chart_data_idx, chart_data in enumerate(chart_json):
        if chart_data["Chart_Position"] == "1":
            smart_insight = generate_visual_description(
                llama70b_client,
                user_query,
                chart_data,
                logging_url,
                code_level_logger,
            )
            business_insight = generate_business_recommendation(
                llama70b_client,
                user_query,
                chart_data,
                logging_url,
                code_level_logger,
            )
        else:
            smart_insight = "No description"
            business_insight = "No description"

        chart_json[chart_data_idx]["Smart_Insight"] = smart_insight
        chart_json[chart_data_idx]["Business_Insight"] = business_insight

    return chart_json


def generate_single_up_d3(
    user_query: str,
    story_question: dict,
    data_summary: DataSummary,
    filters: dict,
    aggregations: list,
    database_properties: dict,
    ups_idx: int,
    client_id: str,
    user_id: str,
    session_id: str,
    database_name: str,
    table_name: str,
    logging_url: str,
    code_level_logger: logging.Logger,
) -> list:
    # start_sub_question = perf_counter()
    # for trial in range(3):
    #     try:
    #         sub_questions: list = generate_sub_questions(
    #             llama70b_client,
    #             story_question,
    #             user_query,
    #             filters,
    #             aggregations,
    #             data_summary,
    #         )
    #         break
    #     except Exception:
    #         print(traceback.format_exc())
    sub_questions: list = []
    story_question["sub_questions"] = sub_questions
    # sub_question_inference_time = perf_counter() - start_sub_question
    # print(f"Sub Story Questions Inference Time: {sub_question_inference_time}")

    story_question["overall_title"] = story_question["main_title"]

    # start_sql_axis = perf_counter()
    # Generate Chart Axes
    chart_axis = generate_axis_names(
        llama70b_client,
        story_question,
        data_summary,
        logging_url,
        session_id,
        code_level_logger,
    )
    # chart_sql_axis_inference_time = perf_counter() - start_sql_axis
    # print(f"Story Chart Axes Inference Time: {chart_sql_axis_inference_time}")

    # start_sql = perf_counter()
    # Generate Chart SQL
    chart_sql = generate_sql_query(
        llama70b_client,
        data_summary,
        chart_axis,
        filters,
        aggregations,
        database_name,
        table_name,
        logging_url,
        session_id,
        code_level_logger,
    )
    # chart_sql_inference_time = perf_counter() - start_sql
    # print(f"Story Chart SQLs Inference Time: {chart_sql_inference_time}")

    # start_sql_exec = perf_counter()
    # Execute Chart SQL
    chart_data = execute_sql_query(
        llama70b_client,
        data_summary,
        filters,
        aggregations,
        database_name,
        table_name,
        chart_sql,
        data_summary.sql_library,
        database_properties,
        chart_axis,
        logging_url,
        session_id,
        code_level_logger,
    )
    # chart_sql_execution_time = perf_counter() - start_sql_exec
    # print(f"Story Chart SQLs Execution Time: {chart_sql_execution_time}")

    # start_postprocess_data = perf_counter()
    # Execute Chart SQL
    chart_data = postprocess_chart_data(
        chart_data,
        session_id,
        code_level_logger,
    )
    # chart_postprocess_data_time = perf_counter() - start_postprocess_data
    # print(f"Story Chart Data Postprocess Time: {chart_postprocess_data_time}")

    # start_sql_extract = perf_counter()
    # Extract Chart Data
    chart_json = extract_chart_data_d3(
        llama70b_client,
        user_query,
        data_summary,
        chart_data,
        data_summary.sql_library,
        database_properties,
        ups_idx,
        client_id,
        user_id,
        database_name,
        logging_url,
        session_id,
        code_level_logger,
    )
    # chart_data_extraction_time = perf_counter() - start_sql_extract
    # print(f"Story Chart Data Extraction Time: {chart_data_extraction_time}")

    chart_json = remove_duplicate_charts(chart_json)

    # Change main chart if main chart is card chart
    if len(chart_json) >= 1 and chart_json[0]["Chart_Type"] == "card_chart":
        chart_json = change_main_chart(chart_json)

    # Add Visual Description Chart & Add Business Recommendation Chart
    if len(chart_json) > 0:
        try:
            chart_json.append(
                generate_visual_description_chart(
                    llama70b_client,
                    user_query,
                    chart_json[0],
                    logging_url,
                    session_id,
                    code_level_logger,
                    len(chart_json) + 1,
                )
            )
        except Exception:
            print(chart_json[0])
            print(traceback.format_exc())

        try:
            chart_json.append(
                generate_business_recommendation_chart(
                    llama70b_client,
                    user_query,
                    chart_json[0],
                    logging_url,
                    session_id,
                    code_level_logger,
                    len(chart_json) + 1,
                )
            )
        except Exception:
            print(chart_json[0])
            print(traceback.format_exc())

    return chart_json


def generate_beautiful_table(
    user_query: str,
    data_summary: DataSummary,
    database_name: str,
    table_name: str,
    database_properties: dict,
    client_id: str,
    user_id: str,
    chart_id: str,
    session_id: str,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    beautiful_table_sql_query = generate_beautiful_table_sql_query(
        database_name,
        table_name,
        data_summary.sql_library,
        data_summary,
    )

    chart_data = execute_beautiful_table_sql_query(
        beautiful_table_sql_query,
        data_summary.sql_library,
        database_properties,
        database_name,
    )

    chart_json = extract_beautiful_table_data(
        llama70b_client,
        user_query,
        chart_id,
        beautiful_table_sql_query,
        "Data Asset Table",
        {},
        chart_data,
        database_properties,
        1,
        1,
        "Data Asset Table",
        client_id,
        user_id,
        session_id,
        data_summary.sql_library,
        database_name,
        logging_url,
        code_level_logger,
    )

    return chart_json


def GraphUpsSummary_SSE_d3(
    user_query: str,
    database_identifier: str,
    user_dimensions: dict,
    user_aggregations: list,
    table_collection: str,
    column_collection: str,
    database_name: str,
    table_name: str,
    client_id: str,
    user_id: str,
    session_id: str,
    embedding_model_url: str,
    current_version: str,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    start_saraswati = perf_counter()

    data: dict = {
        "type": "info",
        "message": random.choice(METADATA_RETRIEVAL_MESSAGE_TEMPLATES),
    }
    yield json.dumps({"data": data}) + "\r\n"

    start_summary = perf_counter()
    # Generate Data Summary
    for trial in range(2):
        try:
            data_summary: DataSummary = summarize(
                qdrant_client,
                database_name,
                database_identifier,
                table_collection,
                column_collection,
                table_name,
                embedding_model_url,
                logging_url,
                session_id,
                code_level_logger,
            )
            break
        except Exception:
            print(traceback.format_exc())
    summary_inference_time = perf_counter() - start_summary
    print(f"Summary Inference Time: {summary_inference_time}")
    # print("Data Summary")
    # print(data_summary)
    # print()

    data = {
        "type": "info",
        "message": random.choice(NARRATIVE_GENERATION_MESSAGE_TEMPLATES),
    }
    yield json.dumps({"data": data}) + "\r\n"

    input_tokens = 0
    output_tokens = 0
    start_narrative = perf_counter()
    for trial in range(3):
        try:
            story_narrative_question, input_tokens, output_tokens = (
                generate_narrative_question_d3(
                    llama70b_client,
                    user_query,
                    user_dimensions,
                    user_aggregations,
                    data_summary,
                    logging_url,
                    session_id,
                    user_id,
                    input_tokens,
                    output_tokens,
                    table_name,
                    code_level_logger,
                )
            )
            break
        except Exception:
            print(traceback.format_exc())

    narrative_inference_time = perf_counter() - start_narrative
    print(f"Narrative Inference Time: {narrative_inference_time}")

    if story_narrative_question is None:
        code_level_logger.error("Narrative is not generated properly!")
        raise ValueError("Narrative is not generated properly!")

    # data = {
    #     "type": "info",
    #     "message": random.choice(NARRATIVE_SHOW_MESSAGE_TEMPLATES).format(
    #         narrative=story_narrative_question.narrative
    #     ),
    # }
    # yield json.dumps({"data": data}) + "\r\n"

    UPS_chart_data_history: list = []
    Last_UPS: list = []
    visual_idx: int = 1

    data = {
        "type": "info",
        "message": random.choice(START_CHART_GENERATION_MESSAGE_TEMPLATES),
    }
    yield json.dumps({"data": data}) + "\r\n"

    for ups_idx, story_question in enumerate(
        story_narrative_question.main_questions,
        start=1,
    ):
        chart_id = story_question["chart_id"]
        start_single_up = perf_counter()
        try:
            result = generate_single_up_SSE_d3(
                user_query,
                story_question.copy(),
                data_summary,
                user_dimensions,
                user_aggregations,
                data_summary.database_properties,
                ups_idx,
                client_id,
                user_id,
                database_name,
                table_name,
                logging_url,
                session_id,
                code_level_logger,
            )

            if result != []:
                # Arrange and clean up the result before adding to UPS_chart_data_history
                arranged_result = []
                for result_dict in result:
                    edited_result_dict = result_dict.copy()
                    edited_result_dict["Chart_Name"] = f"Visual {visual_idx}"
                    if "Aggregated_Table_JSON" in edited_result_dict.keys():
                        edited_result_dict["Aggregated_Table_JSON"]["Chart_Name"] = (
                            f"Visual {visual_idx}"
                        )

                    arranged_result.append(edited_result_dict)

                cleaned_result = remove_unused_keys_UPS(arranged_result)

                # Drop Visual if it has duplicate chart data
                for cleaned_result_data in cleaned_result:
                    if (
                        "Chart_Data" in cleaned_result_data.keys()
                        and cleaned_result_data["Chart_Data"] in UPS_chart_data_history
                    ):
                        continue

                # Add Chart Data to UPS history for duplicate charts removal
                for cleaned_result_data in cleaned_result:
                    if "Chart_Data" in cleaned_result_data.keys():
                        UPS_chart_data_history.append(cleaned_result_data["Chart_Data"])

                # Set latest result to Last UPS
                Last_UPS = cleaned_result

                # Stream the cleaned result immediately as a JSON object with a message.
                data = {
                    "type": "result",
                    "message": f"Result {visual_idx}",
                    "result": cleaned_result,
                }
                yield json.dumps({"data": data}) + "\r\n"

                # data = {
                #     "type": "info",
                #     "message": random.choice(CHART_GENERATION_MESSAGE_TEMPLATES).format(
                #         visual_idx=visual_idx
                #     ),
                # }
                # yield json.dumps({"data": data}) + "\r\n"

                visual_idx += 1
                single_up_inference_time = perf_counter() - start_single_up
                single_up_total_inference_time = (
                    single_up_inference_time
                    + narrative_inference_time
                    + summary_inference_time
                )

                logging_url_chart = logging_url + "chart"
                log_entry_data = {
                    "chart_id": chart_id,
                    "total_inference_time": single_up_total_inference_time,
                    "status": "Success",
                }
                requests.post(
                    logging_url_chart, json=log_entry_data, verify=False
                ).json()
        except Exception:
            # Handle exceptions and continue processing other callbacks.
            print(traceback.format_exc())
            # logger.error(traceback.format_exc())
            continue
        if visual_idx >= 7:
            break

    # data = {
    #     "type": "info",
    #     "message": random.choice(FINALIZING_CHART_MESSAGE_TEMPLATES),
    # }
    # yield json.dumps({"data": data}) + "\r\n"

    saraswati_inference_time = perf_counter() - start_saraswati
    print(f"Saraswati Inference Time: {saraswati_inference_time}")

    time.sleep(1)

    data = {"type": "return", "message": Last_UPS}
    yield json.dumps({"data": data}) + "\r\n"


def GraphUpsSummary_SSE_Joined_Table_d3(
    user_query: str,
    user_dimensions: dict,
    user_aggregations: list,
    table_collection: str,
    column_collection: str,
    database_name: str,
    table_name: str,
    combined_table_description: str,
    client_id: str,
    user_id: str,
    session_id: str,
    embedding_model_url: str,
    table_join_sql_query: str,
    table_level_metadata_list: list,
    column_level_metadata_list: list,
    logging_url: str,
    code_level_logger: logging.Logger,
):
    start_saraswati = perf_counter()

    data: dict = {
        "type": "info",
        "message": random.choice(METADATA_RETRIEVAL_MESSAGE_TEMPLATES),
    }
    yield json.dumps({"data": data}) + "\r\n"

    start_summary = perf_counter()
    # Generate Data Summary
    for trial in range(2):
        try:
            data_summary: DataSummary = summarize_joined_table(
                qdrant_client,
                database_name,
                table_name,
                combined_table_description,
                table_join_sql_query,
                table_level_metadata_list,
                column_level_metadata_list,
                session_id,
                code_level_logger,
            )
            break
        except Exception:
            print(traceback.format_exc())
    summary_inference_time = perf_counter() - start_summary
    # print(f"Summary Inference Time: {summary_inference_time}")
    # print("Data Summary")
    # print(data_summary)
    # print()

    data = {
        "type": "info",
        "message": random.choice(NARRATIVE_GENERATION_MESSAGE_TEMPLATES),
    }
    yield json.dumps({"data": data}) + "\r\n"

    input_tokens: int = 0
    output_tokens: int = 0
    start_narrative = perf_counter()
    for trial in range(3):
        try:
            story_narrative_question, input_tokens, output_tokens = (
                generate_narrative_question_d3(
                    llama70b_client,
                    user_query,
                    user_dimensions,
                    user_aggregations,
                    data_summary,
                    logging_url,
                    session_id,
                    user_id,
                    input_tokens,
                    output_tokens,
                    table_name,
                    code_level_logger,
                )
            )
            break
        except Exception:
            print(traceback.format_exc())

    narrative_inference_time = perf_counter() - start_narrative
    print(f"Narrative Inference Time: {narrative_inference_time}")

    if story_narrative_question is None:
        code_level_logger.error("Narrative is not generated properly!")
        raise ValueError("Narrative is not generated properly!")

    # data = {
    #     "type": "info",
    #     "message": random.choice(NARRATIVE_SHOW_MESSAGE_TEMPLATES).format(
    #         narrative=story_narrative_question.narrative
    #     ),
    # }
    # yield json.dumps({"data": data}) + "\r\n"

    UPS_chart_data_history: list = []
    Last_UPS: list = []
    visual_idx: int = 1

    data = {
        "type": "info",
        "message": random.choice(START_CHART_GENERATION_MESSAGE_TEMPLATES),
    }
    yield json.dumps({"data": data}) + "\r\n"

    for ups_idx, story_question in enumerate(
        story_narrative_question.main_questions,
        start=1,
    ):
        chart_id = story_question["chart_id"]
        start_single_up = perf_counter()
        try:
            result = generate_single_up_SSE_d3(
                user_query,
                story_question.copy(),
                data_summary,
                user_dimensions,
                user_aggregations,
                data_summary.database_properties,
                ups_idx,
                client_id,
                user_id,
                database_name,
                table_name,
                logging_url,
                session_id,
                code_level_logger,
            )

            if result != []:
                # Arrange and clean up the result before adding to UPS_chart_data_history
                arranged_result = []
                for result_dict in result:
                    edited_result_dict = result_dict.copy()
                    edited_result_dict["Chart_Name"] = f"Visual {visual_idx}"
                    if "Aggregated_Table_JSON" in edited_result_dict.keys():
                        edited_result_dict["Aggregated_Table_JSON"]["Chart_Name"] = (
                            f"Visual {visual_idx}"
                        )

                    arranged_result.append(edited_result_dict)

                cleaned_result = remove_unused_keys_UPS(arranged_result)

                # Drop Visual if it has duplicate chart data
                for cleaned_result_data in cleaned_result:
                    if (
                        "Chart_Data" in cleaned_result_data.keys()
                        and cleaned_result_data["Chart_Data"] in UPS_chart_data_history
                    ):
                        continue

                # Add Chart Data to UPS history for duplicate charts removal
                for cleaned_result_data in cleaned_result:
                    if "Chart_Data" in cleaned_result_data.keys():
                        UPS_chart_data_history.append(cleaned_result_data["Chart_Data"])

                # Set latest result to Last UPS
                Last_UPS = cleaned_result

                # Stream the cleaned result immediately as a JSON object with a message.
                data = {
                    "type": "result",
                    "message": f"Result {visual_idx}",
                    "result": cleaned_result,
                }
                yield json.dumps({"data": data}) + "\r\n"

                # data = {
                #     "type": "info",
                #     "message": random.choice(CHART_GENERATION_MESSAGE_TEMPLATES).format(
                #         visual_idx=visual_idx
                #     ),
                # }
                # yield json.dumps({"data": data}) + "\r\n"

                visual_idx += 1
                single_up_inference_time = perf_counter() - start_single_up
                single_up_total_inference_time = (
                    single_up_inference_time
                    + narrative_inference_time
                    + summary_inference_time
                )

                logging_url_chart = logging_url + "chart"
                log_entry_data = {
                    "chart_id": chart_id,
                    "total_inference_time": single_up_total_inference_time,
                    "status": "Success",
                }
                requests.post(
                    logging_url_chart, json=log_entry_data, verify=False
                ).json()

        except Exception:
            # Handle exceptions and continue processing other callbacks.
            print(traceback.format_exc())
            # logger.error(traceback.format_exc())
            continue
        if visual_idx >= 7:
            break

    # data = {
    #     "type": "info",
    #     "message": random.choice(FINALIZING_CHART_MESSAGE_TEMPLATES),
    # }
    # yield json.dumps({"data": data}) + "\r\n"

    saraswati_inference_time = perf_counter() - start_saraswati
    print(f"Saraswati Inference Time: {saraswati_inference_time}")

    time.sleep(1)

    data = {"type": "return", "message": Last_UPS}
    yield json.dumps({"data": data}) + "\r\n"


@router.post(
    "/streaming/GraphUpsSummary/d3",
    response_class=StreamingResponse,
)
def StreamingGraphUpsSummaryd3(response: Response, input_list: list = Body(...)):
    current_version = version

    if len(input_list) == 4:
        # Set random database table name
        database_name = "joined_database"
        table_name = "joined_table_a2ejsd"
        user_dimensions: dict = {}
        user_aggregations: list = []

        # User Query
        if isinstance(input_list[0], str):
            user_query: str = (
                input_list[0].replace('"', "'").replace("(", "").replace(")", "")
            )
        else:
            return Response(
                "User query format is not valid. Must be in 'str' format!",
                400,
            )

        # Session ID
        if isinstance(input_list[1], str):
            session_id: str = input_list[1]
        else:
            return Response(
                "Session ID format is not valid. Must be in 'str' format!",
                400,
            )

        blue_river_data = get_blue_river_output_from_sql(session_id)

        table_join_sql_query = blue_river_data[0]["SQL_Query"]
        table_level_metadata_list = blue_river_data[0]["Table_Level_Metadata"]
        column_level_metadata_list = blue_river_data[0]["Column_Level_Metadata"]
        combined_table_description = blue_river_data[0]["Combined_LLM_Description"]

        client_id = (
            input_list[2].replace('"', "") if isinstance(input_list[2], str) else ""
        )
        user_id = (
            input_list[3].replace('"', "") if isinstance(input_list[3], str) else ""
        )

        headers = {
            "Content-Type": "application/json",
            "X-Accel-Buffering": "no",
        }

        code_level_logger: logging.Logger = LogManager(
            session_id=session_id
        ).get_logger_by_name(code_level_logger_name)

        return StreamingResponse(
            GraphUpsSummary_SSE_Joined_Table_d3(
                user_query,
                user_dimensions,
                user_aggregations,
                table_collection,
                column_collection,
                database_name,
                table_name,
                combined_table_description,
                client_id,
                user_id,
                session_id,
                embedding_model_url,
                table_join_sql_query,
                table_level_metadata_list,
                column_level_metadata_list,
                logging_url,
                code_level_logger,
            ),
            media_type="application/json",
            headers=headers,
        )

    if isinstance(input_list[0], str):
        chart_database_table_concat: str = input_list[0]
    else:
        return Response("Table format is not valid. Must be in 'str' format!", 400)

    database_name, table_name = chart_database_table_concat.split(".", 1)

    if isinstance(input_list[1], str):
        database_identifier: str = input_list[1]
    else:
        return Response(
            "Database identifier format is not valid. Must be in 'str' format!",
            400,
        )

    if isinstance(input_list[2], str):
        user_query = input_list[2].replace('"', "'").replace("(", "").replace(")", "")
    else:
        return Response(
            "User query format is not valid. Must be in 'str' format!",
            400,
        )

    if isinstance(input_list[3], str):
        user_dimensions = ast.literal_eval(input_list[3].replace('"', '"'))
    elif isinstance(input_list[3], dict):
        user_dimensions = input_list[3]
    else:
        return Response(
            "User Dimension format is not valid. Must be in 'str' or 'dict' format!",
            400,
        )

    if isinstance(input_list[4], str):
        user_aggregations = ast.literal_eval(input_list[4].replace('"', '"'))
    elif isinstance(input_list[4], list):
        user_aggregations = input_list[4]
    else:
        return Response(
            "User Aggregation format is not valid. Must be in 'str' or 'list' format!",
            400,
        )

    if isinstance(input_list[5], str):
        client_id = input_list[5].replace('"', "")
    else:
        return Response(
            "Client id format is not valid. Must be in 'str' format!",
            400,
        )

    if isinstance(input_list[6], str):
        user_id = input_list[6].replace('"', "")
    else:
        return Response(
            "User id format is not valid. Must be in 'str' format!",
            400,
        )

    if isinstance(input_list[7], str):
        session_id = input_list[7].replace('"', "")
    else:
        return Response(
            "Session id format is not valid. Must be in 'str' format!",
            400,
        )

    headers = {
        "Content-Type": "application/json",
        "X-Accel-Buffering": "no",
    }

    code_level_logger = LogManager(session_id=session_id).get_logger_by_name(
        code_level_logger_name
    )

    return StreamingResponse(
        GraphUpsSummary_SSE_d3(
            user_query,
            database_identifier,
            user_dimensions,
            user_aggregations,
            table_collection,
            column_collection,
            database_name,
            table_name,
            client_id,
            user_id,
            session_id,
            embedding_model_url,
            current_version,
            logging_url,
            code_level_logger,
        ),
        media_type="application/json",
        headers=headers,
    )


@router.post(
    "/DataAssetTable",
)
def DataAssetTable(response: Response, input_list: list = Body(...)):
    if len(input_list) == 4:
        # Set random database table name
        database_name = "joined_database"
        table_name = "joined_table_a2ejsd"

        # User Query
        if isinstance(input_list[0], str):
            user_query: str = (
                input_list[0].replace('"', "'").replace("(", "").replace(")", "")
            )
        else:
            return Response(
                "User query format is not valid. Must be in 'str' format!",
                400,
            )

        # Session ID
        if isinstance(input_list[1], str):
            session_id: str = input_list[1]
        else:
            return Response(
                "Session ID format is not valid. Must be in 'str' format!",
                400,
            )

        blue_river_data = get_blue_river_output_from_sql(session_id)

        table_join_sql_query = blue_river_data[0]["SQL_Query"]
        table_level_metadata_list = blue_river_data[0]["Table_Level_Metadata"]
        column_level_metadata_list = blue_river_data[0]["Column_Level_Metadata"]
        combined_table_description = blue_river_data[0]["Combined_LLM_Description"]

        client_id = (
            input_list[2].replace('"', "") if isinstance(input_list[2], str) else ""
        )
        user_id = (
            input_list[3].replace('"', "") if isinstance(input_list[3], str) else ""
        )

        code_level_logger = LogManager(session_id).get_logger_by_name(
            code_level_logger_name
        )

        data_summary: DataSummary = summarize_joined_table(
            qdrant_client,
            database_name,
            table_name,
            combined_table_description,
            table_join_sql_query,
            table_level_metadata_list,
            column_level_metadata_list,
            session_id,
            code_level_logger,
        )
    else:
        # Initialize session_id
        session_id = ""

        if isinstance(input_list[0], str):
            chart_database_table_concat: str = input_list[0]
        else:
            return Response("Table format is not valid. Must be in 'str' format!", 400)

        database_name, table_name = chart_database_table_concat.split(".", 1)

        if isinstance(input_list[1], str):
            database_identifier: str = input_list[1]
        else:
            return Response(
                "Database identifier format is not valid. Must be in 'str' format!",
                400,
            )

        if isinstance(input_list[2], str):
            user_query = (
                input_list[2].replace('"', "'").replace("(", "").replace(")", "")
            )
        else:
            return Response(
                "User query format is not valid. Must be in 'str' format!",
                400,
            )

        if isinstance(input_list[5], str):
            client_id = input_list[5].replace('"', "")
        else:
            return Response(
                "Client id format is not valid. Must be in 'str' format!",
                400,
            )

        if isinstance(input_list[6], str):
            user_id = input_list[6].replace('"', "")
        else:
            return Response(
                "User id format is not valid. Must be in 'str' format!",
                400,
            )

        code_level_logger = LogManager(session_id).get_logger_by_name(
            code_level_logger_name
        )

        data_summary = summarize(
            qdrant_client,
            database_name,
            database_identifier,
            table_collection,
            column_collection,
            table_name,
            embedding_model_url,
            logging_url,
            session_id,
            code_level_logger,
        )

    # start_beautiful_table = perf_counter()
    # Generate Beautiful Table
    beautiful_table_json = generate_beautiful_table(
        user_query,
        data_summary,
        database_name,
        table_name,
        data_summary.database_properties,
        client_id,
        user_id,
        session_id,
        "",
        logging_url,
        code_level_logger,
    )
    # beautiful_table_time = perf_counter() - start_beautiful_table
    # print(f"Beautiful Table Inference Time: {beautiful_table_time}")

    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = "0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"

    return beautiful_table_json


@router.post(
    "/UpdateUps/d3",
)
def UpdateUpsD3(response: Response, chart_json: list = Body(...)):
    separated_chart_json: dict = {}

    # Group the dictionaries by 'Chart_Name'
    for item in chart_json:
        chart_name = item.get("Chart_Name")
        if chart_name not in separated_chart_json:
            separated_chart_json[chart_name] = []
        separated_chart_json[chart_name].append(item)
        session_id = item.get("Session_ID")

    database_logger = LogManager(session_id).get_logger_by_name("database_logger")

    new_chart_json: list = update_chart_data_d3(
        llama70b_client,
        separated_chart_json,
        logging_url,
        session_id,
        database_logger,
    )
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = "0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"

    return new_chart_json


@router.post("/generate/insight")
def insight_generator(
    user_query: str,
    session_id: str,
    chart_data: dict = Body(...),
):
    code_log_manager = LogManager(session_id)

    database_logger = code_log_manager.get_logger_by_name("database_logger")

    try:
        smart_insights = generate_visual_description(
            llama70b_client,
            user_query,
            chart_data,
            logging_url,
            database_logger,
        )
    except Exception:
        print("\n=================================================")
        print("Smart Insight Generation Error")
        print(traceback.format_exc())
        # logger.error(traceback.format_exc())
        print("=================================================\n")
        smart_insights = "No insights generated"

    try:
        business_insights = generate_business_recommendation(
            llama70b_client,
            user_query,
            chart_data,
            logging_url,
            database_logger,
        )
    except Exception:
        print("\n=================================================")
        print("Smart Insight Generation Error")
        print(traceback.format_exc())
        # logger.error(traceback.format_exc())
        print("=================================================\n")
        business_insights = "No insights generated"

    return JSONResponse(
        content={
            "message": "Insight generated",
            "smart_insight": smart_insights,
            "business_insight": business_insights,
        },
        status_code=200,
    )
