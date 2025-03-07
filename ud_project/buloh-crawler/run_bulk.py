import tasks
from src.utils import Logger


def clear_file(file_path):
    log = Logger(name="FileClearing")
    """Clears the contents of a file."""
    try:
        with open(file_path, "w") as file:
            file.truncate(0)
        log.info(f"Cleared file: {file_path}")
    except Exception as e:
        log.error(f"Error clearing file {file_path}: {str(e)}")


def process_bulk():
    """Process bulk keywords and usernames."""
    log = Logger(name="TagCrawlerRun")
    try:
        # Read and process keywords
        with open("data/keywords.txt", "r") as keywords:
            for keyword in keywords:
                tasks.keyword_task.delay(keyword.strip())  # Ensure no extra spaces
                log.info(f"Processing keyword: {keyword.strip()}")
        # Clear the keyword file after processing
        clear_file("data/keywords.txt")

        # Read and process usernames
        with open("data/usernames.txt", "r") as usernames:
            for username in usernames:
                tasks.user_task.delay(username.strip())  # Ensure no extra spaces
                log.info(f"Processing username: {username.strip()}")
                break  # Process only the first username
        # Clear the usernames file after processing
        clear_file("data/usernames.txt")

        # tasks.trending_task.delay()

        log.info("Bulk processing completed successfully.")
    except Exception as e:
        log.error(f"Error during bulk processing: {str(e)}")


if __name__ == "__main__":
    log = Logger(name="BulkCrawlerRun")
    log.info("Starting bulk processing...")
    process_bulk()
    log.info("Bulk processing finished.")
