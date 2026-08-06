# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TimelineEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    event_date_raw: str | None = None
    event_date: datetime | None = None
    description: str
    source_evidence_id: int | None = None
    sequence_order: int
