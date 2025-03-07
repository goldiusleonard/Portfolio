"""Agent endpoint module."""

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.api.endpoints.functions import agent_function
from app.core.dependencies import get_db
from app.models.schemas.agent_schema import AgentCreate
from app.models.schemas.start_agent_builder_schema import StartAgentBuilderSchema
from app.models.update_model.agent_update import AgentUpdate

agent_module = APIRouter()


@agent_module.post("/")
def create_agent(
    agent_data: AgentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict:
    """Create a new agent."""
    return agent_function.create_agent(
        agent_data=agent_data.model_dump(),
        db=db,
        background_tasks=background_tasks,
    )


@agent_module.get("/")
def list_agents(db: Session = Depends(get_db)) -> list[dict]:  # noqa: FA102
    """List all agents."""
    return agent_function.get_agent_list(db=db)


@agent_module.get("/{agent_id}")
def get_agent_details(agent_id: int, db: Session = Depends(get_db)) -> dict:
    """Get details of a specific agent by ID."""
    return agent_function.get_agent_details(agent_id=agent_id, db=db)


@agent_module.get("/{agent_id}/crawler-preview")
def get_agent_crawler_preview(agent_id: int, db: Session = Depends(get_db)) -> dict:
    """Get crawler preview of a specific agent by ID."""
    return agent_function.get_agent_crawler_preview(agent_id=agent_id, db=db)


@agent_module.get("/{agent_id}/content-list")
def get_agent_content_list(agent_id: int, db: Session = Depends(get_db)) -> dict:
    """Get content list of a specific agent by ID."""
    return agent_function.get_agent_content_list(agent_id=agent_id, db=db)


@agent_module.post("/{agent_id}/start-agent-builder")
def start_agent_builder(
    start_agent_data: StartAgentBuilderSchema,
    db: Session = Depends(get_db),
) -> dict:
    """Get crawler preview of a specific agent by ID."""
    return agent_function.start_agent_builder(start_agent_data, db=db)


@agent_module.put("/{agent_id}")
def update_agent(
    agent_id: int,
    data: AgentUpdate,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> dict:
    """Update the data of an agent."""
    return agent_function.update_agent(
        agent_id=agent_id,
        data=data,
        db=db,
        background_tasks=background_tasks,
    )


@agent_module.patch("/{agent_id}/status")
def update_agent_status(
    agent_id: int,
    status: str,
    db: Session = Depends(get_db),
) -> dict:
    """Update the status of an agent."""
    return agent_function.update_agent_status(agent_id=agent_id, status=status, db=db)


@agent_module.patch("/{agent_id}/is-published")
def update_agent_is_published(
    agent_id: int,
    is_published: bool,  # noqa: FBT001
    db: Session = Depends(get_db),
) -> dict:
    """Update the is published flag of an agent."""
    return agent_function.update_agent_is_published(
        agent_id=agent_id,
        is_published=is_published,
        db=db,
    )
