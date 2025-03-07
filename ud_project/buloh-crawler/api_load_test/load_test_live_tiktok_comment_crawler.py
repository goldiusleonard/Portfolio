import random
import time
import requests
import os
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


class TikTokStream:
    def __init__(self, username, user_id):
        self.username = username
        self.user_id = user_id
        self.is_streaming = False

    def start_streaming(self):
        """Start streaming and print received comments."""
        url = f"{BASE_URL}/tiktok/live/comments/start-streaming"
        params = {"username": self.username, "user_id": self.user_id}

        try:
            print(f"Starting stream for {self.username} ({self.user_id})...")
            response = requests.post(url, params=params, stream=True, verify=False)

            if response.status_code == 200:
                self.is_streaming = True
                print(
                    f"Stream started successfully for {self.username} ({self.user_id})."
                )

                try:
                    for line in response.iter_lines():
                        if line:
                            print(
                                f"Comment retrieved for {self.username} ({self.user_id})"
                            )
                except Exception:
                    print("\nStream interrupted and stopped.")
            else:
                print(
                    f"Failed to start stream for {self.username} ({self.user_id}). Status code: {response.status_code}"
                )
                print(response.text)
        except requests.exceptions.RequestException as e:
            print(f"Error starting stream for {self.username} ({self.user_id}): {e}")

    def stop_streaming(self):
        """Stop streaming after 20 seconds."""
        url = f"{BASE_URL}/tiktok/live/comments/stop-streaming"
        params = {"username": self.username, "user_id": self.user_id}

        try:
            response = requests.post(url, params=params, verify=False)

            if response.status_code == 200:
                data = response.json()
                print(
                    f"Recording stopped successfully for {self.username} ({self.user_id})"
                )
                print(data.get("message", "No message provided"))
            else:
                print(response.json().get("detail", "No error message provided"))
        except requests.exceptions.RequestException as e:
            print(f"Error stopping stream for {self.username} ({self.user_id}): {e}")


def start_stream_thread(streamer):
    streamer.start_streaming()


def stop_stream_thread(streamer):
    time.sleep(20)
    streamer.stop_streaming()


def run_load_test(username, num_users):
    """Run load testing for multiple users, where each user has two threads (start and stop)."""
    with ThreadPoolExecutor(max_workers=num_users * 2) as executor:
        start_threads = []
        stop_threads = []

        for _ in range(num_users):
            streamer = TikTokStream(username, f"user_id_{random.randint(1000, 9999)}")

            start_thread = executor.submit(start_stream_thread, streamer)
            start_threads.append(start_thread)

            stop_thread = executor.submit(stop_stream_thread, streamer)
            stop_threads.append(stop_thread)

        for start_thread, stop_thread in zip(start_threads, stop_threads):
            start_thread.result()
            stop_thread.result()

    print("Load test complete.")


if __name__ == "__main__":
    username = str(input("Enter the TikTok username: "))
    num_users = int(input("Enter the number of users: "))

    start_time = time.time()
    run_load_test(username, num_users)
    total_time = time.time() - start_time

    print(f"Total inference time for {num_users} users: {total_time:.2f} seconds")
