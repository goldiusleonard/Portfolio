import pytest
from fastapi import UploadFile, HTTPException
from fastapi.responses import JSONResponse
from unittest.mock import patch, MagicMock, AsyncMock
from src.modules.transcription import generate_transcription


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("LIT_SERVER_URL", "http://mockserver.com/transcribe")


@pytest.mark.asyncio
async def test_generate_transcription_success(mock_env):
    video_file = MagicMock(spec=UploadFile)
    video_file.filename = "test_video.mp4"
    video_file.content_type = "video/mp4"
    video_file.read = AsyncMock(return_value=b"fake_video_data")

    with patch("src.modules.transcription.httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "transcript": "This is a test transcription.",
            "language": "en",
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        response = await generate_transcription(video=video_file)

        assert response.status_code == 200
        assert (
            response.body
            == JSONResponse(
                content={
                    "message": "Transcription successful.",
                    "transcript": "This is a test transcription.",
                    "language": "en",
                }
            ).body
        )


@pytest.mark.asyncio
async def test_generate_transcription_invalid_file(mock_env):
    invalid_file = MagicMock(spec=UploadFile)
    invalid_file.filename = "test_file.txt"
    invalid_file.content_type = "text/plain"
    invalid_file.read = AsyncMock(return_value=b"fake_text_data")

    with pytest.raises(HTTPException) as exc_info:
        await generate_transcription(video=invalid_file)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Uploaded file is not a valid video format."


@pytest.mark.asyncio
async def test_generate_transcription_no_transcript(mock_env):
    video_file = MagicMock(spec=UploadFile)
    video_file.filename = "test_video.mp4"
    video_file.content_type = "video/mp4"
    video_file.read = AsyncMock(return_value=b"fake_video_data")

    with patch("src.modules.transcription.httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with pytest.raises(HTTPException) as exc_info:
            await generate_transcription(video=video_file)

        assert exc_info.value.status_code == 422
        assert (
            exc_info.value.detail
            == "Failed to transcribe the video. No valid transcription found."
        )
