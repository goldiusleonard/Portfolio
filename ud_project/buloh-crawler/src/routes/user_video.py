import uuid
import queue
from typing import Dict
from pydantic import BaseModel
from fastapi import APIRouter, BackgroundTasks, HTTPException
from ..crawlers.user_video import UserVideoCrawler
from ..utils import Logger

router = APIRouter()
log = Logger(name="User Video Crawler API (Agent Builder)")

# Define a queue with a fixed size
MAX_QUEUE_SIZE = 20
task_queue: queue.Queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
task_status: Dict[str, str] = {}


# Request model for crawling videos by username
class UserVideoRequest(BaseModel):
    type: str
    username: str
    count: str
    cursor: str


def background_user_crawl(
    type: str,
    username: str,
    count: str,
    cursor: str,
    task_id: str,
    request_id: int,
):
    """Background task to crawl videos based on a username."""
    task_status[task_id] = "in_progress"
    try:
        UserVideoCrawler().crawl(
            type=type,
            username=username,
            count=count,
            cursor=cursor,
            request_id=request_id,
        )
        task_status[task_id] = "completed"
        log.info(f"Background user crawl completed with task ID: {task_id}")
    except Exception as e:
        log.error(f"Error during background user crawl: {str(e)}")
        task_status[task_id] = "failed"
    finally:
        # Remove task from queue when done
        task_queue.get()
        task_queue.task_done()


@router.post("/crawler/user-video")
def crawl_user_videos(body: UserVideoRequest, background_tasks: BackgroundTasks):
    """API endpoint to initiate a user-based video crawl as a background task."""
    # Generate unique task ID
    task_id = str(uuid.uuid4())

    # Check if the queue is full
    if task_queue.full():
        log.error("Queue is full. Please try again later.")
        raise HTTPException(
            status_code=429, detail="Queue is full. Please try again later."
        )

    # Add task to queue and set status
    task_queue.put(task_id)
    task_status[task_id] = "pending"

    # Add the background task
    background_tasks.add_task(
        background_user_crawl,
        body.type,
        body.username,
        body.count,
        body.cursor,
        task_id,
    )

    log.info(f"User video crawl background task added with task ID: {task_id}")
    return {"detail": "User video data is being submitted...", "task_id": task_id}


@router.get("/crawler/tasks/{task_id}")
def get_task_status(task_id: str):
    """API endpoint to check the status of a user-based video crawl task."""
    status = task_status.get(task_id, "Task ID not found")
    if status == "Task ID not found":
        raise HTTPException(status_code=404, detail=status)
    return {"task_id": task_id, "status": status}
