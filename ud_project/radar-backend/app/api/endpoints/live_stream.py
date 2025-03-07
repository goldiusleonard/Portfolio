"""FastAPI router module for handling live stream functionality and WebSocket connections."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.orm import Session  # noqa: TCH002

from app.api.endpoints.functions import live_stream_function
from app.core.config import get_settings
from app.core.db_config import get_live_db, get_mcmc_db
from app.core.websocket import websocket_manager
from utils.logger import Logger


class ChunkData(BaseModel):
    """Data model for stream chunk processing."""

    stream_id: str
    chunk_number: int
    transcription: dict
    caption: dict
    justification: dict
    risk_level: str


settings = get_settings()
logger = Logger(__name__)
live_stream_module = APIRouter()


@live_stream_module.post("/start_stream/")
async def start_stream(
    username: str,
    user_id: int,
    live_db: Session = Depends(get_live_db),
    stream_id: str | None = None,
) -> dict[str, Any]:
    """Start a new live stream."""
    if not stream_id:
        stream_id = str(uuid.uuid4())

    result = await live_stream_function.start_live_stream(
        username=username,
        stream_id=stream_id,
        user_id=str(user_id),
        live_db=live_db,
    )

    return {
        "message": "Live stream started successfully",
        "stream_id": stream_id,
        "details": result,
    }


@live_stream_module.post("/process_chunk/")
async def process_chunk(
    stream_id: str,
    chunk_number: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_live_db),
) -> dict[str, Any]:
    """Process an uploaded stream chunk."""
    chunk_data = await file.read()
    return await live_stream_function.process_stream_chunk(
        stream_id=stream_id,
        chunk_number=chunk_number,
        chunk_data=chunk_data,
        db=db,
    )


@live_stream_module.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket) -> None:
    """WebSocket endpoint for receiving global notifications about live streams."""
    logger.info("Notification WebSocket connection attempt received")

    await websocket_manager.connect_notifications(websocket)

    try:
        await websocket.send_json(
            {
                "type": "connection_status",
                "status": "connected",
                "total_connections": len(websocket_manager.notification_connections),
            },
        )

        # Keep connection alive
        while True:
            message = await websocket.receive_text()
            logger.info(
                "Received websocket message: %s. Active connections: %d",
                message,
                len(websocket_manager.notification_connections),
            )
            # Echo back
            await websocket.send_json(
                {
                    "type": "acknowledgment",
                    "message": f"Received: {message}",
                    "total_connections": len(
                        websocket_manager.notification_connections,
                    ),
                },
            )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnect detected")
    except Exception:
        logger.exception("WebSocket error")
    finally:
        # Cleanup
        await websocket_manager.disconnect_notifications(websocket)
        logger.info(
            "WebSocket cleanup complete. Remaining connections: %d",
            len(websocket_manager.notification_connections),
        )


@live_stream_module.websocket("/ws/{stream_id}")
async def websocket_endpoint(websocket: WebSocket, stream_id: str) -> None:
    """WebSocket endpoint for receiving real-time updates for a specific live stream."""
    await websocket_manager.connect_live_stream(stream_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await websocket_manager.disconnect_live_stream(stream_id, websocket)
        logger.info("Client disconnected from WebSocket for stream %s.", stream_id)
    except Exception:
        logger.exception("Error in websocket_endpoint for stream %s", stream_id)
        await websocket_manager.disconnect_live_stream(stream_id, websocket)


@live_stream_module.post("/stop_stream/")
async def stop_stream(
    username: str,
    user_id: int,
    stream_id: str,
    live_db: Session = Depends(get_live_db),
) -> dict:
    """Stop a live stream."""
    return await live_stream_function.stop_live_stream(
        username=username,
        user_id=user_id,
        stream_id=stream_id,
        db=live_db,
    )


@live_stream_module.get("/details/{stream_id}")
def get_live_stream_details(
    stream_id: str,
    live_db: Session = Depends(get_live_db),
    mcmc_db: Session = Depends(get_mcmc_db),
) -> dict:
    """Get detailed information about a specific live stream."""
    return live_stream_function.get_live_stream_details(
        stream_id=stream_id,
        live_db=live_db,
        mcmc_db=mcmc_db,
    )
