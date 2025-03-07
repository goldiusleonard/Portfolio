import pytest
from unittest.mock import patch, MagicMock

from src.utils.mongodb import save_mongodb


@pytest.fixture
def mock_mongo_client():
    with patch("src.utils.mongodb.MongoClient") as MockMongoClient:
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()

        # Set up the mock chain to return a mock collection when we access the database
        MockMongoClient.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        yield mock_client, mock_db, mock_collection


def test_save_mongodb_success(mock_mongo_client):
    # Unpacking mock client and collection
    mock_client, mock_db, mock_collection = mock_mongo_client

    # Input data
    article_list = [
        {"title": "Article 1", "content": "Content of article 1"},
        {"title": "Article 2", "content": "Content of article 2"},
    ]
    topic_dict = {
        "category": "Hate Speech",
        "sub_category": "Royal",
        "topic": "Royal Heritage",
    }
    news_query = "Royal Family deals with Hate Speech"

    # Call the function to test
    save_mongodb(article_list, topic_dict, news_query)

    # Assert the update_one is called correctly (mocked, so no DB hit)
    for article in article_list:
        unique_id = article["article_id"]
        mock_collection.update_one.assert_any_call(
            {"article_id": unique_id}, {"$setOnInsert": article}, upsert=True
        )
