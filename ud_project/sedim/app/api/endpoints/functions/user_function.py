"""User Functions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException
from sqlalchemy import or_

from app.auth import auth
from app.core.dependencies import get_db
from app.models import user_table as user

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.update_model.user_update import UserUpdate


def get_all_users_data(db: Session = None) -> list[dict]:
    """Get all users data."""
    if db is None:
        with next(get_db()) as session:
            return _query_users(session)
    return _query_users(db)


def _query_users(db: Session) -> list[dict]:
    """Query user data and return in a serializable format."""
    try:
        results_query = db.query(
            user.User.Id,
            user.User.UserName,
            user.User.Email,
            user.User.IsActive,
            user.User.CreatedAt,
        )
        # Convert each row to a dictionary
        return [dict(row._asdict()) for row in results_query.all()]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get users: {e!s}",
        ) from e


def post_single_user(
    user_name: str,
    password_hash: str,
    email: str,
    *,  # Add this to make subsequent parameters keyword-only
    is_active: bool,
    db: Session,
) -> dict:
    """Post a single user."""
    try:
        is_user_exist = user_already_created(user_name, email, db)
        if is_user_exist:
            return {"message": "User with this email or user_name already exists."}

        user_data = user.User(
            UserName=user_name,
            PasswordHash=auth.get_password_hash(password_hash),
            Email=email,
            IsActive=is_active,
        )
        db.add(user_data)
        db.commit()
        is_user_created = user_already_created(user_name, email, db)
        if is_user_created:
            return {"message": "User created successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to insert content: {e!s}",
        ) from e


def user_already_created(user_name: str, email: str, db: Session) -> bool:
    """Check if user already exists."""
    user_exist = (
        db.query(user.User)
        .filter(
            or_(user.User.Email == email, user.User.UserName == user_name),
        )
        .all()
    )

    return bool(user_exist)


def get_user_by_id(user_id: int, db: Session) -> bool:
    """Get user by ID."""
    return bool(db.query(user.User).filter(user.User.Id == user_id).first())


def edit_single_user_data(user_update: UserUpdate, db: Session) -> dict:
    """Edit a single user's data."""
    try:
        # Check if user exists
        is_user_exist = get_user_by_id(user_update.user_id, db)
        if not is_user_exist:
            return {"message": "User does not exist"}

        # Fetch and update the user directly
        user_query = db.query(user.User).filter(user.User.Id == user_update.user_id)
        user_record = user_query.first()

        if user_record:
            # Update the user data
            user_record.UserName = user_update.user_name
            user_record.Email = user_update.email
            user_record.PasswordHash = auth.get_password_hash(user_update.password_hash)
            user_record.IsActive = bool(user_update.is_active)
            # Ensure boolean conversion

            # Commit the changes to the database
            db.commit()
            # Verify the update
            db.refresh(user_record)

            return {
                "message": "User updated successfully",
                "updated_data": {
                    "user_id": user_record.Id,
                    "user_name": user_record.UserName,
                    "email": user_record.Email,
                    "is_active": user_record.IsActive,
                },
            }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update user: {e!s}",
        ) from e

    return {"message": "User not found"}


def delete_single_user(user_id: int, db: Session) -> dict:
    """Delete a single user."""
    try:
        # Check if the user exists
        is_user_exist = get_user_by_id(user_id, db)
        if is_user_exist:
            # Delete the user
            db.query(user.User).filter(user.User.Id == user_id).delete()
            db.commit()
            return {"message": "User deleted successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete user: {e!s}",
        ) from e
    else:
        return {"message": "User deleted successfully"}


def get_email_user_name_by_id(user_id: int, db: Session) -> dict:
    """Get email and user name by user ID."""
    user_name_email = (
        db.query(user.User.UserName, user.User.Email)
        .filter(user.User.Id == user_id)
        .first()
    )

    if user_name_email:
        return {
            "user_name": user_name_email[0],
            "email": user_name_email[1],
        }
    return {"message": "No data found"}
