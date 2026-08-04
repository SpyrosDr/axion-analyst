# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database.db import Base


class EntitySearch(Base):
    __tablename__ = "entity_searches"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, nullable=False)
    entity_type = Column(String, nullable=True)
    provider = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    sources = Column(JSON, nullable=False, default=list)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    case = relationship("Case", back_populates="entity_searches")
    created_by = relationship("User")
