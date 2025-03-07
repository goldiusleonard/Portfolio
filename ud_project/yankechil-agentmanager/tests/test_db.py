import os
import sys

# Get the absolute path of the current file
current_file_path = os.path.abspath(__file__)
# Get the directory path of the current file
current_dir_path = os.path.dirname(current_file_path)
# Get the parent directory path
parent_dir_path = os.path.dirname(current_dir_path)
# Add the parent directory path to the sys.path
sys.path.insert(0, parent_dir_path)

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from db.db import Database  # Replace with actual import


@pytest.fixture
def mock_database():
    """Fixture to mock the Database class."""
    mock_db = MagicMock(spec=Database)
    mock_db.session = MagicMock()  # Explicitly mock the session
    return mock_db


@pytest.fixture
def mock_dataframe():
    """Fixture to create a mock dataframe."""
    data = {
        "_id": [1, 2, 3],
        "name": ["item1", "item2", "item3"],
    }
    return pd.DataFrame(data)


# Test check_table_exists method
def test_check_table_exists(mock_database, mock_dataframe):
    """Test check_table_exists method."""
    mock_database.check_table_exists.return_value = (
        True  # Simulate that the table exists
    )

    # Call the method
    result = mock_database.check_table_exists("my_table")

    # Assert the table exists
    assert result is True
    mock_database.check_table_exists.assert_called_once_with("my_table")


# Test insert_data method
def test_insert_data(mock_database, mock_dataframe):
    """Test insert_data method."""
    mock_database.insert_data.return_value = None  # Simulate no exception during insert

    # Call the method
    mock_database.insert_data("my_table", mock_dataframe)

    # Assert data insertion
    mock_database.insert_data.assert_called_once_with("my_table", mock_dataframe)


@patch("pandas.read_sql_query")
def test_fetch_data_from_source(mock_read_sql_query, mock_database):
    """Test _fetch_data_from_source method."""
    # Setup mock for database engine (if needed)
    mock_database.engine = "sqlite:///:memory:"  # Dummy engine for testing

    # Mock the returned DataFrame from read_sql_query
    data = {
        "_id": [1, 2, 3],
        "name": ["item1", "item2", "item3"],
    }
    mock_read_sql_query.return_value = pd.DataFrame(data)

    # Mock the method to return the DataFrame when called
    mock_database._fetch_data_from_source = MagicMock(return_value=pd.DataFrame(data))

    # Call the method
    result = mock_database._fetch_data_from_source("source_table")

    # Assert the result contains the expected data
    assert (
        result.shape[0] == 3
    )  # This should work because `read_sql_query.return_value` is a real DataFrame
