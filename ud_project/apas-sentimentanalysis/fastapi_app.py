import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from langfuse import Langfuse
from pydantic import BaseModel
from fastapi.responses import JSONResponse

from apas_db_final import SentimentAnalyzer

# Load environment variables
load_dotenv()

# Set the IP address to 192.168.30.142
api_ip = "0.0.0.0"  # Change this to your desired IP
port_sentiment = int(os.getenv("PORT_SENTIMENT", 8555))

# Initialize Langfuse with the provided API keys and host
langfuse = Langfuse(
    secret_key="sk-lf-a06110bb-e5d5-441e-9129-c77f90660f2f",
    public_key="pk-lf-7ec24703-cd25-4ae1-a073-9c97a9dba317",
    host="http://195.242.13.111:3000",
)

# Create FastAPI instance
app = FastAPI()

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:8080",
    f"http://{api_ip}:{port_sentiment}",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define a configuration class
class AppConfig:
    host: str = api_ip
    port: int = port_sentiment


# Initialize the SentimentAnalyzer
sentiment_analyzer = SentimentAnalyzer()


# Define a Pydantic model for optional query params
class SentimentRequest(BaseModel):
    text: str


# Function to count tokens (naive approach for text)
def count_tokens(text):
    return len(text.split())  # Simple tokenization using space


# Function to track input, output, and latency
def track_sentiment_inference(
    agent_name,
    input_text,
    output,
    latency,
    input_tokens,
    output_tokens,
    error=None,
):
    langfuse.trace(
        type="sentiment_analysis_inference",
        input=input_text,
        output=output,
        latency=latency,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        error=error,
        metadata={
            "timestamp": time.time(),
            "agent": agent_name,  # Label the trace with agent name
            "input_length (Tokens)": len(input_text),
            "output_length (Tokens)": len(str(output)) if output else 0,
        },
    )


@app.get("/sentiment/")
async def analyze_sentiment(
    text: str = Query(..., description="The text summary to analyze for sentiment"),
):
    """Analyze the sentiment of the provided summary using a transformer model and an API."""
    start_time = time.time()

    try:
        # Count tokens in input
        input_tokens = count_tokens(text)

        # Transformer-based sentiment analysis
        transformer_result = sentiment_analyzer.analyze_sentiment_transformer(text)
        sorted_emotions = sorted(
            transformer_result[0],
            key=lambda x: x["score"],
            reverse=True,
        )
        top_transformer_sentiment = sorted_emotions[0]["label"]
        top_transformer_sentiment_score = sorted_emotions[0]["score"]

        # API-based sentiment analysis
        sentiment_api, sentiment_api_score = sentiment_analyzer.analyze_sentiment_api(
            text,
        )

        if sentiment_api is None:
            raise HTTPException(
                status_code=500,
                detail="Error with API sentiment analysis",
            )

        # Simplify API sentiment to positive, negative, or neutral
        simplified_api_sentiment = 0
        if "positive" in sentiment_api.lower():
            simplified_api_sentiment = 1
        elif "negative" in sentiment_api.lower():
            simplified_api_sentiment = -1

        # Prepare the output
        output = {
            "transformer": {
                "sentiment": top_transformer_sentiment,
                "sentiment_score": top_transformer_sentiment_score,
            },
            "api": {
                "sentiment": simplified_api_sentiment,  # Return simplified sentiment
                "sentiment_score": sentiment_api_score,
            },
        }

        # Count tokens in output
        output_tokens = count_tokens(str(output))

        # Calculate latency
        latency = time.time() - start_time

        # Track the sentiment analysis input and output in Langfuse
        track_sentiment_inference(
            agent_name="APAS-Sentiment",
            input_text=text,
            output=output,
            latency=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        return output

    except Exception as e:
        latency = time.time() - start_time
        track_sentiment_inference(
            agent_name="APAS-Sentiment",
            input_text=text,
            output=None,
            latency=latency,
            input_tokens=count_tokens(text),
            output_tokens=0,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@app.get("/healthz", response_class=JSONResponse)
async def healthz() -> dict:
    """Health check endpoint to verify the application's status.

    Returns a 200 OK status with a message if the app is healthy.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=AppConfig.host, port=AppConfig.port)
