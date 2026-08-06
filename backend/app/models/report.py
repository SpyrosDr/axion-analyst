# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import relationship

from app.database.db import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    summary_text = Column(Text, nullable=False)
    sections = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, server_default=func.now())

    case = relationship("Case", back_populates="reports")
