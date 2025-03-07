import json
import requests
import ast
import traceback
import os

from fastapi.responses import JSONResponse
from fastapi import Body
from fastapi import Response, APIRouter
from pathlib import Path
from qdrant_client import QdrantClient
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

router = APIRouter()

# MongoDB
mongodb_url: str = os.getenv("MONGODB_URL", "")

if mongodb_url == "":
    raise ValueError("MongoDB URL is not valid!")

feedback_mongodb_database: str = os.getenv("FEEDBACK_MONGODB_DATABASE", "")

if feedback_mongodb_database == "":
    raise ValueError("Feedback MongoDB database is not valid!")

feedback_mongodb_collection: str = os.getenv("FEEDBACK_MONGODB_COLLECTION", "")

if feedback_mongodb_collection == "":
    raise ValueError("Feedback MongoDB collection is not valid!")

chart_logging_mongodb_database: str = os.getenv("CHART_LOGGING_MONGODB_DATABASE", "")

if chart_logging_mongodb_database == "":
    raise ValueError("Chart logging MongoDB database is not valid!")

chart_logging_mongodb_collection: str = os.getenv(
    "CHART_LOGGING_MONGODB_COLLECTION", ""
)

if chart_logging_mongodb_collection == "":
    raise ValueError("Chart logging MongoDB collection is not valid!")

# Embedding Model
embedding_url: str = os.getenv("EMBEDDING_BASE_URL", "")

if embedding_url == "":
    raise ValueError("Embedding URL is not valid!")

# QDrant
qdrant_host: str = os.getenv("QDRANT_HOST", "")
qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")

if qdrant_host == "":
    raise ValueError("Qdrant host is not valid!")

if qdrant_api_key == "":
    raise ValueError("Qdrant api key is not valid!")

# Initialize feedback form template path
feedback_form_file_path: str = str(Path(__file__).parent / "feedback_template.json")


def load_feedback_template():
    # Loading the Feedback Json Template
    # Open the JSON file and load its content into a dictionary
    with open(feedback_form_file_path, "r") as file:
        feedback_template = json.load(file)

    return feedback_template


def _get_feedback(chart_id: str):
    # Connect to MongoDB server
    mongo_db_client = MongoClient(mongodb_url)
    try:
        # OPEN Connection : Access a specific database
        feedback_mongo_db = mongo_db_client[feedback_mongodb_database]

        # Access a specific collection within the database
        if feedback_mongodb_collection not in feedback_mongo_db.list_collection_names():
            feedback_form = load_feedback_template()
            feedback_mongo_db.create_collection(feedback_mongodb_collection)
        else:
            feedback_mongo_db = mongo_db_client[feedback_mongodb_database]
            collection = feedback_mongo_db[feedback_mongodb_collection]

            # Find the the feedback using the chart_id from FE
            document = collection.find_one({"chart_id": chart_id})

            if document is None:
                feedback_form = load_feedback_template()
            elif document == {}:
                feedback_form = load_feedback_template()
            else:
                feedback_form = document
                # Removed '_id'
                feedback_form.pop("_id")

        return feedback_form

    except Exception as e:
        print("\n=================================================")
        print(f"Feedback Retrieval Error {e}")
        print(traceback.format_exc())
        print("=================================================\n")

    # Close the connection
    mongo_db_client.close()


def _save_feedback(chart_feedback: dict) -> None:
    # Connect to MongoDB server
    mongo_db_client = MongoClient(mongodb_url)

    # OPEN Connection : Access a specific database in MONGODB
    feedback_mongo_db = mongo_db_client[feedback_mongodb_database]
    chart_logging_mongo_db = mongo_db_client[chart_logging_mongodb_database]

    # OPEN Connection : QDrant
    qdrant_db_client = QdrantClient(url=qdrant_host, api_key=qdrant_api_key)

    try:
        if feedback_mongodb_collection not in feedback_mongo_db.list_collection_names():
            feedback_mongo_db.create_collection(feedback_mongodb_collection)

        # Access the collection within the database
        chart_feedback_collection = feedback_mongo_db[feedback_mongodb_collection]

        # TO THE MONGO DB
        chart_id = chart_feedback["chart_id"]
        like = str(chart_feedback["like"]).capitalize()
        feedback = chart_feedback["feedback"]

        # Upsert the feedback in MongoDB
        chart_feedback_collection.update_one(
            {"chart_id": chart_id},
            {"$set": {"chart_id": chart_id, "like": like, "feedback": feedback}},
            upsert=True,
        )

    except Exception as e:
        print("\n=================================================")
        print(f"Feedback Save Error: MongoDB Upsertion Error {e}")
        print(traceback.format_exc())
        print("=================================================\n")

    # FROM THE MONGODB
    try:
        # Query MongoDB for user query and question
        chart_collection = chart_logging_mongo_db[chart_logging_mongodb_collection]
        result = chart_collection.find_one(
            {"chart_id": chart_id}, {"user_query": 1, "question": 1, "_id": 0}
        )
    except Exception as e:
        print("\n=================================================")
        print(f"Feedback Save Error: MongoDB Chart Retrieval Error {e}")
        print(traceback.format_exc())
        print("=================================================\n")

    # TO THE QDRANT
    # Embed the user query and question
    user_query = result.get("user_query")
    question = result.get("question")

    embed_user_query = requests.get(
        embedding_url,
        params={"promt": user_query, "model_name": os.getenv("EMBEDDING_MODEL_NAME")},
        verify=False,
    )

    embedded_user_query = ast.literal_eval(embed_user_query.content.decode("utf-8"))

    embed_question = requests.get(
        embedding_url,
        params={"promt": question, "model_name": os.getenv("EMBEDDING_MODEL_NAME")},
        verify=False,
    )
    embedded_question = ast.literal_eval(embed_question.content.decode("utf-8"))

    # Define payload
    payload = {"chart_id": chart_id}

    # Define Qdrant collection names
    qdrant_user_query_collection = os.getenv("FEEDBACK_QDRANT_USER_QUERY_COLLECTION")
    qdrant_question_collection = os.getenv("FEEDBACK_QDRANT_QUESTION_COLLECTION")

    try:
        # Ensure Qdrant collections exist
        if not qdrant_db_client.collection_exists(qdrant_user_query_collection):
            qdrant_db_client.create_collection(
                collection_name=qdrant_user_query_collection,
                vectors_config={"size": 768, "distance": "Cosine"},
                hnsw_config={
                    "m": 100,
                    "ef_construct": 800,
                    "full_scan_threshold": 20000,
                },
            )
        if not qdrant_db_client.collection_exists(qdrant_question_collection):
            qdrant_db_client.create_collection(
                collection_name=qdrant_question_collection,
                vectors_config={"size": 768, "distance": "Cosine"},
                hnsw_config={
                    "m": 100,
                    "ef_construct": 800,
                    "full_scan_threshold": 20000,
                },
            )

        # Delete existing entries in Qdrant for the given chart_id
        qdrant_db_client.delete(qdrant_user_query_collection, [chart_id])
        qdrant_db_client.delete(qdrant_question_collection, [chart_id])

        # Upsert vectors in Qdrant
        qdrant_db_client.upsert(
            collection_name=qdrant_user_query_collection,
            points=[
                {
                    "id": chart_id,
                    "vector": embedded_user_query,
                    "payload": payload,
                }
            ],
        )
        qdrant_db_client.upsert(
            collection_name=qdrant_question_collection,
            points=[
                {
                    "id": chart_id,
                    "vector": embedded_question,
                    "payload": payload,
                }
            ],
        )

    except Exception as e:
        print("\n=================================================")
        print(f"Feedback Save Error: QDrant Upsertion Error {e}")
        print(traceback.format_exc())
        print("=================================================\n")

    # Close connections
    mongo_db_client.close()
    qdrant_db_client.close()


################## FINDING TOP N ####################


# Function to rearrange the dictionary
def process_chart(input_dict: dict):
    # Create a new dictionary based on the desired structure
    output_dict = {"feedback": input_dict["feedback"]}

    # Add 'like' under 'feedback' and convert the boolean to string
    output_dict["feedback"]["like"] = str(input_dict["like"])

    # Keys to remove
    keys_to_remove = ["chart_id", "user_id", "session_id"]

    # Remove the keys
    for key in keys_to_remove:
        output_dict.pop(key, None)

    output_dict["request_time"] = datetime.now()
    output_dict["last_updated"] = datetime.now()

    for key in output_dict:
        if isinstance(output_dict[key], datetime):
            output_dict[key] = output_dict[key].isoformat()

    return output_dict


# Get the charts from the DB
def get_chart_feedback_mongodb(chart_id: str):
    # Connect to MongoDB server
    mongo_db_client = MongoClient(mongodb_url)

    # OPEN Connection : Access a specific database in MONGODB
    feedback_mongo_db = mongo_db_client[feedback_mongodb_database]
    chart_logging_mongo_db = mongo_db_client[chart_logging_mongodb_database]

    # Query chart feedback MongoDB collection for user query
    # check if collection exists
    if feedback_mongodb_collection not in feedback_mongo_db.list_collection_names():
        print(f"Mongo DB collection, {feedback_mongodb_collection} not found")
    else:
        chart_feedback_collection = feedback_mongo_db[feedback_mongodb_collection]
        chart_feedback_result = chart_feedback_collection.find_one(
            {"chart_id": chart_id}, {"_id": 0}
        )

        if chart_feedback_result:
            # preprocess the result
            processed_chart_feedback_result = process_chart(chart_feedback_result)

    # Query chart MongoDB for whole chart
    # check if collection exists
    if (
        chart_logging_mongodb_collection
        not in chart_logging_mongo_db.list_collection_names()
    ):
        print(f"Mongo DB collection, {chart_logging_mongodb_collection} not found")
    else:
        chart_mongodb_collection = chart_logging_mongo_db[
            chart_logging_mongodb_collection
        ]
        chart_result = chart_mongodb_collection.find_one(
            {"chart_id": chart_id}, {"_id": 0}
        )

    # making the results one
    final_processed_chart = {**chart_result, **processed_chart_feedback_result}

    mongo_db_client.close()
    return final_processed_chart


def search_user_query(user_query: str, top_n: int = 10):
    # OPEN Connection : QDrant
    qdrant_db_client = QdrantClient(url=qdrant_host, api_key=qdrant_api_key)

    qdrant_user_query_collection = os.getenv("FEEDBACK_QDRANT_USER_QUERY_COLLECTION")

    # embed the user_query
    embed_user_query = requests.get(
        embedding_url,
        params={"promt": user_query, "model_name": os.getenv("EMBEDDING_MODEL_NAME")},
        verify=False,
    )
    embedded_user_query = ast.literal_eval(embed_user_query.content.decode("utf-8"))

    # to gather all the results in a list
    qdrant_query_result_list = []

    try:
        # Check if the collection exists
        if not qdrant_db_client.collection_exists(qdrant_user_query_collection):
            print(f"Qdrant Collection '{qdrant_user_query_collection}' not found")
        else:
            # Query the Qdrant collection
            qdrant_user_query_results = qdrant_db_client.search(
                collection_name=qdrant_user_query_collection,
                query_vector=embedded_user_query,
                limit=top_n,  # maximum results we want
            )

            for item in qdrant_user_query_results:
                qdrant_query_result_list.append(item.payload)

    except Exception as e:
        print("\n=================================================")
        print(f"User Query Search: Qdrant querying error {e}")
        print(traceback.format_exc())
        print("=================================================\n")

    # querying the mongo db to get the chart
    try:
        chart_feedback_list = []
        # check if results from qdrant are empty
        for result in qdrant_query_result_list:
            # get the chart ids from the list
            mongo_db_chart_id = result["chart_id"]

            # If chart data is not found, skip the chart
            try:
                final_processed_chart_data = get_chart_feedback_mongodb(
                    mongo_db_chart_id
                )
            except Exception:
                continue

            final_processed_chart = json.dumps(final_processed_chart_data)
            chart_feedback_list.append(final_processed_chart)

        return chart_feedback_list

    except Exception as e:
        print("\n=================================================")
        print(f"User Query Search: Qdrant querying error {e}")
        print(traceback.format_exc())
        print("=================================================\n")

    # Close connections
    qdrant_db_client.close()


def search_question(question: str, top_n: int = 10):
    # OPEN Connection : QDrant
    qdrant_db_client = QdrantClient(url=qdrant_host, api_key=qdrant_api_key)

    qdrant_question_collection = os.getenv("FEEDBACK_QDRANT_QUESTION_COLLECTION")

    # embed the question
    embed_question = requests.get(
        embedding_url,
        params={"promt": question, "model_name": os.getenv("EMBEDDING_MODEL_NAME")},
        verify=False,
    )
    embedded_question = ast.literal_eval(embed_question.content.decode("utf-8"))

    # to gather all the results in a list
    qdrant_question_list = []

    try:
        # Check if the collection exists
        if not qdrant_db_client.collection_exists(qdrant_question_collection):
            print(f"Qdrant Collection '{qdrant_question_collection}' not found")
        else:
            # Query the Qdrant collection
            qdrant_question_results = qdrant_db_client.search(
                collection_name=qdrant_question_collection,
                query_vector=embedded_question,
                limit=top_n,  # maximum results we want
            )

            for item in qdrant_question_results:
                qdrant_question_list.append(item.payload)

    except Exception as e:
        print("\n=================================================")
        print(f"Question Search: Qdrant querying error {e}")
        print(traceback.format_exc())
        print("=================================================\n")

    # querying the mongo db to get the chart
    try:
        chart_feedback_list = []
        # check if results from qdrant are empty
        for result in qdrant_question_list:
            # get the chart ids from the list
            mongo_db_chart_id = result["chart_id"]

            # If chart data is not found, skip the chart
            try:
                final_processed_chart_data = get_chart_feedback_mongodb(
                    mongo_db_chart_id
                )
            except Exception:
                continue

            final_processed_chart = json.dumps(final_processed_chart_data)
            chart_feedback_list.append(final_processed_chart)

        return chart_feedback_list

    except Exception as e:
        print("\n=================================================")
        print(f"Question Search: Qdrant querying error {e}")
        print(traceback.format_exc())
        print("=================================================\n")

    # Close connections
    qdrant_db_client.close()


############################################### FAST API ROUTING ##########################################


@router.put("/save")
def save_feedback(chart_feedback: dict = Body(...)):
    save_status = "Feedback successfully saved in DB."
    try:
        _save_feedback(chart_feedback)
    except Exception as e:
        print("\n=================================================")
        print(f"Main: Save Feedback Error {e}")
        print(traceback.format_exc())
        print("=================================================\n")
        save_status = "Feedback not successfully saved in DB."

    return Response(
        content=save_status,
        status_code=200,
    )


@router.get("/search/user_query/{user_query}")
def feedback_user_query(user_query: str, top_n: int = 10):
    try:
        results = search_user_query(user_query, top_n)
        if results is None:
            # Return a 404 status if no feedback form is found
            return JSONResponse(
                content={"error": "No Queries found"},
                status_code=404,
            )

    except Exception as e:
        print("\n=================================================")
        print(f"Main: Search User Query Error {e}")
        print(traceback.format_exc())
        print("=================================================\n")

    return JSONResponse(content={"results": results}, status_code=200)


@router.get("/search/question/{question}")
def feedback_question(question: str, top_n: int = 10):
    try:
        results = search_question(question, top_n)
        if results is None:
            # Return a 404 status if no feedback form is found
            return JSONResponse(
                content={"error": "No Questions found"},
                status_code=404,
            )

    except Exception as e:
        print("\n=================================================")
        print(f"Main: Search Question Error {e}")
        print(traceback.format_exc())
        print("=================================================\n")

    return JSONResponse(content={"results": results}, status_code=200)


@router.get("/chart_id/{chart_id}")
def get_feedback(chart_id: str):
    try:
        feedback_form = _get_feedback(chart_id)

        if feedback_form is None:
            # Return a 404 status if no feedback form is found
            return JSONResponse(
                content={"error": "No Feedback Form found"},
                status_code=404,
            )
    except Exception as e:
        print("\n=================================================")
        print(f"Main: Retrieve Feedback Error {e}")
        print(traceback.format_exc())
        print("=================================================\n")
        # Return a 500 status for unexpected errors
        return JSONResponse(
            content={"error": "An error occurred while retrieving feedback"},
            status_code=500,
        )

    # Return the feedback form content if found
    return JSONResponse(
        content=feedback_form,
        status_code=200,
    )
