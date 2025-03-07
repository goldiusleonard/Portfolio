"""Websocket server for the live video."""

from __future__ import annotations

from contextlib import suppress
from typing import Any

from fastapi import WebSocket  # noqa: TCH002

from utils.logger import Logger

logger = Logger(__name__)


class WebSocketManager:
    """Manager for handling WebSocket connections for live streams and notifications."""

    def __init__(self) -> None:
        """Initialize a new WebSocketManager instance."""
        self.active_connections: dict[str, list[WebSocket]] = {}
        self.notification_connections: list[WebSocket] = []

    async def connect_notifications(self, websocket: WebSocket) -> None:
        """Add a new WebSocket connection for notifications."""
        await websocket.accept()
        self.notification_connections.append(websocket)
        logger.info("New notification connection established")

    async def disconnect_notifications(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection from the global notifications pool."""
        if websocket in self.notification_connections:
            self.notification_connections.remove(websocket)

    async def broadcast_notification(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all notification connections."""
        initial_count = len(self.notification_connections)
        logger.info(
            "Starting broadcast to %d connections. Message type: %s",
            initial_count,
            message.get("type", "unknown"),
        )

        if initial_count == 0:
            logger.warning(
                "No notification connections available for broadcast: %s",
                message,
            )
            return

        valid_connections: list[WebSocket] = []
        for idx, connection in enumerate(self.notification_connections):
            with suppress(Exception):
                await connection.send_json(message)
                valid_connections.append(connection)
                logger.info(
                    "Successfully sent to connection %d/%d",
                    idx + 1,
                    initial_count,
                )

        removed_count = initial_count - len(valid_connections)
        self.notification_connections = valid_connections

        logger.info(
            "Broadcast complete. Valid: %d, Removed: %d, Message: %s",
            len(valid_connections),
            removed_count,
            message,
        )

    async def connect_live_stream(self, stream_id: str, websocket: WebSocket) -> None:
        """Accept and add a WebSocket connection for a specific live stream."""
        await websocket.accept()
        if stream_id not in self.active_connections:
            self.active_connections[stream_id] = []
        self.active_connections[stream_id].append(websocket)

    async def disconnect_live_stream(
        self,
        stream_id: str,
        websocket: WebSocket,
    ) -> None:
        """Remove a WebSocket connection from a specific live stream."""
        self.active_connections[stream_id].remove(websocket)
        if not self.active_connections[stream_id]:
            del self.active_connections[stream_id]

    async def broadcast_to_stream(
        self,
        stream_id: str,
        message: dict[str, Any],
    ) -> None:
        """Broadcast a message to all WebSocket connections for a specific live stream."""
        if stream_id in self.active_connections:
            for connection in self.active_connections[stream_id]:
                with suppress(Exception):
                    await connection.send_json(message)


# Instantiate a single manager to be used across the application
websocket_manager = WebSocketManager()
