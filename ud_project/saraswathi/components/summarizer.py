import json
import os
import pandas as pd
import logging

from typing import Any, Dict, List, Tuple
from vector_db_utils.column import (
    convert_joined_table_column_to_pinecone_format,
    get_column_info_list_from_table,
)
from vector_db_utils.table import get_joined_table_info, get_table_info
from qdrant_client import QdrantClient
from .datamodel import DataSummary

from logging_library.performancelogger.performance_logger import PerformanceLogger


def check_type(dtype: str, value) -> Any:
    """Cast value to right type to ensure it is JSON serializable

    Args:
        dtype (str): type of the data
        value (any): value to be converted

    Returns:
        Any: converted value based on the dtype

    """
    float_dtype_list = ["float", "double", "double_precision", "decimal", "dec"]
    int_dtype_list = [
        "bit",
        "tinyint",
        "smallint",
        "mediumint",
        "int",
        "integer",
        "bigint",
        "numeric",
        "smallmoney",
        "money",
        "real",
    ]

    if dtype.lower() in float_dtype_list:
        return float(value)
    if dtype.lower() in int_dtype_list:
        return int(value)
    return value


def get_column_properties(
    column_info_list: List[Dict],
) -> list[dict]:
    """Get properties of each column from column metadata.

    Args:
        column_info_list (List[Dict]): list of column info from pinecone column level namespace

    Returns:
        List[Dict]: list of column properties dictionary

    """
    properties_list = []
    for column_info in column_info_list:
        data_tribe = column_info["metadata"]["data_tribe"]
        dtype = column_info["metadata"]["sql_data_type"]
        if (
            data_tribe in ["date_related"]
            or "date" in column_info["metadata"]["cleaned_column_name"].lower()
        ):
            dtype = "date"

        properties: dict = {}

        # dtpye list supports only MySQL and SQL Server data types
        string_dtype_list = [
            "char",
            "varchar",
            "nchar",
            "nvarchar",
            "ntext",
            "binary",
            "varbinary",
            "text",
            "tinyblob",
            "tinytext",
            "blob",
            "mediumtext",
            "mediumblob",
            "longtext",
            "longblob",
            "enum",
            "set",
        ]
        boolean_dtype_list = ["bool", "boolean"]
        numeric_dtype_list = [
            "bit",
            "tinyint",
            "smallint",
            "mediumint",
            "int",
            "integer",
            "bigint",
            "numeric",
            "smallmoney",
            "money",
            "real",
            "float",
            "double",
            "double_precision",
            "decimal",
            "dec",
        ]
        date_dtype_list = ["date", "datetime", "datetime2", "smalldatetime"]

        if dtype in numeric_dtype_list:
            properties["dtype"] = "number"
            try:
                properties["avg"] = check_type(
                    dtype,
                    column_info["metadata"]["avg_value"],
                )
            except Exception:
                pass
            try:
                properties["std"] = check_type(
                    dtype,
                    column_info["metadata"]["std_value"],
                )
            except Exception:
                pass
            try:
                properties["min"] = check_type(
                    dtype,
                    column_info["metadata"]["min_value"],
                )
            except Exception:
                pass
            try:
                properties["max"] = check_type(
                    dtype,
                    column_info["metadata"]["max_value"],
                )
            except Exception:
                pass
        elif dtype in boolean_dtype_list:
            properties["dtype"] = "boolean"
        elif dtype in date_dtype_list:
            properties["dtype"] = "date"
        elif dtype in string_dtype_list:
            if column_info["metadata"]["n_unique_per_row_count"] < 0.5:
                properties["dtype"] = "category"
            else:
                properties["dtype"] = "string"
        else:
            data_samples = column_info["metadata"]["10_samples"]
            if data_samples == "":
                properties["dtype"] = str(dtype)
            else:
                data_samples = [
                    sample
                    for sample in column_info["metadata"]["10_samples"].split("|")
                ]
                if pd.api.types.is_categorical_dtype(data_samples):
                    properties["dtype"] = "category"
                elif pd.api.types.is_datetime64_any_dtype(data_samples):
                    properties["dtype"] = "date"
                else:
                    properties["dtype"] = str(dtype)

        # add min max if dtype is date
        if properties["dtype"] == "date":
            try:
                properties["min"] = column_info["metadata"]["min_value"]
                properties["max"] = column_info["metadata"]["max_value"]
            except Exception:
                pass

        # Add additional properties to the output dictionary
        properties["num_unique_values"] = int(column_info["metadata"]["n_unique"])
        try:
            # New version
            properties["description"] = column_info["metadata"]["long_description"]
        except Exception:
            # Previous version
            properties["description"] = column_info["metadata"]["description"]
        properties["semantic_type"] = ""

        data_samples = column_info["metadata"]["10_samples"]
        if data_samples == "":
            properties["samples"] = []
        else:
            data_samples = [
                sample for sample in column_info["metadata"]["10_samples"].split("|")
            ]
            properties["samples"] = data_samples

        properties_list.append(
            {"column": column_info["id"].split(".")[-1], "properties": properties},
        )

    return properties_list


def generate_table_schema(
    table_info: Dict,
    column_info_list: List[dict],
    code_level_logger: logging.Logger,
) -> Tuple[str, str, dict, dict, dict]:
    """Generate database schema sql based on table info and column info.

    Args:
        table_info (Dict): list of table info from pinecone table level namespace
        column_info_list (List[Dict]): list of column info from pinecone column level namespace

    Returns:
        str: SQL Database Schema

    """
    database_schema_sql = generate_database_schema_sql(
        table_info,
        column_info_list,
        code_level_logger,
    )

    # Add Table Description
    if "metadata" in table_info:
        table_description = table_info["metadata"]["table_description"].strip()

        # Add KPI Formula to Table Description
        if (
            "kpi_name" in table_info["metadata"].keys()
            and table_info["metadata"]["kpi_name"] is not None
            and "kpi_formula" in table_info["metadata"].keys()
            and table_info["metadata"]["kpi_formula"] is not None
        ):
            kpi_names = list(table_info["metadata"]["kpi_name"].split("|"))
            kpi_formulas = list(table_info["metadata"]["kpi_formula"].split("|"))

            if kpi_names != [] and kpi_formulas != []:
                table_description += "\n\nProvided the name of KPIs along with their corresponding formulas:\n"
            for kpi_name, kpi_formula in zip(kpi_names, kpi_formulas):
                table_description += f"{kpi_name} = {kpi_formula}\n"
    else:
        table_description = table_info["table_description"].strip()

        # Add KPI Formula to Table Description
        if (
            "kpi_name" in table_info
            and table_info["kpi_name"] is not None
            and "kpi_formula" in table_info
            and table_info["kpi_formula"] is not None
        ):
            kpi_names = list(table_info["kpi_name"].split("|"))
            kpi_formulas = list(table_info["kpi_formula"].split("|"))

            if kpi_names != [] and kpi_formulas != []:
                table_description += "\n\nProvided the name of KPIs along with their corresponding formulas:\n"
            for kpi_name, kpi_formula in zip(kpi_names, kpi_formulas):
                table_description += f"{kpi_name} = {kpi_formula}\n"

    # Add Column Description Dict, Column Samples Dict, & Column Display Names Dict
    column_description_dict: dict = {}
    column_sample_dict: dict = {}
    column_display_name_dict: dict = {}

    for column_info in column_info_list:
        if "metadata" in column_info.keys():
            column_info_copy = column_info["metadata"].copy()
        else:
            column_info_copy = column_info.copy()

        try:
            column_description_dict[column_info_copy["cleaned_column_name"]] = (
                column_info_copy["long_description"]
            )
        except Exception:
            try:
                column_description_dict[column_info_copy["cleaned_column_name"]] = (
                    column_info_copy["column_description"]
                )
            except Exception:
                pass

        try:
            column_sample_dict[column_info_copy["cleaned_column_name"]] = (
                column_info_copy["10_samples"].split("|")[0]
            )
        except Exception:
            try:
                column_sample_dict[column_info_copy["cleaned_column_name"]] = (
                    column_info_copy["all_samples"].split("|")[0]
                )
            except Exception:
                pass

        try:
            column_display_name_dict[column_info_copy["cleaned_column_name"]] = (
                column_info_copy["column_description"]
            )
        except Exception:
            pass

    return (
        database_schema_sql,
        table_description,
        column_description_dict,
        column_sample_dict,
        column_display_name_dict,
    )


def generate_database_schema_sql(
    table_info: Dict,
    column_info_list: List[dict],
    code_level_logger: logging.Logger,
):
    column_sql_str = ""
    if "metadata" in table_info:
        table_info = table_info["metadata"]
    sql_database = (
        table_info["sql_database_name"].lower().replace("_", "").replace(" ", "")
    )
    table_name = table_info["table_name"]
    # sql_database = "mysql"
    sql_database = get_sql_library(sql_database, code_level_logger).lower()

    primary_key_columns: list = []
    autoincrement_seq_names: list = []
    foreign_columns: list = []

    column_info_list_len = len(column_info_list)
    for column_info_idx, column_info in enumerate(column_info_list):
        if "metadata" in column_info.keys():
            column_info_copy = column_info["metadata"].copy()
        else:
            column_info_copy = column_info.copy()

        if sql_database in ["mysql", "mariadb"]:
            column_sql_str += f"""    `{column_info_copy['cleaned_column_name']}` {column_info_copy['sql_data_type']}"""
        elif sql_database in ["postgresql", "sqlite", "oracle"]:
            column_sql_str += f"""    "{column_info_copy['cleaned_column_name']}" {column_info_copy['sql_data_type']}"""
        elif sql_database == "sqlserver":
            column_sql_str += f"""    [{column_info_copy['cleaned_column_name']}] {column_info_copy['sql_data_type']}"""

        try:
            if column_info_copy["is_primary"]:
                primary_key_columns.append(column_info_copy["cleaned_column_name"])
        except Exception:
            pass

        try:
            if column_info_copy["is_unsigned"]:
                if sql_database in ["mysql", "mariadb"]:
                    column_sql_str += " UNSIGNED"
                elif (
                    sql_database == "postgresql"
                    or sql_database == "sqlite"
                    or sql_database == "sqlserver"
                    or sql_database == "oracle"
                ):
                    column_sql_str += (
                        f""" CHECK ("{column_info_copy['cleaned_column_name']}" >= 0)"""
                    )
        except Exception:
            pass

        try:
            if column_info_copy["is_zerofill"]:
                if sql_database in ["mysql", "mariadb"]:
                    column_sql_str += " ZEROFILL"
        except Exception:
            pass

        try:
            if column_info_copy["is_autoincrement"]:
                if sql_database in ["mysql", "mariadb"]:
                    column_sql_str += " AUTO_INCREMENT"
                elif sql_database == "postgresql":
                    column_sql_str += f""" DEFAULT NEXTVAL("{table_name}_{column_info_copy['cleaned_column_name']}_seq")"""
                    autoincrement_seq_names.append(
                        f"{table_name}_{column_info_copy['cleaned_column_name']}_seq",
                    )
                elif sql_database == "sqlite":
                    column_sql_str += " AUTOINCREMENT"
                elif sql_database == "sqlserver":
                    column_sql_str += " IDENTITY(1,1)"
                elif sql_database == "oracle":
                    column_sql_str += f""" DEFAULT {table_name}_{column_info_copy['cleaned_column_name']}_seq.NEXTVAL"""
                    autoincrement_seq_names.append(
                        f"{table_name}_{column_info_copy['cleaned_column_name']}_seq",
                    )
        except Exception:
            pass

        try:
            if column_info_copy["is_unique"]:
                column_sql_str += " UNIQUE"
        except Exception:
            pass

        try:
            if column_info_copy["is_nullable"]:
                column_sql_str += " NULL"
            else:
                column_sql_str += " NOT NULL"
        except Exception:
            pass

        try:
            if column_info_copy["is_foreignkey"]:
                if sql_database in ["mysql", "mariadb"]:
                    foreign_columns.append(
                        {
                            "column_name": column_info_copy["cleaned_column_name"],
                            "reference_table_name": column_info_copy["reference_table"],
                            "reference_column_name": column_info_copy[
                                "reference_column"
                            ],
                        },
                    )
                elif sql_database == "postgresql":
                    column_sql_str += f" REFERENCES {column_info_copy['reference_table']}({column_info_copy['reference_column']})"
                elif (
                    sql_database == "sqlite"
                    or sql_database == "sqlserver"
                    or sql_database == "oracle"
                ):
                    foreign_columns.append(
                        {
                            "column_name": column_info_copy["cleaned_column_name"],
                            "reference_table_name": column_info_copy["reference_table"],
                            "reference_column_name": column_info_copy[
                                "reference_column"
                            ],
                        },
                    )
        except Exception:
            pass

        if column_info_idx < (column_info_list_len - 1):
            column_sql_str += ", \n"

    if primary_key_columns != []:
        if sql_database in [
            "mysql",
            "mariadb",
            "postgresql",
            "sqlite",
        ] or sql_database in ["sqlserver", "oracle"]:
            primary_key_sql = "PRIMARY KEY ("
            primary_key_columns_len = len(primary_key_columns)
            for primary_key_column_idx, primary_key_column in enumerate(
                primary_key_columns,
            ):
                if primary_key_column_idx == (primary_key_columns_len - 1):
                    primary_key_sql += f"{primary_key_column}"
                else:
                    primary_key_sql += f"{primary_key_column},"

            primary_key_sql += ")"
        else:
            logging.error(
                f"SQL database {sql_database} is not supported in generate_database_schema_sql!"
            )
            raise ValueError(
                f"SQL database {sql_database} is not supported in generate_database_schema_sql!"
            )

        column_sql_str += f", \n    {primary_key_sql}"

    if foreign_columns != []:
        if sql_database in ["mysql", "mariadb", "sqlite", "sqlserver"]:
            for foreign_column in foreign_columns:
                column_sql_str += f", \n    FOREIGN KEY({foreign_column['column_name']}) REFERENCES {foreign_column['reference_table_name']}({foreign_column['reference_column_name']})"
        elif sql_database == "oracle":
            for foreign_column in foreign_columns:
                column_sql_str += f", \n    CONSTRAINT fk_{foreign_column['column_name']} FOREIGN KEY ({foreign_column['column_name']}) REFERENCES {foreign_column['reference_table_name']}({foreign_column['reference_column_name']})"

    if sql_database == "postgresql":
        # Remove Database Name
        database_schema_sql = f"""CREATE TABLE {table_info['table_name'][table_info['table_name'].find('.')+1:]} (
{column_sql_str}
);"""
    else:
        database_schema_sql = f"""CREATE TABLE "{table_info['table_name']}" (
{column_sql_str}
);"""

    if autoincrement_seq_names != []:
        if sql_database == "postgresql":
            for autoincrement_seq_name in autoincrement_seq_names:
                database_schema_sql = (
                    f"CREATE SEQUENCE {autoincrement_seq_name}; \n"
                    + database_schema_sql
                )
        elif sql_database == "oracle":
            for autoincrement_seq_name in autoincrement_seq_names:
                database_schema_sql = (
                    f"CREATE SEQUENCE {autoincrement_seq_name} START WITH 1 INCREMENT BY 1; \n"
                    + database_schema_sql
                )

    return database_schema_sql


def get_sql_library(
    sql_database: str,
    code_level_logger: logging.Logger,
) -> str:
    sql_library: str = ""

    if "mysql" in sql_database.lower():
        sql_library = "MySQL"
    elif "postgresql" in sql_database.lower():
        sql_library = "PostgreSQL"
    elif "oracle" in sql_database.lower():
        sql_library = "Oracle"
    elif "mariadb" in sql_database.lower():
        sql_library = "MariaDB"
    elif "sqlite" in sql_database.lower():
        sql_library = "SQLite"
    elif "sqlserver" in sql_database.lower():
        sql_library = "SQLServer"
    else:
        code_level_logger.error(
            f"SQL Library {sql_database} is not supported in get_sql_library!"
        )
        raise RuntimeError(
            f"SQL Library {sql_database} is not supported in get_sql_library!"
        )

    return sql_library


def get_column_name_list(
    column_info_list: list,
    code_level_logger: logging.Logger,
) -> list:
    column_name_list = []

    for column_info in column_info_list:
        if (
            "metadata" in column_info.keys()
            and column_info["metadata"]["cleaned_column_name"] != ""
        ):
            column_name_list.append(column_info["metadata"]["cleaned_column_name"])
        elif column_info["cleaned_column_name"] != "":
            column_name_list.append(column_info["cleaned_column_name"])

    if column_name_list == []:
        code_level_logger.error("No column name extracted!")
        raise RuntimeError("No column name extracted!")

    return column_name_list


def get_n_unique_value_dict(
    column_info_list: list,
    code_level_logger: logging.Logger,
) -> dict:
    column_n_uniques: dict = {}

    for column_info in column_info_list:
        if "metadata" in column_info.keys():
            column_n_uniques[column_info["metadata"]["cleaned_column_name"]] = (
                column_info["metadata"]["n_unique"]
            )
        else:
            column_n_uniques[column_info["cleaned_column_name"]] = column_info[
                "n_unique"
            ]

    if column_n_uniques == {}:
        code_level_logger.error("No column number of uniques extracted!")
        raise RuntimeError("No column number of uniques extracted!")

    return column_n_uniques


def get_column_data_tribes(
    column_info_list: list,
    code_level_logger: logging.Logger,
) -> dict:
    column_data_tribes: dict = {}

    for column_info in column_info_list:
        if "metadata" in column_info.keys():
            column_data_tribes[column_info["metadata"]["cleaned_column_name"]] = (
                column_info["metadata"]["data_tribe"]
            )
        else:
            column_data_tribes[column_info["cleaned_column_name"]] = column_info[
                "data_tribe"
            ]

    if column_data_tribes == {}:
        code_level_logger.error("No column data tribes extracted!")
        raise RuntimeError("No column data tribes extracted!")

    return column_data_tribes


def get_column_sql_data_types(
    column_info_list: list,
    code_level_logger: logging.Logger,
) -> dict:
    column_sql_data_types: dict = {}

    for column_info in column_info_list:
        if "metadata" in column_info.keys():
            column_sql_data_types[column_info["metadata"]["cleaned_column_name"]] = (
                column_info["metadata"]["sql_data_type"]
            )
        else:
            column_sql_data_types[column_info["cleaned_column_name"]] = column_info[
                "sql_data_type"
            ]

    if column_sql_data_types == {}:
        code_level_logger.error("No column sql data types extracted!")
        raise RuntimeError("No column sql data types extracted!")

    return column_sql_data_types


def summarize(
    qdrant_client: QdrantClient,
    database_name: str,
    database_identifier: str,
    table_collection: str,
    column_collection: str,
    table_name: str,
    embedding_model_url: str,
    logging_url: str,
    session_id: str,
    code_level_logger: logging.Logger,
) -> DataSummary:
    """Summarize a table from pinecone containing all the column metadata.

    Args:
        index (pinecone.Index): pinecone index used to get table metadata and column metadata
        database_name (str): database name of the pinecone
        table_collection (str): namespace used from the pinecone index to get table metadata
        column_collection (str): namespace used from the pinecone index to get column metadata
        table_name (str): table name to be summarized
        embeddings (AzureOpenAIEmbeddings): Langchain OpenAI/Cohere embedder class

    Returns:
        dict: table summary dictionary

    """

    with PerformanceLogger(session_id):
        table_info = get_table_info(
            embedding_model_url,
            qdrant_client,
            table_name,
            database_name,
            database_identifier,
            table_collection,
            code_level_logger,
        )

        column_info_list = get_column_info_list_from_table(
            embedding_model_url,
            qdrant_client,
            f"{database_name}.{table_name}",
            f"{database_name}.{table_name}",
            database_identifier,
            column_collection,
            code_level_logger,
        )

        column_name_list = get_column_name_list(
            column_info_list,
            code_level_logger,
        )

        column_n_unique_value_dict = get_n_unique_value_dict(
            column_info_list,
            code_level_logger,
        )

        (
            database_schema_sql,
            table_description,
            column_description_dict,
            column_sample_dict,
            column_display_name_dict,
        ) = generate_table_schema(
            table_info,
            column_info_list,
            code_level_logger,
        )

        db_tag = table_info["metadata"]["database_identifier"]

        # db_tag = "label3"

        database_properties: dict = {}

        client_db_credentials: list = json.loads(os.getenv("CLIENT_DB", "[]"))

        for client_db_data in client_db_credentials:
            if client_db_data["db_tag"] == db_tag:
                database_properties = client_db_data
                break

        if database_properties == {}:
            code_level_logger.error("Database Properties is not found!")
            raise RuntimeError("Database Properties is not found!")

        sql_library = get_sql_library(
            database_properties["database_type"],
            code_level_logger,
        )

        column_data_tribes = get_column_data_tribes(
            column_info_list,
            code_level_logger,
        )

        column_sql_data_types = get_column_sql_data_types(
            column_info_list,
            code_level_logger,
        )

        return DataSummary(
            database_schema_sql=database_schema_sql,
            table_description=table_description,
            column_description_dict=column_description_dict,
            column_sample_dict=column_sample_dict,
            sql_library=sql_library,
            database_properties=database_properties,
            column_name_list=column_name_list,
            column_display_name_dict=column_display_name_dict,
            column_data_tribes=column_data_tribes,
            column_n_unique_value_dict=column_n_unique_value_dict,
            column_sql_data_types=column_sql_data_types,
            table_join_sql_query="",
        )


def summarize_without_query_metadata(
    table_info: dict,
    column_info_list: list,
    code_level_logger: logging.Logger,
) -> DataSummary:
    """This Python function generates a summary of data related to a table without including query
    metadata.

    :param table_info: The `table_info` parameter is a dictionary containing information about a
    database table. It likely includes details such as the table name, schema, and metadata
    :type table_info: dict
    :param column_info_list: The `column_info_list` parameter is a list containing information about the
    columns in a table. Each element in the list represents a column and contains details such as the
    column name, data type, constraints, and other relevant information. This information is used to
    generate a summary of the table's schema and
    :type column_info_list: list
    :return: The function `summarize_without_query_metadata` returns a `DataSummary` object with the
    following attributes:
    """
    column_name_list = get_column_name_list(
        column_info_list,
        code_level_logger,
    )

    column_n_unique_value_dict = get_n_unique_value_dict(
        column_info_list,
        code_level_logger,
    )

    (
        database_schema_sql,
        table_description,
        column_description_dict,
        column_sample_dict,
        column_display_name_dict,
    ) = generate_table_schema(
        table_info,
        column_info_list,
        code_level_logger,
    )

    db_tag = table_info["database_identifier"]

    # db_tag = "label1"

    database_properties = {}

    client_db_credentials: list = json.loads(os.getenv("CLIENT_DB", "[]"))

    for client_db_data in client_db_credentials:
        if client_db_data["db_tag"] == db_tag:
            database_properties = client_db_data
            break

    if database_properties == {}:
        code_level_logger.error("Database Properties is not found!")
        raise RuntimeError("Database Properties is not found!")

    sql_library = get_sql_library(
        database_properties["database_type"],
        code_level_logger,
    )

    column_data_tribes = get_column_data_tribes(
        column_info_list,
        code_level_logger,
    )

    column_sql_data_types = get_column_sql_data_types(
        column_info_list,
        code_level_logger,
    )

    return DataSummary(
        database_schema_sql=database_schema_sql,
        table_description=table_description,
        column_description_dict=column_description_dict,
        column_sample_dict=column_sample_dict,
        sql_library=sql_library,
        database_properties=database_properties,
        column_name_list=column_name_list,
        column_display_name_dict=column_display_name_dict,
        column_data_tribes=column_data_tribes,
        column_n_unique_value_dict=column_n_unique_value_dict,
        column_sql_data_types=column_sql_data_types,
        table_join_sql_query="",
    )


def summarize_joined_table(
    qdrant_client: QdrantClient,
    database_name: str,
    table_name: str,
    combined_table_description: str,
    table_join_sql_query: str,
    table_level_metadata_list: list,
    column_level_metadata_list: list,
    session_id: str,
    code_level_logger: logging.Logger,
) -> DataSummary:
    """Summarize a table from pinecone containing all the column metadata.

    Args:
        index (pinecone.Index): pinecone index used to get table metadata and column metadata
        database_name (str): database name of the pinecone
        table_collection (str): namespace used from the pinecone index to get table metadata
        column_collection (str): namespace used from the pinecone index to get column metadata
        table_name (str): table name to be summarized
        embeddings (AzureOpenAIEmbeddings): Langchain OpenAI/Cohere embedder class

    Returns:
        dict: table summary dictionary

    """

    with PerformanceLogger(session_id):
        table_info = get_joined_table_info(
            database_name,
            table_name,
            combined_table_description,
            table_level_metadata_list,
            code_level_logger,
        )

        column_info_list = convert_joined_table_column_to_pinecone_format(
            column_level_metadata_list,
        )

        column_name_list = get_column_name_list(
            column_info_list,
            code_level_logger,
        )

        column_n_unique_value_dict = get_n_unique_value_dict(
            column_info_list,
            code_level_logger,
        )

        (
            database_schema_sql,
            table_description,
            column_description_dict,
            column_sample_dict,
            column_display_name_dict,
        ) = generate_table_schema(
            table_info,
            column_info_list,
            code_level_logger,
        )

        db_tag = table_info["database_identifier"]

        # db_tag = "label3"

        database_properties: dict = {}

        client_db_credentials: list = json.loads(os.getenv("CLIENT_DB", "[]"))

        for client_db_data in client_db_credentials:
            if client_db_data["db_tag"] == db_tag:
                database_properties = client_db_data
                break

        if database_properties == {}:
            code_level_logger.error(
                f"Database Properties for {database_name}.{table_name} is not found!"
            )
            raise RuntimeError("Database Properties is not found!")

        sql_library = get_sql_library(
            database_properties["database_type"], code_level_logger
        )

        column_data_tribes = get_column_data_tribes(
            column_info_list,
            code_level_logger,
        )

        column_sql_data_types = get_column_sql_data_types(
            column_info_list,
            code_level_logger,
        )

        return DataSummary(
            database_schema_sql=database_schema_sql,
            table_description=table_description,
            column_description_dict=column_description_dict,
            column_sample_dict=column_sample_dict,
            sql_library=sql_library,
            database_properties=database_properties,
            column_name_list=column_name_list,
            column_display_name_dict=column_display_name_dict,
            column_data_tribes=column_data_tribes,
            column_n_unique_value_dict=column_n_unique_value_dict,
            column_sql_data_types=column_sql_data_types,
            table_join_sql_query=table_join_sql_query,
        )
