from anthropic import Anthropic

from app.ai.client import AIProviderError
from app.ai.output_schemas import AICaseAnalysis
from app.ai.prompts import SYSTEM_PROMPT, build_user_message
from app.config import settings

_MAX_TOKENS = 4096
_TOOL_NAME = "submit_case_analysis"


def analyze_case(
    context: str, description: str, evidence_texts: list[str]
) -> AICaseAnalysis:
    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    user_message = build_user_message(context, description, evidence_texts)

    try:
        response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
            tools=[
                {
                    "name": _TOOL_NAME,
                    "description": (
                        "Submit the structured case analysis: extracted entities, "
                        "a chronological timeline, a risk assessment, and draft "
                        "report sections."
                    ),
                    "input_schema": AICaseAnalysis.model_json_schema(),
                    "strict": True,
                }
            ],
            tool_choice={"type": "tool", "name": _TOOL_NAME},
        )
        tool_use_block = next(
            (block for block in response.content if block.type == "tool_use"),
            None,
        )
        if tool_use_block is None:
            raise AIProviderError("Anthropic response contained no tool_use block")
        return AICaseAnalysis.model_validate(tool_use_block.input)
    except AIProviderError:
        raise
    except Exception as exc:  # network, API, or parsing failure
        raise AIProviderError(f"Anthropic request failed: {exc}") from exc
