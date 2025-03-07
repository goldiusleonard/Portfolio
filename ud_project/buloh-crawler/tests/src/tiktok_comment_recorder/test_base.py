from unittest.mock import patch, MagicMock
from src.modules.live_tiktok_comment_crawler import (
    start_live_comment_streaming,
    stop_live_comment_streaming,
    remove_all_active_sessions,
)
from fastapi import HTTPException
import pytest
import asyncio
import json


@pytest.fixture(autouse=True)
def mock_redis_client():
    with patch("src.modules.live_tiktok_comment_crawler.redis_client") as mock_redis:
        yield mock_redis


@pytest.fixture
def redis_pubsub():
    pubsub = MagicMock()
    pubsub.unsubscribe = MagicMock()
    pubsub.close = MagicMock()
    return pubsub


def test_start_live_comment_streaming_in_progress():
    username = "test_username"
    user_id = "test@userdata.tech"

    with patch(
        "src.modules.live_tiktok_comment_crawler.active_comment_sessions", {}
    ) as mock_active_comment_sessions:
        mock_active_comment_sessions[user_id] = [username]

        with pytest.raises(HTTPException) as exc_info:
            start_live_comment_streaming(username, user_id)

        assert exc_info.value.status_code == 400
        assert (
            exc_info.value.detail
            == f"Recording already in progress for user '{username}' with user ID '{user_id}'."
        )


@patch("src.modules.live_tiktok_comment_crawler.get_room_id_from_user")
def test_start_live_comment_room_id_not_found(mock_get_room_id):
    username = "test_username2"
    user_id = "test2@userdata.tech"

    mock_get_room_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        start_live_comment_streaming(username, user_id)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "The user is not currently live."


@patch("src.modules.live_tiktok_comment_crawler.get_room_id_from_user")
@patch("src.modules.live_tiktok_comment_crawler.is_user_in_live")
def test_start_live_comment_user_not_live(
    mock_is_user_in_live,
    mock_get_room_id,
):
    username = "test_username3"
    user_id = "test3@userdata.tech"

    mock_get_room_id.return_value = "room_001"
    mock_is_user_in_live.return_value = False

    with pytest.raises(HTTPException) as exc_info:
        start_live_comment_streaming(username, user_id)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "The user is not currently live."


mocked_comment_data_1 = {
    "id": 7451485853455059730,
    "text": "how are you?",
    "user": {"nickname": "dayangaleesya8"},
    "created_at": "2024-12-23 14:11:02",
}

mocked_comment_data_2 = {
    "id": 7451485853455059731,
    "text": "nice to meet you",
    "user": {"nickname": "pucung_"},
    "created_at": "2024-12-23 14:12:02",
}

mocked_comment_data_3 = {
    "id": 7451485853455059732,
    "text": "hello",
    "user": {"nickname": "tech_guru"},
    "created_at": "2024-12-23 14:13:02",
}


@patch("src.modules.live_tiktok_comment_crawler.get_room_id_from_user")
@patch("src.modules.live_tiktok_comment_crawler.is_user_in_live")
@patch("src.modules.live_tiktok_comment_crawler.create_tiktok_client")
@patch("src.modules.live_tiktok_comment_crawler.setup_client_events")
@patch("src.modules.live_tiktok_comment_crawler.run_client_in_thread")
@patch("src.modules.live_tiktok_comment_crawler.comment_stream")
@patch("asyncio.Queue")
def test_start_live_comment_streaming_success(
    mock_Queue,
    mock_comment_stream,
    mock_run_client_in_thread,
    mock_setup_client_events,
    mock_create_tiktok_client,
    mock_is_user_in_live,
    mock_get_room_id,
):
    username = "test_username4"
    user_id = "test4@userdata.tech"
    room_id = "room_002"

    mock_get_room_id.return_value = room_id
    mock_is_user_in_live.return_value = True

    mock_tiktok_client = MagicMock()
    mock_create_tiktok_client.return_value = mock_tiktok_client

    mock_comments_queue = MagicMock()
    mock_Queue.return_value = mock_comments_queue

    async def mock_async_generator():
        yield f"data: {str(mocked_comment_data_1)}\n\n"
        yield f"data: {str(mocked_comment_data_2)}\n\n"
        yield f"data: {str(mocked_comment_data_3)}\n\n"

    mock_comment_stream.return_value = mock_async_generator()

    with patch("src.modules.live_tiktok_comment_crawler.active_comment_sessions", {}):
        response = start_live_comment_streaming(username, user_id)

    active_comment_sessions = {}
    active_comment_sessions[user_id] = [username]

    mock_get_room_id.assert_called_once_with(username)
    mock_is_user_in_live.assert_called_once_with(room_id)
    mock_create_tiktok_client.assert_called_once_with(username)

    mock_setup_client_events.assert_called_once_with(
        mock_tiktok_client,
        mock_comments_queue,
        user_id,
        username,
        room_id,
        active_comment_sessions,
    )
    mock_run_client_in_thread.assert_called_once_with(
        mock_tiktok_client, user_id, username, active_comment_sessions
    )
    mock_comment_stream.assert_called_once()

    collected_data = []

    async def gather_content():
        async for data in response.body_iterator:
            collected_data.append(data)

    asyncio.run(gather_content())

    assert len(collected_data) == 3
    assert collected_data[0] == f"data: {str(mocked_comment_data_1)}\n\n"
    assert collected_data[1] == f"data: {str(mocked_comment_data_2)}\n\n"
    assert collected_data[2] == f"data: {str(mocked_comment_data_3)}\n\n"


@patch("src.modules.live_tiktok_comment_crawler.redis_client.publish")
@patch("src.modules.live_tiktok_comment_crawler.connect_redis_channel")
@patch("src.modules.live_tiktok_comment_crawler.active_comment_sessions", {})
@patch("time.sleep", return_value=None)
def test_stop_live_comment_streaming_no_active_session(
    mock_sleep,
    mock_connect_redis,
    mock_publish,
    redis_pubsub,
):
    username = "test_username5"
    user_id = "test5@userdata.tech"

    mock_connect_redis.return_value = redis_pubsub
    mock_publish.return_value = True

    redis_pubsub.get_message.side_effect = [
        {
            "type": "message",
            "data": json.dumps(
                {"action": "STOPPED", "user_id": user_id, "username": username}
            ),
        }
    ]

    response = stop_live_comment_streaming(username, user_id)

    assert response == {
        "message": f"Stream comments stopped successfully for user '{username}' with user ID '{user_id}'."
    }

    mock_publish.assert_called_once_with(
        "live_tiktok_comment_channel",
        json.dumps({"action": "STOP", "user_id": user_id, "username": username}),
    )

    redis_pubsub.unsubscribe.assert_called_once()
    redis_pubsub.close.assert_called_once()


@patch("src.modules.live_tiktok_comment_crawler.redis_client.publish")
def test_stop_live_comment_streaming_success(mock_publish):
    username = "test_username6"
    user_id = "test6@userdata.tech"

    active_comment_sessions = {}
    active_comment_sessions[user_id] = [username]

    with patch(
        "src.modules.live_tiktok_comment_crawler.active_comment_sessions",
        active_comment_sessions,
    ):
        response = stop_live_comment_streaming(username, user_id)

    assert (
        user_id not in active_comment_sessions
        or username not in active_comment_sessions[user_id]
    )
    mock_publish.assert_called_once_with(
        "live_tiktok_comment_channel",
        json.dumps({"action": "STOPPED", "user_id": user_id, "username": username}),
    )
    assert response == {
        "message": f"Stream comments stopped successfully for user '{username}' with user ID '{user_id}'."
    }


@patch("src.modules.live_tiktok_comment_crawler.connect_redis_channel")
@patch("src.modules.live_tiktok_comment_crawler.redis_client.publish")
@patch("time.sleep", return_value=None)
def test_remove_all_active_comment_sessions_success(
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
        "message": "All active comment sessions have been removed successfully."
    }
    mock_connect_redis_channel.assert_called_once()
    mock_redis_publish.assert_called_once_with(
        "live_tiktok_comment_channel",
        json.dumps({"action": "REMOVE_ALL_SESSIONS"}),
    )
