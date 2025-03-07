import httpx
import os
import boto3

from typing import Dict, Union
from datetime import datetime
from termcolor import cprint
from io import BytesIO
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from typing import Optional
from .logger import Logger
from .exceptions import http_exception_msg

load_dotenv()

log = Logger(name="Helpers")
ACCOUNT_NAME = os.getenv("ACCOUNT_NAME")
ACCESS_KEY = os.getenv("ACCESS_KEY")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")


def send_api_request(
    url: str, headers: Dict[str, str], params: Dict[str, str]
) -> Dict[str, Union[Dict, str]]:
    """Send an API request and return the response or an error message.

    Args:
        url (str): The API endpoint URL.
        headers (Dict[str, str]): The request headers.
        params (Dict[str, str]): The query parameters for the request.

    Returns:
        Dict[str, Union[Dict, str]]: The API response or an error message.
    """
    try:
        cprint("Sending API request...", "blue")
        response = httpx.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            # Return the response JSON
            return response.json()
        else:
            # Handle non-200 status codes
            return {
                "error": {
                    "code": response.status_code,
                    "message": http_exception_msg.get(
                        response.status_code, "Unknown HTTP error"
                    ),
                }
            }

    except httpx.HTTPStatusError as http_error:
        # Handle HTTP errors explicitly
        status_code = http_error.response.status_code
        return {
            "error": {
                "code": status_code,
                "message": http_exception_msg.get(status_code, str(http_error)),
            }
        }

    except httpx.RequestError as req_error:
        # Handle request-related errors
        return {
            "error": {
                "code": "REQUEST_ERROR",
                "message": f"Request error: {str(req_error)}. Please try again later.",
            }
        }

    except Exception as e:
        # Handle other errors
        return {
            "error": {
                "code": "UNEXPECTED_ERROR",
                "message": f"Unexpected error: {str(e)}. Please try again later.",
            }
        }


def is_curr_year_video(epoch: str) -> bool:
    """
    Args:
        epoch (str): The timestamp of the video.

    Returns:
        bool: True if the video is from the current year, False otherwise.
    """
    current_year = datetime.now().year
    video_year = datetime.fromtimestamp(int(epoch)).year
    return video_year == current_year


def download_file(url: str) -> Union[BytesIO, None]:
    try:
        response = httpx.get(url, timeout=30)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx, 5xx)
        return BytesIO(response.content)
    except httpx.RequestError as e:
        log.error(f"Request error occurred while fetching {url}: {str(e)}")
    except httpx.HTTPStatusError as e:
        log.error(f"HTTP error occurred while fetching {url}: {str(e)}")
    except Exception as e:
        log.error(f"Unexpected error occurred while fetching {url}: {str(e)}")
    return None


def generate_presigned_url(bucket_name, object_key, expiration=3600):
    """
    Generate a pre-signed URL for an S3 object.

    :param bucket_name: Name of the S3 bucket
    :param object_key: Key of the object in the bucket
    :param expiration: Time in seconds for the URL to remain valid
    :return: Pre-signed URL as a string
    """
    try:
        # Create an S3 client
        s3_client = boto3.client("s3")

        # Generate the pre-signed URL
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_key},
            ExpiresIn=expiration,
        )
        return url
    except Exception as e:
        print(f"Error generating pre-signed URL: {e}")
        return None


def upload_s3_file(
    bucket_name: str,
    filename: str,
    data: Union[BytesIO, bytes, str],
    extension: str,
    folder: Optional[str] = None,
) -> str:
    """
    Upload a file to S3 bucket.

    Args:
        bucket_name: Name of the S3 bucket
        filename: Name of the file without extension
        data: File data as BytesIO, bytes, or string
        extension: File extension without dot
        folder: Optional folder path within bucket

    Returns:
        str: URL of the uploaded file

    Raises:
        RuntimeError: If upload fails
        ValueError: If input parameters are invalid
    """
    # Input validation
    if not bucket_name or not filename or not extension:
        raise ValueError("bucket_name, filename, and extension are required")

    # Convert data to BytesIO if needed
    if isinstance(data, str):
        file_obj = BytesIO(data.encode("utf-8"))
    elif isinstance(data, bytes):
        file_obj = BytesIO(data)
    elif isinstance(data, BytesIO):
        file_obj = data
        file_obj.seek(0)  # Reset file pointer to beginning
    else:
        raise ValueError("data must be BytesIO, bytes, or str")

    # Initialize S3 client
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )

    # Check/create bucket
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError as e:
        error_code = int(e.response["Error"]["Code"])
        if error_code == 404:
            try:
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": AWS_REGION},
                )
                print(f"Bucket '{bucket_name}' created successfully.")
            except ClientError as create_error:
                raise RuntimeError(f"Failed to create bucket: {str(create_error)}")
        else:
            raise RuntimeError(f"Error accessing bucket: {str(e)}")

    # Construct S3 key
    s3_key = f"{folder}/{filename}.{extension}" if folder else f"{filename}.{extension}"
    s3_key = s3_key.lstrip("/")  # Remove leading slash if present

    # Upload file
    try:
        s3_client.upload_fileobj(
            file_obj,
            bucket_name,
            s3_key,
            ExtraArgs={
                "ContentType": f"application/{extension}"
            },  # Set appropriate content type
        )
        log.info(f"File uploaded successfully to S3: {bucket_name}/{s3_key}")

        # Generate URL
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": s3_key},
            ExpiresIn=3600,  # URL expires in 1 hour
        )
        return presigned_url

    except Exception as e:
        raise RuntimeError(f"Failed to upload file to S3: {str(e)}")
