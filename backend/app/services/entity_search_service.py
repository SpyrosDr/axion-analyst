# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.models.entity_search import EntitySearch
from app.models.user import User
from app.schemas.entity_search_schema import EntitySearchCreate
from app.search import client as search_client
from app.services import case_service, permissions


def _require_case_access(db: Session, case_id: int, user: User, *, edit: bool):
    case = case_service.get_case_or_404(db, case_id, user)
    if edit:
        case_service.require_edit(case, user)
    return case


def run_search(db: Session, data: EntitySearchCreate, user: User) -> EntitySearch:
    if data.case_id is not None:
        # Persisting a search against a case is a write to that case's
        # record, same access bar as adding evidence.
        _require_case_access(db, data.case_id, user, edit=True)

    result = search_client.search_entity(data.query, data.entity_type)

    search = EntitySearch(
        query=data.query,
        entity_type=data.entity_type,
        provider=settings.SEARCH_PROVIDER,
        summary=result.summary,
        sources=[source.model_dump() for source in result.sources],
        case_id=data.case_id,
        created_by_id=user.id,
    )
    db.add(search)
    db.commit()
    db.refresh(search)
    return search


def list_searches(
    db: Session, user: User, case_id: int | None
) -> list[EntitySearch]:
    if case_id is not None:
        _require_case_access(db, case_id, user, edit=False)
        return (
            db.query(EntitySearch)
            .filter(EntitySearch.case_id == case_id)
            .order_by(EntitySearch.id.desc())
            .all()
        )

    return (
        db.query(EntitySearch)
        .filter(EntitySearch.created_by_id == user.id)
        .order_by(EntitySearch.id.desc())
        .all()
    )


def get_search(db: Session, search_id: int, user: User) -> EntitySearch:
    search = db.query(EntitySearch).filter(EntitySearch.id == search_id).first()
    if search is None:
        raise HTTPException(status_code=404, detail=f"Search {search_id} not found")

    if search.case_id is not None:
        _require_case_access(db, search.case_id, user, edit=False)
    elif search.created_by_id != user.id and not permissions.has_global_access(user):
        raise HTTPException(status_code=404, detail=f"Search {search_id} not found")

    return search
