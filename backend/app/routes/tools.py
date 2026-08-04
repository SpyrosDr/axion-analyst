# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.db import get_db
from app.models.user import User
from app.schemas.entity_search_schema import EntitySearchCreate, EntitySearchResponse
from app.services import entity_search_service

router = APIRouter(prefix="/tools", tags=["Tools"])


@router.post("/entity-search", response_model=EntitySearchResponse)
def create_entity_search(
    search_in: EntitySearchCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return entity_search_service.run_search(db, search_in, user)


@router.get("/entity-search", response_model=list[EntitySearchResponse])
def list_entity_searches(
    case_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return entity_search_service.list_searches(db, user, case_id)


@router.get("/entity-search/{search_id}", response_model=EntitySearchResponse)
def get_entity_search(
    search_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return entity_search_service.get_search(db, search_id, user)
