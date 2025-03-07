"""Module contains tests for the agent_function in the app.api.endpoints.functions module."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.api.endpoints.functions.agent_function import (
    create_agent,
    get_agent_content_list,
    get_agent_crawler_preview,
    get_agent_details,
    get_agent_list,
    start_agent_builder,
    start_crawling,
    update_agent,
    update_agent_is_published,
)
from app.core.constants import SUCCESS_CODE
from app.models.schemas.start_agent_builder_schema import StartAgentBuilderSchema
from app.models.update_model.agent_update import AgentUpdate


@pytest.fixture
def mock_db_session() -> MagicMock:
    """Mock the database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_background_tasks() -> MagicMock:
    """Mock the background tasks."""
    return MagicMock(spec=BackgroundTasks)


def test_create_agent(
    mock_db_session: Session,
    mock_background_tasks: BackgroundTasks,
) -> None:
    """Test the create_agent function."""
    agent_data = {
        "agentName": "TestAgent",
        "description": "Test Description",
        "category": "TestCategory",
        "subcategory": "TestSubCategory",
        "createdBy": "Tester",
        "createdTime": "2023-01-01",
        "crawlingStartDate": "2023-01-01",
        "crawlingEndDate": "2023-01-02",
        "isPublished": False,
        "isUsernameCrawler": False,
        "isKeywordCrawler": False,
        "usernameList": [],
        "keywordList": [],
        "legalDocuments": [],
        "URLList": [],
        "socialMediaList": [],
    }
    mock_db_session.query().filter().all.return_value = []

    result = create_agent(agent_data, mock_db_session, mock_background_tasks)

    assert result == {"message": "Agent created successfully"}  # noqa: S101
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_background_tasks.add_task.assert_called_once()


def test_get_agent_list(mock_db_session: Session) -> None:
    """Test the get_agent_list function."""
    mock_db_session.query().group_by().all.return_value = [
        MagicMock(
            id=1,
            agentName="TestAgent",
            category="TestCategory",
            subcategory="TestSubCategory",
            createdBy="Tester",
            createdTime=datetime.strptime("2023-01-01", "%Y-%m-%d"),  # noqa: DTZ007
            crawlingStartDate=datetime.strptime("2023-01-01", "%Y-%m-%d"),  # noqa: DTZ007
            crawlingEndDate=datetime.strptime("2023-01-02", "%Y-%m-%d"),  # noqa: DTZ007
            isPublished=False,
            isUsernameCrawler=False,
            isKeywordCrawler=False,
            usernameList=[],
            keywordList=[],
            legalDocuments=[],
            URLList=[],
            socialMediaList=[],
        ),
    ]

    result = get_agent_list(mock_db_session)

    assert len(result) == 1  # noqa: S101
    assert result[0]["agentName"] == "TestAgent"  # noqa: S101


def test_get_agent_details(mock_db_session: Session) -> None:
    """Test the get_agent_details function."""
    mock_db_session.query().filter().first.return_value = MagicMock(
        id=1,
        agentName="TestAgent",
        createdBy="Tester",
        createdTime=datetime.strptime("2023-01-01", "%Y-%m-%d"),  # noqa: DTZ007
        description="Test Description",
        category="TestCategory",
        subcategory="TestSubCategory",
        crawlingStartDate=datetime.strptime("2023-01-01", "%Y-%m-%d"),  # noqa: DTZ007
        crawlingEndDate=datetime.strptime("2023-01-02", "%Y-%m-%d"),  # noqa: DTZ007
        legalDocuments=[],
        URLList=[],
        socialMediaList=[],
        isPublished=True,
        isUsernameCrawler=False,
        isKeywordCrawler=False,
        usernameList=[],
        keywordList=[],
    )

    result = get_agent_details(1, mock_db_session)

    assert result["agentName"] == "TestAgent"  # noqa: S101


def test_get_agent_crawler_preview(mock_db_session: Session) -> None:
    """Test the get_agent_crawler_preview function."""
    mock_db_session.query().filter().first.return_value = MagicMock(
        id=1,
        category="TestCategory",
        subcategory="TestSubCategory",
    )
    mock_db_session.query().filter().all.return_value = [
        MagicMock(preprocessed_unbiased_id=1),
    ]
    mock_db_session.query().filter().all.return_value = [
        MagicMock(video_screenshot="screenshot", video_summary="summary"),
    ]
    mock_db_session.query().filter().group_by().all.return_value = [("keyword", 5)]

    result = get_agent_crawler_preview(1, mock_db_session)

    assert result["categoryDetail"]["category"] == "TestCategory"  # noqa: S101
    assert result["categoryDetail"]["subCategory"] == "TestSubCategory"  # noqa: S101


def test_get_agent_content_list(mock_db_session: Session) -> None:
    """Test the get_agent_content_list function."""
    mock_db_session.query().filter().first.return_value = MagicMock(id=1)
    mock_db_session.query().filter().all.return_value = [
        MagicMock(
            id=1,
            video_id="vid1",
            user_handle="user1",
            video_posted_timestamp=datetime.now(tz=UTC),
            video_source="source1",
            video_hashtags="hashtags",
        ),
    ]
    mock_db_session.query().filter().outerjoin().first.return_value = MagicMock(
        category_id=1,
        sub_category_id=1,
        risk_status="low",
        timestamp=datetime.now(tz=UTC),
        identification_id="id1",
    )
    mock_db_session.query().filter().first.return_value = MagicMock(
        category_name="Category1",
    )
    mock_db_session.query().filter().first.return_value = MagicMock(
        sub_category_name="SubCategory1",
    )
    mock_db_session.query().join().filter().first.return_value = MagicMock(
        topic_category_name="Topic1",
    )

    result = get_agent_content_list(1, mock_db_session)

    assert len(result["data"]) == 1  # noqa: S101
    assert result["data"][0]["video_id"] == "vid1"  # noqa: S101


def test_update_agent(
    mock_db_session: Session,
    mock_background_tasks: BackgroundTasks,
) -> None:
    """Test the update_agent function."""
    agent_update_data = AgentUpdate(
        agentID=1,
        agentName="UpdatedAgent",
        createdBy="Updated By",
        createdTime="14 Jan 2025",
        description="Updated Description",
        category="Updated Category",
        subcategory="Updated SubCategory",
        crawlingStartDate="14 Jan 2025",
        crawlingEndDate="14 Jan 2025",
        legalDocuments=[],
        URLList=[],
        socialMediaList=[],
        isPublished=True,
        isUsernameCrawler=True,
        isKeywordCrawler=True,
    )
    mock_db_session.query().filter().first.return_value = MagicMock()

    result = update_agent(
        agent_update_data.agentID,
        agent_update_data,
        mock_db_session,
        mock_background_tasks,
    )

    assert result == {"message": "Agent updated successfully"}  # noqa: S101
    mock_db_session.commit.assert_called()
    mock_background_tasks.add_task.assert_called_once()


def test_update_agent_is_published(mock_db_session: Session) -> None:
    """Test the update_agent_is_published function."""
    result = update_agent_is_published(1, True, mock_db_session)  # noqa: FBT003

    assert result == {"message": "Agent isPublished updated successfully"}  # noqa: S101
    mock_db_session.commit.assert_called_once()


@patch("app.api.endpoints.functions.agent_function.requests.post")
def test_start_agent_builder(mock_post: MagicMock, mock_db_session: Session) -> None:
    """Test the start_agent_builder function."""
    start_agent_data = StartAgentBuilderSchema(
        agent_id=1,
        files_name=["file1", "file2"],
        risk_levels={"test": {"high": 1, "medium": 2}},
    )
    mock_db_session.query().filter().first.return_value = MagicMock(
        id=1,
        agentName="TestAgent",
        category="TestCategory",
        subcategory="TestSubCategory",
        crawlingStartDate=datetime.strptime("2023-01-01", "%Y-%m-%d"),  # noqa: DTZ007
        crawlingEndDate=datetime.strptime("2023-01-02", "%Y-%m-%d"),  # noqa: DTZ007
    )
    mock_post.return_value.status_code = SUCCESS_CODE

    result = start_agent_builder(start_agent_data, mock_db_session)

    assert result == {"message": "Agent builder started successfully"}  # noqa: S101
    mock_post.assert_called_once()


@patch("app.api.endpoints.functions.agent_function.requests.post")
@patch("app.api.endpoints.functions.agent_function.get_preprocessed_data")
def test_start_crawling(
    mock_get_preprocessed_data: MagicMock,
    mock_post: MagicMock,
) -> None:
    """Test the start_crawling function."""
    agent_data = MagicMock(
        agentName="TestAgent",
        id=1,
        category="TestCategory",
        subcategory="TestSubCategory",
        crawlingStartDate=datetime.now(tz=UTC),
        crawlingEndDate=datetime.now(tz=UTC),
        URLList=["http://example.com"],
        usernameList=["user1"],
        keywordList=["keyword1"],
        createdBy="Tester",
        description="Test Description",
    )
    mock_post.return_value.status_code = SUCCESS_CODE
    mock_post.return_value.json.return_value = {"request_id": "req123"}
    mock_get_preprocessed_data.return_value = [MagicMock(id=1)]

    start_crawling(agent_data)

    mock_post.assert_called_once()
    mock_get_preprocessed_data.assert_called_once()
