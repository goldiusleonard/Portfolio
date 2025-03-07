
from pymongo import MongoClient
from dotenv import load_dotenv
import urllib.parse
import os

load_dotenv()

# Fetch MongoDB connection details from environment variables
mongo_host = os.getenv("mongo_host", "localhost")
mongo_user = os.getenv("mongo_user")
mongo_password = os.getenv("mongo_password")
mongo_port = os.getenv("mongo_port", "27017")
mongo_db = os.getenv("mongo_db")
mongo_collection_name = os.getenv("mongo_collection_name")

# Validate that mongo_port is a valid integer
try:
    mongo_port = int(mongo_port)  # Try converting the port to an integer
    if mongo_port <= 0:
        raise ValueError("MongoDB port must be a positive integer.")
except ValueError:
    raise ValueError(f"Invalid port number: {mongo_port}. It must be a positive integer.")

# Ensure mongo_user and mongo_password are valid strings
mongo_user = str(mongo_user) if mongo_user else "default_user"
mongo_password = str(mongo_password) if mongo_password else "default_password"

# URL-encode the username and password to handle special characters
mongo_user_encoded = urllib.parse.quote_plus(mongo_user)
mongo_password_encoded = urllib.parse.quote_plus(mongo_password)

# Construct MongoDB connection URI with authentication source (admin)
mongo_uri = f"mongodb://{mongo_user_encoded}:{mongo_password_encoded}@{mongo_host}:{mongo_port}/"
# Try connecting to MongoDB
try:
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    # Check if MongoDB is reachable
    client.admin.command("ping")
    print("MongoDB connection successful!")
except Exception as e:
    print(f"MongoDB connection failed: {e}")