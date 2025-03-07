"""Agent update model."""

from __future__ import annotations

from pydantic import BaseModel


class AgentUpdate(BaseModel):
    """Schema for updating an Agent."""

    agentName: str  # noqa: N815
    agentID: int  # noqa: N815
    createdBy: str  # noqa: N815
    createdTime: str  # noqa: N815
    description: str | None = None
    category: str
    subcategory: str
    crawlingStartDate: str  # noqa: N815
    crawlingEndDate: str  # noqa: N815
    legalDocuments: list[str] | None = None  # noqa: N815
    URLList: list[str] | None = None
    socialMediaList: list[str] | None = None  # noqa: N815
    isPublished: bool = False  # noqa: N815
    isUsernameCrawler: bool  # noqa: N815
    isKeywordCrawler: bool  # noqa: N815
    usernameList: list[str] | None = None  # noqa: N815
    keywordList: list[str] | None = None  # noqa: N815
