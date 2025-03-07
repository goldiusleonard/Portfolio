from src.transcriber.base import Transcriber
from litserve import LitAPI, LitServer
import os
import tempfile
import torch
import anyio

torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

class TranscriberAPI(LitAPI):
    def __init__(self, batch_size=16):
        self.batch_size = batch_size
        self.model = None

    def setup(self, device):
        self.model = Transcriber(
            device=device,
            batch_size=self.batch_size
        )

    def decode_request(self, request):
        if "video" not in request:
            raise ValueError("Request must contain a 'video' key with the file content.")
        
        video_file = request["video"]

        # Use anyio to convert the asynchronous read operation to a synchronous one
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            video_content = anyio.run(video_file.read)
            temp_file.write(video_content)
            temp_path = temp_file.name
        
        return {"video_path": temp_path}

    def predict(self, data):
        results = []
        for item in data:  # Iterate through the batched list
            video_path = item["video_path"]
            try:
                # Transcribe the video
                transcription_result = self.model.transcribe_video(video_path, return_text_only=True)
                
                # Assuming the transcription result is a list or tuple
                transcript = transcription_result[0] if transcription_result else ""
            finally:
                if os.path.exists(video_path):
                    os.remove(video_path)
            
            # Append the result for this item
            results.append({"transcript": transcript})
        return results  # Return a list of results

    def encode_response(self, output):
        return output

if __name__ == "__main__":
    # Detect environment and set devices/workers
    if torch.cuda.is_available():
        accelerator = "cuda"
        devices = torch.cuda.device_count()
    else:
        accelerator = "cpu"
        devices = 1

    # Configure workers per device dynamically
    workers_per_device = 2 if accelerator == "cuda" else 1

    # Log the environment configuration
    print(f"Environment: Accelerator={accelerator}, Devices={devices}, Workers per device={workers_per_device}")

    server = LitServer(TranscriberAPI(batch_size=16), accelerator=accelerator, devices="3", workers_per_device=1, max_batch_size=16)
    server.run(
        host="0.0.0.0",
        port="8000",
    )