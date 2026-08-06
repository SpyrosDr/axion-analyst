# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

from openai import OpenAI

from app.ai.client import AIProviderError
from app.ai.output_schemas import AICaseAnalysis
from app.ai.prompts import SYSTEM_PROMPT, build_user_message
from app.config import settings

_MAX_TOKENS = 4096


def analyze_case(
    context: str, description: str, evidence_texts: list[str]
) -> AICaseAnalysis:
    if not settings.OPENAI_MODEL:
        raise AIProviderError(
            "OPENAI_MODEL is not set; add OPENAI_MODEL=<a current OpenAI model that "
            "supports Structured Outputs> to backend/.env"
        )

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    user_message = build_user_message(context, description, evidence_texts)

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            max_tokens=_MAX_TOKENS,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "case_analysis",
                    "schema": AICaseAnalysis.model_json_schema(),
                    "strict": True,
                },
            },
        )
        content = response.choices[0].message.content
        if content is None:
            raise AIProviderError("OpenAI response contained no content")
        return AICaseAnalysis.model_validate_json(content)
    except AIProviderError:
        raise
    except Exception as exc:  # network, API, or parsing failure
        raise AIProviderError(f"OpenAI request failed: {exc}") from exc
