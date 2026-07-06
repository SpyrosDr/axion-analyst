from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database.db import Base


class CaseCollaborator(Base):
    __tablename__ = "case_collaborators"
    __table_args__ = (UniqueConstraint("case_id", "user_id", name="uq_case_user"),)

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    # "viewer" | "editor" | "manager" -- see app/services/permissions.py.
    role = Column(String, nullable=False, default="viewer")

    case = relationship("Case", back_populates="collaborator_links")
    user = relationship("User", back_populates="collaborations")
