import logging
import os

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#####################  local saving  #####################
log_file_path = "./application.log"
# Delete the log file if it already exists
if os.path.exists(log_file_path):
    os.remove(log_file_path)

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

# #####################  mongodb saving  #####################
# # Create a MongoDB client
# client = MongoClient("mongodb://localhost:27017/")

# # Create a database and collection
# db = client["log_database"]
# collection = db["log_collection"]


# # Define a custom logging handler to store logs in MongoDB
# class MongoDBHandler(logging.Handler):
#     def emit(self, record):
#         log_data = {
#             "timestamp": record.created,
#             "level": record.levelname,
#             "message": record.getMessage(),
#             "module": record.module,
#             "funcName": record.funcName,
#             "lineno": record.lineno,
#         }
#         collection.insert_one(log_data)


# # Add the MongoDB handler to the logger
# mongodb_handler = MongoDBHandler()
# logger.addHandler(mongodb_handler)

# # Define a formatter for the logger
# formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# mongodb_handler.setFormatter(formatter)
