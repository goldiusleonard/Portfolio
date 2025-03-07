"""Functions for common methods."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from app.models import user_table


def get_user_name_by_email(email: str, db: Session) -> str:
    """Get the user name by the email."""
    return (
        db.query(user_table.User.UserName)
        .filter(user_table.User.Email == email)
        .first()[0]
    )
