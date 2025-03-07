"""User role functions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from app.models import role_table as role
from app.models import user_role_table as user_role

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.update_model.role_update import RoleUpdate

from sqlalchemy import and_


def get_all_user_role_data(db: Session = None) -> list[tuple]:
    """Get all user role data."""
    try:
        results_query = db.query(
            user_role.UserRole.Id,
            user_role.UserRole.UserId,
            user_role.UserRole.RoleId,
            user_role.UserRole.RoleType,
            user_role.UserRole.IsActive,
        )

        return [dict(row._asdict()) for row in results_query.all()]

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get users: {e!s}",
        ) from e


def map_single_user_role(
    user_id: int,
    role_id: int,
    permission_type: str,
    db: Session,
    *,
    is_active: bool,
) -> dict:
    """Map a single user role."""
    try:
        is_user_role_exist = user_role_already_created(user_id, role_id, db)
        if is_user_role_exist:
            return {"message": "Permission already exists."}

        user_role_data = user_role.UserRole(
            UserId=user_id,
            RoleId=role_id,
            RoleType=permission_type,
            IsActive=is_active,
        )
        db.add(user_role_data)
        db.commit()
        is_role_created = user_role_already_created(user_id, role_id, db)
        if is_role_created:
            return {"message": "Permission created successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to insert content: {e!s}",
        ) from e


def user_role_already_created(
    user_id: int,
    role_id: int,
    db: Session,
) -> bool:
    """Check if the user role already exists."""
    user_role_exist = (
        db.query(user_role.UserRole)
        .filter(
            and_(
                user_role.UserRole.UserId == user_id,
                user_role.UserRole.RoleId == role_id,
            ),
        )
        .all()
    )
    return bool(user_role_exist)


def get_role_by_id(role_id: int, db: Session) -> bool:
    """Get the role by the ID."""
    role_exist = db.query(role.Role).filter(role.Role.Id == role_id).first()
    return role_exist is not None


def edit_single_role_data(role_update: RoleUpdate, db: Session) -> dict:
    """Edit a single role data."""
    try:
        # Check if role exists
        is_role_exist = get_role_by_id(role_update.role_id, db)
        if not is_role_exist:
            return {"message": "Role does not exist"}

        # Fetch the existing role data
        role_data = (
            db.query(
                role.Role,
            )
            .filter(
                role.Role.Id == role_update.role_id,
            )
            .first()
        )

        # Update the role data
        role_data.RoleName = role_update.role_name
        role_data.Description = role_update.description
        role_data.IsActive = role_update.is_active
        role_data.RoleType = role_update.role_type
        # Commit the changes to the database
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update role: {e!s}",
        ) from e
    else:
        return {"message": "Role updated successfully"}


def delete_single_role(role_id: int, db: Session) -> dict:
    """Delete a single role from the database."""
    try:
        # Check if the role exists
        is_role_exist = get_role_by_id(role_id, db)
        if is_role_exist:
            # Delete the role
            db.query(role.Role).filter(role.Role.Id == role_id).delete(
                synchronize_session=False,
            )
            db.commit()
            return {"message": "Role deleted successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete role: {e!s}",
        ) from e
    else:
        return {"message": "Role does not exist"}


def get_permission_type_by_user_id_from_user_role(
    user_id: int,
    db: Session,
) -> str | bool:
    """Get the permission type by the user ID from the user role table."""
    permission_exist = (
        db.query(user_role.UserRole.RoleType)
        .filter(
            user_role.UserRole.UserId == user_id,
            user_role.UserRole.IsActive,
        )
        .first()
    )
    if permission_exist:
        return permission_exist.RoleType
    return False
