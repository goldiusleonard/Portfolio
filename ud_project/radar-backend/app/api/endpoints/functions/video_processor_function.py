"""Functions for processing video data through various APIs."""

from __future__ import annotations

import asyncio
import io
from typing import Any

import aiohttp
from fastapi import HTTPException

from app.core.config import get_settings
from utils.logger import Logger

logger = Logger(__name__)
settings = get_settings()

HTTP_OK = 200


def _raise_http_error(status_code: int, detail: str) -> None:
    """Raise HTTPException (addresses TRY301)."""
    raise HTTPException(status_code=status_code, detail=detail)


async def get_transcription(chunk_data: bytes, chunk_number: int) -> dict | None:
    """Send a video chunk to the transcription API and get the transcription result."""
    try:
        async with aiohttp.ClientSession() as session:
            form = aiohttp.FormData()
            form.add_field(
                "video",
                io.BytesIO(chunk_data),
                filename=f"chunk_{chunk_number}.mp4",
                content_type="video/mp4",
            )

            logger.debug("Sending chunk %d to transcription API...", chunk_number)

            async with session.post(
                f"{settings.TRANSCRIPTION_API_URL}/transcription",
                data=form,
                headers={"accept": "application/json"},
            ) as response:
                logger.debug(
                    "Transcription API response status for chunk %d: %d",
                    chunk_number,
                    response.status,
                )

                if response.status == HTTP_OK:
                    result = await response.json()
                    logger.debug(
                        "Transcription result for chunk %d: %s",
                        chunk_number,
                        result,
                    )
                    return result
                error_text = await response.text()
                logger.warning(
                    "Transcription API error for chunk %d: %s",
                    chunk_number,
                    error_text,
                )
                return None

    except Exception:
        logger.exception(
            "Unhandled error processing chunk %d transcription",
            chunk_number,
        )
        return None


async def get_caption(chunk_data: bytes) -> dict:
    """Get caption from API with timeout."""
    try:
        async with aiohttp.ClientSession() as session:
            timeout = aiohttp.ClientTimeout(total=30)

            form = aiohttp.FormData()
            form.add_field(
                "file",
                io.BytesIO(chunk_data),
                filename="chunk.mp4",
                content_type="video/mp4",
            )

            async with session.post(
                settings.CAPTION_API_URL,
                data=form,
                timeout=timeout,
            ) as response:
                logger.info("Caption API response status: %d", response.status)

                if response.status != HTTP_OK:
                    error_text = await response.text()
                    truncated = error_text.encode("ascii", errors="replace").decode(
                        "ascii",
                    )[:200]
                    logger.error("Caption service error: %s", truncated)
                    _raise_http_error(
                        response.status,
                        f"Caption service error: {truncated}",
                    )

                return await response.json()

    except asyncio.TimeoutError as exc:
        logger.exception("Caption API request timed out")
        raise HTTPException(
            status_code=504,
            detail="Caption service timeout",
        ) from exc
    except Exception as e:
        logger.exception("Caption failed")
        raise HTTPException(
            status_code=500,
            detail=f"Caption failed: {e!s}",
        ) from e


async def get_justification(text: str) -> dict[str, Any]:
    """Get justification from API."""
    async with aiohttp.ClientSession() as session:
        params = {"text": text}
        async with session.get(
            settings.JUSTIFICATION_API_URL,
            params=params,
        ) as response:
            logger.info("Justification API response status: %d", response.status)
            logger.info(
                "Justification API URL used: %s",
                settings.JUSTIFICATION_API_URL,
            )

            if response.status != HTTP_OK:
                _raise_http_error(
                    response.status,
                    "Justification service error",
                )
            return await response.json()
