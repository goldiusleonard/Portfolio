import uvicorn
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from Amu_prompt import gen_category_subcategory
from logging_section import setup_logging

logger = setup_logging()
app = FastAPI()
load_dotenv()
API_IP = os.getenv("API_IP")
PORT = int(os.getenv("PORT"))

# Configure CORS
origins = [
    "http://localhost",
    f"http://{API_IP}:{PORT}",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/Amu")
def run_Amu(text: str = Query(..., title="Text")):
    """Endpoint for generating category and subcategories based on content and perspective.
    The content and perspective are passed as query parameters.
    """
    try:
        # Call the gen_subcategory function with the content and perspective from the query parameters
        result = gen_category_subcategory(text)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating subcategory: {e}",
        )

@app.get("/healthz", response_class=JSONResponse)
async def healthz() -> dict:
    """Health check endpoint to verify the application's status.

    Returns a 200 OK status with a message if the app is healthy.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host=API_IP, port=PORT)
