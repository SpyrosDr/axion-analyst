from pydantic import BaseModel, ConfigDict


class AIEntity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_type: str
    value: str


class AITimelineEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_date: str | None  # ISO 8601 date string (YYYY-MM-DD), or null if no date is identifiable
    description: str


class AIRiskAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk_level: str  # "low" | "medium" | "high"
    risk_indicators: list[str]
    next_steps: list[str]


class AIReportSections(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overview: str
    evidence: str
    entities: str
    timeline: str
    risk_assessment: str
    recommendations: str


class AICaseAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entities: list[AIEntity]
    timeline_events: list[AITimelineEvent]
    risk_assessment: AIRiskAssessment
    report_sections: AIReportSections
