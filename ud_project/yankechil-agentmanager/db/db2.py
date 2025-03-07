import sys

sys.stdout.reconfigure(encoding="utf-8")
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from log_mongo import logger

# Reconfigure stdout for UTF-8
sys.stdout.reconfigure(encoding="utf-8")

# Load environment variables
load_dotenv()

# Database URL configuration
mysql_database = os.getenv("mysql_database")
if not mysql_database:
    logger.error("mysql_database not found")


# class Database:
#     def __init__(self, db_url: str, output_schemas: list, input_schemas:list=None):
class Database:
    def __init__(
        self,
        engine,
        session,
        output_schemas: list,
        input_schemas: list = None,
    ):
        self.engine = engine

        self.session = session

        # Store schema classes for reference
        self.input_schemas = input_schemas
        self.output_schemas = output_schemas

    def get_session(self):
        return self.session

    def get_engine(self):
        return self.engine

    def get_input_schemas(self):
        return self.input_schemas

    def get_output_schemas(self):
        return self.output_schemas

    async def close(self):
        import asyncio

        if asyncio.get_event_loop().is_running():
            try:
                await self.session.close()
                async with self.engine.connect() as conn:
                    # Do something with the connection...
                    await conn.close()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
        else:
            logger.warning(
                "The event loop is already closed. Cannot perform async close.",
            )

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

    async def get_data_from_table(self, table_source_name: str) -> pd.DataFrame:
        """Get data from the source table if it exists."""
        logger.info(f"Checking if the source table '{table_source_name}' exists.")

        # Step 1: Check if the table exists
        # inspector = Inspector.from_engine(self.engine)
        # table_names = inspector.get_table_names()
        inspector = inspect(self.engine)
        table_names = inspector.get_table_names()
        if table_source_name not in table_names:
            logger.warning(f"Table '{table_source_name}' does not exist.")
            return (
                pd.DataFrame()
            )  # Return an empty DataFrame if the table doesn't exist

        # Step 2: Fetch the data from the table
        try:
            logger.info(f"Fetching data from the source table: {table_source_name}")
            df = await self._fetch_data_from_source(table_source_name)

            if df.empty:
                logger.warning(f"Table '{table_source_name}' is empty.")
            return df

        except Exception as e:
            logger.error(
                f"An error occurred while fetching data from '{table_source_name}': {e}"
            )
            return pd.DataFrame()  # Return an empty DataFrame in case of error

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
            # raise

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
            # raise

        except Exception as e:
            # Handle other exceptions
            self.session.rollback()  # Ensure session consistency by rolling back
            logger.error(f"Failed to insert row {i}: {e}")
            # raise

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

    async def _fetch_data_from_source(self, table_name: str) -> pd.DataFrame:
        """Helper function to fetch all data from source table asynchronously."""
        try:
            query = f"SELECT * FROM {table_name}"

            # Record the start time for performance logging
            start_time = pd.Timestamp.now()

            # Use async connection to execute the query
            async with self.engine.connect() as conn:
                result = await conn.execute(query)
                rows = await result.fetchall()

                if not rows:
                    logger.warning(f"No data found in table '{table_name}'.")

                # Convert to DataFrame and return
                new_rows_df = pd.DataFrame(
                    rows,
                    columns=[column[0] for column in result.keys()],
                )

            elapsed_time = pd.Timestamp.now() - start_time
            logger.info(
                f"Fetched {new_rows_df.shape[0]} rows from '{table_name}' in {elapsed_time}."
            )
            return new_rows_df
        except Exception as e:
            logger.error(f"Error fetching new rows from '{table_name}': {e}")
            return pd.DataFrame()  # Return an empty DataFrame in case of error

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
