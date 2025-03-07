import os
import uvicorn
from typing import List
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from src.modules.transcription import router as transcription_router
from vers import version

# Load environment variables
load_dotenv()

TAGS_METADATA: List[dict] = [
    {
        "name": "Transcription",
        "description": ("Endpoints for generating audio transcription from video."),
    },
]


# Create FastAPI instance
app = FastAPI(
    debug=False,
    title="Volga-AudioProcess",
    description="API for generating audio transcription from video.",
    version=version,
    openapi_tags=TAGS_METADATA,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transcription_router, prefix="", tags=["Transcription"])


@app.get("/healthz", response_class=JSONResponse)
async def healthz():
    """
    Health check endpoint to verify the application's status.
    Returns a 200 OK status with a message if the app is healthy.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("VOLGA_API_PORT", 8000)),
        h11_max_incomplete_event_size=5000000000,
        timeout_keep_alive=10,
    )
