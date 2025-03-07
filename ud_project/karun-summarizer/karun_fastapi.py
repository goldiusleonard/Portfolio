import logging
import os
import uvicorn

from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from karun import LLMConfig, SummaryGenerator
from logging.handlers import RotatingFileHandler
from pydantic import BaseModel
from fastapi.responses import JSONResponse


def setup_api_logging():
    logger = logging.getLogger("karun_fastapi")
    logger.setLevel(logging.INFO)
    logger.handlers = []

    os.makedirs("logs", exist_ok=True)
    log_file = f'logs/karun_api_{datetime.now().strftime("%Y%m%d")}.log'

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1024 * 1024,  # 1 MB
        backupCount=5,  # Keep 5 backup files
        encoding="utf-8",
    )

    formatter = logging.Formatter(
        "%(asctime)s,%(msecs)03d | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)

    logger.propagate = False
    logger.addHandler(file_handler)
    return logger


# API Models
class SummaryRequest(BaseModel):
    text: str = ""


class SummaryResponse(BaseModel):
    summary: str


# Initialize FastAPI and Logger
app = FastAPI(
    title="Karun Agent API",
    description="API for text summarization using LLM",
    version="1.0.0",
)
logger = setup_api_logging()
load_dotenv()


# Startup validation
@app.on_event("startup")
async def startup_event():
    required_vars = ["LLM_BASE_URL", "LLM_API_KEY", "MODEL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )


# Initialize LLM configuration and generator
llm_config = LLMConfig(
    base_url=os.getenv("LLM_BASE_URL"),
    api_key=os.getenv("LLM_API_KEY"),
    model=os.getenv("MODEL"),
    tone=os.getenv("TONE", "informative"),
    summary_format=os.getenv("SUMMARY_FORMAT", "paragraph"),
)
generator = SummaryGenerator(llm_config)


@app.post("/summary", response_model=SummaryResponse)
async def generate_summary(request: SummaryRequest):
    request_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    logger.info(f"Request {request_id} | Input text: {request.text}")

    if not request.text.strip():
        logger.warning(f"Request {request_id} | Empty input received")
        return SummaryResponse(summary="None")

    try:
        start_time = datetime.now()
        summary = await generator.generate_summary(request.text)
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(
            f"Request {request_id} | Generated summary: {summary if summary else 'None'}"
        )
        logger.info(f"Request {request_id} | Processing time: {processing_time:.0f}ms")

        return SummaryResponse(summary=summary if summary else "None")
    except Exception as e:
        logger.error(f"Request {request_id} | Error generating summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating summary")

@app.get("/healthz", response_class=JSONResponse)
async def healthz() -> dict:
    """Health check endpoint to verify the application's status.

    Returns a 200 OK status with a message if the app is healthy.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("karun_fastapi:app", host="0.0.0.0", port=8000, reload=True)
