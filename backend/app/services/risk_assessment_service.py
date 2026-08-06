# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

from sqlalchemy.orm import Session

from app.ai import client as ai_client
from app.ai.output_schemas import AICaseAnalysis
from app.ai.providers import mock_provider
from app.config import settings
from app.models.risk_assessment import RiskAssessment
from app.schemas.case_schema import CaseInput
from app.services import (
    case_service,
    entity_extraction_service,
    evidence_service,
    timeline_service,
)


def assess_case_risk_for_case(
    db: Session, case_id: int, analysis: AICaseAnalysis | None = None
) -> RiskAssessment:
    case = case_service.get_case_by_id_or_404(db, case_id)
    evidence_items = evidence_service.list_evidence(db, case_id)

    if settings.AI_PROVIDER == "mock":
        entities = entity_extraction_service.extract_entities(db, case_id)
        timeline_events = timeline_service.build_timeline(db, case_id)

        # mock_provider is the swappable "brain" -- this service is the
        # orchestration layer that a real AI provider plugs into.
        base = mock_provider.assess_case(
            CaseInput(
                context=case.context,
                description=case.description,
                evidence_items=[item.content for item in evidence_items],
            )
        )

        risk_indicators = list(base["risk_indicators"])
        risk_level = base["risk_level"]

        distinct_accounts = {
            e.value for e in entities if e.entity_type == "account_number"
        }
        if len(distinct_accounts) >= 2:
            risk_indicators.append(
                f"Multiple distinct account numbers referenced ({len(distinct_accounts)})"
            )

        if len(timeline_events) >= 5:
            risk_indicators.append("Large number of timestamped events in case history")

        if len(distinct_accounts) >= 2 or len(timeline_events) >= 5:
            risk_level = "high"
        elif len(risk_indicators) >= 2:
            risk_level = "medium"

        assessment = RiskAssessment(
            case_id=case_id,
            risk_level=risk_level,
            risk_indicators=risk_indicators,
            next_steps=base["next_steps"],
            provider=base["provider"],
        )
    else:
        if analysis is None:
            # One AI call covers everything: persist the entity and timeline
            # slices from this same result so all stored data is consistent.
            analysis = ai_client.analyze_case(
                context=case.context,
                description=case.description,
                evidence_texts=[item.content for item in evidence_items],
            )
            entity_extraction_service.extract_entities(db, case_id, analysis)
            timeline_service.build_timeline(db, case_id, analysis)
        # When analysis was passed in (report generation), the caller has
        # already persisted the entity/timeline slices from it.

        # Trust the real model's judgment as final -- skip the mock path's
        # heuristic escalation bumps, which existed only to compensate for
        # the simplistic keyword-matching mock.
        assessment = RiskAssessment(
            case_id=case_id,
            risk_level=analysis.risk_assessment.risk_level,
            risk_indicators=analysis.risk_assessment.risk_indicators,
            next_steps=analysis.risk_assessment.next_steps,
            provider=settings.AI_PROVIDER,
        )

    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment
