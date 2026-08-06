# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

from app.ai.output_schemas import AICaseAnalysis
from app.ai.pseudonymizer import Pseudonymizer
from app.config import settings


class AIProviderError(Exception):
    """Raised when an AI provider call fails (network, API, or parsing error)."""


def analyze_case(
    context: str, description: str, evidence_texts: list[str]
) -> AICaseAnalysis:
    if settings.AI_PROVIDER == "openai":
        from app.ai.providers.openai_provider import analyze_case as impl
    elif settings.AI_PROVIDER == "anthropic":
        from app.ai.providers.anthropic_provider import analyze_case as impl
    else:
        raise ValueError(
            f"analyze_case() called with AI_PROVIDER={settings.AI_PROVIDER!r}; only "
            "'openai'/'anthropic' are valid here, callers must branch on 'mock' "
            "themselves before reaching this function"
        )

    # Confidential case data (person names, emails, account numbers) must not
    # leave the system in the clear -- swap them for consistent fake
    # stand-ins before the provider call, then restore the real values in
    # the structured result.
    pseudonymizer = Pseudonymizer()
    masked_context = pseudonymizer.pseudonymize(context)
    masked_description = pseudonymizer.pseudonymize(description)
    masked_evidence_texts = [pseudonymizer.pseudonymize(t) for t in evidence_texts]

    analysis = impl(masked_context, masked_description, masked_evidence_texts)
    return _restore_analysis(analysis, pseudonymizer)


def _restore_analysis(
    analysis: AICaseAnalysis, pseudonymizer: Pseudonymizer
) -> AICaseAnalysis:
    for entity in analysis.entities:
        entity.value = pseudonymizer.restore(entity.value)
    for event in analysis.timeline_events:
        event.description = pseudonymizer.restore(event.description)

    risk = analysis.risk_assessment
    risk.risk_indicators = [pseudonymizer.restore(item) for item in risk.risk_indicators]
    risk.next_steps = [pseudonymizer.restore(item) for item in risk.next_steps]

    sections = analysis.report_sections
    sections.overview = pseudonymizer.restore(sections.overview)
    sections.evidence = pseudonymizer.restore(sections.evidence)
    sections.entities = pseudonymizer.restore(sections.entities)
    sections.timeline = pseudonymizer.restore(sections.timeline)
    sections.risk_assessment = pseudonymizer.restore(sections.risk_assessment)
    sections.recommendations = pseudonymizer.restore(sections.recommendations)

    return analysis
