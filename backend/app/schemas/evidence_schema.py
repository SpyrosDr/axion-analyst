# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EvidenceCreate(BaseModel):
    title: str = ""
    type: str = ""
    content: str


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    title: str
    type: str
    content: str
    created_at: datetime
