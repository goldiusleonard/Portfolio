"""Preprocessed Unbiased Functions."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.preprocessed_unbiased_table import PreprocessedUnbiased


def get_preprocessed_data(request_id: str, db: Session = Depends(get_db)) -> dict:
    """Get preprocessed data by request_id."""
    try:
        return (
            db.query(PreprocessedUnbiased)
            .filter(
                PreprocessedUnbiased.request_id == request_id,
            )
            .all()
        )

    except Exception as e:  # noqa: TRY302
        raise e  # noqa: TRY201
