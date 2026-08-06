# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.ai import client as ai_client
from app.ai.output_schemas import AICaseAnalysis
from app.config import settings
from app.models.timeline import TimelineEvent
from app.services import case_service, evidence_service

ISO_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
SLASH_DATE_RE = re.compile(r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b")
_MONTH_NAMES = (
    r"January|February|March|April|May|June|July|August|September|October|"
    r"November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
)
MONTH_DATE_RE = re.compile(rf"\b((?:{_MONTH_NAMES})\.?\s+\d{{1,2}},?\s+\d{{4}})\b")


def _parse_date(text: str) -> tuple[str | None, datetime | None]:
    for pattern, fmts in (
        (ISO_DATE_RE, ["%Y-%m-%d"]),
        (SLASH_DATE_RE, ["%m/%d/%Y", "%m/%d/%y"]),
        (MONTH_DATE_RE, ["%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y"]),
    ):
        match = pattern.search(text)
        if not match:
            continue
        raw = match.group(1)
        for fmt in fmts:
            try:
                return raw, datetime.strptime(raw.replace(".", ""), fmt)
            except ValueError:
                continue
        return raw, None
    return None, None


def build_timeline(
    db: Session, case_id: int, analysis: AICaseAnalysis | None = None
) -> list[TimelineEvent]:
    case = case_service.get_case_by_id_or_404(db, case_id)
    evidence_items = evidence_service.list_evidence(db, case_id)

    db.query(TimelineEvent).filter(TimelineEvent.case_id == case_id).delete()

    if settings.AI_PROVIDER == "mock":
        events = []
        for index, item in enumerate(evidence_items):
            text = f"{item.title} {item.content}".strip()
            raw_date, parsed_date = _parse_date(text)
            events.append(
                TimelineEvent(
                    case_id=case_id,
                    event_date_raw=raw_date,
                    event_date=parsed_date,
                    description=text,
                    source_evidence_id=item.id,
                    sequence_order=index,
                )
            )

        events.sort(
            key=lambda e: (
                e.event_date is None,
                e.event_date or datetime.max,
                e.sequence_order,
            )
        )
        # sequence_order is the canonical display order (the frontend sorts
        # by it) -- reassign it post-sort so it reflects chronological order
        # rather than the order evidence happened to be entered in.
        for index, event in enumerate(events):
            event.sequence_order = index
    else:
        # Shared-analysis pattern: see entity_extraction_service.
        if analysis is None:
            analysis = ai_client.analyze_case(
                context=case.context,
                description=case.description,
                evidence_texts=[item.content for item in evidence_items],
            )
        events = []
        for index, ev in enumerate(analysis.timeline_events):
            parsed_date = None
            if ev.event_date:
                try:
                    parsed_date = datetime.strptime(ev.event_date, "%Y-%m-%d")
                except ValueError:
                    parsed_date = None
            events.append(
                TimelineEvent(
                    case_id=case_id,
                    event_date_raw=ev.event_date,
                    event_date=parsed_date,
                    description=ev.description,
                    # See entity_extraction_service for why this stays unset
                    # on the AI path.
                    source_evidence_id=None,
                    sequence_order=index,
                )
            )
        # Trust the prompt's instruction to return events pre-sorted
        # chronologically -- do not re-sort here.

    db.add_all(events)
    db.commit()
    for event in events:
        db.refresh(event)
    return events
