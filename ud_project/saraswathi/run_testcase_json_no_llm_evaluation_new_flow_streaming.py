import ast
import csv
import json
import os
import re
import traceback
import logging

from argparse import ArgumentParser
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import Tuple, Any
from uuid import uuid1
from qdrant_client import QdrantClient
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

from components.axis import generate_axis_names
from components.datamodel import DataSummary
from components.executor import (
    execute_beautiful_table_sql_query,
    execute_sql_query,
)
from components.extractor import (
    extract_beautiful_table_data,
    extract_chart_data_testcase,
    extract_chart_data_d3,
)
from components.postprocess import postprocess_chart_data
from components.question import (
    generate_narrative_question_d3,
)
from components.sql_query import generate_beautiful_table_sql_query, generate_sql_query
from components.summarizer import summarize
from components.utils import (
    arrange_UPS,
    remove_unused_keys_UPS,
    remove_duplicate_charts,
    change_main_chart,
)

load_dotenv()

if os.getenv("QDRANT_HOST") is not None:
    qdrant_host: str = os.getenv("QDRANT_HOST", "")
else:
    raise RuntimeError("Qdrant host is not provided!")

if os.getenv("QDRANT_API_KEY") is not None:
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
else:
    raise RuntimeError("Qdrant password is not provided!")

if os.getenv("QDRANT_TABLE_COLLECTION") is not None:
    table_collection: str = os.getenv("QDRANT_TABLE_COLLECTION", "")
else:
    raise RuntimeError("Table collection is not provided!")

if os.getenv("QDRANT_COLUMN_COLLECTION") is not None:
    column_collection: str = os.getenv("QDRANT_COLUMN_COLLECTION", "")
else:
    raise RuntimeError("Column collection is not provided!")

logging_url = os.getenv("LOGGING_URL", "")

if logging_url == "":
    raise ValueError("Logging URL is not valid!")

mixtral_client = OpenAI(
    base_url=os.getenv("MIXTRAL_LLM_BASE_URL"),
    api_key=os.getenv("MIXTRAL_LLM_API_KEY"),  # dummy api key (not used)
)


def parse_args():
    parser = ArgumentParser()

    parser.add_argument(
        "--testcase_json_path",
        type=str,
        required=False,
        default="./test_cases/saraswati_inference_time_test.json",
    )
    parser.add_argument(
        "--result_json_root",
        type=str,
        required=False,
        default="./testcase_results/",
    )
    parser.add_argument(
        "--database_identifier",
        type=str,
        required=False,
        default="label1",
    )  # choose between 'label1', 'label2', 'label3', 'label4'. 'label1' for `mysql`, 'label2' for 'postgresql', 'label3' for 'mariadb', 'label4' for 'oracle'.

    args = parser.parse_args()

    return args


def generate_beautiful_table(
    user_query,
    UPS_dicts: list,
    data_summary: DataSummary,
    database_name: str,
    table_name: str,
    database_properties: dict,
    client_id: str,
    user_id: str,
    chart_id: str,
    session_id: str,
    code_level_logger: logging.Logger,
):
    chart_columns = []

    for UPS_dict in UPS_dicts:
        if "Aggregated_Table_Column" in UPS_dict.keys():
            chart_columns.extend(UPS_dict["Aggregated_Table_Column"])

    chart_columns = list(set(chart_columns))

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
        mixtral_client,
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


def generate_single_up(
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
) -> Tuple[dict, dict, int]:
    # start_sub_question = perf_counter()
    # for trial in range(3):
    #     try:
    #         sub_questions: list = generate_sub_questions(
    #             mixtral_client,
    #             story_question,
    #             user_query,
    #             filters,
    #             aggregations,
    #             data_summary,
    #         )
    #         break
    #     except Exception:
    #         print(traceback.format_exc())
    # story_question["sub_questions"] = sub_questions
    story_question["sub_questions"] = []
    # sub_question_inference_time = perf_counter() - start_sub_question
    # print(f"Sub Story Questions Inference Time: {sub_question_inference_time}")

    # print(f"UPS Title {ups_idx}")
    # print(overall_title)
    # print()

    # start_sql_axis = perf_counter()
    # Generate Chart Axes
    chart_axis = generate_axis_names(
        mixtral_client,
        story_question,
        data_summary,
        logging_url,
        session_id,
        code_level_logger,
    )
    # chart_sql_axis_inference_time = perf_counter() - start_sql_axis
    # print(f"Story Chart Axes Inference Time: {chart_sql_axis_inference_time}")

    # print(f"Chart Axis {ups_idx}")
    # print(chart_axis)
    # print()

    # start_sql = perf_counter()
    # Generate Chart SQL
    chart_sql = generate_sql_query(
        mixtral_client,
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

    # print(f"Chart SQL {ups_idx}")
    # print(chart_sql)
    # print()

    # start_sql_exec = perf_counter()
    # Execute Chart SQL
    chart_data = execute_sql_query(
        mixtral_client,
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
    # print("Chart Data")
    # print(chart_data)
    # print()

    print("Passed execute_sql_query function")

    valid_sql_count = 0
    empty_count = 0

    if len(chart_data["chart_data"]) == 0:
        empty_count += 1
    else:
        valid_sql_count += 1

    for item in chart_data["sub_questions"]:
        if len(item["chart_data"]) == 0:
            empty_count += 1
        else:
            valid_sql_count += 1

    # start_postprocess_data = perf_counter()
    # Execute Chart SQL
    chart_data = postprocess_chart_data(
        chart_data,
        session_id,
        code_level_logger,
    )
    # chart_postprocess_data_time = perf_counter() - start_postprocess_data
    # print(f"Story Chart Data Postprocess Time: {chart_postprocess_data_time}")

    # print("Postprocessed Chart Data")
    # print(chart_data)
    # print()
    print("Passed postprocess function")
    # start_sql_extract = perf_counter()
    # Extract Chart Data
    chart_json = extract_chart_data_testcase(
        mixtral_client,
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
        code_level_logger,
    )
    # chart_data_extraction_time = perf_counter() - start_sql_extract
    # print(f"Story Chart Data Extraction Time: {chart_data_extraction_time}")

    print("Chart JSON")
    print(chart_json)
    print()
    print(f"Generate Single Up: {chart_json}, {story_question}, {valid_sql_count}")
    return chart_json, story_question, valid_sql_count


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
) -> tuple[Any, int]:
    # start_sub_question = perf_counter()
    # for trial in range(3):
    #     try:
    #         sub_questions: list = generate_sub_questions(
    #             mixtral_client,
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
        mixtral_client,
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
        mixtral_client,
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
        mixtral_client,
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

    valid_sql_count = 0
    empty_count = 0

    if len(chart_data["chart_data"]) == 0:
        empty_count += 1
    else:
        valid_sql_count += 1
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
        mixtral_client,
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

    return chart_json, valid_sql_count


def _main():
    args = parse_args()

    CLIENT_DB = ast.literal_eval(os.getenv("CLIENT_DB"))

    for db_detail in CLIENT_DB:
        if db_detail["db_tag"] == args.database_identifier:
            if db_detail["database_type"] == "mysql":
                database_properties = {
                    "db_tag": "MySQL",
                    "hostname": db_detail["hostname"],
                    "username": db_detail["username"],
                    "password": db_detail["password"],
                    "port": db_detail["port"],
                }
            elif db_detail["database_type"] == "postgresql":
                database_properties = {
                    "db_tag": "PostgreSQL",
                    "hostname": db_detail["hostname"],
                    "username": db_detail["username"],
                    "password": db_detail["password"],
                    "port": db_detail["port"],
                }
            elif db_detail["database_type"] == "mariadb":
                database_properties = {
                    "db_tag": "MariaDB",
                    "hostname": db_detail["hostname"],
                    "username": db_detail["username"],
                    "password": db_detail["password"],
                    "port": db_detail["port"],
                }
            elif db_detail["database_type"] == "oracle":
                database_properties = {
                    "db_tag": "Oracle",
                    "hostname": db_detail["hostname"],
                    "username": db_detail["username"],
                    "password": db_detail["password"],
                    "port": db_detail["port"],
                }
            break

    qdrant_client = QdrantClient(
        url=qdrant_host,
        api_key=qdrant_api_key,
    )

    embedding_model_url = os.getenv("EMBEDDING_BASE_URL")
    # sql_library = database_properties["db_tag"].lower()

    with open(args.testcase_json_path) as testcase_input_file:
        testcase_inputs = json.load(testcase_input_file)
        result_json_root = Path(args.result_json_root) / str(uuid1())

        if not Path(result_json_root).exists():
            Path(result_json_root).mkdir(parents=True, exist_ok=True)

        result_csv_root_path = Path(result_json_root) / "valid_json_rate.csv"

        with open(result_csv_root_path, "w") as csv_file:
            csv_writer = csv.writer(csv_file)

            csv_writer.writerow(
                [
                    "Input",
                    "Inference Time",
                    "Inference_Time_To_First_Chart",
                    "Valid SQL Query Rate",
                    "Valid JSON Rate",
                ],
            )

            for testcase_input in tqdm(testcase_inputs):
                database_name = testcase_input["database_name"]
                table_name = testcase_input["table_name"]
                user_query = testcase_input["user_query"]
                user_dimensions = testcase_input["user_dimension"]
                user_aggregations = testcase_input["user_aggregation"]
                client_id = testcase_input["client_id"]
                user_id = testcase_input["user_id"]
                session_id = ""

                filtered_user_query = re.sub("[^A-Za-z0-9]+", "", user_query).replace(
                    "?",
                    "",
                )

                result_json_root_path = (
                    Path(result_json_root) / f"{filtered_user_query[:100]}.json"
                )

                with open(result_json_root_path, "w") as outfile:
                    try:
                        start_saraswati = perf_counter()
                        start_time_to_first_chart = perf_counter()
                        print("Starting process 1")
                        # Generate Data Summary
                        for trial in range(2):
                            try:
                                data_summary = summarize(
                                    qdrant_client,
                                    database_name,
                                    args.database_identifier,
                                    table_collection,
                                    column_collection,
                                    table_name,
                                    embedding_model_url,
                                    logging_url,
                                )
                                print("Starting process 2")
                                break
                            except Exception:
                                print(traceback.format_exc())

                        # summary_inference_time = perf_counter() - start_saraswati

                        # start_story = perf_counter()
                        input_tokens = 0
                        output_tokens = 0
                        for trial in range(3):
                            try:
                                (
                                    story_narrative_question,
                                    input_tokens,
                                    output_tokens,
                                ) = generate_narrative_question_d3(
                                    mixtral_client,
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
                                )
                                print("Starting process 3")
                                break
                            except Exception:
                                print(traceback.format_exc())

                        # story_inference_time = perf_counter() - start_story

                        UPS_dicts = []
                        questions = []
                        total_valid_sql_count = 0
                        time_to_first_chart = 0
                        total_sub_questions = 0

                        print("Starting process 4")
                        for ups_idx, story_question in enumerate(
                            story_narrative_question.main_questions,
                            start=1,
                        ):
                            try:
                                print("Got here, Begining of Generate Single Up")
                                result, valid_sql_count = generate_single_up_d3(
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
                                )

                                print("Got here, End of Generate Single Up")
                            except Exception:
                                print("There was an error")
                                continue

                            if time_to_first_chart == 0 and result != []:
                                time_to_first_chart = (
                                    perf_counter() - start_time_to_first_chart
                                )

                            print(f"Time to first chart: {time_to_first_chart}")
                            # total_sub_questions += len(result1["sub_questions"])

                            UPS_dicts.extend(result)
                            # questions.append(result1)
                            total_valid_sql_count += valid_sql_count

                        # start_beautiful_table = perf_counter()

                        # Generate Beautiful Table
                        beautiful_table_json = generate_beautiful_table(
                            user_query,
                            UPS_dicts,
                            data_summary,
                            database_name,
                            table_name,
                            database_properties,
                            client_id,
                            user_id,
                            "",
                        )
                        # beautiful_table_time = perf_counter() - start_beautiful_table
                        # print(f"Beautiful Table Inference Time: {beautiful_table_time}")

                        UPS_dicts = arrange_UPS(UPS_dicts)

                        UPS_dicts = remove_unused_keys_UPS(UPS_dicts)

                        print("Starting process 5")

                        print("UPS Dicts at GUS_Non_SSE : ", UPS_dicts)

                        number_of_valid_json = 0
                        for UPS_dict in UPS_dicts:
                            number_of_valid_json += 1
                        UPS_dicts.append(beautiful_table_json)

                        saraswati_inference_time = perf_counter() - start_saraswati
                        # print(f"Saraswati Inference Time: {saraswati_inference_time}")
                    except Exception:
                        print(traceback.format_exc())
                        continue

                    total_main_questions = len(story_narrative_question.main_questions)

                    number_of_questions = total_main_questions + total_sub_questions

                    print("Total number of questions : ", number_of_questions)
                    # scores = calculate_eval_scores(eval_scores)

                    if number_of_questions <= 0:
                        dictionary = {
                            "Input": user_query,
                            "Data_Summary": asdict(data_summary),
                            "Story_Skeleton": asdict(story_narrative_question),
                            "Story_Questions": questions,
                            "JSON": UPS_dicts,
                            "Inference_Time": round(saraswati_inference_time, 2),
                            "Inference_Time_To_First_Chart": round(
                                time_to_first_chart,
                                2,
                            ),
                            "Valid_SQL_Query_Rate": 0.0,
                            "Valid_JSON_Rate": 0.0,
                            # "Evaluation_Scores": eval_scores,
                        }

                        json_object = json.dumps(dictionary, indent=4, default=str)
                        outfile.write(json_object)

                        csv_writer.writerow(
                            [
                                user_query,
                                round(saraswati_inference_time, 2),
                                round(time_to_first_chart, 2),
                                0.0,
                                0.0,
                            ],
                        )
                    else:
                        print(
                            f"Number of valid json : {number_of_valid_json},\n Number of valid sql count : {total_valid_sql_count}\n "
                        )
                        dictionary = {
                            "Input": user_query,
                            "Data_Summary": asdict(data_summary),
                            "Story_Skeleton": asdict(story_narrative_question),
                            "Story_Questions": questions,
                            "JSON": UPS_dicts,
                            "Inference_Time": round(saraswati_inference_time, 2),
                            "Inference_Time_To_First_Chart": round(
                                time_to_first_chart,
                                2,
                            ),
                            "Valid_SQL_Query_Rate": round(
                                (
                                    (
                                        float(total_valid_sql_count)
                                        / (number_of_questions)
                                    )
                                    * 100
                                ),
                                2,
                            ),
                            "Valid_JSON_Rate": round(
                                (
                                    (
                                        float(number_of_valid_json)
                                        / (number_of_questions)
                                    )
                                    * 100
                                ),
                                2,
                            ),
                            # "Evaluation_Scores": eval_scores,
                        }

                        json_object = json.dumps(dictionary, indent=4, default=str)
                        outfile.write(json_object)

                        csv_writer.writerow(
                            [
                                user_query,
                                round(saraswati_inference_time, 2),
                                round(time_to_first_chart, 2),
                                round(
                                    (
                                        float(valid_sql_count)
                                        / (number_of_questions)
                                        * 100
                                    ),
                                    2,
                                ),
                                round(
                                    (
                                        float(number_of_valid_json)
                                        / (number_of_questions)
                                        * 100
                                    ),
                                    2,
                                ),
                            ],
                        )


if __name__ == "__main__":
    _main()
