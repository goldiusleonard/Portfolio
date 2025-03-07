import asyncio
import threading
import logging
import time
import warnings
import json
import os

from TikTokLive.client.client import TikTokLiveClient
from TikTokLive.client.web.web_settings import WebDefaults
from TikTokLive.events import ConnectEvent, CommentEvent
from TikTokLive.client.errors import UserOfflineError
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from datetime import datetime
from dotenv import load_dotenv
from ..tiktok_live_recorder import is_user_in_live

logger = logging.getLogger(__name__)
warnings.filterwarnings(
    "ignore", category=Warning, message=".*websockets.exceptions.ConnectionClosedOK.*"
)

load_dotenv()

WebDefaults.tiktok_sign_api_key = os.getenv("SIGN_API_KEY")


def create_tiktok_client(username: str) -> TikTokLiveClient:
    """Create a new TikTok Live client instance."""
    return TikTokLiveClient(
        unique_id=username,
    )


def setup_client_events(
    client, comments, user_id, username, room_id, active_comment_sessions
):
    """Set up event handlers for the TikTok Live client."""

    @client.on(ConnectEvent)
    async def on_connect(event: ConnectEvent):
        logger.info(f"Connected to @{event.unique_id} (Room ID: {client.room_id})")

    @client.on(CommentEvent)
    async def on_comment(event: CommentEvent):
        if (
            user_id not in active_comment_sessions
            or username not in active_comment_sessions[user_id]
            or not is_user_in_live(room_id)
        ):
            await comments.put({"stop": True})
            return

        created_at = datetime.fromtimestamp(event.common.create_time / 1000.0).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        data = {
            "id": event.common.msg_id,
            "text": event.comment,
            "user": {
                "id": event.user.id,
                "sec_uid": event.user.sec_uid,
                "unique_id": event.user.display_id,
                "nickname": event.user.nickname,
                "signature": "",
                "avatar": event.user.avatar_thumb.url_list[1]
                if event.user.avatar_thumb.url_list
                else "",
                "verified": event.user.verified,
                "secret": event.user.secret,
                "aweme_count": 0,
                "following_count": event.user.follow_info.following_count,
                "follower_count": event.user.follow_info.follower_count,
                "total_favorited": 0,
                "ins_id": "",
                "youtube_channel_title": "",
                "youtube_channel_id": "",
                "twitter_name": "",
                "twitter_id": "",
            },
            "create_time": event.common.create_time,
            "digg_count": 0,
            "reply_total": 0,
            "status": 1,
            "updated_at": created_at,
            "created_at": created_at,
            "is_flagged": False,
            "request_id": None,
        }

        try:
            await comments.put(data)
        except Exception as e:
            logger.error(f"Error putting comment in queue: {str(e)}")


def run_client_in_thread(client, user_id, username, active_comment_sessions):
    """Run the TikTok Live client in a separate thread."""

    def run_client():
        try:
            client.run(process_connect_events=False)
        except UserOfflineError:
            logger.error(f"User '{username}' is offline.")
            raise RuntimeError(
                status_code=400,
                detail=f"TikTok user '{username}' is offline or not found",
            )
        except (ConnectionClosedError, ConnectionClosedOK):
            logger.warning("Connection closed unexpectedly")
            try:
                logger.info("Attempting to reconnect...")
                time.sleep(5)
                run_client()
            except Exception as e:
                logger.error(f"Error during reconnection attempt: {str(e)}")
                if (
                    user_id in active_comment_sessions
                    and username in active_comment_sessions[user_id]
                ):
                    active_comment_sessions[user_id].remove(username)

                    if not active_comment_sessions[user_id]:
                        del active_comment_sessions[user_id]
                        logger.info(
                            f"No active recordings left for user ID '{user_id}'."
                        )
        except Exception as e:
            logger.error(f"Error in client run: {str(e)}")
            raise

    client_thread = threading.Thread(target=run_client)
    client_thread.daemon = True
    client_thread.start()


def disconnect_client_sync(client):
    """Synchronously disconnect the TikTok Live client."""
    try:
        # Use asyncio.run to execute the async function in a synchronous context
        asyncio.run(disconnect_client(client))
        logger.info("Client disconnected")
    except asyncio.TimeoutError:
        logger.warning("Disconnect timed out.")
    except Exception as e:
        logger.error(f"Error disconnecting client: {str(e)}")


async def disconnect_client(client):
    """Safely disconnect the TikTok Live client."""
    try:
        await asyncio.wait_for(client.disconnect(), timeout=10.0)
        logger.info("Client disconnected")
    except asyncio.TimeoutError:
        logger.warning("Disconnect timed out.")
    except Exception as e:
        logger.error(f"Error disconnecting client: {str(e)}")


async def comment_stream(
    client, comments, user_id, username, room_id, active_comment_sessions, start_time
):
    """Handle the streaming of comments."""

    try:
        while True:
            if (
                user_id not in active_comment_sessions
                or username not in active_comment_sessions[user_id]
            ):
                logger.info(
                    f"TikTok comment recording for user {username} has stopped."
                )
                data = {
                    "message": f"TikTok comment recording for user {username} has stopped."
                }
                yield f"data: {json.dumps(data)}\n\n"
                break
            if not is_user_in_live(room_id):
                logger.info(
                    f"User {username} has ended the live session. Stopping recording."
                )
                data = {"message": "Live session has ended."}
                yield f"data: {json.dumps(data)}\n\n"
                break

            try:
                data = await asyncio.wait_for(comments.get(), timeout=5.0)
            except asyncio.TimeoutError:
                if not is_user_in_live(room_id):
                    logger.info(
                        f"User {username} has ended the live session. Stopping recording."
                    )
                    data = {"message": "Live session has ended."}
                    yield f"data: {json.dumps(data)}\n\n"
                    break
                else:
                    logger.info(
                        f"User {username} is still live. Waiting for a comment..."
                    )
                    continue

            if data.get("stop"):
                logger.info(
                    f"User {username} has ended the live session. Stopping recording."
                )
                data = {"message": "Live session has ended."}
                yield f"data: {json.dumps(data)}\n\n"
                break

            if data:
                yield f"data: {json.dumps(data)}\n\n"

    except Exception as e:
        if not isinstance(e, ConnectionClosedOK):
            logger.error(f"Error in comment stream: {str(e)}")
    finally:
        await disconnect_client(client)

        data = {
            "message": "Stream comments stopped successfully",
            "user_id": user_id,
            "username": username,
            "start_time": start_time,
            "end_time": datetime.now().isoformat(),
        }
        yield f"data: {json.dumps(data)}\n\n"

        if (
            user_id in active_comment_sessions
            and username in active_comment_sessions[user_id]
        ):
            active_comment_sessions[user_id].remove(username)

            if not active_comment_sessions[user_id]:
                del active_comment_sessions[user_id]
                logger.info(f"No active recordings left for user ID '{user_id}'.")
