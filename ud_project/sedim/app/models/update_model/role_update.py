"""docstring for role update."""

from pydantic import BaseModel


class RoleUpdate(BaseModel):
    """Docstring for role update."""

    role_id: int
    role_name: str
    description: str
    role_type: str
    is_active: bool
