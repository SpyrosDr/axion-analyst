from app.ai.output_schemas import AICaseAnalysis
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
    return impl(context, description, evidence_texts)
