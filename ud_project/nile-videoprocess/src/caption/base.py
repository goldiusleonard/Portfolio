import os
import numpy as np
import subprocess
import tempfile
import json
import base64
import httpx
import traceback

from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from PIL import Image
from pymongo import MongoClient
from dotenv import load_dotenv
from typing import List, Dict, Union, Any, Optional
from ..keyframe_extraction import ImageSelector
from ..utils import configure_logging

# Load environment variables
load_dotenv()

# MongoDB and MySQL setup
uri = os.getenv("MONGO_URI")
client = MongoClient(uri)
db = client["marketplace"]
collection = db["video"]

db_details = {
    "host": os.getenv("MYSQL_HOST"),
    "database": os.getenv("MYSQL_DATABASE"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
}

# Configure logging
logger = configure_logging()


def process_frame_data(frame_data: bytes) -> Optional[np.ndarray]:
    """
    Process frame data with proper color space handling.

    Args:
        frame_data: Raw frame data in bytes

    Returns:
        Optional[np.ndarray]: Processed frame as numpy array or None if processing fails
    """
    try:
        # Load image using PIL
        frame = Image.open(BytesIO(frame_data))

        # Convert PIL image to numpy array
        frame_np = np.array(frame)

        # Handle different color modes
        if frame.mode == "L":  # Grayscale
            # Convert grayscale to RGB by stacking the same channel 3 times
            frame_np = np.stack((frame_np,) * 3, axis=-1)
        elif frame.mode == "RGBA":
            # Convert RGBA to RGB by removing alpha channel
            frame_np = frame_np[..., :3]
        elif frame.mode not in ["RGB", "BGR"]:
            # Convert any other mode to RGB using PIL
            frame_rgb = frame.convert("RGB")
            frame_np = np.array(frame_rgb)

        # Ensure we have a 3-channel RGB image
        if len(frame_np.shape) != 3 or frame_np.shape[2] != 3:
            logger.error(f"Invalid frame shape after processing: {frame_np.shape}")
            return None

        return frame_np

    except Exception as e:
        logger.error(f"Failed to process frame: {e}")
        return None


class VideoCaptioner:
    def __init__(self, florence_url: str):
        self.florence_url = florence_url
        self.keyframe_extractor = ImageSelector()

    def extract_keyframes(
        self, video_path: str, max_workers: int = 4
    ) -> List[Dict[str, Union[float, Image.Image]]]:
        """
        Extract keyframes with improved frame processing and error handling.
        """
        try:
            # Get video info using ffprobe
            ffprobe_command = [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=duration,r_frame_rate",
                "-of",
                "json",
                video_path,
            ]
            video_info_str = subprocess.check_output(ffprobe_command, text=True)
            video_info: Dict[str, Any] = json.loads(video_info_str)

            # Optimize ffmpeg command
            ffmpeg_command = [
                "ffmpeg",
                "-hwaccel",
                "auto",
                "-i",
                video_path,
                "-vf",
                "select='eq(pict_type,I)',fps=1",
                "-vsync",
                "0",
                "-frame_pts",
                "1",
                "-f",
                "image2pipe",
                "-pix_fmt",
                "rgb24",  # Force RGB24 output
                "-vcodec",
                "mjpeg",
                "-q:v",
                "2",
                "-threads",
                str(os.cpu_count()),
                "-",
            ]

            process = subprocess.Popen(
                ffmpeg_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=10**8,
            )

            frames_data: List[Optional[np.ndarray]] = []
            current_frame = bytearray()

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_frame: Dict[Any, int] = {}

                if process.stdout is None:
                    raise ValueError("Process stdout is None")

                while True:
                    chunk = process.stdout.read(1024 * 1024)
                    if not chunk:
                        break

                    current_frame.extend(chunk)

                    while True:
                        start = current_frame.find(b"\xff\xd8")
                        if start == -1:
                            break

                        end = current_frame.find(b"\xff\xd9", start)
                        if end == -1:
                            break

                        frame_data = current_frame[start : end + 2]
                        current_frame = current_frame[end + 2 :]

                        future = executor.submit(process_frame_data, frame_data)
                        future_to_frame[future] = len(frames_data)
                        frames_data.append(None)

                # Collect results
                for future in future_to_frame:
                    frame_idx = future_to_frame[future]
                    result = future.result()
                    if result is not None:
                        frames_data[frame_idx] = result

            # Remove None values and filter frames
            frames = [f for f in frames_data if f is not None]
            if not frames:
                logger.error("No valid frames were extracted")
                return []

            # Select best frames
            best_frames_np = self.keyframe_extractor.select_best_frames(frames)

            # Convert numpy arrays to PIL Images
            best_frames = [Image.fromarray(frame_np) for frame_np in best_frames_np]

            # Calculate timestamps
            duration = float(video_info["streams"][0]["duration"])
            keyframes_info = [
                {"time": round(idx * duration / len(frames), 2), "image": frame}
                for idx, frame in enumerate(best_frames)
            ]

            logger.info(f"Successfully extracted {len(keyframes_info)} keyframes")
            return keyframes_info

        except Exception as e:
            logger.error(f"Failed to extract keyframes: {e}")
            return []

    def generate_caption(self, frame):
        """
        Send the frame to the Florence API and return the generated caption using base64 encoding.
        """
        # Convert the image frame to a base64 encoded string
        with BytesIO() as buffer:
            frame.save(buffer, format="JPEG")
            frame_data = buffer.getvalue()

        image_b64 = base64.b64encode(frame_data).decode("utf-8")

        # Define API URL and headers
        api_url = f"{self.florence_url}/predict"
        headers = {"Content-Type": "application/json"}
        data = {"image": image_b64}

        # Start the timer for response time
        # start_time = time.time()

        # Send the POST request with base64 encoded image using httpx
        with httpx.Client() as client:
            response = client.post(
                api_url,
                headers=headers,
                json=data,
                timeout=30.0,  # 30 second timeout
            )

        # Calculate response time
        # response_time = time.time() - start_time

        # Check response status
        response.raise_for_status()

        # Get caption from response
        result = response.json()
        caption = result.get("caption")

        return caption

    def caption_video_with_keyframes(self, video_path: str) -> list:
        """
        Captions a video by extracting keyframes and generating captions for each.

        Args:
            video_path (str): Path to the input video file.

        Returns:
            list: A list of dictionaries where each dictionary contains the timestamp and caption.
        """
        keyframes_info = self.extract_keyframes(video_path)
        captions = []

        for keyframe in keyframes_info:
            timestamp = keyframe["time"]
            frame = keyframe["image"]

            try:
                caption = self.generate_caption(frame=frame)
                captions.append({"time": timestamp, "caption": caption})
                logger.info(f"Timestamp: {timestamp}, Caption: {caption}")
            except Exception as e:
                print(traceback.format_exc())
                logger.error(
                    f"Failed to process keyframe with timestamp {timestamp} : {e}"
                )

        return captions

    def caption_video_from_file(self, file) -> list:
        """
        Processes an MP4 file object, saves it temporarily using `tempfile`,
        and generates captions for keyframes.

        Args:
            file: An MP4 file object (e.g., from an HTTP request or form upload).

        Returns:
            list: A list of dictionaries containing timestamps and captions.
        """
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=True) as temp_file:
                # Save the uploaded video to a temporary file
                temp_file.write(file.read())
                temp_file.flush()  # Ensure data is written to disk
                logger.info(f"Temporary video file saved to '{temp_file.name}'.")

                # Generate captions for the video
                captions = self.caption_video_with_keyframes(temp_file.name)

                logger.info("Processed video successfully, temporary file closed.")
                return captions

        except Exception as e:
            logger.error(f"Failed to process uploaded video file: {e}")
            return []
