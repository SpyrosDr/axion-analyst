# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

import httpx

from app.config import settings
from app.search.client import SearchProviderError
from app.search.output_schemas import EntitySearchResult, SearchSource

_TAVILY_URL = "https://api.tavily.com/search"
_TIMEOUT_SECONDS = 20.0


def search_entity(query: str, entity_type: str | None) -> EntitySearchResult:
    if not settings.TAVILY_API_KEY:
        raise SearchProviderError(
            "TAVILY_API_KEY is not set; add it to backend/.env to use SEARCH_PROVIDER=tavily"
        )

    search_query = f"{query} {entity_type}" if entity_type else query

    try:
        response = httpx.post(
            _TAVILY_URL,
            json={
                "api_key": settings.TAVILY_API_KEY,
                "query": search_query,
                "include_answer": True,
                "max_results": 5,
            },
            timeout=_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()

        summary = data.get("answer") or "No summary was returned for this search."
        sources = [
            SearchSource(
                title=result.get("title", "") or result.get("url", ""),
                url=result.get("url", ""),
                snippet=result.get("content", ""),
            )
            for result in data.get("results", [])
        ]

        return EntitySearchResult(summary=summary, sources=sources)
    except SearchProviderError:
        raise
    except Exception as exc:  # network, API, or parsing failure
        raise SearchProviderError(f"Tavily request failed: {exc}") from exc
