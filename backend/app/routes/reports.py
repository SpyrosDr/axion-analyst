# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.db import get_db
from app.models.report import Report
from app.models.user import User
from app.schemas.report_schema import ReportResponse
from app.services import case_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    # Enforce the same case-level access check as every other route -- a
    # report id alone was previously enough to read any case's report.
    case_service.get_case_or_404(db, report.case_id, user)
    return report
