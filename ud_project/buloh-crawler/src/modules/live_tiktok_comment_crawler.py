from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from asyncio import Queue
from datetime import datetime
from ..utils import Logger, get_env_variable
from dotenv import load_dotenv
from ..tiktok_comment_recorder import (
    create_tiktok_client,
    setup_client_events,
    run_client_in_thread,
    comment_stream,
)
from ..tiktok_live_recorder import is_user_in_live, get_room_id_from_user
from ..modules.live_tiktok_video_crawler import redis_client
from redis import ConnectionError
import asyncio
import logging
import json
import threading
import time
import traceback

load_dotenv()

log = Logger(name="database_logger")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

active_comment_sessions: dict = {}

comment_channel_name: str = get_env_variable(
    "COMMENT_CHANNEL_NAME", "Video channel name is not provided!"
)

shutdown_flag = False


async def handle_stop_message(message):
    """Handle incoming stop message from other replicas."""
    message_data = json.loads(message["data"])
    action = message_data.get("action")
    user_id = message_data.get("user_id")
    username = message_data.get("username")

    if action == "STOP":
        if (
            user_id in active_comment_sessions
            and username in active_comment_sessions[user_id]
        ):
            active_comment_sessions[user_id].remove(username)

            if not active_comment_sessions[user_id]:
                del active_comment_sessions[user_id]

            redis_client.publish(
                comment_channel_name,
                json.dumps(
                    {"action": "STOPPED", "user_id": user_id, "username": username}
                ),
            )
        else:
            redis_client.publish(
                comment_channel_name,
                json.dumps(
                    {"action": "NOT_FOUND", "user_id": user_id, "username": username}
                ),
            )

    elif action == "REMOVE_ALL_SESSIONS":
        try:
            active_comment_sessions.clear()
            logger.info("Sessions cleared by replica.")

            redis_client.publish(
                comment_channel_name, json.dumps({"action": "REMOVE_ALL_SESSIONS_ACK"})
            )
        except Exception as e:
            logger.error(f"Error removing sessions: {str(e)}")
            redis_client.publish(
                comment_channel_name,
                json.dumps({"action": "REMOVE_ALL_SESSIONS_FAILED"}),
            )


def connect_redis_channel():
    """Reconnects to Redis and resubscribe to the channel."""
    global redis_client

    pubsub = redis_client.pubsub()
    pubsub.subscribe(comment_channel_name)
    logger.info(f"Connected to Redis Pub/Sub {comment_channel_name}.")
    return pubsub


def subscribe_to_stop_channel():
    """Subscribe to the Redis channel for receiving stop messages from other replicas."""
    pubsub = connect_redis_channel()

    while not shutdown_flag:
        try:
            message = pubsub.get_message()
            if message and message["type"] == "message":
                asyncio.run(handle_stop_message(message))
            time.sleep(1)

        except (ConnectionError, OSError) as e:
            logger.error(f"Connection error while reading from Redis: {e}")
            time.sleep(2)
            pubsub = connect_redis_channel()

        except ValueError as e:
            logger.error(f"ValueError: {e}. Attempting to reconnect to Redis.")
            time.sleep(2)
            pubsub = connect_redis_channel()

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            break

    pubsub.unsubscribe(comment_channel_name)
    pubsub.close()
    logger.info(f"Closed Redis Pub/Sub for comment channel: {comment_channel_name}.")


def start_comment_channel():
    """Start the Redis Pub/Sub listener in a background thread."""
    thread = threading.Thread(target=subscribe_to_stop_channel)
    thread.daemon = True
    thread.start()


def close_comment_channel():
    """Clean up Redis Pub/Sub connection and close the Redis client."""
    global shutdown_flag
    shutdown_flag = True


@router.post("/live/comments/start-streaming")
def start_live_comment_streaming(username: str, user_id: str):
    """Start the TikTokLiveClient stream for a specific unique_id and user_id."""

    start_time = datetime.now().isoformat()

    if (
        user_id in active_comment_sessions
        and username in active_comment_sessions[user_id]
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Recording already in progress for user '{username}' with user ID '{user_id}'.",
        )

    if user_id not in active_comment_sessions:
        active_comment_sessions[user_id] = []

    active_comment_sessions[user_id].append(username)

    for trial in range(3):
        try:
            room_id = get_room_id_from_user(username)
            if not room_id:
                logger.error("Room ID not found for the user.")
                raise HTTPException(
                    status_code=400, detail="Room ID not found for the user."
                )
            break
        except Exception:
            print(traceback.format_exc())

    if not is_user_in_live(room_id):
        logger.error("The user is not currently live.")
        raise HTTPException(status_code=400, detail="The user is not currently live.")

    client = create_tiktok_client(username)
    comments: Queue[str] = asyncio.Queue()

    setup_client_events(
        client, comments, user_id, username, room_id, active_comment_sessions
    )
    run_client_in_thread(client, user_id, username, active_comment_sessions)

    return StreamingResponse(
        comment_stream(
            client,
            comments,
            user_id,
            username,
            room_id,
            active_comment_sessions,
            start_time,
        ),
        media_type="application/json",
    )


@router.post("/live/comments/stop-streaming")
def stop_live_comment_streaming(username: str, user_id: str):
    """Stop the TikTokLiveClient stream for a specific username and user_id"""
    pubsub = connect_redis_channel()

    try:
        if (
            user_id in active_comment_sessions
            and username in active_comment_sessions[user_id]
        ):
            active_comment_sessions[user_id].remove(username)

            if not active_comment_sessions[user_id]:
                del active_comment_sessions[user_id]
                logger.info(f"No active recordings left for user ID '{user_id}'.")

            redis_client.publish(
                comment_channel_name,
                json.dumps(
                    {"action": "STOPPED", "user_id": user_id, "username": username}
                ),
            )

            return {
                "message": f"Stream comments stopped successfully for user '{username}' with user ID '{user_id}'."
            }

        else:
            redis_client.publish(
                comment_channel_name,
                json.dumps(
                    {"action": "STOP", "user_id": user_id, "username": username}
                ),
            )

            stop_confirmed = False
            response_count = 0
            max_wait_time = 15
            start_time = time.time()

            while response_count < 1:
                message = pubsub.get_message()
                if message and message["type"] == "message":
                    message_data = json.loads(message["data"])
                    action = message_data.get("action")

                    if (
                        action == "STOPPED"
                        and message_data.get("user_id") == user_id
                        and message_data.get("username") == username
                    ):
                        stop_confirmed = True
                        break
                    elif (
                        action == "NOT_FOUND"
                        and message_data.get("user_id") == user_id
                        and message_data.get("username") == username
                    ):
                        response_count += 1
                        logger.info(f"Response count not found: {response_count}")

                elapsed_time = time.time() - start_time
                if elapsed_time > max_wait_time:
                    logger.warning(
                        f"Max wait time of {max_wait_time} seconds exceeded."
                    )
                    return {
                        "message": f"Timeout: No response received after {max_wait_time} seconds for user '{username}' with user ID '{user_id}'."
                    }
                time.sleep(2)

            if stop_confirmed:
                return {
                    "message": f"Stream comments stopped successfully for user '{username}' with user ID '{user_id}'."
                }
            else:
                return {
                    "message": f"No active recording session for tiktok username '{username}' from '{user_id}' user ID."
                }
    finally:
        pubsub.unsubscribe(comment_channel_name)
        pubsub.close()
        logger.info(f"Disconnected from Redis Pub/Sub {comment_channel_name} channel.")


@router.post("/live/comments/remove-all-sessions")
def remove_all_active_sessions():
    """Remove all active comment sessions across all replicas."""
    pubsub = None
    try:
        pubsub = connect_redis_channel()

        # Clear sessions on this instance first
        global active_comment_sessions
        active_comment_sessions.clear()

        # Broadcast remove sessions message to all replicas
        redis_client.publish(
            comment_channel_name, json.dumps({"action": "REMOVE_ALL_SESSIONS"})
        )

        # Track acknowledgments
        feedback_received = 0
        max_wait_time = 15
        start_time = time.time()

        # Wait for acknowledgment
        while feedback_received < 1:
            message = pubsub.get_message()
            if message and message["type"] == "message":
                message_data = json.loads(message["data"])
                action = message_data.get("action")

                if action == "REMOVE_ALL_SESSIONS_ACK":
                    feedback_received += 1
                    logger.info("Received confirmation of comment sessions cleared")
                elif action == "REMOVE_ALL_SESSIONS_FAILED":
                    logger.error("Failed to clear comment sessions on some replicas")
                    return {
                        "message": "Failed to remove all comment sessions on some replicas."
                    }

            elapsed_time = time.time() - start_time
            if elapsed_time > max_wait_time:
                logger.warning(f"Max wait time of {max_wait_time} seconds exceeded.")
                return {
                    "message": "Timeout: No feedback received after waiting for removal of all sessions."
                }
            time.sleep(0.5)

        if feedback_received == 1:
            logger.info("All active comment sessions have been removed.")
            return {
                "message": "All active comment sessions have been removed successfully."
            }
        else:
            return {
                "message": "Failed to receive feedback for removing all comment sessions."
            }

    except Exception as e:
        logger.error(f"Error in remove_all_active_sessions: {str(e)}")
        return {"message": f"Error removing sessions: {str(e)}"}
    finally:
        if pubsub:
            try:
                pubsub.unsubscribe(comment_channel_name)
                pubsub.close()
                logger.info(
                    f"Disconnected from Redis Pub/Sub {comment_channel_name} channel"
                )
            except Exception as e:
                logger.error(f"Error closing Redis connection: {str(e)}")
