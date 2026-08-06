# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

from pydantic import BaseModel, ConfigDict


class SearchSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    url: str
    snippet: str = ""


class EntitySearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    sources: list[SearchSource]
