import asyncio
import multiprocessing
import os
import time
from concurrent.futures import ThreadPoolExecutor

import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from langfuse import Langfuse
from pydantic import BaseModel

import config
from justification_risk import JustificationAndRiskLevelV0
from log_mongo import logger

langfuse = Langfuse(
    secret_key="sk-tr-f08349gh-e4dj8-4661e-8829-c9899899f2f",
    public_key="pk-tr-7ec24703-cd25-4ae1-a065-9c97a9dba317",
    host="http://195.242.13.111:3000",
)

# Load environment variables
load_dotenv()

# Get the environment variables
api_ip = os.getenv("api_ip")
port_justification = int(
    os.getenv("port_justification") or 8003,
)
LLAMA_BASE_URL_HEALTH = os.getenv("LLAMA_BASE_URL_HEALTH")
LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")


def count_tokens(text):
    return len(text.split())  # Simple tokenization using spaces


def track_agent_inference(
    agent_name,
    input_text,
    output,
    latency,
    input_tokens,
    output_tokens,
    error=None,
):
    langfuse.trace(
        type="agent_analysis_inference",  # Label for the trace
        input=input_text,  # Input text data
        output=output,  # Output text data
        latency=latency,  # Latency in seconds
        input_tokens=input_tokens,  # Number of tokens in input
        output_tokens=output_tokens,  # Number of tokens in output
        error=error,  # Error message, if any
        metadata={
            "timestamp": time.time(),  # Record the time of inference
            "agent": agent_name,  # Agent's name for identification
            "input_length (Tokens)": input_tokens,
            "output_length (Tokens)": output_tokens if output else 0,
        },
    )


# Automatically calculate the number of workers
def calculate_workers():
    cpu_cores = multiprocessing.cpu_count()
    num_cores = (2 * cpu_cores) + 1
    print(f"num of core: {num_cores}")
    return num_cores  # Formula to determine optimal workers


# Calculate the number of workers
default_workers = calculate_workers()

app = FastAPI()

# CORS configuration
origins = [
    "http://localhost",
    "http://localhost:8080",
    f"http://{api_ip}:{port_justification}",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Configuration class
class AppConfig:
    host: str = api_ip
    port: int = port_justification
    workers: int = default_workers  # Set the workers dynamically based on CPU count


# Define input model
class JustificationInput(BaseModel):
    text: str


# Create a thread pool executor for concurrency
executor = ThreadPoolExecutor(max_workers=AppConfig.workers)


async def analyze_justification_concurrently(text: str):
    """Executes the JustificationAndRiskLevelV0 analyze method in a thread pool."""
    loop = asyncio.get_event_loop()
    analyzer = JustificationAndRiskLevelV0(config.system_prompt, config.class_names_arr)
    return await loop.run_in_executor(executor, analyzer.analyze, text)


@app.get("/justification/")
async def justification(
    text: str = Query(...),
):
    # Record the start time
    start_time = time.time()

    try:
        if not api_ip:
            raise ValueError("Environment variable 'api_ip' is not set")
        health_check_url = f"{LLAMA_BASE_URL_HEALTH}/health"
        response = requests.get(
            health_check_url,
            headers={"Authorization": f"Bearer {LLAMA_API_KEY}"},
            timeout=5,
        )

        if response.status_code != 200:
            logger.error(
                f"LLM Health check failed: {response.status_code}, Response: {response.text}",
            )
            raise HTTPException(status_code=404, detail="Internal Server Error.")

        # Check if the input text is empty or None
        if not text or text.strip() == "" or text.strip() == "none":
            return {
                "eng_justification": "None",
                "malay_justification": "None",
                "risk_status": "None",
                "irrelevant_score": "None",
            }
        # Validate input
        input_data = JustificationInput(text=text)
        input_tokens = count_tokens(input_data.text)
        if not input_data.text:
            raise HTTPException(status_code=400, detail="Input text cannot be empty.")

        if len(input_data.text) > 10000:  # Limit input size
            raise HTTPException(status_code=400, detail="Input text is too long.")

        # Run the analysis concurrently
        res = await analyze_justification_concurrently(input_data.text)

        # Handle the response
        if res:
            eng_justification, malay_justification, risk_status, irrelevant_score = res
        else:
            eng_justification = malay_justification = risk_status = irrelevant_score = (
                "None"
            )
        output_tokens = count_tokens(str(res))

        # Record the end time and calculate elapsed time
        end_time = time.time()
        elapsed_time = end_time - start_time
        track_agent_inference(
            agent_name="tatau-riskandjustification",
            input_text=input_data.text,
            output=str(res),
            latency=elapsed_time,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        # Log execution time
        logger.info(
            f"Justification agent run successfully in {elapsed_time:.4f} seconds.",
        )

        logger.info("Justification agent run successfully.")
        return {
            "eng_justification": eng_justification,
            "malay_justification": malay_justification,
            "risk_status": risk_status,
            "irrelevant_score": irrelevant_score,
        }

    except Exception as e:
        logger.error(f"Error analyzing justification: {e}")
        latency = time.time() - start_time
        track_agent_inference(
            agent_name="tatau-riskandjustification",
            input_text=input_data.text,
            output=None,
            latency=latency,
            input_tokens=input_tokens,
            output_tokens=0,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@app.get("/health")
async def justification_health_check():
    """Health check endpoint for the /justification/ service and its dependencies."""
    health_status = {
        "status": "healthy",
        "details": {},
    }

    try:
        # Check if required environment variables are set
        if not api_ip:
            health_status["details"]["api_ip"] = "missing"
            health_status["status"] = "unhealthy"

        if not LLAMA_BASE_URL_HEALTH:
            health_status["details"]["LLAMA_BASE_URL"] = "missing"
            health_status["status"] = "unhealthy"

        if not LLAMA_API_KEY:
            health_status["details"]["LLAMA_API_KEY"] = "missing"
            health_status["status"] = "unhealthy"

        # Check external LLM service health
        health_check_url = f"{LLAMA_BASE_URL_HEALTH}/health"
        try:
            response = requests.get(
                health_check_url,
                headers={"Authorization": f"Bearer {LLAMA_BASE_URL_HEALTH}"},
                timeout=5,
            )
            if response.status_code == 200:
                health_status["details"]["LLM_service"] = "healthy"
            else:
                health_status["details"]["LLM_service"] = (
                    f"unhealthy ({response.status_code})"
                )
                health_status["status"] = "unhealthy"
        except requests.RequestException as e:
            health_status["details"]["LLM_service"] = f"unreachable: {e}"
            health_status["status"] = "unhealthy"

        # Add more checks if needed, e.g., database connectivity

    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["details"]["error"] = str(e)
        logger.error(f"Justification health check failed: {e}")

    return health_status


@app.get("/healthz", response_class=JSONResponse)
async def healthz():
    """
    Health check endpoint to verify the application's status.
    Returns a 200 OK status with a message if the app is healthy.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    # Use uvicorn to run the app, passing in the dynamically calculated number of workers
    uvicorn.run(
        "api:app",
        host=AppConfig.host,
        port=AppConfig.port,
        workers=AppConfig.workers,
        reload=False,
    )
