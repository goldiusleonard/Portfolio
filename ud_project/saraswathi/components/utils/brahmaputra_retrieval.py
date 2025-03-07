import ast
import os

import mysql.connector

# import psycopg2
# import sqlite3
# import pyodbc
# import cx_Oracle


def get_blue_river_output_from_sql(session_id: str):
    """Retrieve the blue river output information from various SQL databases as a Python dictionary."""
    database_properties: dict = ast.literal_eval(os.getenv("BRAHMAPUTRA_DB", "{}"))
    if database_properties == {}:
        raise ValueError("BRAHMAPUTRA_DB environment variable is not set")

    table_name = database_properties["table_name"]
    database_library: str = database_properties["database_library"]

    try:
        conn = None
        cursor = None
        select_query = ""

        if database_library.lower() == "mysql" or database_library.lower() == "mariadb":
            host: str = database_properties["hostname"]
            user: str = database_properties["username"]
            port: int = int(database_properties["port"])
            password: str = database_properties["password"]
            database_name: str = database_properties["database_name"]

            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database_name,
                port=port,
            )
            cursor = conn.cursor()
            select_query = (
                f"SELECT BlueRiverOutput FROM {table_name} WHERE SessionID = %s"
            )
        # elif database_library.lower() == "postgresql":
        #     host: str = database_properties["hostname"]
        #     user: str = database_properties["username"]
        #     port: int = int(database_properties["port"])
        #     password: str = database_properties["password"]
        #     database_name: str = database_properties["database_name"]

        #     conn = psycopg2.connect(
        #         host=host, user=user, password=password, dbname=database_name, port=port
        #     )
        #     cursor = conn.cursor()
        #     select_query = (
        #         f"SELECT BlueRiverOutput FROM {table_name} WHERE SessionID = %s"
        #     )
        # elif database_library.lower() == "sqlite":
        #     database_path: str = database_properties["database_path"]

        #     conn = sqlite3.connect(database_path)
        #     cursor = conn.cursor()
        #     select_query = (
        #         f"SELECT BlueRiverOutput FROM {table_name} WHERE SessionID = ?"
        #     )
        # elif database_library.lower() == "sqlserver":
        #     host: str = database_properties["hostname"]
        #     user: str = database_properties["username"]
        #     port: int = int(database_properties["port"])
        #     password: str = database_properties["password"]
        #     database_name: str = database_properties["database_name"]

        #     conn = pyodbc.connect(
        #         f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={host},{port};DATABASE={database_name};UID={user};PWD={password}"
        #     )
        #     cursor = conn.cursor()
        #     select_query = (
        #         f"SELECT BlueRiverOutput FROM {table_name} WHERE SessionID = ?"
        #     )
        # elif database_library.lower() == "oracle":
        #     host: str = database_properties["hostname"]
        #     user: str = database_properties["username"]
        #     port: int = int(database_properties["port"])
        #     password: str = database_properties["password"]
        #     database_name: str = database_properties["database_name"]

        #     dsn = cx_Oracle.makedsn(host, port, service_name=database_name)
        #     conn = cx_Oracle.connect(user=user, password=password, dsn=dsn)
        #     cursor = conn.cursor()
        #     select_query = (
        #         f"SELECT BlueRiverOutput FROM {table_name} WHERE SessionID = :1"
        #     )
        else:
            raise ValueError(f"Unsupported database library: {database_library}")

        # Execute the query and fetch the slot data
        cursor.execute(select_query, (session_id,))
        blue_river_output = cursor.fetchone()  # Fetch one result

        if blue_river_output and blue_river_output[0]:
            # Convert the JSON data to a Python dictionary
            blue_river_dict = ast.literal_eval(blue_river_output[0])
            return blue_river_dict
        return []

    except Exception as err:
        print(f"Error: {err}")
        return []
    finally:
        # Ensure the connection is closed
        if conn:
            if cursor:
                cursor.close()
            conn.close()
