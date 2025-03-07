import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import Column, MetaData, Table, create_engine
from sqlalchemy.orm import declarative_base, scoped_session
from sqlalchemy.orm.session import sessionmaker

from log_mongo import logger

load_dotenv()
mysql_database = os.getenv("mysql_database")


class Database:
    def __init__(self, db_url):
        """Initialize the database connection.

        Args:
        db_url (str): The URL of the database.

        """
        self.db_url = db_url
        self.engine = create_engine(db_url)
        self.Base = declarative_base()
        self.metadata = MetaData()
        self.Session = scoped_session(sessionmaker(bind=self.engine))

    def create_table(self, table_name, columns):
        """Create a table in the database.

        Args:
        table_name (str): The name of the table.
        columns (list): A list of column names and data types.

        """
        table = Table(table_name, self.metadata)
        # Add the columns to the table
        for column in columns:
            table.append_column(
                Column(
                    column["name"],
                    column["type"],
                    **{k: v for k, v in column.items() if k not in ["name", "type"]},
                ),
            )

        self.metadata.create_all(self.engine)

    def insert_data(self, table_name, data):
        """Insert data into a table.

        Args:
        table_name (str): The name of the table.
        data (pd.DataFrame): The data to be inserted.

        """
        try:
            data.to_sql(
                table_name,
                self.engine,
                schema=mysql_database,
                index=False,
                if_exists="append",
            )
            logger.info(f"Data inserted into {table_name} successfully.")
        except Exception as e:
            logger.error(f"Failed to insert data into {table_name}: {e!s}")

    def get_data(self, table_name):
        """Retrieve data from a table.

        Args:
        table_name (str): The name of the table.

        Returns:
        pd.DataFrame: The retrieved data.

        """
        try:
            data = pd.read_sql_table(table_name, self.engine, index_col=False)
            logger.info(f"Data retrieved from {table_name} successfully.")
            return data
        except Exception as e:
            logger.error(f"Failed to retrieve data from {table_name}: {e!s}")
            return None
