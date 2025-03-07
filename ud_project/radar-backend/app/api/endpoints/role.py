"""Role endpoints."""
# fastapi

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# sqlalchemy
from app.api.endpoints.functions import role_function

# import
from app.core.dependencies import get_db
from app.models.update_model.role_update import RoleUpdate

role_module = APIRouter()


@role_module.get("/get_all_roles/")
def get_all_roles(db: Session = Depends(get_db)) -> dict:
    """Get all roles."""
    return role_function.get_all_roles_data(db)


@role_module.post("/insert_single_role/")
def insert_user_handle(
    role_name: str,
    description: str,
    *,
    is_active: bool,
    role_type: str,
    db: Session = Depends(get_db),
) -> dict:
    """Insert a single role."""
    return role_function.post_single_role(
        role_name=role_name,
        description=description,
        role_type=role_type,
        is_active=is_active,
        db=db,
    )


@role_module.put("/edit_single_role/")
def edit_single_role(
    role_update: RoleUpdate,  # Use Pydantic model as request body
    db: Session = Depends(get_db),
) -> dict:
    """Edit a single role."""
    role_updated = RoleUpdate(
        role_id=role_update.role_id,
        role_name=role_update.role_name,
        description=role_update.description,
        role_type=role_update.role_type,
        is_active=role_update.is_active,
    )

    return role_function.edit_single_role_data(
        role_update=role_updated,
        db=db,
    )


@role_module.delete("/delete_single_role/")
def delete_single_role(role_id: int, db: Session = Depends(get_db)) -> dict:
    """Delete a single role."""
    return role_function.delete_single_role(role_id, db)


@role_module.get("/get_roleName_roleType_by_id/")
def get_role_name_role_type_by_id(role_id: int, db: Session = Depends(get_db)) -> dict:
    """Get role name and role type by id."""
    return role_function.get_rolename_roletype_by_id(role_id, db)


@role_module.get("/get_role_name/")
def get_user_role(user_email: str, db: Session = Depends(get_db)) -> str:
    """Get role by user_name and user_email."""
    return role_function.get_rolename_by_username_email(user_email, db)


###############ROLES########################
