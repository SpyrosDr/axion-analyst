# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

from app.config import settings
from app.search.output_schemas import EntitySearchResult


class SearchProviderError(Exception):
    """Raised when a search provider call fails (network, API, or parsing error)."""


def search_entity(query: str, entity_type: str | None) -> EntitySearchResult:
    # Unlike app.ai.client.analyze_case, the query is NOT pseudonymized --
    # the entire point is to search the real entity name on the public web,
    # not to protect confidential case data.
    if settings.SEARCH_PROVIDER == "mock":
        from app.search.providers.mock_search_provider import search_entity as impl
    elif settings.SEARCH_PROVIDER == "openai":
        from app.search.providers.openai_search_provider import search_entity as impl
    elif settings.SEARCH_PROVIDER == "anthropic":
        from app.search.providers.anthropic_search_provider import (
            search_entity as impl,
        )
    elif settings.SEARCH_PROVIDER == "tavily":
        from app.search.providers.tavily_search_provider import search_entity as impl
    else:
        raise ValueError(
            f"search_entity() called with SEARCH_PROVIDER={settings.SEARCH_PROVIDER!r}; "
            "only 'mock'/'openai'/'anthropic'/'tavily' are valid"
        )

    return impl(query, entity_type)
