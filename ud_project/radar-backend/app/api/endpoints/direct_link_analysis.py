"""Direct Link Analysis Module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, BackgroundTasks, Depends

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from app.api.endpoints.functions import direct_link_analysis_function
from app.core.dependencies import get_db
from app.models.schemas.direct_link_analysis_schema import DirectLinkAnalysisRequest  # noqa: TCH001

direct_link_analysis_module = APIRouter()


@direct_link_analysis_module.post("/")
def create(
    request: DirectLinkAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict:
    """Create a new direct link analysis request.

    Args:
        request (DirectLinkAnalysisRequest): The request object containing URLs to analyze.
        background_tasks (BackgroundTasks): Background tasks to handle asynchronous processing.
        db (Session): Database session dependency.

    Returns:
        dict: A dictionary containing the result of the direct link analysis.

    """
    return direct_link_analysis_function.create(
        urls=request.urls,
        db=db,
        background_tasks=background_tasks,
    )


@direct_link_analysis_module.get("/content-details")
def get_content_details(db: Session = Depends(get_db)) -> dict:
    """Retrieve content details from the database.

    Args:
        db (Session): The database session dependency.

    Returns:
        dict: A dictionary containing the content details.

    """
    return direct_link_analysis_function.get_content_details(db=db)


@direct_link_analysis_module.get("/agent-content-list/{agent_name}")
def get_agent_content_list(
    agent_name: str = "",
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve a list of content associated with a specific agent.

    Args:
        agent_name (str): The name of the agent for which to retrieve the content list.
        db (Session): The database session dependency.

    Returns:
        dict: A dictionaries containing content details associated with the agent.

    """
    return direct_link_analysis_function.get_agent_content_list(
        agent_name=agent_name,
        db=db,
    )


@direct_link_analysis_module.get("/content-list")
def get_content_list(db: Session = Depends(get_db)) -> dict:
    """Retrieve a list of content from the database.

    Args:
        db (Session): The database session dependency.

    Returns:
        dict: A dictionary containing the list of content.

    """
    return direct_link_analysis_function.get_content_list(db=db)


@direct_link_analysis_module.get("/agent-list")
def get_agent_list(db: Session = Depends(get_db)) -> list:
    """Retrieve a list of agents from the database.

    Args:
        db (Session): The database session dependency.

    Returns:
        list[dict]: A list of dictionaries, each representing an agent with its details.

    """
    return direct_link_analysis_function.get_agent_list(db=db)


@direct_link_analysis_module.get("/similar-content/{case_id}")
def get_similar_content(
    case_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve similar content for a given case ID.

    Args:
        case_id (str): The unique identifier of the case for which similar content is to be retrieved.
        db (Session): The database session dependency.

    Returns:
        dict: A dictionary containing the similar content data.

    """
    return direct_link_analysis_function.get_similar_content(
        identification_id=case_id,
        db=db,
    )
