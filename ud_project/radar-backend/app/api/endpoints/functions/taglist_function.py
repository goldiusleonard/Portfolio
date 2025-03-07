"""Taglist Functions."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from app.models.content_data_asset_table import BAContentDataAsset


def get_taglist(
    db: Session,
) -> dict:
    """Retrieve a list of distinct categories from the BAContentDataAsset table.

    Args:
        db (Session): The database session used to query the data.

    Returns:
        dict: A dictionary containing a list of distinct categories under the key 'data'.
              Only non-None categories are included in the list.

    """
    distinct_categories = db.query(BAContentDataAsset.category).distinct().all()

    return {
        "data": [
            category[0] for category in distinct_categories if category[0] is not None
        ],
    }
