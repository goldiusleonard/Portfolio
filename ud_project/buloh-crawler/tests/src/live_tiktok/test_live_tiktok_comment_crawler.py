import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json

# Update imports to match your project structure
from src.modules.live_tiktok_comment_crawler import (
    router,
    active_comment_sessions,
    connect_redis_channel,
    handle_stop_message,
)

client = TestClient(router)


@pytest.fixture(autouse=True)
def clear_sessions():
    active_comment_sessions.clear()
    yield
    active_comment_sessions.clear()


@pytest.fixture
def mock_redis():
    with patch("src.modules.live_tiktok_comment_crawler.redis_client") as mock:
        mock.pubsub.return_value = Mock()
        yield mock


@pytest.fixture
def mock_room_id():
    with patch("src.modules.live_tiktok_comment_crawler.get_room_id_from_user") as mock:
        mock.return_value = "12345"
        yield mock


@pytest.fixture
def mock_is_user_live():
    with patch("src.modules.live_tiktok_comment_crawler.is_user_in_live") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_tiktok_client():
    with patch("src.modules.live_tiktok_comment_crawler.create_tiktok_client") as mock:
        client = Mock()
        client.start = Mock()
        mock.return_value = client
        yield mock


@pytest.fixture
def mock_setup_events():
    with patch("src.modules.live_tiktok_comment_crawler.setup_client_events") as mock:
        yield mock


@pytest.fixture
def mock_run_client():
    with patch("src.modules.live_tiktok_comment_crawler.run_client_in_thread") as mock:
        yield mock


def test_start_streaming_success(
    mock_room_id,
    mock_is_user_live,
    mock_tiktok_client,
    mock_setup_events,
    mock_run_client,
):
    response = client.post(
        "/live/comments/start-streaming?username=testuser&user_id=123"
    )
    assert response.status_code == 200


def test_start_streaming_already_active():
    active_comment_sessions["123"] = ["testuser"]
    with pytest.raises(Exception) as exc_info:
        client.post("/live/comments/start-streaming?username=testuser&user_id=123")
    assert "Recording already in progress" in str(exc_info.value)


def test_start_streaming_user_not_live(
    mock_room_id, mock_is_user_live, mock_tiktok_client
):
    mock_is_user_live.return_value = False

    with pytest.raises(HTTPException) as exc_info:
        client.post("/live/comments/start-streaming?username=testuser&user_id=123")
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "The user is not currently live."


def test_stop_streaming_success(mock_redis):
    active_comment_sessions["123"] = ["testuser"]
    response = client.post(
        "/live/comments/stop-streaming?username=testuser&user_id=123"
    )
    assert response.status_code == 200
    assert "stopped successfully" in response.json()["message"]


def test_stop_streaming_not_found(mock_redis):
    pubsub = Mock()
    pubsub.get_message.return_value = {
        "type": "message",
        "data": json.dumps(
            {"action": "NOT_FOUND", "user_id": "123", "username": "testuser"}
        ),
    }
    mock_redis.pubsub.return_value = pubsub

    response = client.post(
        "/live/comments/stop-streaming?username=testuser&user_id=123"
    )
    assert response.status_code == 200
    assert "No active recording session" in response.json()["message"]


def test_remove_all_sessions_success(mock_redis):
    pubsub = Mock()
    pubsub.get_message.return_value = {
        "type": "message",
        "data": json.dumps({"action": "REMOVE_ALL_SESSIONS_ACK"}),
    }
    mock_redis.pubsub.return_value = pubsub

    active_comment_sessions["123"] = ["testuser"]
    response = client.post("/live/comments/remove-all-sessions")

    assert response.status_code == 200
    assert "removed successfully" in response.json()["message"]
    assert len(active_comment_sessions) == 0


@pytest.mark.asyncio
async def test_handle_stop_message():
    active_comment_sessions["123"] = ["testuser"]
    message = {
        "data": json.dumps({"action": "STOP", "user_id": "123", "username": "testuser"})
    }

    await handle_stop_message(message)
    assert "123" not in active_comment_sessions


def test_connect_redis_channel(mock_redis):
    connect_redis_channel()
    mock_redis.pubsub.assert_called_once()
