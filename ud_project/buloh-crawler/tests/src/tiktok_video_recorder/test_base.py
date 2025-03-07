from unittest.mock import patch, MagicMock
from src.modules.live_tiktok_video_crawler import (
    start_live_video_recording,
    stop_live_video_recording,
    check_user_live_status,
    stream_live_video_display,
    remove_all_active_sessions,
)
from fastapi import HTTPException, Request
import pytest
import json
import asyncio


@pytest.fixture(autouse=True)
def mock_redis_client():
    with patch("src.modules.live_tiktok_video_crawler.redis_client") as mock_redis:
        yield mock_redis


@pytest.fixture
def redis_pubsub():
    pubsub = MagicMock()
    pubsub.unsubscribe = MagicMock()
    pubsub.close = MagicMock()
    return pubsub


def test_start_live_video_recording_in_progress():
    username = "test_username"
    user_id = "test@userdata.tech"
    save_interval = 10

    with patch(
        "src.modules.live_tiktok_video_crawler.active_video_sessions", {}
    ) as mock_active_video_sessions:
        mock_active_video_sessions[user_id] = [username]

        with pytest.raises(HTTPException) as exc_info:
            start_live_video_recording(username, user_id, save_interval)

        assert exc_info.value.status_code == 400
        assert (
            exc_info.value.detail
            == f"Recording already in progress for user '{username}' with user ID '{user_id}'."
        )


@patch("src.modules.live_tiktok_video_crawler.get_room_id_from_user")
def test_start_live_video_room_id_not_found(mock_get_room_id):
    username = "test_username2"
    user_id = "test2@userdata.tech"
    save_interval = 10

    mock_get_room_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        start_live_video_recording(username, user_id, save_interval)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "The user is not currently live."


@patch("src.modules.live_tiktok_video_crawler.get_room_id_from_user")
@patch("src.modules.live_tiktok_video_crawler.is_user_in_live")
def test_start_live_video_user_not_live(
    mock_is_user_in_live, mock_get_room_id, mock_redis_client
):
    username = "test_username3"
    user_id = "test3@userdata.tech"
    save_interval = 10

    mock_get_room_id.return_value = "room_001"
    mock_is_user_in_live.return_value = False

    with pytest.raises(HTTPException) as exc_info:
        start_live_video_recording(username, user_id, save_interval)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "The user is not currently live."


@patch("src.modules.live_tiktok_video_crawler.datetime")
@patch("src.modules.live_tiktok_video_crawler.is_country_blacklisted")
@patch("src.modules.live_tiktok_video_crawler.get_room_id_from_user")
@patch("src.modules.live_tiktok_video_crawler.is_user_in_live")
@patch("src.modules.live_tiktok_video_crawler.get_live_url")
@patch("src.modules.live_tiktok_video_crawler.start_recording")
@patch("asyncio.Queue")
def test_start_live_video_recording_success(
    mock_Queue,
    mock_start_recording,
    mock_get_live_url,
    mock_is_user_in_live,
    mock_get_room_id,
    mock_is_country_blacklisted,
    mock_datetime,
):
    username = "test_username4"
    user_id = "test4@userdata.tech"
    save_interval = 10
    room_id = "room_002"
    live_url = "http://example.com/live"
    start_time = "2025-01-16T12:00:00"

    mock_is_country_blacklisted.return_value = False
    mock_get_room_id.return_value = room_id
    mock_is_user_in_live.return_value = True
    mock_get_live_url.return_value = live_url
    mock_start_recording.return_value = iter([b"video_chunk_1", b"video_chunk_2"])
    mock_datetime.now.return_value.isoformat.return_value = start_time

    mock_video_queue = MagicMock()
    mock_Queue.return_value = mock_video_queue

    with patch("src.modules.live_tiktok_video_crawler.active_video_sessions", {}):
        response = start_live_video_recording(username, user_id, save_interval)

    active_comment_sessions = {}
    active_comment_sessions[user_id] = [username]

    mock_is_country_blacklisted.assert_called_once_with(username)
    mock_get_room_id.assert_called_once_with(username)
    mock_is_user_in_live.assert_called_once_with(room_id)
    mock_get_live_url.assert_called_once_with(room_id)
    mock_start_recording.assert_called_once_with(
        username,
        live_url,
        save_interval,
        user_id,
        room_id,
        active_comment_sessions,
        start_time,
    )

    collected_data = []

    async def gather_content():
        async for chunk in response.body_iterator:
            collected_data.append(chunk)

    asyncio.run(gather_content())

    assert len(collected_data) == 2
    assert collected_data[0] == b"video_chunk_1"
    assert collected_data[1] == b"video_chunk_2"


@patch("src.modules.live_tiktok_video_crawler.redis_client.publish")
@patch("src.modules.live_tiktok_video_crawler.connect_redis_channel")
@patch("src.modules.live_tiktok_video_crawler.active_video_sessions", {})
@patch("time.sleep", return_value=None)
def test_stop_live_video_recording_no_active_session(
    mock_sleep,
    mock_connect_redis_channel,
    mock_redis_publish,
    redis_pubsub,
):
    username = "test_username5"
    user_id = "test5@userdata.tech"

    mock_connect_redis_channel.return_value = redis_pubsub
    mock_redis_publish.return_value = True

    redis_pubsub.get_message.side_effect = [
        {
            "type": "message",
            "data": json.dumps(
                {"action": "STOPPED", "user_id": user_id, "username": username}
            ),
        }
    ]

    response = stop_live_video_recording(username, user_id)

    assert response == {
        "message": f"Stream videos stopped successfully for user '{username}' with user ID '{user_id}'."
    }

    mock_redis_publish.assert_called_once_with(
        "live_tiktok_video_channel",
        json.dumps({"action": "STOP", "user_id": user_id, "username": username}),
    )

    redis_pubsub.unsubscribe.assert_called_once()
    redis_pubsub.close.assert_called_once()


@patch("src.modules.live_tiktok_video_crawler.redis_client.publish")
def test_stop_live_video_recording_success(mock_redis_publish):
    username = "test_username6"
    user_id = "test6@userdata.tech"

    active_video_sessions = {}
    active_video_sessions[user_id] = [username]

    with patch(
        "src.modules.live_tiktok_video_crawler.active_video_sessions",
        active_video_sessions,
    ):
        response = stop_live_video_recording(username, user_id)

    assert (
        user_id not in active_video_sessions
        or username not in active_video_sessions[user_id]
    )
    mock_redis_publish.assert_called_once_with(
        "live_tiktok_video_channel",
        json.dumps({"action": "STOPPED", "user_id": user_id, "username": username}),
    )
    assert response == {
        "message": f"Stream videos stopped successfully for user '{username}' with user ID '{user_id}'."
    }


@patch("src.modules.live_tiktok_video_crawler.get_room_id_from_user")
@patch("src.modules.live_tiktok_video_crawler.is_user_in_live")
def test_check_user_live_status_success(
    mock_is_user_in_live, mock_get_room_id_from_user
):
    username = "test_user7"
    room_id = "007"

    mock_get_room_id_from_user.return_value = room_id
    mock_is_user_in_live.return_value = True

    result = check_user_live_status(username=username)

    assert result["data"].alive
    assert result["data"].username == username
    assert result["data"].room_id == room_id
    mock_get_room_id_from_user.assert_called_once_with(username)
    mock_is_user_in_live.assert_called_once_with(room_id)


@patch("src.modules.live_tiktok_video_crawler.get_room_id_from_user")
@patch("src.modules.live_tiktok_video_crawler.is_user_in_live")
@patch("src.modules.live_tiktok_video_crawler.get_live_url")
@patch("src.modules.live_tiktok_video_crawler.stream_live_video")
def test_stream_live_video_display_success(
    mock_stream_live_video,
    mock_get_live_url,
    mock_is_user_in_live,
    mock_get_room_id_from_user,
):
    username = "test_user8"
    room_id = "008"
    live_url = "http://example.com/live"

    mock_stream_live_video.return_value = iter(
        [b"video_chunk_1", b"video_chunk_2", b"video_chunk_3"]
    )
    mock_get_room_id_from_user.return_value = room_id
    mock_is_user_in_live.return_value = True
    mock_get_live_url.return_value = live_url
    mock_request = Request(scope={"type": "http"})

    result = stream_live_video_display(request=mock_request, username=username)

    collected_data = []

    async def gather_content():
        async for chunk in result.body_iterator:
            collected_data.append(chunk)

    asyncio.run(gather_content())

    assert len(collected_data) == 3
    assert collected_data[0] == b"video_chunk_1"
    assert collected_data[1] == b"video_chunk_2"
    assert collected_data[2] == b"video_chunk_3"

    mock_get_room_id_from_user.assert_called_with(username)
    mock_is_user_in_live.assert_called_once_with(room_id)
    mock_get_live_url.assert_called_once_with(room_id)
    mock_stream_live_video.assert_called_once_with(live_url, mock_request)


@patch("src.modules.live_tiktok_video_crawler.connect_redis_channel")
@patch("src.modules.live_tiktok_video_crawler.redis_client.publish")
@patch("time.sleep", return_value=None)
def test_remove_all_active_video_sessions_success(
    mock_sleep,
    mock_redis_publish,
    mock_connect_redis_channel,
    redis_pubsub,
):
    mock_connect_redis_channel.return_value = redis_pubsub
    mock_redis_publish.return_value = True
    redis_pubsub.get_message.side_effect = [
        {
            "type": "message",
            "data": json.dumps({"action": "REMOVE_ALL_SESSIONS_ACK"}),
        }
    ]

    response = remove_all_active_sessions()

    assert response == {
        "message": "All active video sessions have been removed successfully."
    }
    mock_connect_redis_channel.assert_called_once()
    mock_redis_publish.assert_called_once_with(
        "live_tiktok_video_channel",
        json.dumps({"action": "REMOVE_ALL_SESSIONS"}),
    )
