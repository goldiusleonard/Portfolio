import os
from pymongo import MongoClient


def collection_exists(db, collection_name):
    """
    Check if a collection exists in the specified MongoDB database.

    :param db: The MongoDB database instance.
    :param collection_name: The name of the collection to check.
    :return: True if the collection exists, otherwise False.
    """
    return collection_name in db.list_collection_names()


def read_module_ids_from_env():
    """
    Reads module IDs from the .env file and returns them as a list of dictionaries.

    :return: A list of dictionaries with module names and their respective IDs.
    """
    env_file_path = os.getenv("ENV_FILE_PATH", ".env")
    modules = []

    with open(env_file_path, "r") as file:
        lines = file.readlines()

    for line in lines:
        if line.startswith("MODULEID_"):
            key, value = line.strip().split("=")
            module_name = key.replace("MODULEID_", "").lower()
            module_id = int(value)
            modules.append({"module_name": module_name, "module_id": module_id})

    return modules


def insert_modules_into_mongo(db, modules, collection_name):
    """
    Insert modules into MongoDB collection if they are not already present.

    :param db: The MongoDB database instance.
    :param modules: A list of dictionaries containing 'module_name' and 'module_id'.
    :param collection_name: The name of the MongoDB collection.
    :return: None
    """
    collection = db[collection_name]
    for module in modules:
        if collection.count_documents({"module_id": module["module_id"]}) == 0:
            collection.insert_one(module)
            print(
                f"Inserted module {module['module_name']} into '{collection_name}' collection."
            )


def setup_modules():
    """
    Reads module information from the .env file, connects to MongoDB, checks if
    the module collection exists, and inserts modules if necessary.

    :return: None
    """
    try:
        modules = read_module_ids_from_env()

        client = MongoClient(os.getenv("MONGODB_URL"))
        db_name = os.getenv("CHART_LLM_CALL_MODULE_MONGODB_DATABASE")
        collection_name = os.getenv("CHART_LLM_CALL_MODULE_MONGODB_COLLECTION")
        db = client[db_name]

        if not collection_exists(db, collection_name):
            print(
                f"{collection_name} collection does not exist. Creating and inserting modules."
            )
        insert_modules_into_mongo(db, modules, collection_name)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        client.close()
