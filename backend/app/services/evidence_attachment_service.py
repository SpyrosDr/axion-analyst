# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

import secrets
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.models.evidence import Evidence
from app.models.evidence_attachment import EvidenceAttachment
from app.models.user import User

_CHUNK_SIZE = 1024 * 1024  # 1 MiB, read/written incrementally so a large
# upload never has to sit fully in memory at once.


def _upload_dir() -> Path:
    path = Path(settings.EVIDENCE_UPLOAD_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def attachment_path(attachment: EvidenceAttachment) -> Path:
    return _upload_dir() / attachment.storage_key


def _validate_extension(filename: str) -> None:
    ext = Path(filename).suffix.lower().lstrip(".")
    if not ext or ext not in settings.EVIDENCE_ALLOWED_ATTACHMENT_EXTENSIONS:
        allowed = ", ".join(sorted(settings.EVIDENCE_ALLOWED_ATTACHMENT_EXTENSIONS))
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed extensions: {allowed}",
        )


async def add_attachment(
    db: Session, evidence: Evidence, upload: UploadFile, user: User
) -> EvidenceAttachment:
    if not upload.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    _validate_extension(upload.filename)

    # A random token, not the client's filename -- so nothing about the
    # request ever becomes (or influences) a filesystem path. The original
    # name is kept only as DB metadata for display/download.
    storage_key = secrets.token_hex(16)
    dest = _upload_dir() / storage_key
    max_size = settings.EVIDENCE_MAX_ATTACHMENT_SIZE_BYTES

    size = 0
    try:
        with open(dest, "wb") as out:
            while chunk := await upload.read(_CHUNK_SIZE):
                size += len(chunk)
                if size > max_size:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds the {max_size // (1024 * 1024)}MB limit",
                    )
                out.write(chunk)
    except BaseException:
        dest.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()

    attachment = EvidenceAttachment(
        evidence_id=evidence.id,
        # Path(...).name strips any path separators the client filename
        # might contain -- it's never used as a real path (storage_key is),
        # but there's no reason to persist "../../etc/passwd.png" verbatim.
        filename=Path(upload.filename).name,
        content_type=upload.content_type or "application/octet-stream",
        size_bytes=size,
        storage_key=storage_key,
        uploaded_by_id=user.id if user else None,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


def list_attachments(db: Session, evidence_id: int) -> list[EvidenceAttachment]:
    return (
        db.query(EvidenceAttachment)
        .filter(EvidenceAttachment.evidence_id == evidence_id)
        .order_by(EvidenceAttachment.id)
        .all()
    )


def get_attachment_or_404(
    db: Session, evidence_id: int, attachment_id: int
) -> EvidenceAttachment:
    attachment = (
        db.query(EvidenceAttachment)
        .filter(
            EvidenceAttachment.id == attachment_id,
            EvidenceAttachment.evidence_id == evidence_id,
        )
        .first()
    )
    if attachment is None:
        raise HTTPException(
            status_code=404, detail=f"Attachment {attachment_id} not found"
        )
    return attachment


def delete_attachment(db: Session, attachment: EvidenceAttachment) -> None:
    # File removal happens via the model's after_delete event listener, so
    # it stays in sync however the row gets deleted (direct call or a
    # cascade from deleting the parent evidence/case).
    db.delete(attachment)
    db.commit()
