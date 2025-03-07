import uuid
import queue
from typing import Dict
from pydantic import BaseModel
from fastapi import APIRouter, BackgroundTasks, HTTPException
from ..crawlers.keyword_video import KeywordVideoCrawler
from ..utils import Logger

router = APIRouter()
log = Logger(name="Keyword Video Crawler API (Agent Builder)")

# Define a queue with a fixed size
MAX_QUEUE_SIZE = 20
task_queue: queue.Queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)

# Dictionary to track task status
task_status: Dict[str, str] = {}


# Request model for crawling videos by keyword
class KeywordVideoRequest(BaseModel):
    type: str
    keyword: str
    region: str
    count: str
    cursor: str


def background_keyword_crawl(
    type: str,
    keyword: str,
    region: str,
    count: str,
    cursor: str,
    task_id: str,
    request_id: int,
):
    """Background task to crawl videos based on a keyword."""
    task_status[task_id] = "in_progress"
    try:
        KeywordVideoCrawler().crawl(
            type=type,
            keyword=keyword,
            region=region,
            count=count,
            cursor=cursor,
            request_id=request_id,
        )
        task_status[task_id] = "completed"
        log.info(f"Background keyword crawl completed with task ID: {task_id}")
    except Exception as e:
        log.error(f"Error during background keyword crawl: {str(e)}")
        task_status[task_id] = "failed"
    finally:
        # Remove task from queue when done
        task_queue.get()
        task_queue.task_done()


@router.post("/crawler/keyword-video")
def crawl_keyword_videos(body: KeywordVideoRequest, background_tasks: BackgroundTasks):
    """API endpoint to initiate a keyword-based video crawl as a background task."""
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
        background_keyword_crawl,
        body.type,
        body.keyword,
        body.region,
        body.count,
        body.cursor,
        task_id,
    )

    log.info(f"Keyword video crawl background task added with task ID: {task_id}")
    return {"detail": "Keyword video data is being submitted...", "task_id": task_id}


@router.get("/crawler/tasks/{task_id}")
def get_task_status(task_id: str):
    """API endpoint to check the status of a keyword-based video crawl task."""
    status = task_status.get(task_id, "Task ID not found")
    if status == "Task ID not found":
        raise HTTPException(status_code=404, detail=status)
    return {"task_id": task_id, "status": status}
