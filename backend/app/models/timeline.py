from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.db import Base


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    event_date_raw = Column(String, nullable=True)
    event_date = Column(DateTime, nullable=True)
    description = Column(Text, nullable=False)
    source_evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=True)
    sequence_order = Column(Integer, nullable=False)

    case = relationship("Case", back_populates="timeline_events")
