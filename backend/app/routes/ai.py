# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.case_schema import CaseAssessmentResponse, CaseInput
from app.services.ai_service import assess_case_risk


router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


@router.post("/assess-case", response_model=CaseAssessmentResponse)
def assess_case(case: CaseInput, user: User = Depends(get_current_user)):
    # Legacy/stateless endpoint: does not persist anything. The persisted
    # equivalent is POST /cases/{case_id}/risk-assessment.
    return assess_case_risk(case)
