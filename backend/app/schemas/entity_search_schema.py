# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.user_schema import UserSummary


class EntitySearchCreate(BaseModel):
    query: str
    entity_type: str | None = None
    case_id: int | None = None


class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    url: str
    snippet: str = ""


class EntitySearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query: str
    entity_type: str | None = None
    provider: str
    summary: str
    sources: list[SourceResponse]
    case_id: int | None = None
    created_by: UserSummary | None = None
    created_at: datetime
