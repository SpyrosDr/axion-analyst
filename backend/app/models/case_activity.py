# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.database.db import Base


class CaseActivity(Base):
    """Append-only per-case audit trail entry ("who did what, when")."""

    __tablename__ = "case_activities"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    # Nullable so history survives if user deletion is ever added.
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # Machine-readable key, e.g. "evidence_added", "status_changed".
    action = Column(String, nullable=False)
    # Human-readable description, e.g. 'added evidence "Invoice #1001"'.
    detail = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    case = relationship("Case", back_populates="activities")
    actor = relationship("User")
