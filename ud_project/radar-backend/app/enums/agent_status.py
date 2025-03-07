"""Agent status enum class."""

from enum import Enum


class AgentStatus(Enum):
    """Enumeration for Agent Status."""

    CRAWLING = "Crawling"
    REVIEW = "Review"
    READY = "Ready"
    PUBLISHED = "Published"
    ACTIVE = "Active"
    DEACTIVE = "Deactive"
