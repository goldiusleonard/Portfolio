"""User table model for database."""

from sqlalchemy import TIMESTAMP, Boolean, Column, Integer, String, func

from app.core.dependencies import Base


class User(Base):
    """User model class representing the User table in database."""

    __tablename__ = "User"
    __table_args__ = ({"schema": "radar_backend_v2"},)
    Id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    UserName = Column(String, nullable=False)
    PasswordHash = Column(String, nullable=False)
    Email = Column(String, nullable=False)
    IsActive = Column(Boolean)
    CreatedAt = Column(
        TIMESTAMP,
        nullable=False,
        server_default=func.current_timestamp(),
    )

    def __repr__(self) -> str:
        """Return string representation of User object.

        Returns
        -------
        str
            String representation showing user ID

        """
        return f"{self.id,self.IsActive}"


metadata = Base.metadata
