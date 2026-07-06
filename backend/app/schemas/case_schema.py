from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.entity_schema import EntityResponse
from app.schemas.evidence_schema import EvidenceResponse
from app.schemas.report_schema import ReportResponse
from app.schemas.risk_schema import RiskAssessmentResponse
from app.schemas.timeline_schema import TimelineEventResponse
from app.schemas.user_schema import UserSummary


class CaseInput(BaseModel):
    context: str
    description: str
    evidence_items: list[str] = Field(default_factory=list)

class CaseAssessmentResponse(BaseModel):
    provider: str
    case_context: str
    risk_level: str
    risk_indicators: list[str]
    next_steps: list[str]
    draft_summary: str


class CaseCreate(BaseModel):
    context: str
    description: str
    evidence_items: list[str] = Field(default_factory=list)


class CaseCollaboratorAdd(BaseModel):
    username: str
    role: str


class CaseCollaboratorRoleUpdate(BaseModel):
    role: str


class CaseCollaboratorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user: UserSummary
    role: str


class CaseStatusUpdate(BaseModel):
    status: str


class CaseActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    actor: UserSummary | None = None
    action: str
    detail: str | None = None
    created_at: datetime


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    context: str
    description: str
    status: str = "open"
    created_at: datetime
    owner: UserSummary | None = None
    latest_risk_level: str | None = None
    my_role: str | None = None


class CaseDetailResponse(CaseResponse):
    # Collaborators (with their roles) are served by the dedicated
    # GET /cases/{id}/collaborators endpoint, not duplicated here.
    evidence_items: list[EvidenceResponse] = Field(default_factory=list)
    entities: list[EntityResponse] = Field(default_factory=list)
    timeline_events: list[TimelineEventResponse] = Field(default_factory=list)
    risk_assessments: list[RiskAssessmentResponse] = Field(default_factory=list)
    reports: list[ReportResponse] = Field(default_factory=list)
