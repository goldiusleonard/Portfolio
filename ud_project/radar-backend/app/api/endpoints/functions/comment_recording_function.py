"""Functions for handling TikTok live comment recording and streaming."""

import asyncio
import json
from datetime import datetime, timezone

import aiohttp
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db_config import get_live_db_async
from app.core.websocket import websocket_manager
from app.models.comment_table import CommentRecord
from app.models.watchlist_table import Watchlist
from utils.logger import Logger

logger = Logger(__name__)
settings = get_settings()

HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_SERVER_ERROR = 500

MAX_RETRIES = 3
RETRY_DELAY = 5
CHUNK_SIZE = 1024
LOG_INTERVAL = 100
MAX_ERROR_LENGTH = 200
CONNECT_TIMEOUT = 30
READ_TIMEOUT = 300


def _handle_recording_error(error_type: str, status_code: int, error_text: str) -> None:
    """Handle recording errors by raising appropriate HTTP exception.

    Args:
        error_type: Type of error (start/restart)
        status_code: HTTP status code
        error_text: Error message from the response

    """
    raise HTTPException(
        status_code=status_code,
        detail=f"Failed to {error_type} recording: {error_text}",
    )


async def start_comment_recording(
    username: str,
    stream_id: str,
    user_id: str,
    db: AsyncSession,
) -> dict:
    """Start recording TikTok live comments."""
    logger.info(
        "Starting comment recording for user %s with stream_id %s",
        username,
        stream_id,
    )

    # Check watchlist entry
    result = await db.execute(
        select(Watchlist).where(Watchlist.user_handle == username),
    )
    watchlist_entry = result.scalar_one_or_none()

    if watchlist_entry is None:
        raise HTTPException(status_code=HTTP_NOT_FOUND, detail="User not in watchlist")

    try:
        async with aiohttp.ClientSession() as session:
            url = f"{settings.TIKTOK_API_BASE_URL}/tiktok/live/comments/start-streaming"
            params = {"username": username, "user_id": user_id}

            async with session.post(url, params=params) as response:
                if response.status == HTTP_BAD_REQUEST:
                    error_text = await response.text()
                    if "Recording already in progress" in error_text:
                        logger.info(
                            "Recording already in progress for %s, stopping and restarting...",
                            username,
                        )

                        try:
                            await stop_comment_recording(username, user_id, db)
                            await asyncio.sleep(2)

                            async with session.post(
                                url,
                                params=params,
                            ) as retry_response:
                                if retry_response.status != HTTP_OK:
                                    retry_error = await retry_response.text()
                                    logger.exception(
                                        "Failed to restart recording after stop: %s",
                                        retry_error,
                                    )
                                    _handle_recording_error(
                                        "restart",
                                        retry_response.status,
                                        retry_error,
                                    )

                                logger.info(
                                    "Successfully restarted recording for %s",
                                    username,
                                )
                        except Exception as e:
                            logger.exception("Error during stop-restart sequence")
                            raise HTTPException(
                                status_code=HTTP_SERVER_ERROR,
                                detail=f"Failed to restart recording: {e!s}",
                            ) from e
                elif response.status != HTTP_OK:
                    error_text = await response.text()
                    logger.exception("Failed to start recording: %s", error_text)
                    _handle_recording_error("start", response.status, error_text)

        # Update database flag and start comment stream
        watchlist_entry.is_comment_recording = True
        await db.commit()

        # Start the comment stream handler
        task = asyncio.create_task(
            handle_comment_stream(username, stream_id, user_id, db),
        )

        task.set_name(f"comment_stream_{username}")

    except Exception as e:
        watchlist_entry.is_comment_recording = False
        await db.commit()
        logger.exception("Error in start_comment_recording")
        raise HTTPException(
            status_code=HTTP_SERVER_ERROR,
            detail=f"Failed to start comment recording: {e!s}",
        ) from e
    else:
        logger.info("Comment recording started successfully for %s", username)
        return {
            "message": f"Comment recording started successfully for {username}",
            "stream_id": stream_id,
        }


async def handle_comment_stream(  # noqa: C901, PLR0911, PLR0912, PLR0915
    username: str,
    stream_id: str,
    user_id: str,
    db: AsyncSession,  # noqa: ARG001
) -> None:
    """Handle TikTok comment stream connection and processing."""
    logger.info("Initializing comment stream handler for %s", username)

    timeout = aiohttp.ClientTimeout(
        total=None,
        connect=CONNECT_TIMEOUT,
        sock_read=READ_TIMEOUT,
        sock_connect=CONNECT_TIMEOUT,
    )

    retry_count = 0

    while retry_count < MAX_RETRIES:
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"{settings.TIKTOK_API_BASE_URL}/tiktok/live/comments/start-streaming"
                params = {"username": username, "user_id": user_id}

                logger.info("Connecting to comment stream API for %s", username)
                async with session.post(url, params=params) as response:
                    if response.status != HTTP_OK:
                        error_text = await response.text()
                        truncated = error_text.encode("ascii", errors="replace").decode(
                            "ascii",
                        )[:MAX_ERROR_LENGTH]
                        logger.error(
                            "Failed to connect to comment stream for %s. Status: %s, Response: %s",
                            username,
                            response.status,
                            truncated,
                        )

                        if (
                            response.status == HTTP_BAD_REQUEST
                            and "Recording already in progress" in error_text
                        ):
                            logger.error(
                                "TikTok says recording is already in progress for %s. Stopping.",
                                username,
                            )
                            return

                        retry_count += 1
                        if retry_count < MAX_RETRIES:
                            logger.info(
                                "Retry %s/%s in %s seconds.",
                                retry_count,
                                MAX_RETRIES,
                                RETRY_DELAY,
                            )
                            await asyncio.sleep(RETRY_DELAY)
                            continue
                        return

                    logger.info(
                        "Successfully connected to comment stream for %s",
                        username,
                    )
                    comment_count = 0

                    async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                        try:
                            if not chunk:
                                continue

                            chunk_text = chunk.decode("utf-8")
                            lines = chunk_text.strip().split("\n")

                            for line in lines:
                                if not line or not line.startswith("data: "):
                                    continue

                                try:
                                    json_str = line[6:]
                                    comment_data = json.loads(json_str)

                                    if (
                                        "message" in comment_data
                                        and "has stopped" in comment_data["message"]
                                    ):
                                        logger.info(
                                            "Received stop message for %s",
                                            username,
                                        )
                                        return

                                    comment_count += 1
                                    if comment_count % LOG_INTERVAL == 0:
                                        logger.info(
                                            "Processed %s comments for %s",
                                            comment_count,
                                            username,
                                        )

                                    await save_comment_to_db(
                                        stream_id,
                                        username,
                                        comment_data,
                                    )

                                    await websocket_manager.broadcast_to_stream(
                                        stream_id,
                                        {
                                            "type": "comment",
                                            "data": comment_data,
                                        },
                                    )

                                except json.JSONDecodeError:
                                    logger.debug(
                                        "Received invalid JSON in comment stream",
                                    )
                                    continue

                        except UnicodeDecodeError:
                            logger.debug(
                                "Received invalid UTF-8 data in comment stream",
                            )
                            continue
                        except Exception:
                            logger.exception(
                                "Error processing comment chunk for %s",
                                username,
                            )
                            continue

                    # If the async for loop ends naturally, we exit.
                    logger.info("Comment stream ended naturally for %s", username)
                    return

        except asyncio.TimeoutError:
            logger.warning("Comment stream timed out for %s", username)
            retry_count += 1
            if retry_count < MAX_RETRIES:
                logger.info(
                    "Retrying comment stream in %s seconds... (Attempt %s/%s)",
                    RETRY_DELAY,
                    retry_count,
                    MAX_RETRIES,
                )
                await asyncio.sleep(RETRY_DELAY)
                continue
            return

        except asyncio.CancelledError:
            logger.info("Comment stream cancelled for %s", username)
            return

        except Exception:
            logger.exception("Error in comment stream for %s", username)
            retry_count += 1
            if retry_count < MAX_RETRIES:
                logger.info(
                    "Retrying in %s seconds... (Attempt %s/%s)",
                    RETRY_DELAY,
                    retry_count,
                    MAX_RETRIES,
                )
                await asyncio.sleep(RETRY_DELAY)
                continue
            return


async def stop_comment_recording(username: str, user_id: str, db: AsyncSession) -> dict:
    """Stop recording TikTok live comments and reset the recording flag."""
    logger.info("Stopping comment recording for %s", username)

    result = await db.execute(
        select(Watchlist).where(Watchlist.user_handle == username),
    )
    watchlist_entry = result.scalar_one_or_none()
    if watchlist_entry is None:
        raise HTTPException(status_code=HTTP_NOT_FOUND, detail="User not in watchlist")

    try:
        async with aiohttp.ClientSession() as session:
            url = f"{settings.TIKTOK_API_BASE_URL}/tiktok/live/comments/stop-streaming"
            params = {"username": username, "user_id": user_id}

            async with session.post(url, params=params) as response:
                error_text = None
                if response.status != HTTP_OK:
                    error_text = await response.text()
                    logger.exception("Failed to stop recording: %s", error_text)

                watchlist_entry.is_comment_recording = False
                await db.commit()

                if error_text:
                    _handle_recording_error("stop", response.status, error_text)

                logger.info("Successfully stopped comment recording for %s", username)
                return {
                    "message": f"Comment recording stopped successfully for {username}",
                }

    except Exception as e:
        watchlist_entry.is_comment_recording = False
        await db.commit()
        logger.exception("Error in stop_comment_recording")
        raise HTTPException(
            status_code=HTTP_SERVER_ERROR,
            detail=f"Failed to stop comment recording: {e!s}",
        ) from e


async def save_comment_to_db(stream_id: str, username: str, comment: dict) -> None:
    """Save one comment to the DB."""
    try:
        async with get_live_db_async() as async_session:
            comment_record = CommentRecord(
                StreamId=stream_id,
                Username=username,
                Comment=json.dumps(comment),
                Timestamp=datetime.now(timezone.utc),
            )
            async_session.add(comment_record)
            await async_session.commit()
    except Exception:
        logger.exception("Failed to save comment")
        raise


async def setup_comment_websocket(
    websocket: aiohttp.ClientWebSocketResponse,
    stream_id: str,
) -> None:
    """Set up WebSocket connection for comment streaming.

    Args:
        websocket: The WebSocket connection
        stream_id: The ID of the stream

    """
    await websocket_manager.connect_live_stream(stream_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        logger.exception("WebSocket error")
    finally:
        await websocket_manager.disconnect_live_stream(stream_id, websocket)
