import torch
import io
import logging
import base64
import os
import subprocess
import multiprocessing

from typing import Any, Dict
from litserve import LitAPI, LitServer
from PIL import Image
from transformers import AutoModelForCausalLM, AutoProcessor, AutoConfig
from dotenv import load_dotenv

# Set the multiprocessing start method to 'spawn'
multiprocessing.set_start_method('spawn', force=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class FlorenceAPI(LitAPI):
    def setup(self, device: str) -> None:
        """
        Load the Florence model and processor, and move them to the specified device.
        Args:
            device (str): The device to load the model onto ("cpu" or "cuda").
        """
        self.device = device
        MODEL_NAME = os.getenv("MODEL_NAME")
        
        # Hugging Face login (retrieve and use the token)
        hf_token = os.getenv("HF_TOKEN")  # You can store the Hugging Face token in your .env file
        if not hf_token:
            logger.error("Hugging Face token is required.")
            raise ValueError("Hugging Face token is missing.")
        
        # Hugging Face authentication
        subprocess.run(["huggingface-cli", "login", "--token", hf_token])
        logger.info("Hugging Face login successful.")
        
        config = AutoConfig.from_pretrained(MODEL_NAME, trust_remote_code=True)
        config.vision_config.model_type = "davit"
        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME, trust_remote_code=True, config=config,
        )
        self.processor = AutoProcessor.from_pretrained(
            MODEL_NAME, trust_remote_code=True, config=config,
        )
        self.model.to(self.device)
        self.model.eval()
        logger.info("Florence model and processor loaded successfully.")

    def decode_request(self, request: Dict[str, Any]) -> Image.Image:
        """
        Decode the input image file from the request.
        Args:
            request (Dict[str, Any]): The request containing base64 encoded image
        Returns:
            Image.Image: A PIL Image object.
        """
        try:
            # Decode base64 string to bytes
            image_bytes = base64.b64decode(request['image'])
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            return image
        except Exception as e:
            logger.error(f"Error decoding image: {str(e)}")
            raise

    def predict(self, image: Image.Image) -> str:
        """
        Accepts an image file (PIL Image), processes it, and generates a caption using the Florence model.
        Args:
            image (Image.Image): The input image as a PIL Image object.
        Returns:
            str: The generated caption for the image.
        """
        # Process the image
        inputs = self.processor(
            text="<MORE_DETAILED_CAPTION>",
            images=image,
            return_tensors="pt"
        ).to(self.device)

        # Generate caption
        with torch.no_grad():
            outputs = self.model.generate(
                input_ids=inputs["input_ids"],
                pixel_values=inputs["pixel_values"],
                max_new_tokens=1024,
                do_sample=False,
                num_beams=3
            )

        # Decode and return the caption
        caption = self.processor.decode(outputs[0], skip_special_tokens=True)
        return caption

    def encode_response(self, output: str) -> Dict[str, str]:
        """
        Encode the response into a dictionary format.
        Args:
            output (str): The generated caption.
        Returns:
            Dict[str, str]: A dictionary containing the caption.
        """
        return {"caption": output}

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
    logger.info(f"Environment: Accelerator={accelerator}, Devices={devices}, Workers per device={workers_per_device}")

    # Start the server
    api = FlorenceAPI()
    server = LitServer(
        api,
        accelerator=accelerator,
        devices=devices,
        workers_per_device=workers_per_device
    )
    server.run(port=8000)