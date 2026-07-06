from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.db import Base


class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    entity_type = Column(String, nullable=False)
    value = Column(String, nullable=False)
    source_evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=True)

    case = relationship("Case", back_populates="entities")
