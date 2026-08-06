# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func
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


def _find_cached_result(
    db: Session, query: str, entity_type: str | None
) -> EntitySearch | None:
    """Look up a recent EntitySearch for the same (query, entity_type,
    provider) to avoid re-hitting the search provider. The result content is
    about a public entity, not confidential case data (see the comment in
    app.search.client), so it's safe to reuse across cases and users --
    only the provider call is skipped, a fresh row is still written for
    whoever asked this time."""
    ttl = settings.SEARCH_CACHE_TTL_SECONDS
    if ttl <= 0:
        return None

    # Naive UTC to match created_at, which is set by the DB's func.now()
    # (CURRENT_TIMESTAMP) -- naive on SQLite. A tz-aware value here would
    # compare incorrectly against that stored, offset-less string.
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=ttl)
    return (
        db.query(EntitySearch)
        .filter(
            func.lower(func.trim(EntitySearch.query)) == query.strip().lower(),
            EntitySearch.entity_type == entity_type,
            EntitySearch.provider == settings.SEARCH_PROVIDER,
            EntitySearch.created_at >= cutoff,
        )
        .order_by(EntitySearch.id.desc())
        .first()
    )


def run_search(db: Session, data: EntitySearchCreate, user: User) -> EntitySearch:
    if data.case_id is not None:
        # Persisting a search against a case is a write to that case's
        # record, same access bar as adding evidence.
        _require_case_access(db, data.case_id, user, edit=True)

    cached = _find_cached_result(db, data.query, data.entity_type)
    if cached is not None:
        summary, sources = cached.summary, cached.sources
    else:
        result = search_client.search_entity(data.query, data.entity_type)
        summary = result.summary
        sources = [source.model_dump() for source in result.sources]

    search = EntitySearch(
        query=data.query,
        entity_type=data.entity_type,
        provider=settings.SEARCH_PROVIDER,
        summary=summary,
        sources=sources,
        case_id=data.case_id,
        created_by_id=user.id,
    )
    db.add(search)
    db.commit()
    db.refresh(search)
    return search


def list_searches(
    db: Session,
    user: User,
    case_id: int | None,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[EntitySearch]:
    if case_id is not None:
        _require_case_access(db, case_id, user, edit=False)
        query = db.query(EntitySearch).filter(EntitySearch.case_id == case_id)
    else:
        query = db.query(EntitySearch).filter(EntitySearch.created_by_id == user.id)

    return query.order_by(EntitySearch.id.desc()).offset(offset).limit(limit).all()


def get_search(db: Session, search_id: int, user: User) -> EntitySearch:
    search = db.query(EntitySearch).filter(EntitySearch.id == search_id).first()
    if search is None:
        raise HTTPException(status_code=404, detail=f"Search {search_id} not found")

    if search.case_id is not None:
        _require_case_access(db, search.case_id, user, edit=False)
    elif search.created_by_id != user.id and not permissions.has_global_access(user):
        raise HTTPException(status_code=404, detail=f"Search {search_id} not found")

    return search
