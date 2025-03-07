code_executor_template = {
    "mysql": """import pandas as pd
import mysql.connector

def generate(host, user, password, port, sql_query):
    # Connect to the mysql database
    conn = mysql.connector.connect(
        host=f"{host}",
        user=f"{user}",
        password=f"{password}",
        port={port},
        database=""
    )

    error = ""

    # Create a cursor object
    cur = conn.cursor()

    try:
        # Execute a query
        cur.execute(f'''{sql_query}''')

        # Fetch all rows from the result
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        queried_df = pd.DataFrame(rows, columns=columns)
    except BaseException as e:
        error = e
        queried_df = pd.DataFrame()

    # Close the cursor and the connection
    cur.close()
    conn.close()
    return queried_df, error

processed_data, error = generate(host, user, password, port, sql_query)""",
    "postgresql": """import pandas as pd
from sqlalchemy import create_engine, text

def generate(user, password, host, port, sql_query, database_name):
    # Connect to the PostgreSQL database
    connection_string = f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{database_name}'

    engine = create_engine(connection_string)
    connection = engine.connect()

    error = ""

    try:
        # Execute a query
        result = connection.execute(text(sql_query))

        # Get the column names from the query result
        columns = list(result.keys())

        # Fetch all rows from the result
        rows = result.fetchall()

        # Create a DataFrame from the query result
        queried_df = pd.DataFrame(rows, columns=columns)
    except BaseException as e:
        error = e
        queried_df = pd.DataFrame()
    finally:
        connection.close()
        engine.dispose()
    
    return queried_df, error

processed_data, error = generate(user, password, host, port, sql_query, database_name)""",
    "mariadb": """import pandas as pd
import mysql.connector

def generate(host, user, password, port, sql_query):
    # Connect to the MariaDB database
    conn = mysql.connector.connect(
        host=f"{host}",
        user=f"{user}",
        password=f"{password}",
        port={port},
        database=""
    )

    error = ""

    # Create a cursor object
    cur = conn.cursor()

    try:
        # Execute a query
        cur.execute(f'''{sql_query}''')

        # Fetch all rows from the result
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        queried_df = pd.DataFrame(rows, columns=columns)
    except BaseException as e:
        error = e
        queried_df = pd.DataFrame()

    # Close the cursor and the connection
    cur.close()
    conn.close()
    
    return queried_df, error

processed_data, error = generate(host, user, password, port, sql_query)""",
    "sqlite": """import pandas as pd
import sqlite3

def generate(sqlite_path, sql_query):
    # Connect to the SQLite database
    conn = sqlite3.connect(f"{sqlite_path}")

    error = ""

    # Create a cursor object
    cur = conn.cursor()

    try:
        # Execute a query
        cur.execute(f'''{sql_query}''')

        # Fetch all rows from the result
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        queried_df = pd.DataFrame(rows, columns=columns)
    except BaseException as e:
        error = e
        queried_df = pd.DataFrame()

    # Close the cursor and the connection
    cur.close()
    conn.close()

    return queried_df, error

processed_data, error = generate(sqlite_path, sql_query)""",
    "sqlserver": """import pandas as pd
import pyodbc

def generate(server, uid, pwd, sql_query):
    # Connect to the SQL Server database
    conn = pyodbc.connect(
        'DRIVER={SQL Server};'"""
    + """
        f'SERVER={server};'
        'DATABASE="";'
        f'UID={uid};'
        f'PWD={pwd};'
    )

    error = ""

    # Create a cursor object
    cur = conn.cursor()

    try:
        # Execute a query
        cur.execute(f'''{sql_query}''')

        # Fetch all rows from the result
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        queried_df = pd.DataFrame(rows, columns=columns)
    except BaseException as e:
        error = e
        queried_df = pd.DataFrame()

    # Close the cursor and the connection
    cur.close()
    conn.close()
    
    return queried_df, error

processed_data, error = generate(server, uid, pwd, sql_query)""",
    "oracle": """import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def generate(host, user, password, port, sql_query, database_name):
    engine = create_engine(f'oracle+oracledb://{user}:{password}@{host}:{port}/?service_name={database_name}')
    connection = engine.connect()
    
    error = ""

    try:
        result = connection.execute(text(sql_query))

        # Get the column names from the query result
        columns = list(result.keys())

        # Fetch all rows from the result
        rows = result.fetchall()

        # Create a DataFrame from the query result
        queried_df = pd.DataFrame(rows, columns=columns)
    except SQLAlchemyError as e:
        error = str(e)
        queried_df = pd.DataFrame()
    finally:
        connection.close()
    
    return queried_df, error

processed_data, error = generate(host, user, password, port, sql_query, database_name)""",
}
