from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from app.database.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())
    display_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    avatar_color = Column(String, nullable=True)
    # "none" | "viewer" | "editor" | "manager" -- see app/services/permissions.py.
    # Applies to every case in the system, independent of is_admin.
    global_role = Column(String, nullable=False, default="none")

    owned_cases = relationship("Case", back_populates="owner")
    collaborations = relationship(
        "CaseCollaborator", back_populates="user", cascade="all, delete-orphan"
    )
