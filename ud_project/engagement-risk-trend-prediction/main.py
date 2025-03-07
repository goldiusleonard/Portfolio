import uvicorn
import warnings
from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from dotenv import load_dotenv

from src.modules.engagement_prediction import router as prediction_router
from vers import version

load_dotenv()

# Ignore warnings
warnings.filterwarnings(
    "ignore",
    message="Unverified HTTPS request is being made.*",
    category=UserWarning,
)


TAGS_METADATA: List[dict] = [
    {
        "name": "predict",
        "description": """
        Endpoints that enable the generation of data-driven predictions 
        for various metrics, including engagement metrics (likes, shares, views) 
        and risk analysis, based on user-provided data and criteria.
        """,
    },
]

# App Configuration
app = FastAPI(
    debug=False,
    title="Prediction API",
    summary="An API for generating predictions based on user data.",
    description="""
    The Prediction API enables dynamic forecasting for various metrics like videos, likes, shares, 
    and comments, based on user-defined criteria and data inputs.
    """,
    version=version,
    openapi_tags=TAGS_METADATA,
)

# Middleware for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include Routers
app.include_router(prediction_router, prefix="/predictions", tags=["predict"])


@app.get("/")
def root(response: Response) -> dict[str, str]:
    """The function sets response headers for cache control and CORS, and returns a message indicating that
    the Engagement Risk Trend Prediction is ready.

    :param response: The `response` parameter in the `root` function is an object that represents the
    HTTP response that will be sent back to the client. In this case, the code is setting various
    headers on the response object before returning a JSON response with the message "Engagement Risk Trend Prediction is
    Ready!"\n
    :type response: Response
    :return: a dictionary with the key "Engagement Risk Trend Prediction" and the value "Engagement Risk Trend Prediction is Ready!".
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = "0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"

    return {
        "Engagement Risk Trend Prediction": "Engagement Risk Trend Prediction is Ready!"
    }


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
    )
