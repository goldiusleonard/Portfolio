"""Database connection module."""

from typing import Generator

import pandas as pd
from logging_section import setup_logging
from schema_mysql import Base
from sqlalchemy import inspect
from sqlalchemy.orm import Session, sessionmaker
from vm_database import create_engine_for_schema

logger = setup_logging()


class MySQLConnection:
    # def __init__(self, schema_name: str = "marketplace_dev"):
    def __init__(self, schema_name: str):
        self.schema_name = schema_name
        self.engine = create_engine_for_schema(schema_name)
        self.Session_Vm = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def get_db_session(self) -> Generator[Session, None, None]:
        """Yield a database session for VM with a dynamically chosen schema."""
        db = self.Session_Vm()
        try:
            yield db
        finally:
            db.close()

    def fetch_table(self, table_name: str) -> pd.DataFrame:
        """Fetch a table from MySQL and load it into a Pandas DataFrame."""
        try:
            logger.info(
                f"Fetching table '{table_name}' from MySQL for schema: {self.schema_name}"
            )
            with next(self.get_db_session()) as db:
                query = f"SELECT * FROM {table_name}"
                df = pd.read_sql(query, con=db.bind)
            logger.info(
                f"{len(df)} rows successfully loaded from table '{table_name}'."
            )
            return df
        except Exception as e:
            logger.error(
                f"An error occurred while fetching data from table '{table_name}': {e!s}"
            )
            raise

    def create_table(self):
        """Create all tables in MySQL for a specific schema."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info(f"Tables created successfully for schema: {self.schema_name}")
        except Exception as e:
            logger.error(f"An error occurred while creating tables: {e!s}")

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database for a specific schema."""
        inspector = inspect(self.engine)
        return table_name in inspector.get_table_names()

    def filter_new_data(self, df, table_name: str, primary_key: str) -> pd.DataFrame:
        """Filter out rows from the DataFrame that already exist in the database table.

        Args:
        - df (pd.DataFrame): The DataFrame to filter.
        - table_name (str): The name of the table to check for existing primary key values.
        - primary_key (str): The primary key column to match.

        Returns: pd.DataFrame: The filtered DataFrame with new data.

        """
        # Fetch existing primary key values from the table
        existing_data = self.fetch_table(table_name)[primary_key]

        # Filter out rows from the DataFrame that already exist in the table
        df_new_data = df[~df[primary_key].isin(existing_data)]

        return df_new_data

    def push_table(
        self,
        table_name: str,
        df: pd.DataFrame,
        primary_key: str,
        if_exists: str = "append",
    ):
        """Appends new rows to an existing table for a specific schema, avoiding duplicates based on the primary key."""
        try:
            # Check if the table exists
            if not self.table_exists(table_name):
                logger.info(
                    f"Table '{table_name}' does not exist. Creating it with the defined schema."
                )
                self.create_table()

            # # Fetch existing primary key values from the table
            # existing_data = self.fetch_table(table_name)[primary_key]
            # # existing_data.to_csv('test.csv')

            # # Filter out rows from the DataFrame that already exist in the table
            # df_new_data = df[~df[primary_key].isin(existing_data)]

            # Filter out rows from the DataFrame that already exist in the table
            df_new_data = self.filter_new_data(df, table_name, primary_key)

            # remove column 'id' if exist because mysql will add it
            if primary_key == "id" or "id" in df_new_data.columns:
                df_new_data.drop(columns="id", inplace=True)

            df_new_data.to_csv("test_1.csv")
            print(df_new_data.columns)

            # Append only the new data to the existing table
            if not df_new_data.empty:
                with next(self.get_db_session()) as db:
                    df_new_data.to_sql(
                        table_name, con=db.bind, if_exists=if_exists, index=False
                    )
                logger.info(f"New data successfully appended to {table_name}.")
            else:
                logger.info("No new data to append.")

            # Return True if there were no errors during the process
            return True

        except Exception as e:
            logger.error(f"An error occurred while pushing data to {table_name}: {e!s}")
            return False

    def is_table_populated(self, table_name: str, required_ids: list) -> bool:
        """Check if the SQL table has all the required IDs and their descriptions populated.
        If all required IDs are found with descriptions, it returns True; otherwise, it returns False
        """
        try:
            # query = (
            #     f"SELECT _id "
            #     f"FROM {table_name} "
            #     f"WHERE _id IN ({', '.join(map(lambda x: f'\"{x}\"', required_ids))}) "
            #     f"AND COALESCE(video_description, '') != ''"
            #     )

            ids = ", ".join(
                f'"{x}"' for x in required_ids
            )  # Prepare the list of IDs as a string
            query = (
                f"SELECT _id "
                f"FROM {table_name} "
                f"WHERE _id IN ({ids}) "
                f"AND COALESCE(video_description, '') != '' "
            )

            with next(self.get_db_session()) as db:
                result = pd.read_sql(query, con=db.bind)
                fetched_ids = result["_id"].tolist()

                # Check if fetched_ids(video_captions) contain every ID present in required_ids(mongo video id)
                return set(fetched_ids).issuperset(set(required_ids))
                ## for debug
                # return True

        except Exception as e:
            logger.error(f"Error checking table '{table_name}': {e}")
            raise


# # Initialize the database object for a specific schema
# db = MySQLConnection(schema_name="marketplace_dev")

# # Fetch data from a table
# df = db.fetch_table("replies")
# print(df)

# # Check if a table exists
# table_exists = db.table_exists("reply")
# print(f"Table exists: {table_exists}")


# # Create tables
# db.create_table()

# # Push new data to the table
# db.push_table("test12345", df, primary_key="id")
