"""Database CRUD operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.db.models import BaContentDataAsset

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_content_by_id(db: Session, content_id: int) -> BaContentDataAsset | None:
    """Retrieve a BaContentDataAsset record by its ID.

    Args:
        db: The database session
        content_id: The ID of the content to retrieve

    Returns:
        The content record if found, None otherwise

    """
    return (
        db.query(BaContentDataAsset).filter(BaContentDataAsset.id == content_id).first()
    )


def update_calculated_engagement(
    db: Session,
    content_id: int,
    new_value: float,
) -> BaContentDataAsset | None:
    """Update the calculated engagement for a given content record.

    Args:
        db: The database session
        content_id: The ID of the content to update
        new_value: The new engagement value to set

    Returns:
        The updated content record if found, None otherwise

    """
    record = get_content_by_id(db, content_id)
    if record:
        record.calculated_engagement = new_value
        db.commit()
        db.refresh(record)
    return record


def update_calculated_risk_score(
    db: Session,
    content_id: int,
    new_value: float,
) -> BaContentDataAsset | None:
    """Update the calculated risk score for a given content record.

    Args:
        db: The database session
        content_id: The ID of the content to update
        new_value: The new risk score value to set

    Returns:
        The updated content record if found, None otherwise

    """
    record = get_content_by_id(db, content_id)
    if record:
        record.calculated_risk_score = new_value
        db.commit()
        db.refresh(record)
    return record
