import os
from dotenv import load_dotenv
import redis
from celery import Celery

# Load environment variables
load_dotenv()

# Fetch Redis configuration from environment variables
redis_host = os.getenv("redis_host", "localhost")
redis_port = os.getenv("redis_port", "6379")
redis_db = os.getenv("redis_db", "0")
redis_password = os.getenv("redis_password", "")

# Construct the Redis URL
redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"

# Connect to Redis and perform a ping test
try:
    r = redis.StrictRedis.from_url(redis_url)
    ping_response = r.ping()
    if ping_response:
        print("Successfully connected to Redis!")
except Exception as e:
    print(f"Failed to connect to Redis: {e}")

# Celery configuration
celery_app = Celery(
    "tasks",
    broker=redis_url,
    backend=redis_url
)

# Ensure Celery knows about the task
@celery_app.task(bind=True, name="tasks.test_task")
def test_task(self):
    return "Pong"

# Celery routing configuration (if needed)
celery_app.conf.task_routes = {'tasks.test_task': {'queue': 'default'}}

# Test Celery worker by sending a task synchronously
if __name__ == "__main__":
    try:
        print("Testing Celery task...")
        result = test_task.apply()  # Synchronous execution
        
        print(f"Task result: {result.get(timeout=10)}")  # Should return 'Pong' if successful
    except Exception as e:
        print(f"Failed to execute Celery task: {e}")