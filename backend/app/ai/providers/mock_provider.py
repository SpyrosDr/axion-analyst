from app.schemas.case_schema import CaseInput


def assess_case(case: CaseInput) -> dict:
    risk_indicators = []

    text = f"{case.context} {case.description} {' '.join(case.evidence_items)}".lower()

    if "invoice" in text or "vendor" in text:
        risk_indicators.append("Possible vendor or procurement fraud indicators")

    if "account" in text or "login" in text:
        risk_indicators.append("Possible account takeover or identity-related indicators")

    if "cash" in text or "transfer" in text or "transaction" in text:
        risk_indicators.append("Possible suspicious financial movement indicators")

    if not risk_indicators:
        risk_indicators.append("No clear predefined fraud indicators detected yet")

    return {
        "provider": "mock",
        "case_context": case.context,
        "risk_level": "medium" if len(risk_indicators) >= 2 else "low",
        "risk_indicators": risk_indicators,
        "next_steps": [
            "Collect supporting evidence",
            "Identify involved entities",
            "Build a timeline of events",
            "Document assumptions and open questions",
        ],
        "draft_summary": f"Initial review of the case suggests: {', '.join(risk_indicators)}.",
    }
