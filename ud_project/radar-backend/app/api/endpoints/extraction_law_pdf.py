"""extraction law pdf endpoints."""

import os

import httpx
from fastapi import APIRouter, Path, Query, UploadFile

from app.core.constants import DEFAULT_EXTRACTION_LAW_PDF_URL

extraction_law_pdf = APIRouter()


@extraction_law_pdf.post("/process-document")
async def process_document_pdf(
    file: UploadFile,
    language: str = Query(),
) -> dict:
    """Process document."""
    files = {
        "file": (file.filename, await file.read(), file.content_type),
    }
    params = {"language": language}
    url = os.getenv("DEFAULT_EXTRACTION_LAW_PDF_URL") or DEFAULT_EXTRACTION_LAW_PDF_URL
    timeout = httpx.Timeout(300.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            url=f"{url}/process-document/",
            params=params,
            files=files,
        )
        response.raise_for_status()
        data = response.json()
        return data if data else []


@extraction_law_pdf.get("/list-collections")
async def list_collections_pdf() -> dict:
    """List collection."""
    url = os.getenv("DEFAULT_EXTRACTION_LAW_PDF_URL") or DEFAULT_EXTRACTION_LAW_PDF_URL
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=f"{url}/list-collections/",
        )
        response.raise_for_status()
        data = response.json()
        return data if data else []


@extraction_law_pdf.get("/available-languages")
async def get_available_languages() -> dict:
    """Get available languages."""
    url = os.getenv("DEFAULT_EXTRACTION_LAW_PDF_URL") or DEFAULT_EXTRACTION_LAW_PDF_URL
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=f"{url}/available-languages/",
        )
        response.raise_for_status()
        data = response.json()
        return data if data else []


@extraction_law_pdf.delete("/collections/{collection_name}")
async def delete_collections_pdf(collection_name: str = Path()) -> dict:
    """Delete collections by collection name."""
    url = os.getenv("DEFAULT_EXTRACTION_LAW_PDF_URL") or DEFAULT_EXTRACTION_LAW_PDF_URL
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            url=f"{url}/collections/{collection_name}",
        )
        response.raise_for_status()
        data = response.json()
        return data if data else []
