import time
import uvicorn

from chepir import ComplianceChecker
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from utils import setup_logging

# Initialize logger
logger = setup_logging("chepir_api")


class ViolationDetail(BaseModel):
    """API response model for violation details."""

    category: str
    section_name: str
    description: str
    reference_text: str


class ComplianceResponse(BaseModel):
    """API response model for compliance check results."""

    violations_found: bool
    violations_details: List[ViolationDetail]
    analysis_timestamp: str


class ComplianceRequest(BaseModel):
    """API request model for compliance check."""

    text: str = Query(..., description="Content to check for law violations")


# Initialize FastAPI app with CORS support
app = FastAPI(
    title="Chepir Agent API",
    description="Compliance checking API using vector search and LLM analysis",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize compliance checker
load_dotenv()
try:
    checker = ComplianceChecker()
except Exception as e:
    logger.error(f"Failed to initialize ComplianceChecker: {str(e)}")
    raise


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all unhandled errors."""
    logger.error(f"Unhandled error: {str(exc)}")
    return {"detail": str(exc)}, 500


@app.post("/law_regulated", response_model=ComplianceResponse)
async def check_law_violations(request: ComplianceRequest):
    """
    Check content for law violations across multiple regulatory frameworks.
    Returns detailed violation information if found.
    """
    try:
        start_time = time.time()
        logger.info("Received compliance check request")

        # Validate input
        if not request.text.strip():
            logger.warning("Received empty content")
            raise HTTPException(status_code=400, detail="Empty content")

        # Analyze content
        try:
            violations = checker.analyze_content(request.text.strip())
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

        # Log results with detailed information
        if violations:
            logger.info(f"Found {len(violations)} violations")
            for v in violations:
                logger.info(f"Violation in {v.category}: {v.section_name}")
                logger.info(f"Violation Description: {v.description}")
                logger.info(f"Violation Reference Text: {v.reference_text}")
                logger.info("-" * 80)

        # Prepare response
        response = ComplianceResponse(
            violations_found=bool(violations),
            violations_details=[
                ViolationDetail(
                    category=v.category,
                    section_name=v.section_name,
                    description=v.description,
                    reference_text=v.reference_text,
                )
                for v in violations
            ],
            analysis_timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        logger.info(f"Request processed in {time.time() - start_time:.2f}s")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("chepir_fastapi:app", host="192.168.30.103", port=8001, reload=True)
