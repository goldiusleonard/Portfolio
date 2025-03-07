"""Authentication of user during login."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from app.auth import auth
from app.models import user_table as user


def get_user_by_email_and_password(
    db: Session,
    email: str,
    password: str,
) -> tuple:
    """Retrieve user by email and password.

    Args:
        db (Session): Database session.
        email (str): User's email.
        password (str): User's password.

    Returns:
        Optional[Tuple]: User if found and authenticated, else None.

    """
    final_user = (
        db.query(
            user.User.Id,
            user.User.UserName,
            user.User.Email,
            user.User.PasswordHash,
        )
        .filter(user.User.Email == email)
        .filter(user.User.IsActive)
        .first()
    )
    if final_user and auth.verify_password(password, final_user.PasswordHash):
        return final_user
    return None
