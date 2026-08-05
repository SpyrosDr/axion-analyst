# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.models.case import Case
from app.models.case_collaborator import CaseCollaborator
from app.models.user import User
from app.schemas.case_schema import CaseCreate
from app.services import activity_service, evidence_service, permissions

ALLOWED_STATUSES = {"open", "in_review", "closed"}


def status_label(status: str) -> str:
    # "in_review" -> "In Review", for human-readable activity entries.
    return status.replace("_", " ").title()


def create_case(db: Session, case_in: CaseCreate, owner: User) -> Case:
    case = Case(
        context=case_in.context, description=case_in.description, owner_id=owner.id
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    if case_in.evidence_items:
        evidence_service.add_evidence_items(db, case.id, case_in.evidence_items)
        db.refresh(case)

    activity_service.log(db, case.id, owner, "case_created", "created the case")
    return case


def _accessible_query(db: Session, user: User):
    # A global role (or is_admin) grants access to every case, not just ones
    # the user owns or was explicitly added to as a collaborator.
    if permissions.has_global_access(user):
        return db.query(Case)
    return (
        db.query(Case)
        .outerjoin(CaseCollaborator, CaseCollaborator.case_id == Case.id)
        .filter(or_(Case.owner_id == user.id, CaseCollaborator.user_id == user.id))
        .distinct()
    )


def get_case(db: Session, case_id: int, user: User) -> Case | None:
    return _accessible_query(db, user).filter(Case.id == case_id).first()


def get_case_or_404(db: Session, case_id: int, user: User) -> Case:
    case = get_case(db, case_id, user)
    if case is None:
        # Don't distinguish "doesn't exist" from "you can't see it" -- avoids
        # leaking case existence to users with no access.
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return case


def get_case_by_id_or_404(db: Session, case_id: int) -> Case:
    """Unfiltered lookup for internal service-to-service calls, where access
    was already verified once at the route boundary via get_case_or_404."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return case


def list_cases(
    db: Session, user: User, *, limit: int | None = None, offset: int = 0
) -> list[Case]:
    # Eager-load everything the list response touches per case (owner,
    # my_role via collaborator_links, latest_risk_level via risk_assessments)
    # so serialization doesn't issue three lazy queries per row.
    query = (
        _accessible_query(db, user)
        .options(
            selectinload(Case.owner),
            selectinload(Case.collaborator_links),
            selectinload(Case.risk_assessments),
        )
        .order_by(Case.id)
        .offset(offset)
    )
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def require_edit(case: Case, user: User) -> None:
    if not permissions.can_edit(permissions.effective_role(case, user)):
        raise HTTPException(
            status_code=403, detail="You do not have edit access to this case"
        )


def require_manage(case: Case, user: User) -> None:
    if not permissions.can_manage(permissions.effective_role(case, user)):
        raise HTTPException(
            status_code=403, detail="You do not have manage access to this case"
        )


def require_open(case: Case) -> None:
    if case.status == "closed":
        raise HTTPException(
            status_code=409,
            detail="Case is closed — reopen it to make changes",
        )


def update_status(db: Session, case: Case, status: str, actor: User) -> Case:
    if status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")

    if status == case.status:
        return case

    old_status = case.status
    case.status = status
    db.commit()
    db.refresh(case)
    activity_service.log(
        db,
        case.id,
        actor,
        "status_changed",
        f"changed status from {status_label(old_status)} to {status_label(status)}",
    )
    return case


def delete_case(db: Session, case: Case, requesting_user: User) -> None:
    if case.owner_id != requesting_user.id:
        # The requester has already proven they can see the case, so a 403
        # here leaks nothing new (same reasoning as collaborator management).
        raise HTTPException(
            status_code=403, detail="Only the case owner can delete a case"
        )
    db.delete(case)
    db.commit()
