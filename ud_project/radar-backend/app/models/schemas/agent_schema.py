"""Pydantic schema for Agent."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel


class AgentCreate(BaseModel):
    """Schema for creating an Agent."""

    agentName: str  # noqa: N815
    createdBy: str  # noqa: N815
    createdTime: datetime = datetime.now(tz=UTC)  # noqa: N815
    description: str | None = None
    category: str
    subcategory: str
    crawlingStartDate: datetime  # noqa: N815
    crawlingEndDate: datetime  # noqa: N815
    legalDocuments: list[str] | None = None  # noqa: N815
    URLList: list[str] | None = None
    socialMediaList: list[str] | None = None  # noqa: N815
    isPublished: bool = False  # noqa: N815
    isUsernameCrawler: bool  # noqa: N815
    isKeywordCrawler: bool  # noqa: N815
    usernameList: list[str] | None = None  # noqa: N815
    keywordList: list[str] | None = None  # noqa: N815
