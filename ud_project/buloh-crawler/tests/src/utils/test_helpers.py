import httpx
from unittest.mock import patch, MagicMock
from io import BytesIO
from datetime import datetime
from src.utils.helpers import (
    send_api_request,
    is_curr_year_video,
    download_file,
)


@patch("src.utils.helpers.httpx.get")
def test_send_api_request_success(mock_get):
    """Test send_api_request when the API call is successful."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "success"}
    mock_get.return_value = mock_response

    url = "https://example.com/api"
    headers = {"Authorization": "Bearer test_token"}
    params = {"key": "value"}

    result = send_api_request(url, headers, params)

    assert result == {"data": "success"}
    mock_get.assert_called_once_with(url, headers=headers, params=params, timeout=30)


@patch("src.utils.helpers.httpx.get")
def test_send_api_request_http_error(mock_get):
    """Test send_api_request when an HTTP error occurs."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.side_effect = httpx.HTTPStatusError(
        "Not Found", request=None, response=mock_response
    )

    url = "https://example.com/api"
    headers = {"Authorization": "Bearer test_token"}
    params = {"key": "value"}

    result = send_api_request(url, headers, params)

    assert result["error"]["code"] == 404
    assert result["error"]["message"] == "Not found"
    mock_get.assert_called_once_with(url, headers=headers, params=params, timeout=30)


@patch("src.utils.helpers.httpx.get")
def test_send_api_request_request_error(mock_get):
    """Test send_api_request when a request error occurs."""
    mock_get.side_effect = httpx.RequestError("Request timed out")

    url = "https://example.com/api"
    headers = {"Authorization": "Bearer test_token"}
    params = {"key": "value"}

    result = send_api_request(url, headers, params)

    assert "Request error" in result["error"]["message"]  # Updated assertion
    assert result["error"]["code"] == "REQUEST_ERROR"
    mock_get.assert_called_once_with(url, headers=headers, params=params, timeout=30)


def test_is_curr_year_video():
    """Test is_curr_year_video function."""
    current_epoch = int(datetime.now().timestamp())
    last_year_epoch = int(datetime(datetime.now().year - 1, 1, 1).timestamp())

    assert is_curr_year_video(str(current_epoch)) is True
    assert is_curr_year_video(str(last_year_epoch)) is False


@patch("src.utils.helpers.httpx.get")
def test_download_file_success(mock_get):
    """Test download_file when the file is fetched successfully."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"file content"
    mock_get.return_value = mock_response

    url = "https://example.com/file"
    result = download_file(url)

    assert isinstance(result, BytesIO)
    assert result.read() == b"file content"
    mock_get.assert_called_once_with(url, timeout=30)


@patch("src.utils.helpers.httpx.get")
def test_download_file_failure(mock_get):
    """Test download_file when an error occurs."""
    mock_get.side_effect = httpx.RequestError("Request failed")

    url = "https://example.com/file"
    result = download_file(url)

    assert result is None
    mock_get.assert_called_once_with(url, timeout=30)
