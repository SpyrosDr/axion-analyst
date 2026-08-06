# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

from pathlib import Path

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, event, func
from sqlalchemy.orm import relationship

from app.config import settings
from app.database.db import Base


class EvidenceAttachment(Base):
    """Metadata for a file uploaded against an Evidence item (screenshot,
    PDF, bank statement, etc). The file bytes themselves live on disk under
    settings.EVIDENCE_UPLOAD_DIR, named by `storage_key` -- a
    server-generated token, never the client-supplied filename, so nothing
    about the upload request ever becomes a filesystem path. `filename` is
    the original name, kept only for display and for the download
    response's Content-Disposition header."""

    __tablename__ = "evidence_attachments"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    storage_key = Column(String, nullable=False, unique=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    evidence = relationship("Evidence", back_populates="attachments")
    uploaded_by = relationship("User")


@event.listens_for(EvidenceAttachment, "after_delete")
def _remove_attachment_file(mapper, connection, target: "EvidenceAttachment") -> None:
    """Keeps the on-disk file in sync with the DB row no matter how the row
    is deleted -- a direct DELETE .../attachments/{id} call, or an ORM
    cascade from deleting the parent Evidence or Case. Without this,
    cascading deletes (e.g. deleting a whole case) would silently orphan
    every attachment file that case's evidence ever had."""
    Path(settings.EVIDENCE_UPLOAD_DIR).joinpath(target.storage_key).unlink(
        missing_ok=True
    )
