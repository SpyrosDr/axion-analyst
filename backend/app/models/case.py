# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database.db import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    context = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    # "open" | "in_review" | "closed" -- see case_service.ALLOWED_STATUSES.
    status = Column(String, nullable=False, default="open")
    created_at = Column(DateTime, server_default=func.now())
    # Nullable at the column level only so create_all() never chokes -- app
    # logic always sets this via case_service.create_case.
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    owner = relationship("User", back_populates="owned_cases")
    collaborator_links = relationship(
        "CaseCollaborator", back_populates="case", cascade="all, delete-orphan"
    )
    evidence_items = relationship(
        "Evidence", back_populates="case", cascade="all, delete-orphan"
    )
    entities = relationship(
        "Entity", back_populates="case", cascade="all, delete-orphan"
    )
    timeline_events = relationship(
        "TimelineEvent", back_populates="case", cascade="all, delete-orphan"
    )
    risk_assessments = relationship(
        "RiskAssessment", back_populates="case", cascade="all, delete-orphan"
    )
    reports = relationship(
        "Report", back_populates="case", cascade="all, delete-orphan"
    )
    activities = relationship(
        "CaseActivity", back_populates="case", cascade="all, delete-orphan"
    )
    entity_searches = relationship(
        "EntitySearch", back_populates="case", cascade="all, delete-orphan"
    )

    @property
    def collaborators(self):
        return [link.user for link in self.collaborator_links]

    @property
    def latest_risk_level(self):
        if not self.risk_assessments:
            return None
        return max(self.risk_assessments, key=lambda ra: ra.id).risk_level
