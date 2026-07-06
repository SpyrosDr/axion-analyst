from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    editable_case,
    get_current_user,
    managed_case,
    viewable_case,
)
from app.database.db import get_db
from app.models.case import Case
from app.models.user import User
from app.schemas.case_schema import (
    CaseActivityResponse,
    CaseCollaboratorAdd,
    CaseCollaboratorResponse,
    CaseCollaboratorRoleUpdate,
    CaseCreate,
    CaseDetailResponse,
    CaseResponse,
    CaseStatusUpdate,
)
from app.schemas.entity_schema import EntityResponse
from app.schemas.report_schema import ReportResponse
from app.schemas.risk_schema import RiskAssessmentResponse
from app.schemas.timeline_schema import TimelineEventResponse
from app.services import (
    activity_service,
    case_service,
    collaborator_service,
    permissions,
    report_generation_service,
    risk_assessment_service,
)

router = APIRouter(prefix="/cases", tags=["Cases"])


def _with_my_role(case: Case, user: User) -> Case:
    """Only needed on routes that don't go through the viewable_case
    dependency (create/list); the dependency sets my_role itself."""
    case.my_role = permissions.effective_role(case, user)
    return case


@router.post("", response_model=CaseResponse)
def create_case(
    case_in: CaseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _with_my_role(case_service.create_case(db, case_in, user), user)


@router.get("", response_model=list[CaseResponse])
def list_cases(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return [_with_my_role(case, user) for case in case_service.list_cases(db, user)]


@router.get("/{case_id}", response_model=CaseDetailResponse)
def get_case(case: Case = Depends(viewable_case)):
    return case


@router.delete("/{case_id}", status_code=204)
def delete_case(
    case: Case = Depends(viewable_case),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    case_service.delete_case(db, case, user)


@router.get("/{case_id}/entities", response_model=list[EntityResponse])
def get_entities(case: Case = Depends(viewable_case)):
    # Read-only: returns previously generated entities. Generation (which
    # rewrites rows and may call the AI provider) happens only through
    # POST /cases/{case_id}/report, which requires edit access.
    return case.entities


@router.get("/{case_id}/timeline", response_model=list[TimelineEventResponse])
def get_timeline(case: Case = Depends(viewable_case)):
    # Read-only, same reasoning as get_entities.
    return sorted(case.timeline_events, key=lambda event: event.sequence_order)


@router.post("/{case_id}/risk-assessment", response_model=RiskAssessmentResponse)
def create_risk_assessment(
    case: Case = Depends(editable_case),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    case_service.require_open(case)
    assessment = risk_assessment_service.assess_case_risk_for_case(db, case.id)
    activity_service.log(db, case.id, user, "analysis_run", "ran a risk assessment")
    return assessment


@router.post("/{case_id}/report", response_model=ReportResponse)
def create_report(
    case: Case = Depends(editable_case),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    case_service.require_open(case)
    report = report_generation_service.generate_report(db, case.id)
    activity_service.log(db, case.id, user, "analysis_run", "ran the full analysis")
    return report


@router.patch("/{case_id}/status", response_model=CaseResponse)
def update_status(
    body: CaseStatusUpdate,
    case: Case = Depends(managed_case),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return case_service.update_status(db, case, body.status, user)


@router.get("/{case_id}/activity", response_model=list[CaseActivityResponse])
def list_activity(case: Case = Depends(viewable_case)):
    return activity_service.list_activity(case)


@router.get("/{case_id}/collaborators", response_model=list[CaseCollaboratorResponse])
def list_collaborators(case: Case = Depends(viewable_case)):
    return collaborator_service.list_collaborators(case)


@router.post("/{case_id}/collaborators", response_model=CaseCollaboratorResponse)
def add_collaborator(
    body: CaseCollaboratorAdd,
    case: Case = Depends(viewable_case),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return collaborator_service.add_collaborator(
        db, case, body.username, body.role, requesting_user=user
    )


@router.patch(
    "/{case_id}/collaborators/{user_id}", response_model=CaseCollaboratorResponse
)
def update_collaborator_role(
    user_id: int,
    body: CaseCollaboratorRoleUpdate,
    case: Case = Depends(viewable_case),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return collaborator_service.update_collaborator_role(
        db, case, user_id, body.role, requesting_user=user
    )


@router.delete("/{case_id}/collaborators/{user_id}", status_code=204)
def remove_collaborator(
    user_id: int,
    case: Case = Depends(viewable_case),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    collaborator_service.remove_collaborator(
        db, case, user_id, requesting_user=user
    )
