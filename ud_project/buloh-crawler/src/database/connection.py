from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
MONGODB_HOST = os.getenv("MONGODB_HOST")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")
MONGODB_TEST_DATABASE = os.getenv("MONGODB_TEST_DATABASE")

# Ensure environment variables are loaded properly
if not all([MONGODB_USERNAME, MONGODB_PASSWORD, MONGODB_HOST, MONGODB_DATABASE]):
    raise ValueError("Some MongoDB environment variables are missing!")

# Setup MongoDB URI, connection timeout is set to 30 seconds
uri = f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}/?authSource=admin&retryWrites=true&w=majority"


class MongoDBClient:
    def __init__(self, test=False):
        self.uri = uri
        self.client = None
        self.test = test

    def __enter__(self):
        try:
            # Establish the MongoDB connection with connection parameters
            self.client = MongoClient(
                self.uri,
                server_api=ServerApi("1"),
                minPoolSize=10,
                maxPoolSize=100,
                maxIdleTimeMS=15000,
                socketTimeoutMS=15000,
                waitQueueTimeoutMS=15000,
                connectTimeoutMS=15000,
            )
            # Ping the server to check the connection
            self.client.admin.command("ping")
            print("Pinged your deployment. You successfully connected to MongoDB!")

            # Select the correct database (test or production)
            if self.test:
                self.db = self.client[str(MONGODB_TEST_DATABASE)]
            else:
                self.db = self.client[str(MONGODB_DATABASE)]

            return self.db
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.close()


# Example usage:
try:
    with MongoDBClient() as db:
        print(f"Connected to database: {db.name}")
        # Perform operations with `db`
except Exception as e:
    print(f"Failed to connect: {e}")


class MySQLConnection:
    def __init__(self):
        self.connection = None

    def connect(self):
        """Establish the connection."""
        try:
            self.connection = mysql.connector.connect(
                port=os.getenv("DB_PORT"),
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
            )
            if self.connection.is_connected():
                print("Connected to the database")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            self.connection = None

    def get_cursor(self):
        """Get a cursor for executing queries."""
        if self.connection:
            return self.connection.cursor(dictionary=True)
        else:
            raise Exception("No active database connection")

    def close_connection(self):
        """Close the database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database connection closed")

    def commit(self):
        """Commit the transaction."""
        if self.connection and self.connection.is_connected():
            self.connection.commit()
            print("Transaction committed")
        else:
            raise Exception("No active database connection to commit")

    # Context Manager Protocol
    def __enter__(self):
        """Enter the context (establish connection)."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the context (close connection)."""
        self.close_connection()
        if exc_type:
            print(f"Exception: {exc_value}")
        return True  # Suppresses the exception if any


def fetch_tags_by_request_id(request_id):
    try:
        with MySQLConnection() as db:  # Using the context manager
            cursor = db.get_cursor()
            query = "SELECT type, value FROM tags WHERE request_id = %s"
            cursor.execute(query, (request_id,))
            results = cursor.fetchall()
            return results
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []


if __name__ == "__main__":
    # Example usage
    request_id = 5  # Replace with your request ID
    tags = fetch_tags_by_request_id(request_id)
    print("Tags:", tags)
