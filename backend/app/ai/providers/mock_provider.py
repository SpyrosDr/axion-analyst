# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

from app.schemas.case_schema import CaseInput


def assess_case(case: CaseInput) -> dict:
    """Return transparent, deterministic *signals* for local demos.

    This is intentionally not a decision engine. The mock provider makes the
    demo useful without an API key, while leaving the investigator to decide
    what the facts mean.
    """
    risk_indicators = []

    text = f"{case.context} {case.description} {' '.join(case.evidence_items)}".lower()

    if "invoice" in text or "vendor" in text:
        risk_indicators.append("Vendor or procurement activity requires investigator review")

    if any(marker in text for marker in ("same bank", "bank account matches", "matches the direct deposit", "shares the same account", "related party")):
        risk_indicators.append("Potential related-party connection: vendor and employee bank details appear linked")

    if any(marker in text for marker in ("bypass", "two-person", "exception approval", "approval exception")):
        risk_indicators.append("Policy-exception signal: standard approval control may not have been followed")

    if any(marker in text for marker in ("no supporting", "missing support", "cannot locate support", "no contract", "no statement of work", "missing invoice")):
        risk_indicators.append("Missing-support signal: payment documentation appears incomplete")

    if any(marker in text for marker in ("high-risk geography", "high risk geography", "offshore", "weekend payment", "quarter-end", "month-end")):
        risk_indicators.append("Payment-pattern signal: timing or geography merits additional review")

    if not ("invoice" in text or "vendor" in text) and ("account" in text or "login" in text):
        risk_indicators.append("Possible account takeover or identity-related indicators")

    if not ("invoice" in text or "vendor" in text) and ("cash" in text or "transfer" in text or "transaction" in text):
        risk_indicators.append("Possible suspicious financial movement indicators")

    if not risk_indicators:
        risk_indicators.append("No clear predefined fraud indicators detected yet")

    risk_level = "high" if len(risk_indicators) >= 4 else "medium" if len(risk_indicators) >= 2 else "low"
    return {
        "provider": "mock",
        "case_context": case.context,
        "risk_level": risk_level,
        "risk_indicators": risk_indicators,
        "next_steps": [
            "Verify the vendor's beneficial ownership and bank-account details independently",
            "Obtain contracts, invoices, approvals, and other missing support",
            "Confirm whether any policy exception was authorised and by whom",
            "Document corroborated facts, open questions, and the investigator's assessment",
        ],
        "draft_summary": "Initial, evidence-led review surfaced the following signals for investigator review: " + ", ".join(risk_indicators) + ".",
    }
