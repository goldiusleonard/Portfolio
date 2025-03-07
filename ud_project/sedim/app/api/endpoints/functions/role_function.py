"""role functionalities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from app.models import role_table, user_role_table, user_table

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.update_model.role_update import RoleUpdate


def get_all_roles_data(db: Session) -> dict:  # Changed return type to dict
    """Get all roles data from the database."""
    try:
        results_query = db.query(
            role_table.Role.Id,
            role_table.Role.RoleName,
            role_table.Role.Description,
            role_table.Role.IsActive,
            role_table.Role.RoleType,
        )

        results = results_query.all()
        return {
            "roles": [
                dict(
                    zip(  # Wrap in a dict with "roles" key
                        ["Id", "RoleName", "Description", "IsActive", "RoleType"],
                        row,
                    ),
                )
                for row in results
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get roles: {e!s}",
        ) from e


def post_single_role(
    role_name: str,
    description: str,
    role_type: str,
    *,
    is_active: bool,
    db: Session,
) -> dict:
    """Create a single role in the database."""
    try:
        is_role_exist = role_already_created(role_name, db)
        if is_role_exist:
            return {"message": "Role already exists."}

        role_data = role_table.Role(
            RoleName=role_name,
            Description=description,
            IsActive=is_active,
            RoleType=role_type,
        )
        db.add(role_data)
        db.commit()
        is_role_created = role_already_created(role_name, db)
        if is_role_created:
            return {"message": "Role created successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to insert content: {e!s}",
        ) from e


def role_already_created(role_name: str, db: Session) -> bool:
    """Check if the role already exists in the database."""
    return bool(
        db.query(role_table.Role).filter(role_table.Role.RoleName == role_name).first(),
    )


def get_role_by_id(role_id: int, db: Session) -> bool:
    """Get the role by the role ID."""
    role_exist = db.query(role_table.Role).filter(role_table.Role.Id == role_id).first()
    return bool(role_exist)


def edit_single_role_data(role_update: RoleUpdate, db: Session) -> dict:
    """Edit a single role data in the database."""
    try:
        # Check if role exists
        if not get_role_by_id(role_update.role_id, db):
            return {"message": "Role does not exist"}

        # Fetch the existing role data
        role_data = (
            db.query(role_table.Role)
            .filter(
                role_table.Role.Id == role_update.role_id,
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
            db.query(role_table.Role).filter(role_table.Role.Id == role_id).delete(
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


def get_rolename_roletype_by_id(role_id: int, db: Session) -> tuple:
    """Get the role name and role type by the role ID."""
    role_name_role_type = (
        db.query(role_table.Role.RoleName, role_table.Role.RoleType)
        .filter(role_table.Role.Id == role_id)
        .first()
    )

    if role_name_role_type:
        return {
            "role_name": role_name_role_type[0],
            "role_type": role_name_role_type[1],
        }
    return "No data found"


def get_rolename_by_username_email(user_email: str, db: Session) -> str:
    """Get role by user email."""
    user_id = get_user_id_by_email(user_email, db)

    if user_id is None:
        return "No data found"

    role_name = (
        db.query(user_role_table.UserRole.RoleType)
        .filter(user_role_table.UserRole.UserId == user_id)
        .first()
    )

    if role_name:
        return role_name[0]  # Extract RoleType value from the tuple
    return "No data found"


def get_user_id_by_email(user_email: str, db: Session) -> int | None:
    """Retrieve user ID by email."""
    user = (
        db.query(user_table.User.Id).filter(user_table.User.Email == user_email).first()
    )

    if user:
        return user[0]  # Extract ID from the tuple
    return None
