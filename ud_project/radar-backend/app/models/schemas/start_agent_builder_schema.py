"""Pydantic schema for Starting Agent Builder."""

from __future__ import annotations

from pydantic import BaseModel


class StartAgentBuilderSchema(BaseModel):
    """Schema for starting an Agent Builder."""

    agent_id: int
    files_name: list[str]
    risk_levels: dict
