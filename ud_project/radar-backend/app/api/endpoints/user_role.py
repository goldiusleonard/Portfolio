"""User role endpoint module for managing user role mappings."""

# fastapi

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.endpoints.functions import user_role_function
from app.core.dependencies import get_db

user_role_module = APIRouter()


###############ROLES#######################
@user_role_module.get("/get_all_user_roles/")
def get_all_roles(db: Session = Depends(get_db)) -> dict:
    """Get all user role mappings."""
    try:
        # Get all user_role from the database
        user_role = user_role_function.get_all_user_role_data(db=db)
    except SQLAlchemyError as e:
        # Handle SQLAlchemy specific exceptions
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {e!s}",
        ) from e
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(
            status_code=400,
            detail=f"Unexpected error: {e!s}",
        ) from e
    else:
        # Return users as a response
        return {"user_role": user_role}


@user_role_module.post("/create_user_role/")
def insert_user_handle(
    user_id: int,
    role_id: int,
    permissaon_type: str,
    db: Session = Depends(get_db),
    *,
    is_active: bool,
) -> dict:
    """Create a new user role mapping.

    Parameters
    ----------
    user_id : int
        ID of the user to map
    role_id : int
        ID of the role to map
    permissaon_type : str
        Type of permission to grant
    is_active : bool
        Whether the role mapping is active
    db : Session
        Database session

    Returns
    -------
    dict
        The created user role mapping

    """
    return user_role_function.map_single_user_role(
        user_id,
        role_id,
        permissaon_type,
        is_active=is_active,  # Pass as keyword arg
        db=db,
    )


###############ROLES########################
