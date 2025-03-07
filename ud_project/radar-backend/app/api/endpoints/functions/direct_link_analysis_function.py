"""Module for retrieving direct link analysis."""

from __future__ import annotations

import os
import time
import uuid
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import requests
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import case, func
from sqlalchemy.orm import aliased

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from app.api.endpoints.functions.preprocessed_data_function import get_preprocessed_data
from app.core.constants import DEFAULT_CRAWLER_URL_FOR_DIRECT_LINK
from app.core.dependencies import get_db
from app.enums.agent_status import AgentStatus
from app.models.analysis_output_table import AnalysisOutput
from app.models.category_table import Category
from app.models.content_data_asset_table import BAContentDataAsset
from app.models.direct_link_analysis_table import DirectLinkAnalysis
from app.models.map_direct_link_analysis_preprocessed_unbiased_table import (
    MapDirectLinkAnalysisPreprocessedUnbiased,
)
from app.models.preprocessed_unbiased_table import PreprocessedUnbiased
from app.models.profile_data_asset_table import BAProfileDataAsset
from app.models.sub_category_table import SubCategory
from app.models.topic_category_table import TopicCategory
from app.models.topic_keywords_details_table import TopicKeywordsDetails
from utils.logger import Logger

log = Logger("DirectLinkAnalysis_Function")


def create(
    urls: list[str],
    db: Session,
    background_tasks: BackgroundTasks,
) -> dict:
    """Create a new direct link analysis agent.

    Args:
        urls (list[str]): List of URLs to analyze.
        db (Session): Database session.
        background_tasks (BackgroundTasks): Background tasks to execute.

    Returns:
        dict: A message indicating success or failure.

    """
    agent_name = str(uuid.uuid4())
    try:
        new_direct_link_analysis = DirectLinkAnalysis(
            URLList=urls,
            agentName=agent_name,
            status=AgentStatus.READY.value,
        )
        db.add(new_direct_link_analysis)
        db.commit()
        db.refresh(new_direct_link_analysis)
        background_tasks.add_task(start_crawling, new_direct_link_analysis)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create agent: {e!s}",
        ) from e
    else:
        return {
            "message": "Direct link analysis created successfully",
            "agent_name": agent_name,
        }


def update_agent_status(agent_id: int, status: AgentStatus, db: Session) -> dict:
    """Update the status of an agent.

    Args:
        agent_id (int): ID of the agent.
        status (AgentStatus): New status to set.
        db (Session): Database session.

    Returns:
        dict: A message indicating success or failure.

    """
    if status not in [status.value for status in AgentStatus]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {status}. Must be one of {[status.value for status in AgentStatus]}",
        )
    db.query(DirectLinkAnalysis).filter(DirectLinkAnalysis.id == agent_id).update(
        {"status": status},
    )
    db.commit()
    return {"message": "Agent status updated successfully"}


def start_crawling(agent_data: dict) -> None:
    """Start crawling for the given agent.

    Args:
        agent_data (dict): Data of the agent to start crawling.

    """
    log.info("Starting crawling for agent %s", agent_data.agentName)
    log.info("Agent data: %s", agent_data)
    payload = {
        "tags": [
            {
                "type": "url",
                "value": url,
            }
            for url in agent_data.URLList
        ],
        "category": "None",
        "subcategory": "None",
        "fromDate": "2024-01-01",
        "toDate": "2024-12-01",
        "tiktok": True,
        "news": True,
        "agentName": "None",
        "agentID": "None",
        "createdBy": "User1",
        "description": "None",
    }
    crawler_url = os.getenv("CRAWLER_URL") or DEFAULT_CRAWLER_URL_FOR_DIRECT_LINK
    update_agent_status(agent_data.id, AgentStatus.CRAWLING.value, next(get_db()))
    response = requests.post(crawler_url, json=payload, timeout=10)
    http_success = 200
    if response.status_code != http_success:
        log.error("Failed to call crawler API: %s", response.status_code)

    request_id = response.json()["request_id"]
    preprocessed_data = []

    while not preprocessed_data:
        preprocessed_data = get_preprocessed_data(request_id, next(get_db()))
        log.info(preprocessed_data)
        db = next(get_db())
        for data in preprocessed_data:
            mapping = MapDirectLinkAnalysisPreprocessedUnbiased(
                preprocessed_unbiased_id=data.id,
                direct_link_analysis_id=agent_data.id,
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


def get_agent_list(db: Session) -> list[dict]:
    """Retrieve a list of agents.

    Args:
        db (Session): Database session.

    Returns:
        list[dict]: List of agents with their details.

    """
    try:
        agents = (
            db.query(
                DirectLinkAnalysis.id,
                DirectLinkAnalysis.agentName,
                DirectLinkAnalysis.createdTime,
                DirectLinkAnalysis.status,
            )
            .group_by(DirectLinkAnalysis.id)
            .all()
        )

        return [
            {
                "agentName": agent.agentName,
                "agentID": agent.id,
                "createdTime": agent.createdTime.strftime("%d %b %Y"),
                "status": agent.status,
            }
            for agent in agents
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve agents: {e!s}",
        ) from e


def get_agent_content_list(agent_name: str, db: Session) -> dict:
    """Retrieve content list for a specific agent.

    Args:
        agent_name (str): Name of the agent.
        db (Session): Database session.

    Returns:
        dict: Content list for the agent.

    """
    agent_data = (
        db.query(DirectLinkAnalysis)
        .filter(DirectLinkAnalysis.agentName == agent_name)
        .first()
    )
    if not agent_data:
        raise HTTPException(
            status_code=404,
            detail=f"Agent with name {agent_name} not found.",
        )
    map_data = [
        entry.preprocessed_unbiased_id
        for entry in db.query(MapDirectLinkAnalysisPreprocessedUnbiased)
        .filter(
            MapDirectLinkAnalysisPreprocessedUnbiased.direct_link_analysis_id
            == agent_data.id,
            MapDirectLinkAnalysisPreprocessedUnbiased.deleted_at.is_(None),
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

        timestamp = video.video_posted_timestamp
        time_str = timestamp.strftime("%H:%M") if timestamp else "17:20"
        date_str = timestamp.strftime("%d/%m/%y") if timestamp else "11/10/24"

        parsed_url = urlparse(video.video_source)
        social_media = (
            parsed_url.netloc.split(".")[0] if parsed_url.netloc else "unknown"
        )

        result.append(
            {
                "id": analysis_output.identification_id,
                "content": {
                    "image_url": video.video_screenshot,
                    "title": video.title,
                    "link": video.video_source,
                },
                "time": time_str,
                "date": date_str,
                "social_media": social_media,
                "risk": analysis_output.risk_status,
                "topic": topic.topic_category_name if topic else "Unknown",
                "status": agent_data.status,
                "justification": video.video_summary,
            },
        )

    return {"data": result}


def get_content_list(db: Session) -> dict:
    """Retrieve a list of all content.

    Args:
        db (Session): Database session.

    Returns:
        dict: List of all content with details.

    """
    map_data = [
        entry.preprocessed_unbiased_id
        for entry in db.query(MapDirectLinkAnalysisPreprocessedUnbiased)
        .filter(MapDirectLinkAnalysisPreprocessedUnbiased.deleted_at.is_(None))
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

        map_entry = (
            db.query(MapDirectLinkAnalysisPreprocessedUnbiased)
            .filter(
                MapDirectLinkAnalysisPreprocessedUnbiased.preprocessed_unbiased_id
                == video.id,
            )
            .first()
        )
        if map_entry:
            direct_link_analysis = (
                db.query(DirectLinkAnalysis)
                .filter(DirectLinkAnalysis.id == map_entry.direct_link_analysis_id)
                .first()
            )
            status = direct_link_analysis.status if direct_link_analysis else "Unknown"
        else:
            status = "Unknown"

        topic = (
            db.query(TopicCategory.topic_category_name)
            .join(
                TopicKeywordsDetails,
                TopicCategory.id == TopicKeywordsDetails.topic_category_id,
            )
            .filter(TopicKeywordsDetails.preprocessed_unbiased_id == video.id)
            .first()
        )

        timestamp = video.video_posted_timestamp
        time_str = timestamp.strftime("%H:%M") if timestamp else "17:20"
        date_str = timestamp.strftime("%d/%m/%y") if timestamp else "11/10/24"

        parsed_url = urlparse(video.video_source)
        social_media = (
            parsed_url.netloc.split(".")[0] if parsed_url.netloc else "unknown"
        )

        result.append(
            {
                "id": analysis_output.identification_id,
                "content": {
                    "image_url": video.video_screenshot,
                    "title": video.title,
                    "link": video.video_source,
                },
                "time": time_str,
                "date": date_str,
                "social_media": social_media,
                "risk": analysis_output.risk_status,
                "topic": topic.topic_category_name if topic else "Unknown",
                "status": status,
                "justification": video.video_summary,
            },
        )

    return {"data": result}


def get_categories_by_username(username: str, db: Session) -> list:
    """Retrieve a list of categories associated with a given username.

    Args:
        username (str): The username for which to retrieve the categories.
        db (Session): The database session to execute the query.

    Returns:
        list: A list of categories.

    """
    bca = aliased(BAContentDataAsset)
    ao = aliased(AnalysisOutput)
    c = aliased(Category)

    category_risk_subquery = (
        db.query(
            c.category_name,
            func.lower(ao.risk_status).label("risk_status"),
            func.count().over(partition_by=c.category_name).label("category_count"),
            func.row_number()
            .over(
                partition_by=c.category_name,
                order_by=case(
                    (func.lower(ao.risk_status) == "high", 1),
                    (func.lower(ao.risk_status) == "medium", 2),
                    (func.lower(ao.risk_status) == "low", 3),
                    (func.lower(ao.risk_status) == "irrelevant", 4),
                    else_=5,
                ),
            )
            .label("rn"),
        )
        .select_from(bca)
        .outerjoin(ao, ao.video_id == bca.video_id)
        .outerjoin(c, c.id == ao.category_id)
        .filter(bca.user_handle == username)
        .subquery()
    )

    results = (
        db.query(
            category_risk_subquery.c.category_name,
            func.coalesce(category_risk_subquery.c.risk_status, "unknown").label(
                "risk_status",
            ),
            category_risk_subquery.c.category_count,
        )
        .filter(category_risk_subquery.c.rn == 1)
        .all()
    )

    return [row.category_name for row in results]


def get_content_details(db: Session) -> dict:
    """Retrieve detailed content information.

    Args:
        db (Session): Database session.

    Returns:
        dict: Detailed content information.

    """
    try:
        map_data = [
            entry.preprocessed_unbiased_id
            for entry in db.query(MapDirectLinkAnalysisPreprocessedUnbiased)
            .filter(MapDirectLinkAnalysisPreprocessedUnbiased.deleted_at.is_(None))
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
                    BAContentDataAsset.likes,
                    BAContentDataAsset.comments,
                    BAContentDataAsset.shares,
                )
                .filter(AnalysisOutput.preprocessed_unbiased_id == video.id)
                .outerjoin(
                    BAContentDataAsset,
                    BAContentDataAsset.video_id == AnalysisOutput.video_id,
                )
                .first()
            )

            map_entry = (
                db.query(MapDirectLinkAnalysisPreprocessedUnbiased)
                .filter(
                    MapDirectLinkAnalysisPreprocessedUnbiased.preprocessed_unbiased_id
                    == video.id,
                )
                .first()
            )
            if map_entry:
                direct_link_analysis = (
                    db.query(DirectLinkAnalysis)
                    .filter(DirectLinkAnalysis.id == map_entry.direct_link_analysis_id)
                    .first()
                )
                status = (
                    direct_link_analysis.status if direct_link_analysis else "Unknown"
                )
            else:
                status = "Unknown"

            category = (
                db.query(Category.name)
                .filter(Category.id == analysis_output.category_id)
                .first()
            )
            sub_category = (
                db.query(SubCategory.name)
                .filter(SubCategory.id == analysis_output.sub_category_id)
                .first()
            )

            topics = (
                db.query(TopicCategory.topic_category_name)
                .join(
                    TopicKeywordsDetails,
                    TopicCategory.id == TopicKeywordsDetails.topic_category_id,
                )
                .filter(TopicKeywordsDetails.preprocessed_unbiased_id == video.id)
                .all()
            )

            hashtags = video.video_hashtags.split(", ") if video.video_hashtags else []
            timestamp = video.video_posted_timestamp
            time_str = timestamp.strftime("%H:%M") if timestamp else "17:20"
            date_str = timestamp.strftime("%d/%m/%y") if timestamp else "11/10/24"

            parsed_url = urlparse(video.video_source)
            social_media = (
                parsed_url.netloc.split(".")[0] if parsed_url.netloc else "unknown"
            )

            creator_data = (
                db.query(BAProfileDataAsset)
                .filter(BAProfileDataAsset.profile_api_id == video.profile_id)
                .first()
            )

            result.append(
                {
                    "thumbnail": video.video_screenshot,
                    "id": analysis_output.identification_id,
                    "socialLink": video.video_source,
                    "date": date_str,
                    "time": time_str,
                    "socialMediaPlatform": social_media,
                    "risk": analysis_output.risk_status,
                    "status": status,
                    "likes": analysis_output.likes,
                    "comments": analysis_output.comments,
                    "shares": analysis_output.shares,
                    "category": [category.name] if category else [],
                    "sub-category": [sub_category.name] if sub_category else [],
                    "topic": [topic.topic_category_name for topic in topics],
                    "justification": video.video_summary,
                    "keywords": [keyword.replace("#", "") for keyword in hashtags],
                    "hashtags": hashtags,
                    "creator": {
                        "name": creator_data.user_handle if creator_data else "Unknown",
                        "categories": get_categories_by_username(
                            creator_data.user_handle,
                            db,
                        ),
                        "engagement": f"{creator_data.profile_engagement_score:.2f}%"
                        if creator_data
                        else "0%",
                        "following": creator_data.user_following_count
                        if creator_data
                        else 0,
                        "followers": creator_data.user_followers_count
                        if creator_data
                        else 0,
                        "posts": creator_data.user_total_videos if creator_data else 0,
                    },
                },
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve content details: {e!s}",
        ) from e
    else:
        return {"data": result}


def get_similar_content(identification_id: str, db: Session) -> dict:
    """Retrieve similar content based on identification ID.

    Args:
        identification_id (str): The ID of the content to find similar items for.
        db (Session): Database session.

    Returns:
        dict: A dictionary containing similar content details.

    """
    try:
        map_data = [
            entry.preprocessed_unbiased_id
            for entry in db.query(MapDirectLinkAnalysisPreprocessedUnbiased)
            .filter(MapDirectLinkAnalysisPreprocessedUnbiased.deleted_at.is_(None))
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
                    BAContentDataAsset.likes,
                    BAContentDataAsset.comments,
                    BAContentDataAsset.shares,
                )
                .filter(AnalysisOutput.preprocessed_unbiased_id == video.id)
                .outerjoin(
                    BAContentDataAsset,
                    BAContentDataAsset.video_id == AnalysisOutput.video_id,
                )
                .first()
            )

            # Filter content by identification_id
            if (
                analysis_output
                and analysis_output.identification_id == identification_id
            ):
                topics = (
                    db.query(TopicCategory.topic_category_name)
                    .join(
                        TopicKeywordsDetails,
                        TopicCategory.id == TopicKeywordsDetails.topic_category_id,
                    )
                    .filter(TopicKeywordsDetails.preprocessed_unbiased_id == video.id)
                    .all()
                )

                timestamp = video.video_posted_timestamp
                time_str = timestamp.strftime("%H:%M") if timestamp else "17:20"
                date_str = timestamp.strftime("%d/%m/%y") if timestamp else "11/10/24"

                parsed_url = urlparse(video.video_source)
                social_media = (
                    parsed_url.netloc.split(".")[0] if parsed_url.netloc else "unknown"
                )

                result.append(
                    {
                        "caseId": analysis_output.identification_id,
                        "time": time_str,
                        "date": date_str,
                        "socialMedia": social_media,
                        "topic": [topic.topic_category_name for topic in topics],
                        "risk": analysis_output.risk_status,
                    },
                )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve content details: {e!s}",
        ) from e
    else:
        return {"data": result}
