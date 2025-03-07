import os
import random
import time
import requests
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


def get_video_metadata(file_path):
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

        result = subprocess.check_output(command, stderr=subprocess.STDOUT)
        metadata = result.decode("utf-8").strip()
        return metadata
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving metadata: {e.output.decode()}")
        return None


class TikTokVideoRecorder:
    def __init__(self, username, video_recording_interval):
        self.username = username
        self.video_recording_interval = video_recording_interval
        self.is_recording = False
        self.user_id = f"user_id_{random.randint(1000, 9999)}"

    def start_video_recording(self):
        """Start video recording and stream data."""
        url = f"{BASE_URL}/tiktok/live/video/start-recording"
        params = {
            "username": self.username,
            "user_id": self.user_id,
            "save_interval": self.video_recording_interval,
        }

        try:
            print(f"Starting video recording for {self.username} ({self.user_id})...")
            response = requests.post(url, params=params, stream=True, verify=False)

            if response.status_code == 200:
                self.is_recording = True
                print(
                    f"Recording started successfully for {self.username} ({self.user_id})"
                )
                return response
            else:
                print(
                    f"Failed to start video recording for {self.username} ({self.user_id}). Status code: {response.status_code}"
                )
                return None
        except requests.exceptions.RequestException as e:
            print(
                f"Error occurred while starting the recording for {self.username} ({self.user_id}): {e}"
            )
            return None

    def verify_video_chunks(self, response):
        """Save video chunks to disk and retrieve metadata."""
        chunk_size = 1024 * 1024 * 1024
        chunk_count = 1

        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                print(
                    f"Video {chunk_count} retrieved for {self.username} ({self.user_id})"
                )
                chunk_count += 1

    def check_status(self):
        """Check the status of the video recording."""
        url = f"{BASE_URL}/tiktok/live/user/status"
        params = {"username": self.username, "user_id": self.user_id}
        try:
            response = requests.get(url, params=params, verify=False)
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error checking status for {self.username} ({self.user_id}): {e}")
            return None

    def stop_video_recording(self):
        """Stop video recording."""
        url = f"{BASE_URL}/tiktok/live/video/stop-recording"
        params = {"username": self.username, "user_id": self.user_id}

        try:
            response = requests.post(url, params=params, verify=False)
            if response.status_code == 200:
                self.is_recording = False
                print(
                    f"Recording stopped successfully for {self.username} ({self.user_id})"
                )
                return response
            else:
                print(
                    f"Failed to stop video recording for {self.username} ({self.user_id}). Status code: {response.status_code}"
                )
                return None
        except requests.exceptions.RequestException as e:
            print(
                f"Error occurred while stopping the recording for {self.username} ({self.user_id}): {e}"
            )
            return None

    def run_recording(self):
        """Run the video recording session in a separate thread."""
        response = self.start_video_recording()
        if response and response.status_code == 200:
            self.verify_video_chunks(response)
            print(f"Recording is running for {self.username} ({self.user_id})...")
        else:
            print(f"Failed to start recording for {self.username} ({self.user_id})")


def start_recording_thread(recorder):
    """Thread function to start the recording."""
    recorder.run_recording()


def stop_recording_thread(recorder):
    """Thread function to check status and stop the recording after 30 seconds."""
    check_interval = 5
    total_wait_time = 30
    elapsed_time = 0

    while elapsed_time < total_wait_time:
        response = recorder.check_status()
        if response and response.status_code == 200:
            print(f"Status check for {recorder.username} ({recorder.user_id})")
        else:
            print(f"Error checking status for {recorder.username} ({recorder.user_id})")

        time.sleep(check_interval)
        elapsed_time += check_interval

    recorder.stop_video_recording()


def run_load_test(username, num_users, video_recording_interval):
    """Run load testing for multiple users."""

    with ThreadPoolExecutor(max_workers=num_users * 2) as executor:
        start_threads = []
        stop_threads = []

        for _ in range(num_users):
            recorder = TikTokVideoRecorder(username, video_recording_interval)

            start_thread = executor.submit(start_recording_thread, recorder)
            start_threads.append(start_thread)

            stop_thread = executor.submit(stop_recording_thread, recorder)
            stop_threads.append(stop_thread)

        for start_thread, stop_thread in zip(start_threads, stop_threads):
            start_thread.result()
            stop_thread.result()

    print("Load test complete.")


if __name__ == "__main__":
    username = str(input("Enter the TikTok username: "))
    num_users = int(input("Enter the number of users: "))
    video_recording_interval = int(
        input("Enter the save interval for video recordings: ")
    )

    start_time = time.time()
    run_load_test(username, num_users, video_recording_interval)
    total_time = time.time() - start_time

    print(f"Total inference time for {num_users} users: {total_time:.2f} seconds")
