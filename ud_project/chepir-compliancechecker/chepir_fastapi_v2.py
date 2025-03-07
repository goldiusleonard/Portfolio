import time
import uvicorn

from chepir_v2 import ComplianceChecker
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List
from utils import setup_logging

# Initialize logger
logger = setup_logging("chepir_api_v2")


# API request model for compliance check with document selection
class ComplianceRequest(BaseModel):
    document_ids: List[str] = Field(
        ...,
        description="List of Qdrant collection names to analyze against",
        example=[
            "Penal_Code.json.law_document.extraction.test",
            "akta-15-akta-hasutan-1948.v1.en.law_document",
        ],
    )
    text: str = Field(..., description="Content to check for law violations")


# New request model for direct analysis
class DirectAnalysisRequest(BaseModel):
    text: str = Field(
        ...,
        description="Content to check for law violations against all default collections",
    )


# API response model for violation details
class ViolationDetail(BaseModel):
    category: str
    section_name: str
    description: str
    reference_text: str


# API response model for compliance check results
class ComplianceResponse(BaseModel):
    violations_found: bool
    violations_details: List[ViolationDetail]
    analysis_timestamp: str
    documents_analyzed: List[str]


# Custom ComplianceChecker with dynamic collection handling
class CustomComplianceChecker(ComplianceChecker):
    # Initialize collections and order for dynamic selection
    def _setup_collections(self):
        self.collections = {}
        self.collection_order = []

    # Dynamically set collections to analyze
    def set_collections(self, collection_names: List[str]):
        self.collections = {name.upper(): name for name in collection_names}
        self.collection_order = list(self.collections.keys())


app = FastAPI(
    title="Chepir Agent API v2",
    description="Compliance checking API using vector search and LLM analysis",
    version="2.0.1",
)

# Enable CORS for all domains
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
    checker = CustomComplianceChecker()
    direct_checker = ComplianceChecker()
except Exception as e:
    logger.error(f"Failed to initialize ComplianceCheckers: {str(e)}")
    raise


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


# API endpoint for checking law violations in content against selected collections
@app.post(
    "/law_regulated",
    response_model=ComplianceResponse,
    tags=["Law Regulated"],
    responses={
        200: {"description": "Compliance check completed successfully"},
        400: {"description": "Invalid request payload"},
        500: {"description": "Internal server error"},
    },
)
async def check_law_violations(request: ComplianceRequest):
    try:
        start_time = time.time()
        logger.info(
            f"Received compliance check request for collections: {request.document_ids}"
        )
        logger.info(f"Input text content: {request.text}")

        # Validate input
        if not request.text.strip():
            logger.warning("Received empty content")
            raise HTTPException(status_code=400, detail="Empty content")

        if not request.document_ids:
            logger.warning("No collections specified")
            raise HTTPException(status_code=400, detail="No collections specified")

        # Set collections dynamically
        checker.set_collections(request.document_ids)

        # Analyze content using the specified collections
        try:
            violations = checker.analyze_content(
                request.text.strip(), request.document_ids
            )
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

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
            documents_analyzed=request.document_ids,
        )

        logger.info(f"Request processed in {time.time() - start_time:.2f}s")
        logger.info(f"Found {len(violations)} violations in selected collections")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# New API endpoint for direct analysis against all default collections
@app.post(
    "/direct_analysis",
    response_model=ComplianceResponse,
    tags=["Direct Analysis"],
    responses={
        200: {"description": "Direct analysis completed successfully"},
        400: {"description": "Invalid request payload"},
        500: {"description": "Internal server error"},
    },
)
async def direct_analysis(request: DirectAnalysisRequest):
    try:
        start_time = time.time()
        logger.info("Received direct analysis request")
        logger.info(f"Input text content: {request.text}")

        # Validate input
        if not request.text.strip():
            logger.warning("Received empty content")
            raise HTTPException(status_code=400, detail="Empty content")

        # Get the default collection list from the base checker
        default_collections = list(direct_checker.collections.keys())

        # Analyze content using all default collections
        try:
            violations = direct_checker.analyze_content(request.text.strip())
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

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
            documents_analyzed=default_collections,
        )

        logger.info(
            f"Direct analysis request processed in {time.time() - start_time:.2f}s"
        )
        logger.info(f"Found {len(violations)} violations across default collections")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in direct analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/healthz", response_class=JSONResponse)
async def healthz() -> dict:
    """Health check endpoint to verify the application's status.

    Returns a 200 OK status with a message if the app is healthy.
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "chepir_fastapi_v2:app", host="0.0.0.0", port=8050, workers=10, reload=True
    )
