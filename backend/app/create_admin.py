# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

import sys

from app.database.db import SessionLocal, init_db
from app.schemas.user_schema import UserCreate
from app.services import user_service


def create_admin(username: str, password: str):
    init_db()
    db = SessionLocal()
    try:
        return user_service.create_user(
            db, UserCreate(username=username, password=password, is_admin=True)
        )
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m app.create_admin <username> <password>")
        sys.exit(1)

    admin = create_admin(sys.argv[1], sys.argv[2])
    print(f"Created admin user '{admin.username}' (id={admin.id}).")
