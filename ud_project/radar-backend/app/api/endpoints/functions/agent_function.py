"""Agent Functions."""

import os
import time
from datetime import datetime, timezone

import requests
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.endpoints.functions.preprocessed_data_function import get_preprocessed_data
from app.core.constants import DEFAULT_CRAWLER_URL_FOR_AI_AGENT, SUCCESS_CODE
from app.core.dependencies import get_db
from app.enums.agent_status import AgentStatus
from app.models.agent_table import Agent
from app.models.analysis_output_table import AnalysisOutput
from app.models.category_table import Category
from app.models.content_data_asset_table import BAContentDataAsset
from app.models.map_agents_preprocessed_unbiased_table import (
    MapAgentsPreprocessedUnbiased,
)
from app.models.preprocessed_unbiased_table import PreprocessedUnbiased
from app.models.schemas.agent_schema import AgentCreate
from app.models.schemas.start_agent_builder_schema import StartAgentBuilderSchema
from app.models.sub_category_table import SubCategory
from app.models.tags_table import Tags
from app.models.topic_category_table import TopicCategory
from app.models.topic_keywords_details_table import TopicKeywordsDetails
from app.models.update_model.agent_update import AgentUpdate
from utils.logger import Logger

log = Logger("Agent_Function")


def create_agent(
    agent_data: AgentCreate,
    db: Session,
    background_tasks: BackgroundTasks,
) -> dict:
    """Create a new agent."""
    try:
        agent_exist = is_agent_name_exists(agent_data["agentName"], db)
        if agent_exist:
            return {"message": "Agent with this name already exists."}
        agent_data["status"] = AgentStatus.CRAWLING.value

        new_agent = Agent(
            agentName=agent_data["agentName"],
            createdBy=agent_data["createdBy"],
            createdTime=agent_data["createdTime"],
            description=agent_data["description"],
            category=agent_data["category"],
            subcategory=agent_data["subcategory"],
            crawlingStartDate=agent_data["crawlingStartDate"],
            crawlingEndDate=agent_data["crawlingEndDate"],
            legalDocuments=agent_data["legalDocuments"],
            URLList=agent_data["URLList"],
            SocialMediaList=agent_data["socialMediaList"],
            isPublished=agent_data["isPublished"],
            isUsernameCrawler=agent_data["isUsernameCrawler"],
            isKeywordCrawler=agent_data["isKeywordCrawler"],
            usernameList=agent_data["usernameList"],
            keywordList=agent_data["keywordList"],
        )
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)
        background_tasks.add_task(start_crawling, new_agent)
        return {"message": "Agent created successfully"}  # noqa: TRY300
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create agent: {e!s}",
        ) from e


def is_agent_name_exists(agent_name: str, db: Session) -> bool:
    """Check if agent already exists."""
    agent_exist = (
        db.query(Agent)
        .filter(
            or_(Agent.agentName == agent_name),
        )
        .all()
    )

    return bool(agent_exist)


def get_agent_list(db: Session) -> list[dict]:  # noqa: FA102
    """Retrieve and format the list of agents."""
    try:
        agents = (
            db.query(
                Agent.id,
                Agent.agentName,
                Agent.category,
                Agent.subcategory,
                Agent.createdBy,
                Agent.createdTime,
                Agent.crawlingStartDate,
                Agent.crawlingEndDate,
                Agent.status,
                Agent.isPublished,
                func.count().label(
                    "totalContent",
                ),  # Assuming you have a way to count content
            )
            .group_by(Agent.id)
            .all()
        )

        return [
            {
                "agentName": agent.agentName,
                "agentID": agent.id,
                "category": agent.category,
                "subcategory": agent.subcategory,
                "createdBy": agent.createdBy,
                "createdTime": agent.createdTime.strftime("%d %b %Y"),
                "crawlingPeriod": (
                    f"{agent.crawlingStartDate.strftime('%d %b %Y')} - "
                    f"{agent.crawlingEndDate.strftime('%d %b %Y')}"
                ),
                "status": agent.status,
                "totalContent": agent.totalContent,
                "isPublished": agent.isPublished,
            }
            for agent in agents
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve agents: {e!s}",
        ) from e


def get_agent_details(agent_id: int, db: Session) -> dict:
    """Retrieve and format the details of a specific agent by ID."""
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()

        if not agent:
            raise HTTPException(  # noqa: TRY301
                status_code=404,
                detail=f"Agent with ID {agent_id} not found.",
            )

        return {
            "agentName": agent.agentName,
            "agentID": agent.id,
            "createdBy": agent.createdBy,
            "createdTime": agent.createdTime.strftime("%d %b %Y"),
            "description": agent.description,
            "category": agent.category,
            "subcategory": agent.subcategory,
            "crawlingStartDate": agent.crawlingStartDate.strftime("%d %b %Y"),
            "crawlingEndDate": agent.crawlingEndDate.strftime("%d %b %Y"),
            "legalDocuments": agent.legalDocuments,
            "URLList": agent.URLList,
            "socialMediaList": agent.SocialMediaList,
            "isPublished": agent.isPublished,
            "isUsernameCrawler": agent.isUsernameCrawler,
            "isKeywordCrawler": agent.isKeywordCrawler,
            "usernameList": agent.usernameList,
            "keywordList": agent.keywordList,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve agent details: {e!s}",
        ) from e


def get_agent_crawler_preview(agent_id: int, db: Session) -> dict:
    """Get crawler preview of a specific agent by ID."""
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(  # noqa: TRY301
                status_code=404,
                detail=f"Agent with ID {agent_id} not found.",
            )

        map_data = [
            entry.preprocessed_unbiased_id
            for entry in db.query(MapAgentsPreprocessedUnbiased)
            .filter(
                MapAgentsPreprocessedUnbiased.agent_id == agent_id,
                MapAgentsPreprocessedUnbiased.deleted_at.is_(None),
            )
            .all()
        ]
        video_data = (
            db.query(PreprocessedUnbiased)
            .filter(PreprocessedUnbiased.id.in_(map_data))
            .all()
        )
        data_count = len(video_data)
        related_keywords = []

        for video in video_data:
            tag_counts = (
                db.query(Tags.value, func.count(Tags.value))
                .filter(
                    Tags.request_id == video.request_id,
                    Tags.type == "keyword",
                )
                .group_by(Tags.value)
                .all()
            )

            for tag_value, count in tag_counts:
                related_keywords.append({tag_value: f"{count}/{data_count}"})

        return {
            "categoryDetail": {
                "category": agent.category,
                "subCategory": agent.subcategory,
                "totalScannedContent": data_count,
            },
            "videoDetails": [
                {
                    "thumbnailImage": video.video_screenshot
                    if video.video_screenshot
                    else "Unknown",
                    "evaluationSummary": {
                        "contentSummary": video.video_summary
                        if video.video_summary
                        else "Unknown",
                    },
                }
                for video in video_data
            ],
            "relatedKeyword": related_keywords,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve agent crawler preview: {e!s}",
        ) from e


def start_agent_builder(start_agent_data: StartAgentBuilderSchema, db: Session) -> dict:
    """Start agent builder."""
    log.info(f"Starting agent builder for agent id: {start_agent_data.agent_id}")  # noqa: G004
    agent_data = db.query(Agent).filter(Agent.id == start_agent_data.agent_id).first()
    if not agent_data:
        raise HTTPException(
            status_code=404,
            detail=f"Agent with ID {start_agent_data.agent_id} not found.",
        )
    agent_data.legalDocuments = start_agent_data.files_name
    db.commit()
    db.refresh(agent_data)
    payload = {
        "agent_builder_name": agent_data.agentName,
        "post_date": {
            "from_date": agent_data.crawlingStartDate.strftime("%Y-%m-%d"),
            "to_date": agent_data.crawlingEndDate.strftime("%Y-%m-%d"),
        },
        "files_name": start_agent_data.files_name,
        "category": agent_data.category,
        "subcategory": agent_data.subcategory,
        "risk_levels": start_agent_data.risk_levels,
    }
    response = requests.post(os.getenv("START_AGENT_BUILDER_URL"), json=payload)  # noqa: S113
    if response.status_code != SUCCESS_CODE:
        log.error(f"Failed to call crawler API: {response.status_code}")  # noqa: G004
        raise HTTPException(
            status_code=500,
            detail=f"Failed to call crawler API: {response.status_code}",
        )
    log.info(
        f"Agent builder started successfully for agent id: {start_agent_data.agent_id}",  # noqa: G004
    )
    update_agent_status(
        start_agent_data.agent_id,
        AgentStatus.READY.value,
        next(get_db()),
    )
    return {"message": "Agent builder started successfully"}


def get_agent_content_list(agent_id: int, db: Session) -> dict:
    """Get content list of a specific agent by ID."""
    agent_data = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent_data:
        raise HTTPException(
            status_code=404,
            detail=f"Agent with ID {agent_id} not found.",
        )
    map_data = [
        entry.preprocessed_unbiased_id
        for entry in db.query(MapAgentsPreprocessedUnbiased)
        .filter(
            MapAgentsPreprocessedUnbiased.agent_id == agent_id,
            MapAgentsPreprocessedUnbiased.deleted_at.is_(None),
        )
        .all()
    ]

    preprocessed_data = (
        db.query(PreprocessedUnbiased)
        .filter(PreprocessedUnbiased.id.in_(map_data))
        .all()
    )
    result = []
    for video in preprocessed_data:
        analysis_output = (
            db.query(
                AnalysisOutput.category_id,
                AnalysisOutput.sub_category_id,
                AnalysisOutput.risk_status,
                AnalysisOutput.timestamp,
                BAContentDataAsset.identification_id,
            )
            .filter(AnalysisOutput.preprocessed_unbiased_id == video.id)
            .outerjoin(
                BAContentDataAsset,
                BAContentDataAsset.video_id == AnalysisOutput.video_id,
            )
            .first()
        )
        category = (
            db.query(Category)
            .filter(Category.id == analysis_output.category_id)
            .first()
        )
        sub_category = (
            db.query(SubCategory)
            .filter(SubCategory.id == analysis_output.sub_category_id)
            .first()
        )
        topic = (
            db.query(
                TopicCategory.topic_category_name,
            )
            .join(
                TopicKeywordsDetails,
                TopicCategory.id == TopicKeywordsDetails.topic_category_id,
            )
            .filter(
                TopicKeywordsDetails.preprocessed_unbiased_id == video.id,
            )
            .first()
        )

        result.append(
            {
                "video_id": video.video_id,
                "user_handle": video.user_handle,
                "identification_id": analysis_output.identification_id,
                "video_posted_timestamp": video.video_posted_timestamp.isoformat(),
                "video_source": video.video_source,
                "ai_topic": topic.topic_category_name,
                "status": "AI Flagged",  # unknown
                "risk_status": analysis_output.risk_status,
                "category": category.category_name,
                "sub_category": sub_category.sub_category_name,
                "video_hashtags": video.video_hashtags,
                "ss_process_timestamp": analysis_output.timestamp.isoformat(),
            },
        )
    return {"data": result}


def update_agent(
    agent_id: int,
    data: AgentUpdate,
    db: Session,
    background_tasks: BackgroundTasks,
) -> dict:
    """Update the data of an agent."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=404,
            detail=f"Agent with ID {data.agent_id} not found.",
        )
    agent.agentName = data.agentName
    agent.createdBy = data.createdBy
    agent.description = data.description
    agent.category = data.category
    agent.subcategory = data.subcategory
    agent.crawlingStartDate = (
        datetime.strptime(
            data.crawlingStartDate,
            "%d %b %Y",
        )
        .replace(tzinfo=timezone.utc)
        .isoformat()
    )
    agent.crawlingEndDate = (
        datetime.strptime(
            data.crawlingEndDate,
            "%d %b %Y",
        )
        .replace(tzinfo=timezone.utc)
        .isoformat()
    )
    agent.legalDocuments = data.legalDocuments
    agent.URLList = data.URLList
    agent.SocialMediaList = data.socialMediaList
    agent.isPublished = data.isPublished
    agent.isUsernameCrawler = data.isUsernameCrawler
    agent.isKeywordCrawler = data.isKeywordCrawler

    agent.usernameList = data.usernameList
    agent.keywordList = data.keywordList

    db.commit()
    # removing old preprocessed_unbiased data
    db.query(MapAgentsPreprocessedUnbiased).filter(
        MapAgentsPreprocessedUnbiased.agent_id == agent_id,
        MapAgentsPreprocessedUnbiased.deleted_at.is_(None),
    ).update({"deleted_at": func.now()})
    db.commit()
    update_agent_status(agent_id, AgentStatus.CRAWLING.value, db)
    update_agent_is_published(agent_id, False, db)  # noqa: FBT003
    new_agent = db.query(Agent).filter(Agent.id == agent_id).first()
    db.refresh(new_agent)
    background_tasks.add_task(start_crawling, new_agent)
    return {"message": "Agent updated successfully"}


def update_agent_status(agent_id: int, status: AgentStatus, db: Session) -> dict:
    """Update the status of an agent."""
    if status not in [status.value for status in AgentStatus]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {status}. Must be one of {[status.value for status in AgentStatus]}",
        )
    db.query(Agent).filter(Agent.id == agent_id).update({"status": status})
    db.commit()
    return {"message": "Agent status updated successfully"}


def update_agent_is_published(agent_id: int, is_published: bool, db: Session) -> dict:  # noqa: FBT001
    """Update the is_published of an agent."""
    db.query(Agent).filter(Agent.id == agent_id).update({"isPublished": is_published})
    db.commit()
    return {"message": "Agent isPublished updated successfully"}


def start_crawling(agent_data: dict) -> None:
    """Start crawling."""
    log.info(f"Starting crawling for agent {agent_data.agentName}")  # noqa: G004
    log.info(f"Agent data: {agent_data}")  # noqa: G004
    payload = {
        "task": [
            {
                "type": "url",
                "value": url,
            }
            for url in agent_data.URLList
            + [
                {
                    "type": "username",
                    "value": username,
                }
                for username in agent_data.usernameList
            ]
            + [
                {
                    "type": "keyword",
                    "value": keyword,
                }
                for keyword in agent_data.keywordList
            ]
        ],
        "category": agent_data.category,
        "subcategory": agent_data.subcategory,
        "fromDate": str(agent_data.crawlingStartDate),
        "toDate": str(agent_data.crawlingEndDate),
        "tiktok": True,
        "news": True,
        "agentName": agent_data.agentName,
        "agentID": str(agent_data.id),
        "createdBy": agent_data.createdBy,
        "description": agent_data.description,
    }
    crawler_url = os.getenv("CRAWLER_URL") or DEFAULT_CRAWLER_URL_FOR_AI_AGENT
    response = requests.post(crawler_url, json=payload)  # noqa: S113
    if response.status_code != SUCCESS_CODE:
        log.error(f"Failed to call crawler API: {response.status_code}")  # noqa: G004

    request_id = response.json()["request_id"]
    preprocessed_data = []

    while not preprocessed_data:
        preprocessed_data = get_preprocessed_data(request_id, next(get_db()))
        log.info(preprocessed_data)
        db = next(get_db())
        for data in preprocessed_data:
            mapping = MapAgentsPreprocessedUnbiased(
                preprocessed_unbiased_id=data.id,
                agent_id=agent_data.id,
            )
            db.add(mapping)
            db.commit()
        time.sleep(2)
    update_agent_status(agent_data.id, AgentStatus.REVIEW.value, next(get_db()))

    log.info(
        {
            "message": "Crawling completed successfully",
            "request_id": response.json()["request_id"],
        },
    )
