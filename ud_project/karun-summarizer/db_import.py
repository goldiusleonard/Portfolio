import os
import time

import mysql.connector
import pandas as pd
from dotenv import load_dotenv


# Establish MySQL database connection
def connect_to_db():
    load_dotenv()
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        database=os.getenv("MYSQL_DATABASE"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        connect_timeout=30,
    )


# Import video summaries from CSV to MySQL database
def import_summaries_to_db(csv_file: str):
    df = pd.read_csv(csv_file).fillna("")
    print(f"Found {len(df)} summaries to import")

    max_retries = 3
    for attempt in range(max_retries):
        try:
            conn = connect_to_db()
            cursor = conn.cursor(buffered=True)

            # Create table (if not exists)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS video_summary (
                    _id VARCHAR(255) PRIMARY KEY,
                    video_summary TEXT
                )
            """,
            )

            # Insert/update records
            success_count = 0
            for _, row in df.iterrows():
                if row["_id"] and row["video_summary"]:
                    cursor.execute(
                        "INSERT INTO video_summary (_id, video_summary) VALUES (%s, %s) "
                        "ON DUPLICATE KEY UPDATE video_summary = VALUES(video_summary)",
                        (row["_id"], row["video_summary"]),
                    )
                    success_count += 1

            conn.commit()
            print(f"Successfully imported {success_count} summaries to database")
            break

        # Retry on connection errors
        except mysql.connector.Error as e:
            print(f"Connection attempt {attempt + 1} failed: {e!s}")
            if attempt < max_retries - 1:
                print("Retrying in 5 seconds...")
                time.sleep(5)
            else:
                print("Max retries reached. Could not connect to database.")
                raise
        finally:
            if "cursor" in locals():
                cursor.close()
            if "conn" in locals() and conn.is_connected():
                conn.close()


if __name__ == "__main__":
    csv_file = "data/video_summary.csv"
    if os.path.exists(csv_file):
        import_summaries_to_db(csv_file)
    else:
        print(f"Error: File not found - {csv_file}")
