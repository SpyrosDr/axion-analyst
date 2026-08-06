# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EvidenceAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    evidence_id: int
    filename: str
    content_type: str
    size_bytes: int
    uploaded_by_id: int | None
    created_at: datetime
