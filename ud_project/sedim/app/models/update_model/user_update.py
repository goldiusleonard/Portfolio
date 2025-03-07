"""User update model."""

from pydantic import BaseModel


class UserUpdate(BaseModel):
    """model for the user update."""

    user_id: int
    user_name: str
    password_hash: str
    email: str
    is_active: bool
