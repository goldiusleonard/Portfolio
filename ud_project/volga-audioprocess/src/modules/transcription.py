import httpx
import os

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from ..utils import configure_logging

load_dotenv()

LIT_SERVER_URL = os.getenv("LIT_SERVER_URL", "")

if LIT_SERVER_URL == "":
    raise ValueError("LIT_SERVER_URL is not set in the environment!")

logger = configure_logging()

router = APIRouter()


@router.post("/transcription")
async def generate_transcription(
    video: UploadFile = File(...),
):
    """
    Endpoint to transcribe a video file uploaded by the user using LitServe API (httpx).

    Args:
        video (UploadFile): The uploaded video file.

    Returns:
        JSONResponse: The transcription result and detected language.
    """
    if not video.content_type.startswith("video/"):
        raise HTTPException(
            status_code=400, detail="Uploaded file is not a valid video format."
        )

    try:
        video_bytes = await video.read()
    except Exception as e:
        logger.exception("Error reading video file.")
        raise HTTPException(status_code=500, detail=f"Error reading video file: {e}")

    files = {"video": (video.filename, video_bytes, video.content_type)}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                LIT_SERVER_URL, files=files, timeout=None
            )  # Added timeout=None to prevent timeout issues for larger files
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()
        except httpx.HTTPStatusError as e:
            logger.exception(f"HTTP error communicating with LitServe API: {e}")
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except (
            httpx.RequestError
        ) as e:  # Catch other request exceptions (connection, timeout, etc.)
            logger.exception(f"Request error communicating with LitServe API: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error communicating with LitServe API: {e}"
            )
        except Exception as e:
            logger.exception(f"Unexpected error communicating with LitServe API: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error communicating with LitServe API: {e}",
            )

    if not data.get("transcript"):
        raise HTTPException(
            status_code=422,
            detail="Failed to transcribe the video. No valid transcription found.",
        )

    return JSONResponse(
        content={
            "message": "Transcription successful.",
            "transcript": data.get("transcript"),
            "language": data.get("language"),
        },
        status_code=200,
    )
