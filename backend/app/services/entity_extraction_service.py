from sqlalchemy.orm import Session

from app.ai import client as ai_client
from app.ai.output_schemas import AICaseAnalysis
from app.ai.pii_patterns import (
    ACCOUNT_RE,
    AMOUNT_RE,
    EMAIL_RE,
    GENERIC_NUMBER_RE,
    NAME_RE,
    ORG_RE,
)
from app.config import settings
from app.models.entity import Entity
from app.services import case_service, evidence_service

# Lightweight regex/keyword heuristics -- this is a rule-based mock standing in
# for real entity extraction (NER), not an actual language model.


def _scan(text: str, source_evidence_id: int | None, found: dict) -> None:
    for match in AMOUNT_RE.findall(text):
        found.setdefault(("amount", match), source_evidence_id)
    for match in ACCOUNT_RE.findall(text):
        found.setdefault(("account_number", match), source_evidence_id)
    for match in GENERIC_NUMBER_RE.findall(text):
        found.setdefault(("account_number", match), source_evidence_id)
    for match in EMAIL_RE.findall(text):
        found.setdefault(("email", match), source_evidence_id)
    for match in ORG_RE.findall(text):
        found.setdefault(("organization", match), source_evidence_id)
    for match in NAME_RE.findall(text):
        found.setdefault(("person", match), source_evidence_id)


def extract_entities(
    db: Session, case_id: int, analysis: AICaseAnalysis | None = None
) -> list[Entity]:
    case = case_service.get_case_by_id_or_404(db, case_id)
    evidence_items = evidence_service.list_evidence(db, case_id)

    db.query(Entity).filter(Entity.case_id == case_id).delete()

    if settings.AI_PROVIDER == "mock":
        found: dict[tuple[str, str], int | None] = {}
        _scan(f"{case.context} {case.description}", None, found)
        for item in evidence_items:
            _scan(f"{item.title} {item.content}", item.id, found)

        entities = [
            Entity(
                case_id=case_id,
                entity_type=entity_type,
                value=value,
                source_evidence_id=source_evidence_id,
            )
            for (entity_type, value), source_evidence_id in found.items()
        ]
    else:
        # Callers running a full analysis (risk assessment, report) pass in
        # one shared AICaseAnalysis so every persisted slice comes from the
        # same AI call and can't contradict the others.
        if analysis is None:
            analysis = ai_client.analyze_case(
                context=case.context,
                description=case.description,
                evidence_texts=[item.content for item in evidence_items],
            )
        entities = [
            Entity(
                case_id=case_id,
                entity_type=e.entity_type,
                value=e.value,
                # The AI path does not attribute entities to a specific
                # evidence item -- asking an LLM to do that reliably from
                # concatenated text risks silently wrong provenance.
                source_evidence_id=None,
            )
            for e in analysis.entities
        ]

    db.add_all(entities)
    db.commit()
    for entity in entities:
        db.refresh(entity)
    return entities
