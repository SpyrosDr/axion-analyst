from sqlalchemy.orm import Session

from app.models.evidence import Evidence
from app.schemas.evidence_schema import EvidenceCreate


def add_evidence(db: Session, case_id: int, evidence_in: EvidenceCreate) -> Evidence:
    evidence = Evidence(
        case_id=case_id,
        title=evidence_in.title,
        type=evidence_in.type,
        content=evidence_in.content,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


def add_evidence_items(db: Session, case_id: int, items: list[str]) -> list[Evidence]:
    evidence_items = [
        Evidence(case_id=case_id, title="", type="", content=item) for item in items
    ]
    db.add_all(evidence_items)
    db.commit()
    for evidence in evidence_items:
        db.refresh(evidence)
    return evidence_items


def list_evidence(db: Session, case_id: int) -> list[Evidence]:
    return (
        db.query(Evidence)
        .filter(Evidence.case_id == case_id)
        .order_by(Evidence.id)
        .all()
    )
