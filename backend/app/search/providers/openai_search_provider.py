# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

from openai import OpenAI

from app.config import settings
from app.search.client import SearchProviderError
from app.search.output_schemas import EntitySearchResult, SearchSource
from app.search.prompts import SYSTEM_PROMPT, build_user_message


def search_entity(query: str, entity_type: str | None) -> EntitySearchResult:
    if not settings.OPENAI_MODEL:
        raise SearchProviderError(
            "OPENAI_MODEL is not set; add OPENAI_MODEL=<a current OpenAI model that "
            "supports the hosted web_search tool> to backend/.env"
        )

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    user_message = build_user_message(query, entity_type)

    try:
        response = client.responses.create(
            model=settings.OPENAI_MODEL,
            tools=[{"type": "web_search"}],
            instructions=SYSTEM_PROMPT,
            input=user_message,
        )

        summary = response.output_text
        if not summary:
            raise SearchProviderError("OpenAI response contained no output text")

        sources: list[SearchSource] = []
        seen_urls: set[str] = set()
        for item in response.output:
            if getattr(item, "type", None) != "message":
                continue
            for content in item.content:
                for annotation in getattr(content, "annotations", []) or []:
                    if getattr(annotation, "type", None) != "url_citation":
                        continue
                    url = annotation.url
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                    sources.append(
                        SearchSource(
                            title=getattr(annotation, "title", "") or url,
                            url=url,
                        )
                    )

        return EntitySearchResult(summary=summary, sources=sources)
    except SearchProviderError:
        raise
    except Exception as exc:  # network, API, or parsing failure
        raise SearchProviderError(f"OpenAI web search request failed: {exc}") from exc
