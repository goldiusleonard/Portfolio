import uuid
import queue
from fastapi import APIRouter, BackgroundTasks
from typing import List, Dict
from pydantic import BaseModel
from ..utils import Logger
from ..crawlers.url_video import URLVideoCrawler

router = APIRouter()
log = Logger(name="URL Video Crawler API (Agent Builder)")

# Define a queue with a fixed size (e.g., 20 tasks)
MAX_QUEUE_SIZE = 20
task_queue: queue.Queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
# Dictionary to track task status
task_status: Dict[str, str] = {}


class VideoUrlsRequest(BaseModel):
    urls: List[str]


def background_crawl(
    urls: List[str],
    task_id: str,
    request_id: int,
):
    task_status[task_id] = "in_progress"
    try:
        URLVideoCrawler().crawl(
            urls=urls,
            request_id=request_id,
        )
        task_status[task_id] = "completed"
        log.info(f"Background crawl completed with task ID: {task_id}")
    except Exception as e:
        log.error(f"Error during background crawl: {str(e)}")
        task_status[task_id] = "failed"
    finally:
        # Remove the task ID from the queue when done
        task_queue.get()
        task_queue.task_done()


@router.post("/crawler/video-url")
def crawl_video_urls(body: VideoUrlsRequest, background_tasks: BackgroundTasks):
    urls = body.urls

    task_id = str(uuid.uuid4())

    # Check if the queue is full
    if task_queue.full():
        log.error("Queue is full. Please try again later.")
        return {"detail": "Queue is full. Please try again later."}

    # Add the task ID to the queue and initialize status
    task_queue.put(task_id)
    task_status[task_id] = "pending"

    # Add the background task
    background_tasks.add_task(background_crawl, urls, task_id)

    log.info(f"Background task added with task ID: {task_id}")
    return {"detail": "Video data is submitting...", "task_id": task_id}


@router.get("/crawler/tasks/{task_id}")
def get_task_status(task_id: str):
    status = task_status.get(task_id, "Task ID not found")
    if status == "Task ID not found":
        return {"detail": status}
    return {"task_id": task_id, "status": status}
