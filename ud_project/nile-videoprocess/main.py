import os
import uvicorn
from typing import List
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.modules.caption import router as caption_router
from dotenv import load_dotenv

load_dotenv()

# Set tokenizer to non-parallel to avoid deadlock
os.environ["TOKENIZERS_PARALLELISM"] = "false"

TAGS_METADATA: List[dict] = [
    {
        "name": "Caption",
        "description": ("Endpoints for generating caption from video."),
    },
]

app = FastAPI(
    debug=False,
    title="Nile-Video-Process-Agent",
    summary="A comprehensive API for generating caption on videos.",
    description="""The **Nile API** is designed to generate caption for videos.
    """,
    version=os.getenv("VERSION"),
    openapi_tags=TAGS_METADATA,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=[
        "*",
    ],
)

app.include_router(caption_router, prefix="/caption", tags=["Caption"])


@app.get("/healthz", response_class=JSONResponse)
def healthz():
    """
    Health check endpoint to verify the application's status.
    Returns a 200 OK status with a message if the app is healthy.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        h11_max_incomplete_event_size=5000000000,
        timeout_keep_alive=10,
    )
