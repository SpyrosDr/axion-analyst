from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RiskAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    risk_level: str
    risk_indicators: list[str]
    next_steps: list[str]
    provider: str
    created_at: datetime
