from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import editable_case, get_current_user, viewable_case
from app.database.db import get_db
from app.models.case import Case
from app.models.user import User
from app.schemas.evidence_schema import EvidenceCreate, EvidenceResponse
from app.services import activity_service, case_service, evidence_service

router = APIRouter(prefix="/cases/{case_id}/evidence", tags=["Evidence"])


@router.post("", response_model=EvidenceResponse)
def add_evidence(
    evidence_in: EvidenceCreate,
    case: Case = Depends(editable_case),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    case_service.require_open(case)
    evidence = evidence_service.add_evidence(db, case.id, evidence_in)
    detail = (
        f'added evidence "{evidence_in.title}"'
        if evidence_in.title
        else "added evidence"
    )
    activity_service.log(db, case.id, user, "evidence_added", detail)
    return evidence


@router.get("", response_model=list[EvidenceResponse])
def list_evidence(
    case: Case = Depends(viewable_case), db: Session = Depends(get_db)
):
    return evidence_service.list_evidence(db, case.id)
