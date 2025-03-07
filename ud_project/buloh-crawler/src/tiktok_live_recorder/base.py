import re
import json
import time
import os
import ffmpeg
import logging
import threading
from fastapi import Request
from datetime import datetime
from io import BytesIO
from dotenv import load_dotenv
from .http_client import HttpClient
from ..utils import helpers, read_cookies, Logger, get_env_variable
from .combine_files import concatenate_videos, add_metadata_to_video, create_empty_mp4

load_dotenv()

http_client = HttpClient(cookies=read_cookies()).req

log = Logger(name="database_logger")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bucket_name: str = get_env_variable(
    "AWS_BUCKET_NAME", "AWS_BUCKET_NAME is not provided!"
)


def get_live_url(room_id):
    """
    Get the CDN (FLV or M3U8) URL of the streaming.
    """
    url = f"https://webcast.tiktok.com/webcast/room/info/?aid=1988&room_id={room_id}"
    response = http_client.get(url)
    data = response.json()

    if "This account is private" in data:
        logger.error("Error: This account is private.")
        raise RuntimeError("Error: This account is private.")

    live_url_flv = data.get("data", {}).get("stream_url", {}).get("rtmp_pull_url", None)

    if live_url_flv is None and data.get("status_code") == 4003110:
        logger.error("Error: Live streaming is restricted.")
        raise RuntimeError("Error: Live streaming is restricted.")

    return live_url_flv


def is_user_in_live(room_id) -> bool:
    """
    Checking whether the user is live.
    """
    data = http_client.get(
        "https://webcast.tiktok.com:443/webcast/room/check_alive/"
        f"?aid=1988&region=CH&room_ids={room_id}&user_is_login=true"
    ).json()

    if "data" not in data:
        return False

    if isinstance(data["data"], list):
        return data["data"][0].get("alive", False)

    return data["data"].get("alive", False)


def is_country_blacklisted(user):
    """
    Checks if the user is in a blacklisted country that requires login.
    """
    response = http_client.get(
        f"https://www.tiktok.com/@{user}/live", allow_redirects=False
    )

    if response.status_code == 200:
        return False
    else:
        return True


def get_room_id_from_user(user):
    """
    Given a username, get the room_id.
    """
    response = http_client.get(f"https://www.tiktok.com/@{user}/live")
    content = response.text

    if "Please wait..." in content:
        logger.error("Error: IP blocked by WAF.")
        raise RuntimeError("Error: IP blocked by WAF.")

    pattern = re.compile(
        r'<script id="SIGI_STATE" type="application/json">(.*?)</script>', re.DOTALL
    )
    match = pattern.search(content)

    if not match:
        logger.error("Error extracting roomId.")
        raise RuntimeError("Error extracting roomId.")

    data = json.loads(match.group(1))

    if "LiveRoom" not in data and "CurrentRoom" in data:
        return ""

    room_id = (
        data.get("LiveRoom", {})
        .get("liveRoomUserInfo", {})
        .get("user", {})
        .get("roomId", None)
    )

    return room_id


def remove_files(file_paths: list):
    """Function to remove files in the background."""

    for file_path in file_paths:
        try:
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")


def start_recording(
    username: str,
    live_url: str,
    duration: int,
    user_id: str,
    room_id: str,
    active_video_sessions: dict,
    start_recording_time: str,
):
    """
    Start recording tiktok live streams and continuously retrieve video chunks and convert them using FFmpeg.
    """
    try:
        count = 1
        output_dir = f"recordings/server_videos/{user_id}"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        chunk_files = []

        full_video_output = os.path.join(output_dir, f"{username}_full_video.mp4")

        while True:
            if (
                user_id not in active_video_sessions
                or username not in active_video_sessions[user_id]
                or not is_user_in_live(room_id)
            ):
                logger.info("Stop Recording...")
                break
            try:
                response = http_client.get(live_url, stream=True)

                output = os.path.join(output_dir, f"{username}_vid{count}.mp4")

                # Input directly from in-memory stream
                stream = ffmpeg.input("pipe:0")

                if count == 1:
                    start_time = time.time()
                    chunk_data = b""

                for chunk in response.iter_content(chunk_size=4096):
                    chunk_data += chunk
                    elapsed_time = time.time() - start_time

                    if elapsed_time >= duration:
                        chunk_file = output.replace("_flv.mp4", ".mp4")
                        stream = ffmpeg.output(stream, chunk_file, c="copy", t=duration)
                        ffmpeg.run(stream, input=chunk_data, quiet=True)

                        logger.info(
                            f"Video {count} processed and saved as {output.replace('_flv.mp4', '.mp4')}"
                        )

                        with open(chunk_file, "rb") as f:
                            file_content = f.read()
                            yield file_content

                        chunk_files.append(chunk_file)

                        start_time = time.time()
                        chunk_data = b""
                        count += 1
                        break

            except Exception as e:
                logger.error(f"Error retrieving or processing chunk: {e}")
                raise RuntimeError(f"Error retrieving or processing chunk: {e}")

        logger.info("Recording session ended, concatenating chunks...")

        logger.info(f"Chunks to concatenate: {chunk_files}")
        concatenate_videos(chunk_files, full_video_output)

        with open(full_video_output, "rb") as f:
            full_video_content = f.read()

        full_video_bytesio = BytesIO(full_video_content)

        if full_video_bytesio is None:
            raise RuntimeError("Fail to convert video data to bytesio.")

        full_video_url = helpers.upload_s3_file(
            bucket_name=bucket_name,
            filename=full_video_output.replace(".mp4", ""),
            data=full_video_bytesio,
            extension="mp4",
            folder="live-tiktok-recordings",
        )

        logger.info(f"Full video blob url: {full_video_url}")

        temp_file = os.path.join(output_dir, f"{username}_empty_video.mp4")
        create_empty_mp4(temp_file)

        data = {
            "full_video_url": full_video_url,
            "user_id": user_id,
            "username": username,
            "start_time": start_recording_time,
            "end_time": datetime.now().isoformat(),
        }

        temp_file_with_metadata = add_metadata_to_video(temp_file, data)
        logger.info(f"Temporary file with metadata: {temp_file_with_metadata}")

        with open(temp_file_with_metadata, "rb") as f:
            file_content = f.read()
            yield file_content

        all_files_to_remove = [
            full_video_output,
            temp_file,
            temp_file_with_metadata,
        ] + chunk_files

        client_thread = threading.Thread(
            target=remove_files, args=(all_files_to_remove,)
        )
        client_thread.daemon = True
        client_thread.start()

    except Exception as e:
        logger.error("An error occurred while recording.")
        raise RuntimeError(f"Error occurred while recording: {e}")

    finally:
        if (
            user_id in active_video_sessions
            and username in active_video_sessions[user_id]
        ):
            active_video_sessions[user_id].remove(username)

            if not active_video_sessions[user_id]:
                del active_video_sessions[user_id]
                logger.info(f"No active recordings left for user ID '{user_id}'.")


async def stream_live_video(
    live_url: str,
    request: Request,
):
    """
    Stream video chunks from the live stream and yield them to the client.
    This function is called by the live stream display API function.
    """

    try:
        response = http_client.get(live_url, stream=True)
        if response.status_code != 200:
            raise RuntimeError("Failed to connect to live stream.")

        for chunk in response.iter_content(chunk_size=4096):
            if not chunk:
                logger.info("Stream has ended.")
                break
            if await request.is_disconnected():
                logger.info("Client disconnected. Stopping stream.")
                break
            yield chunk
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {str(e)}")
