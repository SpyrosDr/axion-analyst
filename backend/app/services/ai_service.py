from app.ai import client as ai_client
from app.ai.providers.mock_provider import assess_case as mock_assess_case
from app.config import settings
from app.schemas.case_schema import CaseInput


def assess_case_risk(case: CaseInput) -> dict:
    if settings.AI_PROVIDER == "mock":
        return mock_assess_case(case)

    analysis = ai_client.analyze_case(
        context=case.context,
        description=case.description,
        evidence_texts=list(case.evidence_items),
    )
    risk = analysis.risk_assessment
    return {
        "provider": settings.AI_PROVIDER,
        "case_context": case.context,
        "risk_level": risk.risk_level,
        "risk_indicators": risk.risk_indicators,
        "next_steps": risk.next_steps,
        "draft_summary": analysis.report_sections.overview,
    }
