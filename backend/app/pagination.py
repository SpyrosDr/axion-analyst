# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

"""Shared pagination for list endpoints (cases, evidence, activity, entity
searches) that would otherwise return every matching row unbounded. `limit`
defaults small and is capped so a client can't force an unbounded query
just by omitting the param or passing an enormous one; `offset` has no
upper bound since page depth is inherently unbounded."""

from dataclasses import dataclass

from fastapi import Query

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


@dataclass
class Pagination:
    limit: int
    offset: int


def pagination_params(
    limit: int = Query(
        DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Max rows to return."
    ),
    offset: int = Query(0, ge=0, description="Rows to skip, for the next page."),
) -> Pagination:
    return Pagination(limit=limit, offset=offset)
