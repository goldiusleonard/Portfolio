"""Login authentication endpoints."""

# fastapi
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# sqlalchemy
from app.api.endpoints.functions import (
    login_authentication_function,
    user_role_function,
)
from app.auth import auth

# import
from app.core.dependencies import get_db

login_authentication_module = APIRouter()


###############login_authentication#######################


@login_authentication_module.post("/token")
def login_for_access_token(
    email: str,
    password: str,
    db: Session = Depends(get_db),
) -> dict:
    """Login for access token."""
    user = login_authentication_function.get_user_by_email_and_password(
        db,
        email,
        password,
    )
    if user:
        role = user_role_function.get_permission_type_by_user_id_from_user_role(
            user.Id,
            db,
        )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_DELTA)
    access_token = auth.create_access_token(
        data={"sub": user.Email},
        expires_delta=access_token_expires,
    )
    return {
        "user_name": user.UserName,
        "email": user.Email,
        "role": role,
        "access_token": access_token,
        "token_type": "bearer",
    }


###############login_authentication#######################
