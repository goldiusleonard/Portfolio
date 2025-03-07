"""User endpoint module."""


# fastapi

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# Other imports
from app.api.endpoints.functions import user_function
from app.core.dependencies import get_db, get_db_for_post
from app.models.update_model.user_update import UserUpdate

user_module = APIRouter()

###############USERS#######################


@user_module.get("/get_all_users/")
def get_all_users(db: Session = Depends(get_db)) -> dict:
    """Get all users."""
    try:
        # Get all users from the database
        users = user_function.get_all_users_data(db=db)
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
        return {"users": users}


@user_module.post("/insert_single_user/")
def insert_user_handle(
    user_name: str,
    password_hash: str,
    email: str,
    *,
    is_active: bool,
    db: Session = Depends(get_db_for_post),
) -> dict:
    """Insert a single user."""
    return user_function.post_single_user(
        user_name=user_name,
        password_hash=password_hash,
        email=email,
        is_active=is_active,  # Must use keyword argument
        db=db,  # Must use keyword argument
    )


@user_module.put("/edit_single_user/")
def edit_single_user(
    user_data: UserUpdate,  # Use Pydantic model as request body
    db: Session = Depends(get_db_for_post),
) -> dict:
    """Edit a single user."""
    user_update = UserUpdate(
        user_id=user_data.user_id,
        user_name=user_data.user_name,
        password_hash=user_data.password_hash,
        email=user_data.email,
        is_active=user_data.is_active,
    )
    return user_function.edit_single_user_data(user_update=user_update, db=db)


@user_module.delete("/delete_single_user/")
def delete_single_user(user_id: int, db: Session = Depends(get_db_for_post)) -> dict:
    """Delete a single user."""
    return user_function.delete_single_user(user_id, db)


@user_module.get("/get_email_userName_by_id/")
def get_email_user_name_by_id(user_id: int, db: Session = Depends(get_db)) -> dict:
    """Get email and user name by user ID."""
    return user_function.get_email_user_name_by_id(user_id, db)


###############USERS########################
