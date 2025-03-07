"""Role table model for database."""

from sqlalchemy import Boolean, Column, Integer, String

from app.core.dependencies import Base


class Role(Base):
    """Role model class representing the Role table in database."""

    __tablename__ = "Role"
    __table_args__ = ({"schema": "radar_backend_v2"},)
    Id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    RoleName = Column(String, nullable=False)
    Description = Column(String, nullable=True)
    IsActive = Column(Boolean, default=False)
    RoleType = Column(String, nullable=False)

    def __repr__(self) -> str:
        """Return string representation of Role object.

        Returns
        -------
        str
            String representation showing role ID

        """
        return f"{self.Id}"


metadata = Base.metadata
