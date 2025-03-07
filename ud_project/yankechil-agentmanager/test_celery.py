from celery.result import AsyncResult
from api import celery_app

task_id = input("Please enter the task ID: ")

result = AsyncResult(task_id, app=celery_app)

# Print detailed task status information
if result.status == "PENDING":
    print("Task is still pending.")
elif result.status == "STARTED":
    print("Task has started.")
elif result.status == "SUCCESS":
    print(f"Task completed successfully with result: {result.result}")
elif result.status == "FAILURE":
    print(f"Task failed with error: {result.result}")
else:
    print(f"Error: Unable to fetch task status. Status code: {result.status}")