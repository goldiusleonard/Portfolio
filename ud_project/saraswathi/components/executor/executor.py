import json
import os
import pandas as pd
import logging

from typing import Any
from ..datamodel import DataSummary
from .mysql import (
    execute_mysql_mariadb,
    execute_mysql_mariadb_beautiful_table,
    execute_mysql_mariadb_updater,
    run_mysql_mariadb_query_only,
)
from .oracle import (
    execute_oracle,
    execute_oracle_beautiful_table,
    execute_oracle_updater,
    run_oracle_query_only,
)
from .postgresql import (
    execute_postgresql,
    execute_postgresql_beautiful_table,
    execute_postgresql_updater,
    run_postgresql_query_only,
)
from .sqlite import (
    execute_sqlite,
    execute_sqlite_beautiful_table,
    execute_sqlite_updater,
    run_sqlite_query_only,
)
from .sqlserver import (
    execute_sqlserver,
    execute_sqlserver_beautiful_table,
    execute_sqlserver_updater,
    run_sqlserver_query_only,
)
from .template import code_executor_template
from logging_library.performancelogger.performance_logger import PerformanceLogger


def execute_sql_query(
    llama70b_client: Any,
    data_summary: DataSummary,
    filters: dict,
    aggregations: list,
    database_name: str,
    table_name: str,
    chart_query: dict,
    sql_library: str,
    database_properties: dict,
    chart_axis: dict,
    logging_url: str,
    session_id: str,
    code_level_logger: logging.Logger,
) -> dict:
    """Convert and run query"""
    with PerformanceLogger(session_id):
        sql_library = (
            sql_library.lower().replace("_", "").replace("-", "").replace(" ", "")
        )

        if sql_library not in code_executor_template:
            code_level_logger.error(f"SQL Library {sql_library} is not supported!")
            raise RuntimeError(f"SQL Library {sql_library} is not supported!")
        else:
            code_template = code_executor_template[sql_library]

        if sql_library in ["mysql", "mariadb"]:
            host = database_properties["hostname"]
            user = database_properties["username"]
            password = database_properties["password"]
            port = database_properties["port"]
            chart_data = execute_mysql_mariadb(
                llama70b_client,
                data_summary,
                filters,
                aggregations,
                database_name,
                table_name,
                code_template,
                chart_query,
                host,
                user,
                password,
                port,
                chart_axis,
                logging_url,
                code_level_logger,
            )
        elif sql_library == "postgresql":
            host = database_properties["hostname"]
            user = database_properties["username"]
            password = database_properties["password"]
            port = database_properties["port"]
            chart_data = execute_postgresql(
                llama70b_client,
                data_summary,
                filters,
                aggregations,
                database_name,
                table_name,
                code_template,
                chart_query,
                user,
                password,
                host,
                port,
                chart_axis,
                logging_url,
                code_level_logger,
            )
        elif sql_library == "sqlite":
            sqlite_path = database_properties["sqlite_path"]
            chart_data = execute_sqlite(
                llama70b_client,
                data_summary,
                filters,
                aggregations,
                database_name,
                table_name,
                code_template,
                chart_query,
                sqlite_path,
                chart_axis,
                logging_url,
                code_level_logger,
            )
        elif sql_library == "sqlserver":
            server = database_properties["server"]
            uid = database_properties["username"]
            pwd = database_properties["password"]
            chart_data = execute_sqlserver(
                llama70b_client,
                data_summary,
                filters,
                aggregations,
                database_name,
                table_name,
                code_template,
                chart_query,
                server,
                uid,
                pwd,
                chart_axis,
                logging_url,
                code_level_logger,
            )
        elif sql_library == "oracle":
            user = database_properties["username"]
            password = database_properties["password"]
            host = database_properties["hostname"]
            port = database_properties["port"]
            chart_data = execute_oracle(
                llama70b_client,
                data_summary,
                filters,
                aggregations,
                database_name,
                table_name,
                code_template,
                chart_query,
                user,
                password,
                host,
                port,
                chart_axis,
                logging_url,
                code_level_logger,
            )
        else:
            code_level_logger.error(f"SQL Library {sql_library} is not supported!")
            raise RuntimeError(f"SQL Library {sql_library} is not supported!")

        return chart_data


def execute_beautiful_table_sql_query(
    chart_query: str,
    sql_library: str,
    database_properties: dict,
    database_name: str,
):
    sql_library = sql_library.lower().replace("_", "").replace("-", "").replace(" ", "")

    code_template = code_executor_template[sql_library]

    if sql_library in ["mysql", "mariadb"]:
        host = database_properties["hostname"]
        user = database_properties["username"]
        password = database_properties["password"]
        port = database_properties["port"]
        chart_data = execute_mysql_mariadb_beautiful_table(
            code_template,
            chart_query,
            host,
            user,
            password,
            port,
        )
    elif sql_library == "postgresql":
        host = database_properties["hostname"]
        user = database_properties["username"]
        password = database_properties["password"]
        port = database_properties["port"]

        chart_data = execute_postgresql_beautiful_table(
            code_template,
            chart_query,
            user,
            password,
            host,
            port,
            database_name,
        )
    elif sql_library == "sqlite":
        sqlite_path = database_properties["sqlite_path"]
        chart_data = execute_sqlite_beautiful_table(
            code_template,
            chart_query,
            sqlite_path,
        )
    elif sql_library == "sqlserver":
        server = database_properties["server"]
        uid = database_properties["username"]
        pwd = database_properties["password"]
        chart_data = execute_sqlserver_beautiful_table(
            code_template,
            chart_query,
            server,
            uid,
            pwd,
        )
    elif sql_library == "oracle":
        user = database_properties["username"]
        password = database_properties["password"]
        host = database_properties["hostname"]
        port = database_properties["port"]
        chart_data = execute_oracle_beautiful_table(
            code_template,
            chart_query,
            host,
            user,
            password,
            port,
            database_name,
        )
    else:
        raise RuntimeError(f"SQL Library {sql_library} is not supported!")

    chart_data = chart_data.fillna("NaN")

    return chart_data


def execute_sql_query_updater(
    chart_json: dict,
) -> pd.DataFrame:
    database_identifier: str = chart_json["Database_Identifier"]

    database_properties: dict = {}

    for client_db_data in json.loads(os.getenv("CLIENT_DB", "[{}]")):
        if client_db_data["db_tag"] == database_identifier:
            database_properties = client_db_data
            break

    if database_properties == {}:
        raise RuntimeError("Database Properties is not found!")

    sql_library: str = (
        chart_json["Chart_SQL_Library"]
        .lower()
        .replace("_", "")
        .replace("-", "")
        .replace(" ", "")
    )

    code_template = code_executor_template[sql_library]

    if sql_library in ["mysql", "mariadb"]:
        host: str = database_properties["hostname"]
        user: str = database_properties["username"]
        password: str = database_properties["password"]
        port: int = database_properties["port"]
        chart_data = execute_mysql_mariadb_updater(
            code_template,
            chart_json,
            host,
            user,
            password,
            port,
        )
    elif sql_library == "postgresql":
        host = database_properties["hostname"]
        user = database_properties["username"]
        password = database_properties["password"]
        port = database_properties["port"]
        database_name: str = database_properties["database_name"]
        chart_data = execute_postgresql_updater(
            code_template,
            chart_json,
            user,
            password,
            host,
            port,
            database_name,
        )
    elif sql_library == "sqlite":
        sqlite_path = database_properties["sqlite_path"]
        chart_data = execute_sqlite_updater(
            code_template,
            chart_json,
            sqlite_path,
        )
    elif sql_library == "sqlserver":
        server = database_properties["server"]
        uid = database_properties["username"]
        pwd = database_properties["password"]
        chart_data = execute_sqlserver_updater(
            code_template,
            chart_json,
            server,
            uid,
            pwd,
        )
    elif sql_library == "oracle":
        user = database_properties["username"]
        password = database_properties["password"]
        host = database_properties["hostname"]
        port = database_properties["port"]
        database_name = database_properties["database_name"]
        chart_data = execute_oracle_updater(
            code_template,
            chart_json,
            user,
            password,
            host,
            port,
            database_name,
        )
    else:
        raise RuntimeError(f"SQL Library {sql_library} is not supported!")

    return chart_data


def run_sql_query_only(
    sql_query: str,
    database_properties: dict,
    sql_library: str,
) -> pd.DataFrame:
    """Run query"""
    sql_library = sql_library.lower().replace("_", "").replace("-", "").replace(" ", "")

    code_template = code_executor_template[sql_library]

    if sql_library in ["mysql", "mariadb"]:
        host = database_properties["hostname"]
        user = database_properties["username"]
        password = database_properties["password"]
        port = database_properties["port"]
        chart_data = run_mysql_mariadb_query_only(
            sql_query,
            code_template,
            host,
            user,
            password,
            port,
        )
    elif sql_library == "postgresql":
        host = database_properties["hostname"]
        user = database_properties["username"]
        password = database_properties["password"]
        port = database_properties["port"]
        chart_data = run_postgresql_query_only(
            sql_query,
            code_template,
            user,
            password,
            host,
            port,
        )
    elif sql_library == "sqlite":
        sqlite_path = database_properties["sqlite_path"]
        chart_data = run_sqlite_query_only(
            sql_query,
            code_template,
            sqlite_path,
        )
    elif sql_library == "sqlserver":
        server = database_properties["server"]
        uid = database_properties["username"]
        pwd = database_properties["password"]
        chart_data = run_sqlserver_query_only(
            sql_query,
            code_template,
            server,
            uid,
            pwd,
        )
    elif sql_library == "oracle":
        user = database_properties["username"]
        password = database_properties["password"]
        host = database_properties["hostname"]
        port = database_properties["port"]
        chart_data = run_oracle_query_only(
            sql_query,
            code_template,
            user,
            password,
            host,
            port,
        )
    else:
        raise RuntimeError(f"SQL Library {sql_library} is not supported!")

    return chart_data
