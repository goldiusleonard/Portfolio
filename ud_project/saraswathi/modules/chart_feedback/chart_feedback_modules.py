import os

from pymongo import MongoClient
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()


def collection_exists(db, collection_name):
    """
    Check if a collection exists in the specified MongoDB database.

    :param db: The MongoDB database instance.
    :param collection_name: The name of the collection to check.
    :return: True if the collection exists, otherwise False.
    """
    return collection_name in db.list_collection_names()


def setup_modules():
    """
    Set up the MongoDB collection and environment variables with predefined modules.
    Connects to MongoDB, checks if the module collection exists, inserts modules if
    the collection is empty, and updates the environment file with module variables.

    :return: None
    """
    client = MongoClient(os.getenv("MONGODB_URL"))
    qdrant_client = QdrantClient(
        url=os.getenv("QDRANT_HOST"), api_key=os.getenv("QDRANT_API_KEY")
    )

    db_name = os.getenv("FEEDBACK_MONGODB_DATABASE")
    collection_name = os.getenv("FEEDBACK_MONGODB_COLLECTION")

    db = client[db_name]

    if not collection_exists(db, collection_name):
        print(f"{collection_name} collection does not exist. Creating the collection.")
        db.create_collection(collection_name)

    qdrant_user_query_collection_name = os.getenv(
        "FEEDBACK_QDRANT_USER_QUERY_COLLECTION"
    )

    if not qdrant_client.collection_exists(qdrant_user_query_collection_name):
        qdrant_client.create_collection(
            collection_name=qdrant_user_query_collection_name,
            vectors_config={"size": 768, "distance": "Cosine"},
            hnsw_config={
                "m": 100,
                "ef_construct": 800,
                "full_scan_threshold": 20000,
            },
        )

    qdrant_question_collection_name = os.getenv("FEEDBACK_QDRANT_QUESTION_COLLECTION")

    if not qdrant_client.collection_exists(qdrant_question_collection_name):
        qdrant_client.create_collection(
            collection_name=qdrant_question_collection_name,
            vectors_config={"size": 768, "distance": "Cosine"},
            hnsw_config={
                "m": 100,
                "ef_construct": 800,
                "full_scan_threshold": 20000,
            },
        )

    client.close()
