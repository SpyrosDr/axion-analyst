from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database.db import Base


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    title = Column(String, default="")
    type = Column(String, default="")
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    case = relationship("Case", back_populates="evidence_items")
