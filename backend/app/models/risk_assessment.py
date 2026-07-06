from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.database.db import Base


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    risk_level = Column(String, nullable=False)
    risk_indicators = Column(JSON, nullable=False, default=list)
    next_steps = Column(JSON, nullable=False, default=list)
    provider = Column(String, nullable=False, default="mock")
    created_at = Column(DateTime, server_default=func.now())

    case = relationship("Case", back_populates="risk_assessments")
