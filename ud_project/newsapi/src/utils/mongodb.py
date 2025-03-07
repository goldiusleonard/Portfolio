import os
import uuid
import traceback
from pymongo import MongoClient

# MongoDB
mongodb_url: str = os.getenv("MONGODB_URL", "")
if mongodb_url == "":
    raise ValueError("MongoDB URL is not valid!")


newsapi_mongodb_database: str = os.getenv("NEWSAPI_MONGODB_DATABASE", "")
if newsapi_mongodb_database == "":
    raise ValueError("NewsAPI MongoDB database is not valid!")


newsapi_mongodb_collection: str = os.getenv("NEWSAPI_MONGODB_COLLECTION", "")
if newsapi_mongodb_collection == "":
    raise ValueError("NewsAPI MongoDB collection is not valid!")


def save_mongodb(article_list, topic_dict, news_query):
    # MongoDB connection
    client = MongoClient(mongodb_url)

    mongodb = client[newsapi_mongodb_database]  # Replace with your database name

    mongodb_collection = mongodb[newsapi_mongodb_collection]
    try:
        for article in article_list:
            unique_id = str(uuid.uuid4())

            article["article_id"] = unique_id
            article["category"] = topic_dict["category"]
            article["sub_category"] = topic_dict["sub_category"]
            article["topic"] = topic_dict["topic"]
            article["expanded_query"] = news_query

            # Insert only if the document with the same 'id' does not exist
            _ = mongodb_collection.update_one(
                {"article_id": unique_id},  # Filter to check existence
                {
                    "$setOnInsert": article  # Only set fields when inserting (no update if exists)
                },
                upsert=True,
            )

    except Exception as e:
        print("\n=================================================")
        print(f" News Article Save Error: MongoDB Save Error {e}")
        print(traceback.format_exc())
        print("=================================================\n")

    client.close()
