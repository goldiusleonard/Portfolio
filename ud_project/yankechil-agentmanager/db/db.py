import sys

sys.stdout.reconfigure(encoding="utf-8")
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import Column, create_engine
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from log_mongo import logger

# Reconfigure stdout for UTF-8
sys.stdout.reconfigure(encoding="utf-8")

# Load environment variables
load_dotenv()

# Database URL configuration
mysql_database = os.getenv("mysql_database")
if not mysql_database:
    logger.error("mysql_database not found")


# Assuming a shared base class for all dynamic schemas
Base = declarative_base()

class Database:
    def __init__(self, db_url: str, output_schemas: list, input_schemas: list = None):
        self.engine = create_engine(
            db_url,
            connect_args={
                "connect_timeout": 60,  # Timeout for establishing connection (in seconds)
                "read_timeout": 600,
                "write_timeout": 600,
            },
            pool_recycle=3600,  # Recycle connections after 1 hour to avoid connection expiry
            pool_size=10,  # Maximum number of open connections in the pool
            max_overflow=5,  # Number of additional connections allowed beyond pool_size
            pool_pre_ping=True,  # Add this to ensure the connection is alive before using it
        )
        self.session = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )()

        self.metadata = Base.metadata

        # Set global timeout values
        self._set_global_timeout()

        # Store schema classes for reference
        self.input_schemas = input_schemas
        self.output_schemas = output_schemas

        # Ensure dynamic table classes are registered with Base.metadata
        for schema in self.output_schemas:
            if not hasattr(schema, '__bases__') or Base not in schema.__bases__:
                raise ValueError(f"Schema {schema.__name__} does not inherit from the base class.")
        
        # Create all tables from Base.metadata (automatically registers tables)
        Base.metadata.create_all(self.engine)


    def _set_global_timeout(self):
        """Set global timeout values for MySQL server."""
        # Extract connection arguments from the engine to connect directly via pymysql
        connection = self.engine.raw_connection()

        try:
            # Execute the SET GLOBAL commands to change the timeout values
            with connection.cursor() as cursor:
                cursor.execute("SET GLOBAL wait_timeout = 28800;")
                cursor.execute("SET GLOBAL interactive_timeout = 28800;")
                connection.commit()
            print("Global timeout values have been updated successfully.")
        except Exception as e:
            print(f"Error setting global timeout values: {e}")
        finally:
            # Ensure the connection is closed
            connection.close()

    def get_session(self):
        return self.session

    def get_engine(self):
        return self.engine

    def get_input_schemas(self):
        return self.input_schemas

    def get_output_schemas(self):
        return self.output_schemas

    def create_tables(self):
        """Create tables in the database."""
        self.metadata.create_all(self.engine)

    def close(self):
        self.session.close()

    def create_table_schema(self, table_name, columns):
        """Dynamically create a table schema with the given table name and columns.

        Args:
            table_name (str): The name of the table.
            columns (list of tuples): A list of tuples where each tuple contains
                                    the column name, column type, and additional options.

        Returns:
            DeclarativeMeta: A dynamically created SQLAlchemy table schema.

        """
        Base = declarative_base()
        # Dynamically create the table class
        attributes = {"__tablename__": table_name}

        # Add columns dynamically
        for column_name, column_type, column_options in columns:
            attributes[column_name] = Column(column_type, **column_options)

        # Create and return the class
        return type(table_name.capitalize() + "Schema", (Base,), attributes)

    def check_table_exists(self, table_name: str) -> bool:
        """Check if the table exists in the database."""
        try:
            df = pd.read_sql_table(table_name, self.engine)
            if not df.empty:
                return True
        except ValueError:
            return False

    def get_data(self, table_source_name):
        """Get data from the source table.

        Returns:
            pd.DataFrame: Data from the source table.

        """
        logger.info(f"Fetching data from the source table: {table_source_name}")
        df = self._fetch_data_from_source(table_source_name)

        return df

    def get_data_from_table(self, table_source_name: str) -> pd.DataFrame:
        """Get data from the source table if it exists.

        Args:
            table_source_name (str): Name of the source table to fetch data from.

        Returns:
            pd.DataFrame: Data from the source table, or None if the table doesn't exist.

        """
        logger.info(f"Checking if the source table '{table_source_name}' exists.")

        # Step 1: Check if the table exists
        inspector = Inspector.from_engine(self.engine)
        if table_source_name not in inspector.get_table_names():
            logger.warning(f"Table '{table_source_name}' does not exist.")
            return None  # or return pd.DataFrame() if you prefer an empty DataFrame

        # Step 2: If the table exists, fetch the data
        try:
            logger.info(f"Fetching data from the source table: {table_source_name}")
            df = self._fetch_data_from_source(table_source_name)

            if df is not None and not df.empty:
                return df
            logger.warning(f"Table '{table_source_name}' is empty.")
            return None  # or return an empty DataFrame, depending on your needs

        except Exception as e:
            logger.error(
                f"An error occurred while fetching data from '{table_source_name}': {e}",
            )
            return None  # or return an empty DataFrame if preferred

    def get_batch_data_from_table(
        self,
        table_source_name: str,
        batch_size: int = 1000,
        offset: int = 0,
        order_by: str = "id",
    ) -> pd.DataFrame:
        """Get data from the source table in batches, ensuring a consistent order.

        Args:
            table_source_name (str): Name of the source table to fetch data from.
            batch_size (int): Number of rows to fetch in each batch.
            offset (int): The starting point (offset) for the query.
            order_by (str): Column name to order the results by.

        Returns:
            pd.DataFrame: Data from the source table.
        """
        logger.info(
            f"Fetching data from table: {table_source_name}, batch size: {batch_size}, offset: {offset}, order by: {order_by}"
        )

        # Construct SQL query to fetch data in batches with ordering
        query = f"""
            SELECT *
            FROM {table_source_name}
            ORDER BY {order_by} ASC
            LIMIT {batch_size} OFFSET {offset}
        """
        try:
            df = pd.read_sql(query, self.engine)
            return df
        except Exception as e:
            logger.error(f"Error fetching data from {table_source_name}: {e}")
            return pd.DataFrame()  # Return empty DataFrame if an error occurs

    def get_new_rows(self, key_id, table_target_name: str, table_source_name: str):
        """Fetch new rows from table_source_name that do not exist in table_target_name.
        If the target table does not exist or is empty, fetch all rows from the source table.

        Args:
            key_id (str): Column name used to identify rows uniquely.
            table_target_name (str): Name of the target table.
            table_source_name (str): Name of the source table.

        Returns:
            pd.DataFrame: A DataFrame containing new rows from the source table.

        """
        try:
            # Check if the target table exists
            table_exists_query = f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = '{table_target_name}'
            """
            table_exists_df = pd.read_sql_query(table_exists_query, self.engine)
            if table_exists_df.iloc[0, 0] == 0:
                print(
                    f"Target table '{table_target_name}' does not exist. Fetching all rows from source table.",
                )
                all_rows_query = f"SELECT * FROM {table_source_name}"
                return pd.read_sql_query(all_rows_query, self.engine)

            # Check if the target table is empty
            table_empty_query = f"SELECT COUNT(*) AS row_count FROM {table_target_name}"
            table_empty_df = pd.read_sql_query(table_empty_query, self.engine)
            if table_empty_df["row_count"].iloc[0] == 0:
                print(
                    f"Target table '{table_target_name}' is empty. Fetching all rows from source table.",
                )
                all_rows_query = f"SELECT * FROM {table_source_name}"
                return pd.read_sql_query(all_rows_query, self.engine)

            # Query to get the maximum id from the target table
            max_id_query = f"SELECT MAX({key_id}) AS max_id FROM {table_target_name}"
            max_id_df = pd.read_sql_query(max_id_query, self.engine)
            max_id = (
                max_id_df["max_id"].iloc[0]
                if not max_id_df["max_id"].isnull().iloc[0]
                else None
            )

            # Fetch new rows from the source table
            if max_id is None:
                print(
                    "No valid max ID found in the target table. Fetching all rows from source table.",
                )
                new_rows_query = f"SELECT * FROM {table_source_name}"
            else:
                new_rows_query = (
                    f"SELECT * FROM {table_source_name} WHERE {key_id} > '{max_id}'"
                )

            new_rows_df = pd.read_sql_query(new_rows_query, self.engine)
            return new_rows_df

        except Exception as e:
            print(f"An error occurred: {e}")
            return pd.DataFrame()

    def insert_data(self, table_name: str, data: pd.DataFrame):
        """Insert data into a table."""
        try:
            # Replace NaN with None for SQL compatibility
            data = data.where(pd.notnull(data), None)

            # Log the column types and check for duplicate rows
            logger.info(f"Data to be inserted: {data.head()}")
            logger.info(f"Data columns and types: {data.info()}")
            logger.info(f"Duplicate rows: {data[data.duplicated(subset=['_id'])]}")

            logger.info(f"Inserting {data.shape[0]} rows into {table_name}")

            # Insert the data
            data.to_sql(
                table_name,
                self.engine,
                index=False,
                if_exists="append",
                method="multi",
            )
            logger.info(f"Data inserted into {table_name} successfully.")
        except Exception as e:
            logger.error(f"Failed to insert data into {table_name}: {e}")
            logger.error(f"Data attempted to insert: {data.head()}")

    def insert_row_by_row(self, key_id, schema, table_row, i):
        """Insert a single row from a DataFrame into the database."""
        try:
            row_dict = table_row.to_dict()
            # Check if a row with the same unique attributes already exists
            existing_row = (
                self.session.query(schema)
                .filter_by(
                    **{key: row_dict[key] for key in [key_id]},
                )  # key_id is unique column name
                .first()
            )
            if not existing_row:
                # # Convert row to a dictionary and insert it into the table schema
                table_row = schema(**row_dict)

                # Add the new row to the session
                self.session.add(table_row)

                # Commit the changes (this happens for each row)
                self.session.commit()
                logger.info(f"Row {i} inserted successfully.")
            else:
                logger.error(f"Duplicate row found, skipping insertion: {row_dict}")

        except IntegrityError as e:
            # Handle integrity errors (e.g., primary key violations)
            self.session.rollback()  # Rollback the transaction to maintain consistency
            logger.error(f"Integrity error inserting row {i}: {e}")

        except Exception as e:
            # Handle other exceptions
            self.session.rollback()  # Ensure session consistency by rolling back
            logger.error(f"Failed to insert row {i}: {e}")

    def get_new_rows_by_id(
        self,
        key_id,
        table_target_name: str,
        table_source_name: str,
    ):
        """Fetch new rows from table_source_name that do not exist in table_target_name.

        Args:
            table_target_name (str): Name of the target table.
            table_source_name (str): Name of the source table.

        Returns:
            pd.DataFrame: A DataFrame containing new rows from the source table.

        """
        # Query to get the maximum id from table2
        max_id_query = f"""
            SELECT MAX({key_id}) AS max_id 
            FROM {table_target_name}
        """

        # Use try-except block to handle potential errors
        try:
            max_id_df = pd.read_sql_query(max_id_query, self.engine)
        except Exception as e:
            print(f"Error fetching max id: {e}")
            return pd.DataFrame()

        # Get the maximum id value, handle potential None value
        max_id = (
            max_id_df["max_id"].values[0]
            if max_id_df["max_id"].notnull().all()
            else None
        )

        # Query to get new rows from table1
        new_rows_query = f"""
            SELECT * 
            FROM {table_source_name} 
            WHERE {key_id} > '{max_id}' OR {key_id} IS NULL
        """

        # Use try-except block to handle potential errors
        try:
            new_rows_df = pd.read_sql_query(new_rows_query, self.engine)
        except Exception as e:
            print(f"Error fetching new rows: {e}")
            return pd.DataFrame()

        return new_rows_df

    def get_new_rows_by_date(
        self,
        table_target_name: str,
        table_source_name: str,
        start_date: str,
        end_date: str,
    ):
        """Fetch new rows from table_source_name within a specified date range
        that do not exist in table_target_name.

        Args:
            table_target_name (str): Name of the target table.
            table_source_name (str): Name of the source table.
            start_date (str): Start date in 'YYYY-MM-DD' format.
            end_date (str): End date in 'YYYY-MM-DD' format.

        Returns:
            pd.DataFrame: A DataFrame containing new rows from the source table.

        """
        # Validate input dates
        if not start_date or not end_date:
            print("Start date and end date must be provided.")
            return pd.DataFrame()

        date_column = "created_at"
        # Query to get existing rows from the target table within the date range
        existing_rows_query = f"""
            SELECT DISTINCT {date_column} 
            FROM {table_target_name} 
            WHERE {date_column} BETWEEN '{start_date}' AND '{end_date}'
        """

        # Use try-except block to handle potential errors
        try:
            existing_rows_df = pd.read_sql_query(existing_rows_query, self.engine)
        except Exception as e:
            print(f"Error fetching existing rows: {e}")
            return pd.DataFrame()

        # Convert existing dates to a set for comparison
        existing_dates = (
            set(existing_rows_df[date_column].values)
            if not existing_rows_df.empty
            else set()
        )

        # Query to fetch new rows from the source table
        new_rows_query = f"""
            SELECT * 
            FROM {table_source_name} 
            WHERE {date_column} BETWEEN '{start_date}' AND '{end_date}'
        """

        # Use try-except block to handle potential errors
        try:
            source_rows_df = pd.read_sql_query(new_rows_query, self.engine)
        except Exception as e:
            print(f"Error fetching new rows: {e}")
            return pd.DataFrame()

        # Filter out rows that already exist in the target table
        new_rows_df = source_rows_df[~source_rows_df[date_column].isin(existing_dates)]

        return new_rows_df

    def get_new_rows_until_date(
        self,
        table_target_name: str,
        table_source_name: str,
        end_date: str,
    ):
        """Fetch new rows from table_source_name from the beginning of the table
        until a specified end_date that do not exist in table_target_name.

        Args:
            table_target_name (str): Name of the target table.
            table_source_name (str): Name of the source table.
            end_date (str): End date in 'YYYY-MM-DD' format.

        Returns:
            pd.DataFrame: A DataFrame containing new rows from the source table.

        """
        # Validate input date
        if not end_date:
            print("End date must be provided.")
            return pd.DataFrame()

        date_column = "created_at"

        # Query to get existing rows from the target table up to the end date
        existing_rows_query = f"""
            SELECT DISTINCT {date_column} 
            FROM {table_target_name} 
            WHERE {date_column} <= '{end_date}'
        """

        try:
            existing_rows_df = pd.read_sql_query(existing_rows_query, self.engine)
        except Exception as e:
            print(f"Error fetching existing rows: {e}")
            return pd.DataFrame()

        # Convert existing dates to a set for comparison
        existing_dates = (
            set(existing_rows_df[date_column].values)
            if not existing_rows_df.empty
            else set()
        )

        # Query to fetch new rows from the source table up to the end date
        new_rows_query = f"""
            SELECT * 
            FROM {table_source_name} 
            WHERE {date_column} <= '{end_date}'
        """

        try:
            source_rows_df = pd.read_sql_query(new_rows_query, self.engine)
        except Exception as e:
            print(f"Error fetching new rows: {e}")
            return pd.DataFrame()

        # Filter out rows that already exist in the target table
        new_rows_df = source_rows_df[~source_rows_df[date_column].isin(existing_dates)]

        return new_rows_df

    def _fetch_data_from_source(self, table_name: str) -> pd.DataFrame:
        """Helper function to fetch all data from source table."""
        query = f"SELECT * FROM {table_name}"
        return self._fetch_new_rows(query)

    def _fetch_new_rows(self, query: str) -> pd.DataFrame:
        """Helper function to execute a query and fetch new rows."""
        try:
            new_rows_df = pd.read_sql_query(query, self.engine)
            logger.info(f"Fetched {new_rows_df.shape[0]} new rows.")
            return new_rows_df
        except Exception as e:
            logger.error(f"Error fetching new rows: {e}")
            return pd.DataFrame()

    async def insert_new_rows_by_key_id(
        self,
        key_id,
        table_target_name,
        table_source_name,
    ):
        """Insert new rows asynchronously into the target table based on `key_id`."""
        try:
            new_rows_df = self.get_new_rows(
                key_id,
                table_target_name,
                table_source_name,
            )

            if not new_rows_df.empty:
                logger.info(
                    f"Found {new_rows_df.shape[0]} new rows to insert into {table_target_name}",
                )
                await self.insert_data(table_target_name, new_rows_df)

                logger.info(f"New rows inserted into {table_target_name} successfully.")
        except Exception as e:
            logger.error(f"Error inserting new rows into {table_target_name}: {e}")

    # def _format_datetime(self, datetime_str: str) -> str:
    #     """Helper function to format datetime strings."""
    #     try:
    #         return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
    #     except Exception as e:
    #         logger.error(f"Error formatting datetime: {e}")
    #         return datetime_str

    # def insert_new_rows(self, new_rows_df: pd.DataFrame, table_target_name: str):
    #     """Insert the new rows into the target table."""
    #     try:
    #         # Replace NaN with None for SQL compatibility
    #         new_rows_df = new_rows_df.where(pd.notnull(new_rows_df), None)
    #         logger.info(f"Inserting {new_rows_df.shape[0]} rows into {table_target_name}.")

    #         # Use the to_sql method to insert the new rows
    #         new_rows_df.to_sql(table_target_name, self.engine, index=False, if_exists="append", method="multi")

    #         logger.info(f"Data inserted into {table_target_name} successfully.")
    #     except Exception as e:
    #         logger.error(f"Failed to insert data into {table_target_name}: {e}")
    #         logger.error(f"Data attempted to insert: {new_rows_df.head()}")
