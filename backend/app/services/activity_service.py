# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.case_activity import CaseActivity
from app.models.user import User


def log(
    db: Session, case_id: int, actor: User, action: str, detail: str | None = None
) -> CaseActivity:
    entry = CaseActivity(
        case_id=case_id, actor_id=actor.id, action=action, detail=detail
    )
    db.add(entry)
    db.commit()
    return entry


def list_activity(
    db: Session, case: Case, *, limit: int = 50, offset: int = 0
) -> list[CaseActivity]:
    # Queries CaseActivity directly (rather than reading case.activities)
    # so pagination happens in SQL instead of loading every activity row
    # for the case into memory first.
    return (
        db.query(CaseActivity)
        .filter(CaseActivity.case_id == case.id)
        .order_by(CaseActivity.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
