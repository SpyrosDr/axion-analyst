# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    summary_text: str
    sections: dict[str, str]
    created_at: datetime
