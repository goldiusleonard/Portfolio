"""Functions for handling live stream processing and management."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import aiohttp
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TCH002
from sqlalchemy.orm import Session  # noqa: TCH002

from app.api.endpoints.functions.account_details_function import (
    fetch_account_details_from_db,
)
from app.api.endpoints.functions.comment_recording_function import (
    start_comment_recording,
    stop_comment_recording,
)
from app.api.endpoints.functions.video_processor_function import (
    get_caption,
    get_transcription,
)
from app.core.config import get_settings
from app.core.websocket import websocket_manager
from app.models.live_stream_table import LiveStream, StreamChunk
from app.models.watchlist_table import Watchlist
from utils.logger import Logger

logger = Logger(__name__)
settings = get_settings()

HTTP_OK = 200
HTTP_NOT_FOUND = 404
HTTP_SERVER_ERROR = 500


def _raise_http_error(status_code: int, detail: str) -> None:
    """Raise an HTTPException (addresses TRY301)."""
    raise HTTPException(status_code=status_code, detail=detail)


async def start_live_stream(
    username: str,
    stream_id: str,
    user_id: str,
    live_db: Session,
) -> dict:
    """Start a new live stream with proper cleanup of existing streams."""
    try:
        # First, find and cleanup any existing active streams
        existing_stream = (
            live_db.query(LiveStream)
            .filter(
                LiveStream.Username == username,
                LiveStream.Status == "active",
            )
            .first()
        )

        if existing_stream:
            logger.info("Found existing active stream for %s, cleaning up...", username)
            try:
                # Stop the existing recordings
                await stop_recording(username=username, user_id=user_id)
                await stop_comment_recording(
                    username=username,
                    user_id=user_id,
                    db=live_db,
                )

                # Mark existing stream as ended
                existing_stream.Status = "ended"
                existing_stream.EndTime = datetime.now(timezone.utc)
                live_db.flush()

                # Wait briefly for cleanup
                await asyncio.sleep(2)
            except Exception:
                logger.exception("Error during stream cleanup")

        # Reset watchlist flags
        watchlist_entry = (
            live_db.query(Watchlist)
            .filter(
                Watchlist.user_handle == username,
            )
            .first()
        )

        if watchlist_entry:
            watchlist_entry.is_live = True
            watchlist_entry.is_comment_recording = False
            live_db.flush()

        # Create new stream
        live_stream = LiveStream(
            Username=username,
            StreamId=stream_id,
            Status="active",
            StartTime=datetime.now(timezone.utc),
        )
        live_db.add(live_stream)
        live_db.flush()

        # Start comment recording
        await start_comment_recording(
            username=username,
            stream_id=stream_id,
            user_id=user_id,
            db=live_db,
        )

        live_db.commit()

    except Exception as e:
        live_db.rollback()
        logger.exception("Failed to start live stream")
        _raise_http_error(HTTP_SERVER_ERROR, f"Failed to start live stream: {e!s}")
    else:
        return {"message": "Live stream and comment recording started successfully"}


async def process_justification_api(transcription_text: str) -> dict[str, Any]:
    """Call the Justification API with transcription text."""
    try:
        async with aiohttp.ClientSession() as session, session.get(
            settings.JUSTIFICATION_API_URL,
            params={"text": transcription_text},
        ) as response:
            if response.status != HTTP_OK:
                _raise_http_error(
                    response.status,
                    "Failed to call Justification API",
                )
            return await response.json()
    except aiohttp.ClientError as e:
        _raise_http_error(
            HTTP_SERVER_ERROR,
            f"Network Error in Justification API: {e!s}",
        )


def get_notification_line_chart(stream_id: str, db: Session) -> list[dict[str, str]]:
    """Generate risk level line chart for a given stream."""
    try:
        stream_chunks = (
            db.query(StreamChunk)
            .filter(StreamChunk.StreamId == stream_id)
            .order_by(StreamChunk.ChunkNumber)
            .all()
        )

        return [
            {
                "time": chunk.CreatedAt.strftime("%H:%M:%S"),
                "risk": chunk.RiskLevel,
            }
            for chunk in stream_chunks
        ]
    except SQLAlchemyError as e:
        _raise_http_error(
            HTTP_SERVER_ERROR,
            f"Failed to generate NotificationLineChart: {e!s}",
        )


async def process_stream_chunk(
    stream_id: str,
    chunk_number: int,
    chunk_data: bytes,
    db: AsyncSession,
) -> dict:
    """Process and store a stream chunk with enhanced validation."""
    try:
        logger.info("Processing chunk %d for stream %s", chunk_number, stream_id)

        # Initialize defaults
        transcription_text = ""
        caption_result: dict[str, Any] = {}
        eng_justification: list[Any] = []
        malay_justification: list[Any] = []
        risk_level = "Low"
        irrelevant_score = "0/10"

        # Step 1: Try transcription
        try:
            result = await get_transcription(chunk_data, chunk_number)
            transcription_text = result["transcript"]
        except Exception as e:  # noqa: BLE001
            logger.warning("Transcription error: %s", e)

        # Step 2: Try caption
        try:
            caption_result = await get_caption(chunk_data)
        except Exception as e:  # noqa: BLE001
            logger.warning("Caption error: %s", e)

        # Step 3: Process justification if we have transcription
        if transcription_text.strip():
            try:
                justification_response = await process_justification_api(
                    transcription_text,
                )
                eng_justification = justification_response.get("eng_justification", [])
                malay_justification = justification_response.get(
                    "malay_justification",
                    [],
                )
                risk_level = justification_response.get("risk_status", "Low")
                irrelevant_score = justification_response.get(
                    "irrelevant_score",
                    "0/10",
                )
            except Exception as e:  # noqa: BLE001
                logger.warning("Justification error: %s", e)

        if transcription_text.strip():
            await websocket_manager.broadcast_to_stream(
                stream_id,
                {
                    "type": "transcription",
                    "data": {
                        "text": transcription_text,
                        "chunk_number": chunk_number,
                    },
                },
            )

        if caption_result:
            await websocket_manager.broadcast_to_stream(
                stream_id,
                {
                    "type": "caption",
                    "data": caption_result,
                },
            )

        if eng_justification or malay_justification:
            await websocket_manager.broadcast_to_stream(
                stream_id,
                {
                    "type": "justification",
                    "data": {
                        "eng_justification": eng_justification,
                        "malay_justification": malay_justification,
                        "risk_level": risk_level,
                        "irrelevant_score": irrelevant_score,
                    },
                },
            )

        await websocket_manager.broadcast_to_stream(
            stream_id,
            {
                "type": "chunk_update",
                "data": {
                    "chunk_number": chunk_number,
                    "status": "processed",
                    "risk_level": risk_level,
                },
            },
        )
        # Step 4: Save to database
        try:
            chunk = StreamChunk(
                StreamId=stream_id,
                ChunkNumber=chunk_number,
                Transcription={"transcription": transcription_text},
                Caption=caption_result,
                Justification={
                    "eng_justification": eng_justification,
                    "malay_justification": malay_justification,
                    "irrelevant_score": irrelevant_score,
                },
                RiskLevel=risk_level,
                CreatedAt=datetime.now(timezone.utc),
            )
            db.add(chunk)
            await db.commit()
        except Exception:
            logger.exception("Database error")
            await db.rollback()
            raise

        return {  # noqa: TRY300
            "message": "Chunk processed successfully",
            "chunk_number": chunk_number,
            "transcription": transcription_text,
            "risk_level": risk_level,
        }

    except Exception as e:
        logger.exception("Chunk processing error")
        await db.rollback()
        _raise_http_error(HTTP_SERVER_ERROR, f"Chunk processing failed: {e!s}")


async def stop_live_stream(
    username: str,
    user_id: int,
    stream_id: str,
    db: Session,
) -> dict:
    """Stop an ongoing live stream."""
    try:
        live_stream = (
            db.query(LiveStream)
            .filter(LiveStream.StreamId == stream_id, LiveStream.Status == "active")
            .first()
        )
        if not live_stream:
            _raise_http_error(
                HTTP_NOT_FOUND,
                f"Live stream with StreamId {stream_id} not found or already stopped.",
            )
        live_stream.Status = "ended"
        live_stream.EndTime = datetime.now(timezone.utc)
        db.commit()

        await stop_comment_recording(username=username, user_id=user_id, db=db)

    except Exception:
        db.rollback()
        logger.exception("Failed to stop live stream")
        _raise_http_error(HTTP_SERVER_ERROR, "Failed to stop live stream")
    else:
        return {"message": "Live stream stopped successfully"}


async def stop_recording(username: str, user_id: int) -> dict:
    """Stop recording TikTok live video."""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{settings.TIKTOK_API_BASE_URL}/tiktok/live/video/stop-recording"
            params = {
                "username": username,
                "user_id": str(user_id),  # Convert to string as expected by API
            }

            async with session.post(url, params=params) as response:
                if response.status != HTTP_OK:
                    _raise_http_error(
                        response.status,
                        f"Failed to stop recording for {username}",
                    )

                return {
                    "message": f"Video recording stopped successfully for {username}",
                }

    except Exception:
        logger.exception("Failed to stop video recording")
        _raise_http_error(HTTP_SERVER_ERROR, "Failed to stop video recording")


def get_live_stream_details(stream_id: str, live_db: Session, mcmc_db: Session) -> dict:
    """Get detailed information about a specific live stream."""
    try:
        live_stream = (
            live_db.query(LiveStream).filter(LiveStream.StreamId == stream_id).first()
        )
        if not live_stream:
            _raise_http_error(HTTP_NOT_FOUND, "Live stream not found")

        # Get account details directly from mcmc database
        account_details = fetch_account_details_from_db(live_stream.Username, mcmc_db)

        # Get notification line chart data
        notification_line_chart = get_notification_line_chart(stream_id, live_db)

        live_url = f"{settings.FRONTEND_BASE_URL}/@{stream_id}/live"

        return {
            "liveUrl": live_url,
            "accountDetails": account_details,
            "liveJustifications": [
                chunk.Justification for chunk in live_stream.stream_chunks
            ]
            if live_stream.stream_chunks
            else [],
            "liveTranscript": [
                chunk.Transcription for chunk in live_stream.stream_chunks
            ]
            if live_stream.stream_chunks
            else [],
            "notificationLineChart": notification_line_chart,
        }

    except Exception:
        logger.exception("Error fetching live stream details for %s", stream_id)
        _raise_http_error(HTTP_SERVER_ERROR, "Failed to fetch live stream details")
