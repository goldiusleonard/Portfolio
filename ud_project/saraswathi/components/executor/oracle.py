import ast
import importlib
import re
import traceback
import logging
import pandas as pd

from typing import Any
from ..datamodel import DataSummary
from ..utils import remove_null_series, remove_null_x_axis
from .sql_fixer import fix_sql_query

logger = logging.getLogger(__name__)


def execute_oracle(
    llama70b_client: Any,
    data_summary: DataSummary,
    filters: dict,
    aggregations: list,
    database_name: str,
    table_name: str,
    code_template: str,
    chart_query_data: dict,
    user: str,
    password: str,
    host: str,
    port: int,
    chart_axis: dict,
    logging_url: str,
    code_level_logger: logging.Logger,
) -> dict:
    def get_globals_dict(
        code_template: str,
        user: str,
        password: str,
        host: str,
        port: int,
        database_name: str,
    ):
        # Parse the code string into an AST
        tree = ast.parse(code_template)
        # Extract the names of the imported modules and their aliases
        imported_modules: list = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = importlib.import_module(alias.name)
                    imported_modules.append((alias.name, alias.asname, module))
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    module = importlib.import_module(node.module)
                    for alias in node.names:
                        obj = getattr(module, alias.name)
                        imported_modules.append(
                            (f"{node.module}.{alias.name}", alias.asname, obj),
                        )

        # Import the required modules into a dictionary
        globals_dict: dict = {}
        for module_name, alias, obj in imported_modules:
            if alias:
                globals_dict[alias] = obj
            else:
                globals_dict[module_name.split(".")[-1]] = obj

        ex_dicts: dict = {
            "pd": pd,
            "user": user,
            "password": password,
            "host": host,
            "port": port,
            "database_name": database_name,
            "error": "",
        }
        globals_dict.update(ex_dicts)
        return globals_dict

    # Benchmark Purpose
    valid_sql = 0
    total_sql = 0

    sub_chart_data_list = chart_query_data["sub_questions"]

    main_chart_sql = chart_query_data["main_chart_sql"]

    ex_locals = get_globals_dict(
        code_template,
        user,
        password,
        host,
        port,
        database_name,
    )
    ex_locals["sql_query"] = main_chart_sql

    exec(
        code_template.format(
            user=user,
            password=password,
            host=host,
            port=port,
            sql_query=main_chart_sql,
            database_name=database_name,
        ),
        ex_locals,
    )

    if ex_locals["processed_data"].empty:
        if "main_question" in chart_query_data and "main_title" in chart_query_data:
            main_question = chart_query_data["main_question"]
            main_chart_title = chart_query_data["main_title"]
            main_instruction = None
        elif "main_instruction" in chart_query_data:
            main_instruction = chart_query_data["main_instruction"]
            main_question = None
            main_chart_title = None
        else:
            code_level_logger.error("Question and Instruction is empty!")
            raise RuntimeError("Question and Instruction is empty!")

        main_chart_type = chart_query_data["main_chart_type"]
        main_chart_axis = chart_query_data["main_chart_axis"]
        main_chart_sql_raw = chart_query_data["main_chart_sql_raw"]
        main_chart_id = chart_query_data["chart_id"]

        print("Chart Data Empty. Need to Fix")
        for trial in range(1):
            try:
                main_chart_sql, main_chart_sql_raw = fix_sql_query(
                    llama70b_client,
                    main_chart_sql_raw,
                    data_summary,
                    main_chart_id,
                    main_chart_type,
                    main_chart_axis,
                    filters,
                    aggregations,
                    database_name,
                    table_name,
                    ex_locals["error"],
                    logging_url,
                    main_question,
                    main_chart_title,
                    main_instruction,
                )

                ex_locals["sql_query"] = main_chart_sql
                exec(
                    code_template.format(
                        host=host,
                        user=user,
                        password=password,
                        port=port,
                        sql_query=main_chart_sql,
                        database_name=database_name,
                    ),
                    ex_locals,
                )

                if ex_locals["processed_data"].empty:
                    print("Empty Data SQL:")
                    print(ex_locals["sql_query"])
                    code_level_logger.error(
                        f"Chart data is empty. SQL: {ex_locals['sql_query']}"
                    )
                    raise RuntimeError("Chart data is empty")

                chart_query_data["main_chart_sql"] = main_chart_sql
                chart_query_data["main_chart_sql_raw"] = main_chart_sql_raw
                break
            except Exception:
                print(traceback.format_exc())

    if not ex_locals["processed_data"].empty:
        chart_data = ex_locals["processed_data"]
        chart_data_columns = chart_data.columns

        if "xAxis" in chart_data_columns:
            xAxis_column_name = "xAxis"
        elif (
            "xAxis_column" in chart_axis
            and chart_axis["xAxis_column"] in chart_data_columns
        ):
            xAxis_column_name = chart_axis["xAxis_column"]
        else:
            xAxis_column_name = chart_data_columns[0]

        if isinstance(chart_data[xAxis_column_name].values.tolist()[0], str):
            if (
                re.search(
                    r"^\d{4}-\d{2}-\d{2}$",
                    str(chart_data[xAxis_column_name].values.tolist()[0]),
                    re.IGNORECASE,
                )
                or re.search(
                    r"^\d{2}/\d{2}/\d{4}$",
                    str(chart_data[xAxis_column_name].values.tolist()[0]),
                    re.IGNORECASE,
                )
            ) and "to_date" not in main_chart_sql.lower():
                if (
                    "main_question" in chart_query_data
                    and "main_title" in chart_query_data
                ):
                    main_question = chart_query_data["main_question"]
                    main_chart_title = chart_query_data["main_title"]
                    main_instruction = None
                elif "main_instruction" in chart_query_data:
                    main_instruction = chart_query_data["main_instruction"]
                    main_question = None
                    main_chart_title = None
                else:
                    code_level_logger.error("Question and Instruction is empty!")
                    raise RuntimeError("Question and Instruction is empty!")

                main_chart_type = chart_query_data["main_chart_type"]
                main_chart_axis = chart_query_data["main_chart_axis"]
                main_chart_sql_raw = chart_query_data["main_chart_sql_raw"]
                main_chart_id = chart_query_data["chart_id"]

                print("Chart Data Date is not string. Need to Fix")
                for trial in range(1):
                    try:
                        main_chart_sql, main_chart_sql_raw = fix_sql_query(
                            llama70b_client,
                            main_chart_sql_raw,
                            data_summary,
                            main_chart_id,
                            main_chart_type,
                            main_chart_axis,
                            filters,
                            aggregations,
                            database_name,
                            table_name,
                            ex_locals["error"],
                            logging_url,
                            main_question,
                            main_chart_title,
                            main_instruction,
                        )

                        ex_locals["sql_query"] = main_chart_sql
                        exec(
                            code_template.format(
                                host=host,
                                user=user,
                                password=password,
                                port=port,
                                sql_query=main_chart_sql,
                                database_name=database_name,
                            ),
                            ex_locals,
                        )

                        if ex_locals["processed_data"].empty:
                            print("Empty Data SQL:")
                            print(ex_locals["sql_query"])
                            code_level_logger.error(
                                f"Chart data is empty. SQL: {ex_locals['sql_query']}"
                            )
                            raise RuntimeError("Chart data is empty")

                        chart_query_data["main_chart_sql"] = main_chart_sql
                        chart_query_data["main_chart_sql_raw"] = main_chart_sql_raw
                        break
                    except Exception:
                        print(traceback.format_exc())

                if "to_date" not in main_chart_sql.lower():
                    ex_locals["processed_data"] = pd.DataFrame()

    if not ex_locals["processed_data"].empty:
        valid_sql += 1

    total_sql += 1

    # Remove row with null x-axis
    chart_data = remove_null_x_axis(
        ex_locals["processed_data"],
        chart_query_data["main_chart_axis"],
    )

    chart_query_data["chart_data"] = remove_null_series(
        chart_data,
        chart_query_data["main_chart_axis"],
    )

    for sub_chart_data_idx, sub_chart_data in enumerate(sub_chart_data_list):
        if "question" in sub_chart_data and "chart_title" in sub_chart_data:
            sub_question = sub_chart_data["question"]
            sub_chart_title = sub_chart_data["chart_title"]
            sub_instruction = None
        elif "main_instruction" in sub_chart_data:
            sub_instruction = sub_chart_data["main_instruction"]
            sub_question = None
            sub_chart_title = None
        else:
            code_level_logger.error("Question and Instruction is empty!")
            raise RuntimeError("Question and Instruction is empty!")

        sub_chart_sql = sub_chart_data["chart_sql"]
        sub_chart_type = sub_chart_data["chart_type"]
        sub_chart_axis = sub_chart_data["chart_axis"]
        sub_chart_sql_raw = sub_chart_data["chart_sql_raw"]
        sub_chart_id = sub_chart_data["chart_id"]

        ex_locals["sql_query"] = sub_chart_sql
        exec(
            code_template.format(
                user=user,
                password=password,
                host=host,
                port=port,
                sql_query=sub_chart_sql,
                database_name=database_name,
            ),
            ex_locals,
        )

        if ex_locals["processed_data"].empty:
            for trial in range(1):
                try:
                    sub_chart_sql, sub_chart_sql_raw = fix_sql_query(
                        llama70b_client,
                        sub_chart_sql_raw,
                        data_summary,
                        sub_chart_id,
                        sub_chart_type,
                        sub_chart_axis,
                        filters,
                        aggregations,
                        database_name,
                        table_name,
                        ex_locals["error"],
                        logging_url,
                        sub_question,
                        sub_chart_title,
                        sub_instruction,
                    )

                    ex_locals["sql_query"] = sub_chart_sql
                    exec(
                        code_template.format(
                            host=host,
                            user=user,
                            password=password,
                            port=port,
                            sql_query=sub_chart_sql,
                            database_name=database_name,
                        ),
                        ex_locals,
                    )

                    if ex_locals["processed_data"].empty:
                        print("Empty Data SQL:")
                        print(ex_locals["sql_query"])
                        code_level_logger.error(
                            f"Chart data is empty. SQL: {ex_locals['sql_query']}"
                        )
                        raise RuntimeError("Chart data is empty")

                    sub_chart_data_list[sub_chart_data_idx]["chart_sql"] = sub_chart_sql
                    sub_chart_data_list[sub_chart_data_idx]["chart_sql_raw"] = (
                        sub_chart_sql_raw
                    )
                    break
                except Exception:
                    print(traceback.format_exc())

        if not ex_locals["processed_data"].empty:
            chart_data = ex_locals["processed_data"]
            chart_data_columns = chart_data.columns

            if "xAxis" in chart_data_columns:
                xAxis_column_name = "xAxis"
            elif (
                "xAxis_column" in sub_chart_axis.keys()
                and sub_chart_axis["xAxis_column"] in chart_data_columns
            ):
                xAxis_column_name = sub_chart_axis["xAxis_column"]
            else:
                xAxis_column_name = chart_data_columns[0]

            if isinstance(chart_data[xAxis_column_name].values.tolist()[0], str):
                if (
                    re.search(
                        r"^\d{4}-\d{2}-\d{2}$",
                        str(chart_data[xAxis_column_name].values.tolist()[0]),
                        re.IGNORECASE,
                    )
                    or re.search(
                        r"^\d{2}/\d{2}/\d{4}$",
                        str(chart_data[xAxis_column_name].values.tolist()[0]),
                        re.IGNORECASE,
                    )
                ) and "to_date" not in sub_chart_sql.lower():
                    if "question" in sub_chart_data and "chart_title" in sub_chart_data:
                        sub_question = sub_chart_data["question"]
                        sub_chart_title = sub_chart_data["chart_title"]
                        sub_instruction = None
                    elif "main_instruction" in sub_chart_data:
                        sub_instruction = sub_chart_data["main_instruction"]
                        sub_question = None
                        sub_chart_title = None
                    else:
                        code_level_logger.error("Question and Instruction is empty!")
                        raise RuntimeError("Question and Instruction is empty!")

                    sub_chart_type = sub_chart_data["chart_type"]
                    sub_chart_axis = sub_chart_data["chart_axis"]
                    sub_chart_sql_raw = sub_chart_data["chart_sql_raw"]
                    sub_chart_id = sub_chart_data["chart_id"]

                    print("Chart Data Date is not string. Need to Fix")
                    for trial in range(1):
                        try:
                            sub_chart_sql, sub_chart_sql_raw = fix_sql_query(
                                llama70b_client,
                                sub_chart_sql_raw,
                                data_summary,
                                sub_chart_id,
                                sub_chart_type,
                                sub_chart_axis,
                                filters,
                                aggregations,
                                database_name,
                                table_name,
                                ex_locals["error"],
                                logging_url,
                                sub_question,
                                sub_chart_title,
                                sub_instruction,
                            )

                            ex_locals["sql_query"] = sub_chart_sql
                            exec(
                                code_template.format(
                                    host=host,
                                    user=user,
                                    password=password,
                                    port=port,
                                    sql_query=sub_chart_sql,
                                    database_name=database_name,
                                ),
                                ex_locals,
                            )

                            if ex_locals["processed_data"].empty:
                                print("Empty Data SQL:")
                                print(ex_locals["sql_query"])
                                code_level_logger.error(
                                    f"Chart data is empty. SQL: {ex_locals['sql_query']}"
                                )
                                raise RuntimeError("Chart data is empty")

                            sub_chart_data_list[sub_chart_data_idx]["chart_sql"] = (
                                sub_chart_sql
                            )
                            sub_chart_data_list[sub_chart_data_idx]["chart_sql_raw"] = (
                                sub_chart_sql_raw
                            )
                            break
                        except Exception:
                            print(traceback.format_exc())

                    if "to_date" not in sub_chart_sql.lower():
                        ex_locals["processed_data"] = pd.DataFrame()

        if not ex_locals["processed_data"].empty:
            valid_sql += 1

        total_sql += 1

        # Create a new dictionary for the sub-question with both question and chart data with removed null x-axis
        chart_data = remove_null_x_axis(
            ex_locals["processed_data"],
            sub_chart_data["chart_axis"],
        )

        sub_chart_data_list[sub_chart_data_idx]["chart_data"] = remove_null_series(
            chart_data,
            sub_chart_data["chart_axis"],
        )

    # Update the chart_data key with the modified sub_chart_data_list
    chart_query_data["sub_questions"] = sub_chart_data_list

    # Benchmark Purpose
    # print(f"Valid SQL Query Percentage: {float(valid_sql)/total_sql*100}%")

    return chart_query_data


def execute_oracle_beautiful_table(
    code_template: str,
    chart_query: str,
    host: str,
    user: str,
    password: str,
    port: int,
    database_name: str,
) -> pd.DataFrame:
    def get_globals_dict(
        code_template: str,
        user: str,
        password: str,
        host: str,
        port: int,
        database_name: str,
    ):
        # Parse the code string into an AST
        tree = ast.parse(code_template)
        # Extract the names of the imported modules and their aliases
        imported_modules: list = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = importlib.import_module(alias.name)
                    imported_modules.append((alias.name, alias.asname, module))
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    module = importlib.import_module(node.module)
                    for alias in node.names:
                        obj = getattr(module, alias.name)
                        imported_modules.append(
                            (f"{node.module}.{alias.name}", alias.asname, obj),
                        )

        # Import the required modules into a dictionary
        globals_dict: dict = {}
        for module_name, alias, obj in imported_modules:
            if alias:
                globals_dict[alias] = obj
            else:
                globals_dict[module_name.split(".")[-1]] = obj

        ex_dicts: dict = {
            "pd": pd,
            "host": host,
            "user": user,
            "password": password,
            "port": port,
            "database_name": database_name,
            "error": "",
        }
        globals_dict.update(ex_dicts)
        return globals_dict

    ex_locals = get_globals_dict(
        code_template,
        user,
        password,
        host,
        port,
        database_name,
    )

    ex_locals["sql_query"] = chart_query

    exec(
        code_template.format(
            user=user,
            password=password,
            host=host,
            port=port,
            sql_query=chart_query,
            database_name=database_name,
        ),
        ex_locals,
    )

    chart_data = ex_locals["processed_data"]

    return chart_data


def execute_oracle_updater(
    code_template: str,
    chart_json: dict,
    user: str,
    password: str,
    host: str,
    port: int,
    database_name: str,
) -> pd.DataFrame:
    def get_globals_dict(
        code_template: str,
        user: str,
        password: str,
        host: str,
        port: int,
        database_name: str,
    ):
        # Parse the code string into an AST
        tree = ast.parse(code_template)
        # Extract the names of the imported modules and their aliases
        imported_modules: list = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = importlib.import_module(alias.name)
                    imported_modules.append((alias.name, alias.asname, module))
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    module = importlib.import_module(node.module)
                    for alias in node.names:
                        obj = getattr(module, alias.name)
                        imported_modules.append(
                            (f"{node.module}.{alias.name}", alias.asname, obj),
                        )

        # Import the required modules into a dictionary
        globals_dict: dict = {}
        for module_name, alias, obj in imported_modules:
            if alias:
                globals_dict[alias] = obj
            else:
                globals_dict[module_name.split(".")[-1]] = obj

        ex_dicts: dict = {
            "pd": pd,
            "user": user,
            "password": password,
            "host": host,
            "port": port,
            "database_name": database_name,
            "error": "",
        }
        globals_dict.update(ex_dicts)
        return globals_dict

    ex_locals = get_globals_dict(
        code_template,
        user,
        password,
        host,
        port,
        database_name,
    )

    chart_sql_query = chart_json["Chart_Query"]
    ex_locals["sql_query"] = chart_sql_query
    code_template = code_template.format(
        user=user,
        password=password,
        host=host,
        port=port,
        sql_query=chart_sql_query,
        database_name=database_name,
    )
    exec(code_template, ex_locals)

    # Remove row with null x-axis
    chart_data = remove_null_x_axis(
        ex_locals["processed_data"],
        chart_json["Chart_Axis"],
    )

    chart_data = remove_null_series(chart_data, chart_json["Chart_Axis"])

    return chart_data


def run_oracle_query_only(
    sql_query: str,
    code_template: str,
    user: str,
    password: str,
    host: str,
    port: int,
):
    def get_globals_dict(
        code_template: str,
        user: str,
        password: str,
        host: str,
        port: int,
    ):
        # Parse the code string into an AST
        tree = ast.parse(code_template)
        # Extract the names of the imported modules and their aliases
        imported_modules: list = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = importlib.import_module(alias.name)
                    imported_modules.append((alias.name, alias.asname, module))
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    module = importlib.import_module(node.module)
                    for alias in node.names:
                        obj = getattr(module, alias.name)
                        imported_modules.append(
                            (f"{node.module}.{alias.name}", alias.asname, obj),
                        )

        # Import the required modules into a dictionary
        globals_dict: dict = {}
        for module_name, alias, obj in imported_modules:
            if alias:
                globals_dict[alias] = obj
            else:
                globals_dict[module_name.split(".")[-1]] = obj

        ex_dicts: dict = {
            "pd": pd,
            "host": host,
            "username": user,
            "password": password,
            "port": port,
            "error": "",
        }
        globals_dict.update(ex_dicts)
        return globals_dict

    ex_locals = get_globals_dict(
        code_template,
        user,
        password,
        host,
        port,
    )
    ex_locals["sql_query"] = sql_query

    exec(
        code_template.format(
            username=user,
            password=password,
            host=host,
            port=port,
            sql_query=sql_query,
        ),
        ex_locals,
    )

    return ex_locals["processed_data"]
