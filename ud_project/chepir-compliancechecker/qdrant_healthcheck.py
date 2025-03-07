import os
import sys
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from utils import setup_logging

logger = setup_logging("qdrant_healthcheck")


# Checks if required environment variables are present
def validate_env_variables():
    load_dotenv()
    required_vars = ["QDRANT_HOST", "QDRANT_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("\n❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   • {var}")
        return False
    return True


# Tests connection to Qdrant server and lists collections
def check_qdrant_connection():
    if not validate_env_variables():
        logger.error("Missing required environment variables")
        return False

    qdrant_host = os.getenv("QDRANT_HOST")
    api_key = os.getenv("QDRANT_API_KEY")

    print(f"\nAttempting to connect to Qdrant at: {qdrant_host}")
    print("-" * 62)
    logger.info(f"Attempting to connect to Qdrant at: {qdrant_host}")

    try:
        # Validate URL format
        if not qdrant_host.startswith(("http://", "https://")):
            error_msg = "QDRANT_HOST must start with http:// or https://"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Setup Qdrant client
        client = QdrantClient(url=qdrant_host, api_key=api_key, timeout=10)

        # Get list of collections
        collections = client.get_collections()

        print("\n✅ Successfully connected to Qdrant!")
        logger.info("Successfully connected to Qdrant")

        if collections.collections:
            print("\nFound the following collections:")
            print("-" * 32)
            logger.info(f"Found {len(collections.collections)} collections")

            # Display info for each collection
            for collection in collections.collections:
                print(f"📁 Collection: {collection.name}")
                try:
                    info = client.get_collection(collection.name)
                    collection_info = f"Collection: {collection.name}, Vector size: {info.config.params.vectors.size}, Points count: {info.points_count}"
                    print(f"   • Vector size: {info.config.params.vectors.size}")
                    print(f"   • Points count: {info.points_count}")
                    logger.info(collection_info)
                except Exception as collection_error:
                    error_msg = f"Error getting collection details: {collection_error}"
                    print(f"   • {error_msg}")
                    logger.error(error_msg)
                print("-" * 60)
        else:
            msg = "Connected to Qdrant, but no collections found"
            print(f"\n⚠️  {msg}")
            logger.warning(msg)

        return True

    except ValueError as ve:
        print(f"\n❌ Configuration error: {str(ve)}")
        logger.error(f"Configuration error: {str(ve)}")
        return False
    except ConnectionError as ce:
        print("\n❌ Failed to connect to Qdrant!")
        print(f"Connection error: {str(ce)}")
        logger.error(f"Connection error: {str(ce)}")
        return False
    except Exception as e:
        print("\n❌ Unexpected error occurred!")
        print(f"Error details: {str(e)}")
        logger.error(f"Unexpected error: {str(e)}")
        return False


if __name__ == "__main__":
    try:
        success = check_qdrant_connection()
        logger.info(f"Health check completed. Success: {success}")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        msg = "Operation cancelled by user"
        print(f"\n\n{msg}")
        logger.warning(msg)
        sys.exit(1)
