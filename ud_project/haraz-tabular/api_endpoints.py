import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from main_AgentBuilder import run_haraz_AI
from main_directlink import run_haraz_directlink
from fastapi.responses import JSONResponse

app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Wrap the function in an endpoint
@app.get("/Haraz")
def process_data():
    """API endpoint to trigger the data processing pipeline."""
    result = run_haraz_AI()
    if "pipeline executed successfully" in result["message"].lower():
        return {
            "status": "success",
            "message": result["message"],
            "records_processed": result["records_processed"],
        }
    return {
        "status": "failure",
        "message": result["message"],
    }


@app.get("/Haraz_directlink")
def process_directlink_data():
    """API endpoint to trigger the data processing pipeline for directlink"""
    result = run_haraz_directlink()
    if "pipeline executed successfully" in result["message"].lower():
        return {
            "status": "success",
            "message": result["message"],
            "records_processed": result["records_processed"],
            "yankechil_triggered": result["fastapi_triggered"],
        }
    return {
        "status": "failure",
        "message": result["message"],
    }

@app.get("/healthz", response_class=JSONResponse)
async def healthz() -> dict:
    """Health check endpoint to verify the application's status.

    Returns a 200 OK status with a message if the app is healthy.
    """
    return {"status": "healthy"}

# Main entry point
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
