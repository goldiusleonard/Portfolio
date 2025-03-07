import os
import subprocess
import pymysql
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from dotenv import load_dotenv
from datetime import datetime, time

load_dotenv()


# Database connection function
def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor,
    )


# Function to fetch crawl data from DB and schedule the task
def schedule_crawling(request_id, from_date, to_date, limit=2):
    try:
        connection = get_db_connection()
        # Initialize the scheduler
        scheduler = BackgroundScheduler()

        # Fetch `fromDate` and `toDate` from the database
        with connection.cursor() as cursor:
            sql_dates = "SELECT from_date, to_date FROM crawling_data WHERE id = %s"
            cursor.execute(sql_dates, (request_id,))
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"No data found for request_id: {request_id}")

            from_date, to_date = result["from_date"], result["to_date"]

        # Define the task function to be scheduled
        def schedule_task():
            try:
                connection = get_db_connection()
                with connection.cursor() as cursor:
                    # Fetch the tags for this request
                    sql_tags = "SELECT type, value FROM tags WHERE request_id = %s"
                    cursor.execute(sql_tags, (request_id,))
                    tags = cursor.fetchall()

                # Split tags into keywords and usernames
                keywords = [tag["value"] for tag in tags if tag["type"] == "keyword"]
                usernames = [tag["value"] for tag in tags if tag["type"] == "username"]

                # Handle subprocess calls for username and keyword crawling
                for username in usernames:
                    subprocess.run(
                        f"python run.py --type username --username '{username}'",
                        shell=True,
                    )
                for keyword in keywords:
                    subprocess.run(
                        f"python run.py --type keyword --keyword '{keyword}'",
                        shell=True,
                    )
            except Exception as e:
                print(f"Error in crawl task: {e}")

        # Convert date objects to datetime objects
        start_date = datetime.combine(from_date, time.min)
        end_date = datetime.combine(to_date, time.min)

        # CronTrigger to run the task daily at 10:45 PM
        trigger = CronTrigger(hour=12, minute=26)

        # Add the job to the scheduler
        scheduler.add_job(
            schedule_task,
            trigger,
            start_date=start_date,
            end_date=end_date,
            misfire_grace_time=3600,  # Grace time if the job misses a run
            id=f"crawl_job_{request_id}",
        )

        # Define event listeners for success and error
        def job_listener(event):
            if event.exception:
                print(f"Job {event.job_id} failed with error: {event.exception}")
            else:
                print(f"Job {event.job_id} executed successfully.")

        # Add listeners for job events
        scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

        # Start the scheduler
        scheduler.start()

    except Exception as e:
        print(f"Error in scheduling crawl: {e}")
    finally:
        # Ensure the DB connection is closed
        if connection:
            connection.close()
