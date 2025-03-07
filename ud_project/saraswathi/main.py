try:
    __import__("pysqlite3")
    import sys

    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except Exception:
    pass

import uvicorn
import warnings
import urllib3

from multiprocessing.pool import Pool
from typing import List
from vers import version
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from modules.api_logging_and_modules.log_api import router as log_api_router
from modules.api_logging_and_modules.log_api_modules import (
    setup_modules as api_logging_setup_modules,
)
from modules.chart_feedback.chart_feedback import router as chart_feedback_router
from modules.chart_feedback.chart_feedback_modules import (
    setup_modules as chart_feedback_setup_modules,
)
from modules.query_generator_executor import router as query_generator_executor_router
from modules.chart import router as chart_router

warnings.filterwarnings(
    "ignore",
    message="Api key is used with an insecure connection.",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message="Unverified HTTPS request is being made.*",
    category=urllib3.exceptions.InsecureRequestWarning,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    api_logging_setup_modules()
    chart_feedback_setup_modules()
    yield


TAGS_METADATA: List[dict] = [
    {
        "name": "Chart",
        "description": "Generates and customizes data visualizations based on user inputs.",
    },
    {
        "name": "Log",
        "description": "Handles chart logging, LLM interactions for chart data logging, and insight logging.",
    },
    {
        "name": "Feedback",
        "description": "Manages chart feedback, including saving feedback, querying feedback history, and retrieving feedback data.",
    },
    {
        "name": "SQL",
        "description": "Facilitates dynamic SQL query generation and execution for data analysis and visualization.",
    },
]


app = FastAPI(
    debug=False,
    title="Saraswati-Congo-Agent",
    summary="An API for Interactive Data Visualization and Insight Generation.",
    description="""
    The Saraswati-Congo-Agent API provides a comprehensive interface for generating dynamic visualizations 
    and delivering insightful analytics based on user inputs. Saraswati focuses on chart creation, 
    while Congo generates actionable insights through data analysis.
    """,
    version=version,
    lifespan=lifespan,
    openapi_tags=TAGS_METADATA,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # If you want to allow cookies to be sent
    allow_methods=["*"],
    allow_headers=[
        "*",
    ],  # You can customize the allowed headers or use "*" to allow any header
)

app.include_router(log_api_router, prefix="/log", tags=["Log"])
app.include_router(chart_feedback_router, prefix="/feedback", tags=["Feedback"])
app.include_router(query_generator_executor_router, prefix="/sql", tags=["SQL"])
app.include_router(chart_router, prefix="", tags=["Chart"])


@app.get("/healthz", response_class=JSONResponse)
async def healthz():
    """
    Health check endpoint to verify the application's status.
    Returns a 200 OK status with a message if the app is healthy.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    with Pool() as mp_pool:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            h11_max_incomplete_event_size=5000000000,
            timeout_keep_alive=10,
        )
