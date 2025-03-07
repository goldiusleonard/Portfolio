"""Functions for watchlist monitoring, handling stream start/end, and recording."""

from __future__ import annotations

import asyncio
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiohttp
import requests
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TCH002

from app.api.endpoints.functions.comment_recording_function import (
    start_comment_recording,
    stop_comment_recording,
)
from app.api.endpoints.functions.live_stream_function import (
    process_stream_chunk,
    stop_recording,
)
from app.core.config import get_settings
from app.core.db_config import get_live_db_async
from app.core.websocket import websocket_manager
from app.models.live_stream_table import LiveStream
from app.models.notification_table import Notification
from app.models.watchlist_table import Watchlist
from utils.logger import Logger

settings = get_settings()
logger = Logger(__name__)

monitoring_task = None
background_tasks = set()

HTTP_OK = 200


def _raise_http_error(status_code: int, detail: str) -> None:
    """Raise an HTTPException for consistent usage (addresses TRY301)."""
    raise HTTPException(status_code=status_code, detail=detail)


async def get_user_image(db: AsyncSession, username: str) -> str | None:
    """Help to get user image URL."""
    user = await db.execute(select(Watchlist).filter_by(user_handle=username))
    return user.scalar_one_or_none().creator_photo_link if user else None


async def initialize_monitoring() -> None:
    """Initialize the watchlist monitoring task."""
    global monitoring_task  # noqa: PLW0603
    if monitoring_task is None:
        logger.info("Initializing watchlist monitoring.")
        monitoring_task = asyncio.create_task(monitor_watchlist())
    else:
        logger.warning("Watchlist monitoring is already running.")


async def shutdown_monitoring() -> None:
    """Shutdown the watchlist monitoring task."""
    global monitoring_task  # noqa: PLW0603
    if monitoring_task:
        logger.info("Shutting down watchlist monitoring.")
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            logger.info("Watchlist monitoring task cancelled successfully.")
        monitoring_task = None
    else:
        logger.warning("No watchlist monitoring task to shut down.")


async def check_live_status(
    username: str,
    session: aiohttp.ClientSession,
) -> dict[str, Any]:
    """Check if a user is live using an external API."""
    try:
        url = f"{settings.TIKTOK_API_BASE_URL}/tiktok/live/user/status"
        logger.info("Checking live status for %s at %s", username, url)

        headers = {
            "accept": "application/json",
        }

        async with session.get(
            url,
            params={"username": username},
            headers=headers,
        ) as response:
            if response.status != HTTP_OK:
                response_text = await response.text()
                logger.exception(
                    "Failed to check live status for %s: Status %d, Response: %s",
                    username,
                    response.status,
                    response_text,
                )
                return {"data": {"alive": False}}  # Return safe default

            data = await response.json()
            return data.get("data", {})

    except aiohttp.ClientConnectorError:
        logger.exception("Connection error checking live status for %s", username)
        return {"data": {"alive": False}}
    except asyncio.TimeoutError:
        logger.exception("Timeout checking live status for %s", username)
        return {"data": {"alive": False}}
    except Exception:
        logger.exception("Failed to check live status for %s", username)
        return {"data": {"alive": False}}


async def monitor_watchlist() -> None:
    """Monitor watchlist users for live status."""
    try:
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    async with get_live_db_async() as db:
                        result = await db.execute(
                            select(Watchlist),
                        )
                        watchlist = result.scalars().all()

                        for user in watchlist:
                            try:
                                live_status = await check_live_status(
                                    user.user_handle,
                                    session,
                                )
                                is_live = live_status.get("alive", False)

                                if is_live and not user.is_live:
                                    await handle_stream_start(
                                        user.user_handle,
                                        db,
                                        live_status.get("room_id"),
                                    )
                                elif not is_live and user.is_live:
                                    await handle_stream_end(user.user_handle, db)
                            except Exception:  # noqa: PERF203
                                logger.exception(
                                    "Error processing %s",
                                    user.user_handle,
                                )

                except SQLAlchemyError:
                    logger.exception("Database error in monitor_watchlist loop")
                except Exception:
                    logger.exception("Error in monitor_watchlist loop: %s")
                await asyncio.sleep(settings.POLLING_INTERVAL)
    except asyncio.CancelledError:
        logger.info("monitor_watchlist task received cancellation.")
    except Exception as e:  # noqa: BLE001
        logger.critical("Fatal error in monitor_watchlist: %s", e)


async def handle_stream_start(  # noqa: PLR0915, C901
    username: str,
    db: AsyncSession,
    room_id: str | None = None,
) -> dict[str, Any]:
    """Handle stream start event for a user."""
    try:
        # Generate or use provided stream_id right at the start
        stream_id = (
            room_id
            if room_id
            else f"auto_{settings.TIKTOK_API_USER_ID}_{int(datetime.now(timezone.utc).timestamp())}"
        )

        watchlist_user = await db.execute(
            select(Watchlist)
            .where(Watchlist.user_handle == username)
            .with_for_update(),
        )
        watchlist_user = watchlist_user.scalar_one_or_none()

        if not watchlist_user:
            logger.error("Watchlist entry for %s not found", username)
            _raise_http_error(404, f"User {username} not in watchlist")

        if watchlist_user.is_live:
            logger.warning("User %s already marked as live", username)
        else:
            watchlist_user.is_live = True
            await db.flush()

        # Check for existing stream with lock
        existing_stream = await db.execute(
            select(LiveStream)
            .where(LiveStream.StreamId == stream_id)
            .with_for_update(),
        )
        existing_stream = existing_stream.scalar_one_or_none()

        # Handle existing stream scenario
        if existing_stream:
            # Stop existing recordings if stream is active
            if existing_stream.Status == "active":
                logger.info("Stopping existing recordings for %s", stream_id)
                try:
                    await stop_recording(username, settings.TIKTOK_API_USER_ID)
                    await stop_comment_recording(
                        username,
                        settings.TIKTOK_API_USER_ID,
                        db,
                    )
                except Exception as exc:
                    logger.exception("Error handling duplicate stream")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to handle duplicate stream: {exc!s}",
                    ) from exc

                # Cancel any orphaned tasks
                tasks_to_cancel = [
                    t
                    for t in background_tasks
                    if t.get_name() == f"recording_{stream_id}"
                ]
                for task in tasks_to_cancel:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        logger.info("Cancelled orphaned task for %s", stream_id)

            # Reactivate stream
            existing_stream.Status = "active"
            existing_stream.EndTime = None
            notification_sent = existing_stream.notification_sent

        else:
            # Create new stream entry
            existing_stream = LiveStream(
                Username=username,
                StreamId=stream_id,
                Status="active",
                StartTime=datetime.now(timezone.utc),
                notification_sent=False,
            )
            db.add(existing_stream)
            notification_sent = False

        await db.flush()

        # Send notification only if not previously sent
        if not notification_sent:
            message = {
                "type": "live_notification",
                "data": {
                    "username": username,
                    "is_live": True,
                    "stream_id": stream_id,
                    "datetime": datetime.now(timezone.utc).isoformat(),
                    "image_url": (await get_user_image(db, username)),
                },
            }
            await websocket_manager.broadcast_notification(message)
            existing_stream.notification_sent = True

        await db.commit()

        # Start new recordings
        await start_comment_recording(
            username,
            stream_id,
            settings.TIKTOK_API_USER_ID,
            db,
        )
        await asyncio.sleep(1)
        task = asyncio.create_task(
            start_recording(username, stream_id),
            name=f"recording_{stream_id}",
        )
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

        return {"stream_id": stream_id, "status": "restarted" if room_id else "started"}  # noqa: TRY300

    except SQLAlchemyError:
        logger.exception("Database error in handle_stream_start for %s", username)
        await db.rollback()
        raise
    except Exception:
        logger.exception("Exception in handle_stream_start for %s", username)
        await db.rollback()
        raise


def get_video_metadata(file_path: Path) -> str | None:
    """Retrieve the metadata (comment) from the video file."""
    try:
        command = [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "format_tags=comment",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            file_path,
        ]

        result = subprocess.check_output(command, stderr=subprocess.STDOUT)  # noqa: S603

        return result.decode("utf-8").strip()
    except subprocess.CalledProcessError as exc:
        logger.warning("Error retrieving metadata via ffprobe: %s", exc.output.decode())
        return None


async def start_recording(username: str, stream_id: str) -> None:  # noqa: PLR0915,C901
    """Start recording a TikTok live stream with file-based chunk processing."""
    try:
        save_interval = 5
        chunk_size = 10485760  # 10MB

        async with get_live_db_async() as db:
            result = await db.execute(
                select(LiveStream.last_chunk_number).where(
                    LiveStream.StreamId == stream_id,
                ),
            )
            chunk_number = result.scalar() or 1

        # Create download directory
        download_dir = Path(f"recordings/client_videos/{stream_id}")
        download_dir.mkdir(parents=True, exist_ok=True)

        url = f"{settings.TIKTOK_API_BASE_URL}/tiktok/live/video/start-recording"
        params = {
            "username": username,
            "user_id": settings.TIKTOK_API_USER_ID,
            "save_interval": save_interval,
        }

        logger.info("Starting recording for %s", username)

        try:
            with requests.post(  # noqa: ASYNC210, S113
                url,
                params=params,
                stream=True,
                verify=False,  # noqa: S501
            ) as response:
                if response.status_code != HTTP_OK:
                    logger.error(
                        "Failed to start streaming: %d | Response: %s",
                        response.status_code,
                        response.text,
                    )
                    return

                logger.info("Streaming started successfully for %s", username)

                comment_text = ""

                # Process chunks continuously
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if not chunk:
                        continue

                    logger.info("Processing chunk %d for %s...", chunk_number, username)
                    # Save the chunk
                    chunk_filename = download_dir / f"chunk_{chunk_number}.mp4"
                    with chunk_filename.open("wb") as f:
                        f.write(chunk)
                    logger.info("Saved chunk to %s", chunk_filename)

                    try:
                        async with get_live_db_async() as chunk_db:
                            await process_stream_chunk(
                                stream_id=stream_id,
                                chunk_data=chunk,
                                chunk_number=chunk_number,
                                db=chunk_db,
                            )

                    finally:
                        comment_text = get_video_metadata(chunk_filename)
                        if comment_text:
                            try:
                                metadata_json = json.loads(comment_text)
                                if "full_video_url" in metadata_json:
                                    async with get_live_db_async() as url_db:
                                        # Update the LiveStream table
                                        stmt = (
                                            "UPDATE LiveStream SET FullVideoUrl = :url "
                                            "WHERE StreamId = :stream_id AND Status = 'active'"
                                        )
                                        await url_db.execute(
                                            stmt,
                                            {
                                                "url": metadata_json["full_video_url"],
                                                "stream_id": stream_id,
                                            },
                                        )
                                        await url_db.commit()
                                        logger.info(
                                            "Updated FullVideoUrl for stream %s in chunk %d",
                                            stream_id,
                                            chunk_number,
                                        )

                            except json.JSONDecodeError:
                                logger.warning(
                                    "Invalid JSON in metadata for stream %s in chunk %d",
                                    stream_id,
                                    chunk_number,
                                )
                            except Exception:
                                logger.exception(
                                    "Error updating FullVideoUrl in chunk %d",
                                    chunk_number,
                                )

                        if chunk_filename.exists():
                            chunk_filename.unlink()
                            logger.info("Cleaned up chunk file %s", chunk_filename)

                    async with get_live_db_async() as update_db:
                        await update_db.execute(
                            update(LiveStream)
                            .where(LiveStream.StreamId == stream_id)
                            .values(last_chunk_number=chunk_number),
                        )
                        await update_db.commit()

                    chunk_number += 1

        except Exception:
            logger.exception("Error processing chunks")

    except Exception as e:
        logger.exception("Final recording error")
        _raise_http_error(500, f"Recording failed: {e!s}")


async def handle_stream_end(username: str, db: AsyncSession) -> None:  # noqa: PLR0915
    """Handle stream end event."""
    try:
        result = await db.execute(
            select(Watchlist)
            .where(Watchlist.user_handle == username)
            .with_for_update(),
        )
        user = result.scalar_one_or_none()
        if not user:
            logger.error("Watchlist entry for %s not found.", username)
            _raise_http_error(404, f"Watchlist entry for {username} not found")

        user.is_live = False
        await db.flush()

        # Update LiveStream status
        live_stream_result = await db.execute(
            select(LiveStream)
            .where(LiveStream.Username == username, LiveStream.Status == "active")
            .with_for_update(),
        )
        live_stream = live_stream_result.scalar_one_or_none()

        if live_stream:
            live_stream.Status = "ended"
            live_stream.EndTime = datetime.now(timezone.utc)
            live_stream.notification_sent = False

            # Check if we have the full video URL
            if not live_stream.FullVideoUrl:
                logger.warning(
                    "Stream ended without finding full video URL for %s",
                    username,
                )
            else:
                logger.info(
                    "Stream ended with full video URL: %s",
                    live_stream.FullVideoUrl,
                )

            await db.flush()

            try:
                await stop_recording(username, settings.TIKTOK_API_USER_ID)
                logger.info("Video recording stopped for %s", username)
            except Exception:
                logger.exception("Error stopping video recording")

            try:
                await stop_comment_recording(username, settings.TIKTOK_API_USER_ID, db)
                logger.info("Comment recording stopped for %s", username)
            except Exception:
                logger.exception("Error stopping comment recording")

            # Cancel recording tasks
            tasks_to_cancel = [
                t
                for t in background_tasks
                if t.get_name() == f"recording_{live_stream.StreamId}"
            ]
            for task in tasks_to_cancel:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info("Cancelled task for %s", live_stream.StreamId)

            # Create ended notification
            notification = Notification(
                UserId=settings.TIKTOK_API_USER_ID,
                IsNew=True,
                Name=username,
                Status="ended",
                DateTime=datetime.now(timezone.utc),
                LiveDetail=f"{settings.FRONTEND_BASE_URL}/@{username}/live",
                StreamId=live_stream.StreamId,
            )
            db.add(notification)

            message = {
                "type": "live_notification",
                "data": {
                    "username": username,
                    "is_live": False,
                    "stream_id": live_stream.StreamId,
                    "datetime": datetime.now(timezone.utc).isoformat(),
                    "full_video_url": live_stream.FullVideoUrl,
                    "image_url": (await get_user_image(db, username)),
                },
            }
            await websocket_manager.broadcast_notification(message)
            await db.commit()
            logger.info("Notification broadcast complete, message: %s", message)

    except SQLAlchemyError:
        logger.exception("Database error in handle_stream_end for %s", username)
        db.rollback()
        raise
    except Exception:
        logger.exception("Exception in handle_stream_end for %s", username)
        db.rollback()
        raise
