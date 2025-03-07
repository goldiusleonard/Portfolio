"""Pydantic schema for Law Violation Builder."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel


class EditFileDetailsRequest(BaseModel):
    """Represents a request to edit file details for a law violation record."""

    law_name: str
    category: str
    effective_date: str
    upload_date: str
    publisher: str
    summary: str


@dataclass
class LawViolationData:
    """Represents a law violation data."""

    law_name: str
    category: str
    effective_date: str
    publisher: str
    summary: str


@dataclass
class LawViolationDataEdit:
    """Represents a law violation data."""

    law_name: str
    category: str
    effective_date: str
    upload_date: str
    publisher: str
    summary: str
