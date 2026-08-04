# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

from sqlalchemy.orm import Session

from app.ai import client as ai_client
from app.config import settings
from app.models.report import Report
from app.services import (
    case_service,
    entity_extraction_service,
    evidence_service,
    risk_assessment_service,
    timeline_service,
)


def generate_report(db: Session, case_id: int) -> Report:
    case = case_service.get_case_by_id_or_404(db, case_id)
    evidence_items = evidence_service.list_evidence(db, case_id)

    if settings.AI_PROVIDER == "mock":
        entities = entity_extraction_service.extract_entities(db, case_id)
        timeline_events = timeline_service.build_timeline(db, case_id)
        risk_assessment = risk_assessment_service.assess_case_risk_for_case(
            db, case_id
        )

        overview = f"{case.context}\n\n{case.description}"

        evidence_text = (
            "\n".join(f"- {item.title or item.content}" for item in evidence_items)
            or "No evidence items recorded."
        )

        entities_text = (
            "\n".join(f"- [{e.entity_type}] {e.value}" for e in entities)
            or "No entities extracted."
        )

        timeline_text = (
            "\n".join(
                f"- {event.event_date_raw or f'(evidence #{index + 1})'}: {event.description}"
                for index, event in enumerate(timeline_events)
            )
            or "No timeline events extracted."
        )

        risk_text = f"Risk level: {risk_assessment.risk_level}\n" + "\n".join(
            f"- {indicator}" for indicator in risk_assessment.risk_indicators
        )

        recommendations_text = "\n".join(
            f"- {step}" for step in risk_assessment.next_steps
        )

        sections = {
            "overview": overview,
            "evidence": evidence_text,
            "entities": entities_text,
            "timeline": timeline_text,
            "risk_assessment": risk_text,
            "recommendations": recommendations_text,
        }
    else:
        # One AI call for the entire analysis run. Every persisted slice
        # (entities, timeline, risk assessment, report sections) comes from
        # this single result, so they cannot contradict each other -- and a
        # "Run Analysis" click costs one provider call instead of four.
        analysis = ai_client.analyze_case(
            context=case.context,
            description=case.description,
            evidence_texts=[item.content for item in evidence_items],
        )
        entity_extraction_service.extract_entities(db, case_id, analysis)
        timeline_service.build_timeline(db, case_id, analysis)
        risk_assessment_service.assess_case_risk_for_case(db, case_id, analysis)
        sections = analysis.report_sections.model_dump()

    summary_text = "\n\n".join(
        f"## {name.replace('_', ' ').title()}\n{text}" for name, text in sections.items()
    )

    report = Report(case_id=case_id, summary_text=summary_text, sections=sections)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
