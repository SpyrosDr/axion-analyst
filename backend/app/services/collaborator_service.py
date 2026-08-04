# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.case_collaborator import CaseCollaborator
from app.models.user import User
from app.services import activity_service, permissions, user_service


def _require_manage(case: Case, requesting_user: User) -> None:
    role = permissions.effective_role(case, requesting_user)
    if not permissions.can_manage(role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have rights to manage collaborators on this case",
        )


def _validate_role(role: str) -> None:
    if role not in permissions.ALLOWED_CASE_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")


def _get_link(db: Session, case: Case, user_id: int) -> CaseCollaborator | None:
    return (
        db.query(CaseCollaborator)
        .filter(
            CaseCollaborator.case_id == case.id, CaseCollaborator.user_id == user_id
        )
        .first()
    )


def _get_link_or_404(db: Session, case: Case, user_id: int) -> CaseCollaborator:
    link = _get_link(db, case, user_id)
    if link is None:
        raise HTTPException(status_code=404, detail="Collaborator not found")
    return link


def add_collaborator(
    db: Session, case: Case, username: str, role: str, requesting_user: User
) -> CaseCollaborator:
    _require_manage(case, requesting_user)
    _validate_role(role)

    target = user_service.get_user_by_username(db, username)
    if target is None:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")
    if target.id == case.owner_id:
        raise HTTPException(status_code=400, detail="Owner already has access")

    link = _get_link(db, case, target.id)
    if link is None:
        link = CaseCollaborator(case_id=case.id, user_id=target.id, role=role)
        db.add(link)
        action, detail = "collaborator_added", (
            f"added {target.username} as {role}"
        )
    else:
        link.role = role
        action, detail = "collaborator_role_changed", (
            f"changed {target.username}'s role to {role}"
        )
    db.commit()
    db.refresh(link)
    activity_service.log(db, case.id, requesting_user, action, detail)
    return link


def list_collaborators(case: Case) -> list[CaseCollaborator]:
    return case.collaborator_links


def update_collaborator_role(
    db: Session, case: Case, user_id: int, role: str, requesting_user: User
) -> CaseCollaborator:
    _require_manage(case, requesting_user)
    _validate_role(role)

    link = _get_link_or_404(db, case, user_id)
    link.role = role
    db.commit()
    db.refresh(link)
    activity_service.log(
        db,
        case.id,
        requesting_user,
        "collaborator_role_changed",
        f"changed {link.user.username}'s role to {role}",
    )
    return link


def remove_collaborator(
    db: Session, case: Case, user_id: int, requesting_user: User
) -> None:
    _require_manage(case, requesting_user)

    link = _get_link_or_404(db, case, user_id)
    removed_username = link.user.username
    db.delete(link)
    db.commit()
    activity_service.log(
        db,
        case.id,
        requesting_user,
        "collaborator_removed",
        f"removed {removed_username}",
    )
