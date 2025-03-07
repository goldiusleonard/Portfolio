import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the path to the module to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the MongoDBConnection class (update the path as necessary)
from mongodb import MongoDBConnection


class TestMongoDBConnection(unittest.TestCase):
    @patch("mongodb.MongoClient")
    def test_connect_success(self, mock_mongo_client):
        """Test successful MongoDB connection."""
        # Mock the actual connection string used in the code
        connection_string = "mongodb://AdaMongoDB:Admin2025@52.76.210.195:27017"

        # Mock MongoClient behavior
        mock_client_instance = MagicMock()
        mock_mongo_client.return_value = mock_client_instance

        # Instantiate the MongoDBConnection class
        db_connection = MongoDBConnection(connection_string)

        # Call the connect method
        db_connection.connect()

        # Assertions
        mock_mongo_client.assert_called_once_with(
            connection_string
        )  # Match exact usage
        self.assertIsNotNone(db_connection.client)  # Check if client is set

    @patch("mongodb.MongoClient")
    @patch("mongodb.logger")
    def test_connect_failure(self, mock_logger, mock_mongo_client):
        """Test MongoDB connection failure."""
        # Mock connection string
        connection_string = "mongodb://invalid-host:27017/"

        # Make MongoClient raise an exception
        mock_mongo_client.side_effect = Exception("Connection failed")

        # Instantiate the MongoDBConnection class
        db_connection = MongoDBConnection(connection_string)

        # Call the connect method and verify it raises an exception
        with self.assertRaises(Exception) as context:
            db_connection.connect()

        # Assertions
        mock_logger.error.assert_called_once_with(
            "An error occurred while connecting to MongoDB: Connection failed"
        )
        self.assertEqual(str(context.exception), "Connection failed")


if __name__ == "__main__":
    unittest.main()
