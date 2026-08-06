# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import editable_case, get_current_user, viewable_case
from app.database.db import get_db
from app.models.case import Case
from app.models.user import User
from app.schemas.evidence_attachment_schema import EvidenceAttachmentResponse
from app.services import (
    activity_service,
    case_service,
    evidence_attachment_service,
    evidence_service,
)

router = APIRouter(
    prefix="/cases/{case_id}/evidence/{evidence_id}/attachments",
    tags=["Evidence Attachments"],
)


@router.post("", response_model=EvidenceAttachmentResponse)
async def upload_attachment(
    evidence_id: int,
    file: UploadFile,
    case: Case = Depends(editable_case),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    case_service.require_open(case)
    evidence = evidence_service.get_evidence_or_404(db, case.id, evidence_id)
    attachment = await evidence_attachment_service.add_attachment(
        db, evidence, file, user
    )
    activity_service.log(
        db,
        case.id,
        user,
        "attachment_added",
        f'attached "{attachment.filename}" to evidence',
    )
    return attachment


@router.get("", response_model=list[EvidenceAttachmentResponse])
def list_attachments(
    evidence_id: int,
    case: Case = Depends(viewable_case),
    db: Session = Depends(get_db),
):
    evidence_service.get_evidence_or_404(db, case.id, evidence_id)
    return evidence_attachment_service.list_attachments(db, evidence_id)


@router.get("/{attachment_id}/download")
def download_attachment(
    evidence_id: int,
    attachment_id: int,
    case: Case = Depends(viewable_case),
    db: Session = Depends(get_db),
):
    evidence_service.get_evidence_or_404(db, case.id, evidence_id)
    attachment = evidence_attachment_service.get_attachment_or_404(
        db, evidence_id, attachment_id
    )
    path = evidence_attachment_service.attachment_path(attachment)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Attachment file is missing")

    # filename= makes Starlette send Content-Disposition: attachment, so
    # the browser always downloads/saves rather than rendering the file
    # inline -- relevant even though the upload's extension allowlist
    # already excludes html/svg/etc, as defense in depth.
    return FileResponse(
        path, media_type=attachment.content_type, filename=attachment.filename
    )


@router.delete("/{attachment_id}", status_code=204)
def remove_attachment(
    evidence_id: int,
    attachment_id: int,
    case: Case = Depends(editable_case),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    case_service.require_open(case)
    evidence_service.get_evidence_or_404(db, case.id, evidence_id)
    attachment = evidence_attachment_service.get_attachment_or_404(
        db, evidence_id, attachment_id
    )
    filename = attachment.filename
    evidence_attachment_service.delete_attachment(db, attachment)
    activity_service.log(
        db, case.id, user, "attachment_removed", f'removed attachment "{filename}"'
    )
