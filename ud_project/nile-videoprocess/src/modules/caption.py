import logging
import os
from fastapi import APIRouter, File, UploadFile, Depends
from src.caption.base import VideoCaptioner
from dotenv import load_dotenv

load_dotenv()

# Create an instance of VideoCaptioner
video_captioner = None
log = logging.Logger(name="database_logger")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize VideoCaptioner globally
florence_url = os.getenv("FLORENCE_URL", "")

if florence_url == "":
    raise ValueError("FLORENCE_URL is not set!")

video_captioner = VideoCaptioner(florence_url=florence_url)

router = APIRouter()


def get_video_captioner():
    """Dependency to get the VideoCaptioner instance."""
    if video_captioner is None:
        raise RuntimeError("VideoCaptioner not initialized!")
    return video_captioner


@router.post("/generate_caption")
def generate_video_caption_from_file(
    file: UploadFile = File(...),
    captioner: VideoCaptioner = Depends(get_video_captioner),
):
    """Generate Caption Based on Video Content."""
    try:
        captions = captioner.caption_video_from_file(file.file)
        return {"captions": captions}
    except Exception as e:
        logger.error(f"Error generating captions: {e}")
        return {"error": "Failed to process video"}
