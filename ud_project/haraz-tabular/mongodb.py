import os
import pandas as pd
from dotenv import load_dotenv
from logging_section import setup_logging
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# Set up logging
logger = setup_logging()

# DEFINE THE DATABASE CREDENTIALS (this will be inside the class now)
connection_string = os.getenv("MONGODB_CONNECTION_STRING")


class MongoDBConnection:
    def __init__(self, database_name):
        """Initialize the MongoDBConnection and retrieve connection string from environment."""
        self.connection_string = connection_string
        self.db_name = database_name
        self.client = None
        self.db = None

    def connect(self):
        """Connect to the MongoDB database."""
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.db_name]  # Access the database object
            logger.info(f"Connected to MongoDB database: {self.db_name}")
        except Exception as e:
            logger.error(f"An error occurred while connecting to MongoDB: {e}")
            raise

    def load_mongo_collections(self, collections: list):
        """Load specified MongoDB collections and return each as a Pandas DataFrame in a dictionary.
        Args: collections (list): A list of MongoDB collection names to fetch.
        Returns: dict: A dictionary where keys are collection names, and values are DataFrames containing the collection data.
        """
        if self.db is None:  # Ensure connection is established
            self.connect()

        data = {}
        for collection_name in collections:
            try:
                logger.info(f"Loading '{collection_name}' collection from MongoDB...")
                collection = self.db[collection_name]
                records = list(collection.find())  # Retrieve all records
                logger.info(
                    f"Fetched {len(records)} records from collection: {collection_name}"
                )
                data[collection_name] = pd.DataFrame(records)
            except Exception as e:
                logger.error(f"Error loading collection '{collection_name}': {e}")
        return data

    def close(self):
        if self.client:
            self.client.close()
