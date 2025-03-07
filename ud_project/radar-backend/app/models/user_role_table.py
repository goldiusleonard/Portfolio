"""User role table model for database."""

from sqlalchemy import Boolean, Column, Integer, String

from app.core.dependencies import Base


class UserRole(Base):
    """User role model class representing the UserRole table in database."""

    __tablename__ = "UserRole"
    __table_args__ = ({"schema": "radar_backend_v2"},)
    Id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    UserId = Column(Integer, nullable=False)
    RoleId = Column(Integer, nullable=False)
    RoleType = Column(String, nullable=False)
    IsActive = Column(Boolean, default=True)

    def __repr__(self) -> str:
        """Return string representation of UserRole object.

        Returns
        -------
        str
            String representation showing user role ID

        """
        return f"{self.Id}"


metadata = Base.metadata
