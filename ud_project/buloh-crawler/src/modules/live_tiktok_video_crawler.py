import logging
import redis
import json

from fastapi.responses import StreamingResponse
from ..tiktok_live_recorder import (
    get_live_url,
    is_country_blacklisted,
    get_room_id_from_user,
    start_recording,
    is_user_in_live,
    stream_live_video,
)
from fastapi import HTTPException, APIRouter, Request
from ..utils import Logger, get_env_variable
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv
from redis import ConnectionError
import asyncio
import threading
import time
import traceback

load_dotenv()

log = Logger(name="database_logger")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

active_video_sessions: dict = {}

redis_host: str = get_env_variable("REDIS_HOST", "Redis host is not provided!")
redis_port: int = int(get_env_variable("REDIS_PORT", "Redis port is not provided!"))
redis_password: str = get_env_variable(
    "REDIS_PASSWORD", "Redis password is not provided!"
)
video_channel_name: str = get_env_variable(
    "VIDEO_CHANNEL_NAME", "Video channel name is not provided!"
)

redis_client = redis.Redis(
    host=redis_host,
    port=redis_port,
    decode_responses=True,
    password=redis_password,
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
            user_id in active_video_sessions
            and username in active_video_sessions[user_id]
        ):
            active_video_sessions[user_id].remove(username)

            if not active_video_sessions[user_id]:
                del active_video_sessions[user_id]

            redis_client.publish(
                video_channel_name,
                json.dumps(
                    {"action": "STOPPED", "user_id": user_id, "username": username}
                ),
            )
        else:
            redis_client.publish(
                video_channel_name,
                json.dumps(
                    {"action": "NOT_FOUND", "user_id": user_id, "username": username}
                ),
            )

    elif action == "REMOVE_ALL_SESSIONS":
        try:
            # Clear all sessions on this replica
            active_video_sessions.clear()
            logger.info("Sessions cleared by REMOVE_ALL_SESSIONS command")

            # Send acknowledgment
            redis_client.publish(
                video_channel_name, json.dumps({"action": "REMOVE_ALL_SESSIONS_ACK"})
            )
        except Exception as e:
            logger.error(f"Error removing all sessions: {str(e)}")
            redis_client.publish(
                video_channel_name,
                json.dumps({"action": "REMOVE_ALL_SESSIONS_FAILED", "error": str(e)}),
            )


def connect_redis_channel():
    """Reconnects to Redis and resubscribe to the channel."""
    global redis_client

    pubsub = redis_client.pubsub()
    pubsub.subscribe(video_channel_name)
    logger.info(f"Connected to Redis Pub/Sub {video_channel_name}.")
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

    pubsub.unsubscribe(video_channel_name)
    pubsub.close()
    logger.info(f"Closed Redis Pub/Sub for video channel: {video_channel_name}.")


def start_video_channel():
    """Start the Redis Pub/Sub listener in a background thread."""
    thread = threading.Thread(target=subscribe_to_stop_channel)
    thread.daemon = True
    thread.start()


def close_video_channel():
    """Clean up Redis Pub/Sub connection and close the Redis client."""
    global shutdown_flag
    shutdown_flag = True


@router.post("/live/video/start-recording")
def start_live_video_recording(username: str, user_id: str, save_interval: int):
    """
    Start recording the live stream.
    """
    start_time = datetime.now().isoformat()

    if user_id in active_video_sessions and username in active_video_sessions[user_id]:
        raise HTTPException(
            status_code=400,
            detail=f"Recording already in progress for user '{username}' with user ID '{user_id}'.",
        )

    if user_id not in active_video_sessions:
        active_video_sessions[user_id] = []

    active_video_sessions[user_id].append(username)

    is_blacklisted = is_country_blacklisted(username)
    if is_blacklisted:
        logger.error("The user is in a blacklisted country.")
        raise HTTPException(
            status_code=400, detail="The user is in a blacklisted country."
        )

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

    logger.info(f"Room ID retrieved: {room_id}")

    live_url = get_live_url(room_id)
    if not live_url:
        logger.error("Live URL not found.")
        raise HTTPException(status_code=400, detail="Live URL not found.")

    logger.info(f"Live URL retrieved: {live_url}")

    try:
        logger.info("Start Recording...")

        return StreamingResponse(
            start_recording(
                username,
                live_url,
                save_interval,
                user_id,
                room_id,
                active_video_sessions,
                start_time,
            ),
            media_type="video/mp4",
        )

    except Exception:
        logger.error("An error occurred while processing the request.")
        raise HTTPException(
            status_code=500, detail="An error occurred while processing the request."
        )


@router.post("/live/video/stop-recording")
def stop_live_video_recording(username: str, user_id: str):
    """
    Stop recording the live stream for a specific user.
    """
    pubsub = connect_redis_channel()

    try:
        if (
            user_id in active_video_sessions
            and username in active_video_sessions[user_id]
        ):
            active_video_sessions[user_id].remove(username)

            if not active_video_sessions[user_id]:
                del active_video_sessions[user_id]
                logger.info(f"No active recordings left for user ID '{user_id}'.")

            redis_client.publish(
                video_channel_name,
                json.dumps(
                    {"action": "STOPPED", "user_id": user_id, "username": username}
                ),
            )

            return {
                "message": f"Stream videos stopped successfully for user '{username}' with user ID '{user_id}'."
            }

        else:
            redis_client.publish(
                video_channel_name,
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
                time.sleep(1)

            if stop_confirmed:
                return {
                    "message": f"Stream videos stopped successfully for user '{username}' with user ID '{user_id}'."
                }
            else:
                return {
                    "message": f"No active recording session for tiktok username '{username}' from '{user_id}' user ID."
                }
    finally:
        pubsub.unsubscribe(video_channel_name)
        pubsub.close()
        logger.info(f"Disconnected from Redis Pub/Sub {video_channel_name} channel.")


class CheckAliveResponse(BaseModel):
    alive: bool
    username: str
    room_id: str


@router.get("/live/user/status")
def check_user_live_status(username: str):
    room_id = get_room_id_from_user(username)

    if not room_id:
        alive = False
        room_id = "none"
    else:
        if not is_user_in_live(room_id):
            alive = False
        else:
            alive = True

    return {"data": CheckAliveResponse(alive=alive, username=username, room_id=room_id)}


@router.get("/live/video/stream-display")
def stream_live_video_display(request: Request, username: str):
    """
    API Endpoint that streams FLV video chunks for a given username.
    """
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

    logger.info(f"Room ID retrieved: {room_id}")

    live_url = get_live_url(room_id)
    if not live_url:
        logger.error("Live URL not found.")
        raise HTTPException(status_code=400, detail="Live URL not found.")

    logger.info(f"Live URL retrieved: {live_url}")

    try:
        return StreamingResponse(
            stream_live_video(live_url, request), media_type="video/x-flv"
        )

    except Exception:
        logger.error("An error occurred while processing the request.")
        raise HTTPException(
            status_code=500, detail="An error occurred while processing the request."
        )


@router.post("/live/video/remove-all-sessions")
def remove_all_active_sessions():
    """Remove all active video sessions across all replicas."""
    pubsub = None
    try:
        pubsub = connect_redis_channel()

        # Clear sessions on this instance
        global active_video_sessions
        active_video_sessions.clear()

        # Broadcast remove sessions message to all replicas
        redis_client.publish(
            video_channel_name, json.dumps({"action": "REMOVE_ALL_SESSIONS"})
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
                    logger.info("Received confirmation of sessions cleared")
                elif action == "REMOVE_ALL_SESSIONS_FAILED":
                    logger.error("Failed to clear sessions on some replicas")
                    return {
                        "message": "Failed to remove all video sessions on some replicas."
                    }

            elapsed_time = time.time() - start_time
            if elapsed_time > max_wait_time:
                logger.warning(f"Max wait time of {max_wait_time} seconds exceeded.")
                return {
                    "message": "Timeout: No feedback received after waiting for removal of all sessions."
                }
            time.sleep(0.5)

        if feedback_received == 1:
            logger.info("All active video sessions have been removed.")
            return {
                "message": "All active video sessions have been removed successfully."
            }
        else:
            return {
                "message": "Failed to receive feedback for removing all video sessions."
            }

    except Exception as e:
        logger.error(f"Error in remove_all_active_sessions: {str(e)}")
        return {"message": f"Error removing sessions: {str(e)}"}
    finally:
        if pubsub:
            try:
                pubsub.unsubscribe(video_channel_name)
                pubsub.close()
                logger.info(
                    f"Disconnected from Redis Pub/Sub {video_channel_name} channel"
                )
            except Exception as e:
                logger.error(f"Error closing Redis connection: {str(e)}")
