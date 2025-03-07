import logging
from dotenv import load_dotenv

load_dotenv()

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#####################  local saving  #####################
log_file_path = "./application.log"
# # Delete the log file if it already exists
# if os.path.exists(log_file_path):
#     os.remove(log_file_path)
open(log_file_path, 'w').close()  # Clears file without deleting it

# Configure the logger
logger2 = logging.getLogger(__name__)
handler = logging.FileHandler(log_file_path, encoding="utf-8")
handler.setLevel(logging.DEBUG)

# Create a formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

logger2.addHandler(handler)

# Optional: Set logger level
logger2.setLevel(logging.DEBUG)

# Example log messages
logger2.info("This is an info message.")
logger2.debug("This is a debug message.")

#####################  mongodb saving  #####################

# mongo_host=os.getenv("mongo_host", "localhost")
# mongo_user=os.getenv("mongo_user")
# mongo_password=os.getenv("mongo_password")
# mongo_port=os.getenv("mongo_port", "27017")
# mongo_db = os.getenv("mongo_db")
# mongo_collection_name = os.getenv("mongo_collection_name")


# # Validate that mongo_port is a valid integer
# try:
#     mongo_port = int(mongo_port)  # Try converting the port to an integer
#     if mongo_port <= 0:
#         raise ValueError("MongoDB port must be a positive integer.")
# except ValueError:
#     raise ValueError(f"Invalid port number: {mongo_port}. It must be a positive integer.")

# # Ensure mongo_user and mongo_password are valid strings
# mongo_user = str(mongo_user) if mongo_user else "default_user"
# mongo_password = str(mongo_password) if mongo_password else "default_password"

# # URL-encode the username and password to handle special characters
# mongo_user_encoded = urllib.parse.quote_plus(mongo_user)
# mongo_password_encoded = urllib.parse.quote_plus(mongo_password)

# # Create the MongoDB connection URI
# mongo_uri = f"mongodb://{mongo_user_encoded}:{mongo_password_encoded}@{mongo_host}:{mongo_port}/{mongo_db}"

# # Initialize MongoDB client with the URI
# client = MongoClient(mongo_uri)

# # Create a database and collection
# db = client[mongo_db]
# collection = db[mongo_collection_name]


# # Define a custom logging handler to store logs in MongoDB
# class MongoDBHandler(logging.Handler):
#     def emit(self, record):
#         try:
#             log_data = {
#                 "timestamp": record.created,
#                 "level": record.levelname,
#                 "message": record.getMessage(),
#                 "module": record.module,
#                 "funcName": record.funcName,
#                 "lineno": record.lineno,
#             }
#             # Insert log data into the MongoDB collection
#             collection.insert_one(log_data)
#         except Exception as e:
#             print(f"Error logging to MongoDB: {e}")

# # Create and configure the logger
# logger = logging.getLogger("MongoLogger")
# logger.setLevel(logging.DEBUG)  # Set log level to debug or desired level

# # Add the MongoDB handler to the logger
# mongodb_handler = MongoDBHandler()
# logger.addHandler(mongodb_handler)

# # Define a formatter for the logger
# formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# mongodb_handler.setFormatter(formatter)

# # Test the logging functionality
# logger.info("This is an info message")
# logger.error("This is an error message")