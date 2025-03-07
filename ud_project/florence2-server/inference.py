import httpx
import logging
from pathlib import Path
import time
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_florence_api(image_path: str, api_url: str = "http://localhost:8000/predict") -> None:
    """
    Test the Florence API by sending an image and receiving a caption.
    
    Args:
        image_path (str): Path to the image file to test
        api_url (str): URL of the Florence API endpoint
    """
    try:
        # Check if file exists
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
            
        logger.info(f"Sending request to {api_url} with image: {image_path}")
        start_time = time.time()
        
        # Read and encode the image file as base64
        with open(image_path, 'rb') as file:
            image_bytes = file.read()
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Send POST request with base64 encoded image using httpx
        headers = {'Content-Type': 'application/json'}
        data = {'image': image_b64}
        
        with httpx.Client() as client:
            response = client.post(
                api_url,
                headers=headers,
                json=data,
                timeout=30.0  # 30 second timeout
            )
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Check response status
        response.raise_for_status()
        
        # Get caption from response
        result = response.json()
        caption = result.get('caption')
        
        logger.info(f"Response time: {response_time:.2f} seconds")
        logger.info(f"Generated caption: {caption}")
        
        return caption
        
    except FileNotFoundError as e:
        logger.error(f"File error: {str(e)}")
        raise
    except httpx.HTTPError as e:
        logger.error(f"API request error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise

def run_batch_test(image_directory: str) -> None:
    """
    Test the API with multiple images from a directory.
    
    Args:
        image_directory (str): Path to directory containing test images
    """
    image_dir = Path(image_directory)
    if not image_dir.exists():
        raise FileNotFoundError(f"Directory not found: {image_directory}")
    
    # Process all image files in directory
    image_extensions = ('.jpg', '.jpeg', '.png')
    for image_path in image_dir.glob('*'):
        if image_path.suffix.lower() in image_extensions:
            logger.info(f"\nTesting image: {image_path.name}")
            try:
                test_florence_api(str(image_path))
            except Exception as e:
                logger.error(f"Failed to process {image_path.name}: {str(e)}")

if __name__ == "__main__":
    # Example usage
    # Single image test
    test_image = "images/giraffe.jpg"
    try:
        test_florence_api(test_image)
    except Exception as e:
        logger.error(f"Single image test failed: {str(e)}")
    
    # Batch test
    test_directory = "images"
    try:
        run_batch_test(test_directory)
    except Exception as e:
        logger.error(f"Batch test failed: {str(e)}")