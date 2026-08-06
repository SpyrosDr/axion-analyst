# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.evidence import Evidence
from app.schemas.evidence_schema import EvidenceCreate


def add_evidence(db: Session, case_id: int, evidence_in: EvidenceCreate) -> Evidence:
    evidence = Evidence(
        case_id=case_id,
        title=evidence_in.title,
        type=evidence_in.type,
        content=evidence_in.content,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


def add_evidence_items(db: Session, case_id: int, items: list[str]) -> list[Evidence]:
    evidence_items = [
        Evidence(case_id=case_id, title="", type="", content=item) for item in items
    ]
    db.add_all(evidence_items)
    db.commit()
    for evidence in evidence_items:
        db.refresh(evidence)
    return evidence_items


def list_evidence(
    db: Session, case_id: int, *, limit: int | None = None, offset: int = 0
) -> list[Evidence]:
    # limit=None (the default) returns everything -- required by the
    # internal callers (entity extraction, timeline, risk assessment,
    # report generation) that need the case's complete evidence to
    # analyze, not a page of it. Only the GET /evidence route paginates,
    # by passing an explicit limit.
    query = (
        db.query(Evidence)
        .filter(Evidence.case_id == case_id)
        .order_by(Evidence.id)
        .offset(offset)
    )
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def get_evidence_or_404(db: Session, case_id: int, evidence_id: int) -> Evidence:
    # Scoped to case_id (not just Evidence.id) so an evidence_id that
    # belongs to some *other* case 404s here rather than resolving --
    # the caller already proved access to `case_id`, not to whatever case
    # actually owns that row.
    evidence = (
        db.query(Evidence)
        .filter(Evidence.id == evidence_id, Evidence.case_id == case_id)
        .first()
    )
    if evidence is None:
        raise HTTPException(
            status_code=404, detail=f"Evidence {evidence_id} not found"
        )
    return evidence
