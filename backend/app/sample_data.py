# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.database.db import SessionLocal, init_db
from app.models.case import Case
from app.models.user import User
from app.schemas.case_schema import CaseCreate
from app.schemas.evidence_schema import EvidenceCreate
from app.services import case_service, evidence_service

SAMPLE_CASES_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_cases"


def load_sample_cases(db: Session, owner: User) -> list[Case]:
    created = []
    for path in sorted(SAMPLE_CASES_DIR.glob("*.json")):
        payload = json.loads(path.read_text())
        # Sample evidence uses "Title | detail" so the case viewer resembles
        # a mixed investigation file instead of an undifferentiated text dump.
        raw_evidence = payload.pop("evidence_items", [])
        case_in = CaseCreate(**payload)

        exists = (
            db.query(Case)
            .filter(
                Case.context == case_in.context,
                Case.description == case_in.description,
            )
            .first()
        )
        if exists:
            continue

        case = case_service.create_case(db, case_in, owner)
        for item in raw_evidence:
            title, separator, content = item.partition(" | ")
            evidence_service.add_evidence(
                db,
                case.id,
                EvidenceCreate(
                    title=title if separator else "",
                    type=title.split(":", 1)[0].lower() if separator else "",
                    content=content if separator else item,
                ),
            )
        created.append(case)
    return created


def seed() -> list[Case]:
    init_db()
    db = SessionLocal()
    try:
        owner = db.query(User).filter(User.is_admin.is_(True)).first()
        if owner is None:
            raise RuntimeError(
                "No admin user exists yet -- create one first via "
                "`python -m app.create_admin <username> <password>`."
            )
        return load_sample_cases(db, owner)
    finally:
        db.close()


if __name__ == "__main__":
    seeded = seed()
    print(f"Seeded {len(seeded)} sample case(s).")
