# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

from anthropic import Anthropic

from app.config import settings
from app.search.client import SearchProviderError
from app.search.output_schemas import EntitySearchResult, SearchSource
from app.search.prompts import SYSTEM_PROMPT, build_user_message

_MAX_TOKENS = 2048


def search_entity(query: str, entity_type: str | None) -> EntitySearchResult:
    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    user_message = build_user_message(query, entity_type)

    try:
        response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
        )

        summary_parts: list[str] = []
        sources: list[SearchSource] = []
        seen_urls: set[str] = set()

        for block in response.content:
            if block.type == "text":
                summary_parts.append(block.text)
                for citation in getattr(block, "citations", None) or []:
                    url = getattr(citation, "url", None)
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    sources.append(
                        SearchSource(
                            title=getattr(citation, "title", "") or url,
                            url=url,
                        )
                    )
            elif block.type == "web_search_tool_result":
                for result in getattr(block, "content", None) or []:
                    url = getattr(result, "url", None)
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    sources.append(
                        SearchSource(
                            title=getattr(result, "title", "") or url,
                            url=url,
                        )
                    )

        summary = "\n".join(summary_parts).strip()
        if not summary:
            raise SearchProviderError("Anthropic response contained no text content")

        return EntitySearchResult(summary=summary, sources=sources)
    except SearchProviderError:
        raise
    except Exception as exc:  # network, API, or parsing failure
        raise SearchProviderError(f"Anthropic web search request failed: {exc}") from exc
