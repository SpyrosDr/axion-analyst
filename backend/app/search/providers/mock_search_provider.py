# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

from app.search.output_schemas import EntitySearchResult, SearchSource


def search_entity(query: str, entity_type: str | None) -> EntitySearchResult:
    type_note = f" ({entity_type})" if entity_type else ""
    return EntitySearchResult(
        summary=(
            f"Mock background summary for {query!r}{type_note}. No real web search was "
            "performed -- SEARCH_PROVIDER=mock returns this canned result for local "
            "development and tests."
        ),
        sources=[
            SearchSource(
                title=f"Example source about {query}",
                url="https://example.com/mock-search-result",
                snippet=f"Placeholder snippet mentioning {query}.",
            )
        ],
    )
