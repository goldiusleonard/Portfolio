"""Routing for Fetching Keyword Trend."""

from __future__ import annotations

import logging
import os

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter

from modules.content_stored_procedure import call_update
from modules.profile_stored_procedure import call_update_profile_data_asset

load_dotenv()
router = APIRouter()

SUCCESS_REQUEST_CODE = 200


@router.get("/update_content_data_asset/", name="update_content_data_asset")
async def update_data_asset() -> dict:
    """Update Data Asset."""
    # 1. Update Content Data Asset Table
    message = call_update()

    # 2. Trigger Embedding URL
    embedding_trigger_url = os.getenv("EMBEDDING_TRIGGER_URL")
    headers = {"Content-Type": "application/json"}
    ids_list = message["ids_list"]
    data = {"ids": ids_list}  # List of IDs to process

    timeout = httpx.Timeout(
        connect=10.0,
        read=30.0,
        write=10.0,
        pool=5.0,
    )

    save_collection_result = {}
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                embedding_trigger_url,
                json=data,
                headers=headers,
            )
        if response.status_code == SUCCESS_REQUEST_CODE:
            save_collection_result = response.json()
        else:
            error_message = f"Failed to save collection: {response.status_code}"
            save_collection_result = {
                "error": error_message,
                "details": response.text,
            }
    except httpx.RequestError as e:
        error_message = f"Error during embedding trigger request: {e}"
        logging.exception(error_message)
        save_collection_result = {"error": "Failed to connect to embedding service."}

    # 3. Trigger Wordcloud
    wordcloud_url = os.getenv("WORDCLOUD_TRIGGER_URL")
    wordcloud_result = {}
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            wordcloud_response = await client.get(wordcloud_url, headers=headers)
        if wordcloud_response.status_code == SUCCESS_REQUEST_CODE:
            wordcloud_result = wordcloud_response.json()
        else:
            wordcloud_result = {
                "error": f"Failed to trigger wordcloud: {wordcloud_response.status_code}",
                "details": wordcloud_response.text,
            }
    except httpx.RequestError as e:
        error_message = f"Error during wordcloud trigger request: {e}"
        logging.exception(error_message)
        wordcloud_result = {"error": "Failed to connect to wordcloud service."}

    # 4. Call updates on profile
    profile_data_asset_result = call_update_profile_data_asset()

    return {
        "update_message": message,
        "save_collection_result": save_collection_result,
        "wordcloud_result": wordcloud_result,
        "profile_data_asset_result": profile_data_asset_result,
    }
