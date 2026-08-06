# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


_ALEMBIC_INI = Path(__file__).resolve().parent.parent.parent / "alembic.ini"


def init_db():
    """Bring the database schema up to date on startup.

    Uses Alembic migrations rather than `Base.metadata.create_all()` so that
    schema changes no longer require deleting the database file: a brand
    new database gets migrated from empty to `head`, and a database created
    by an older version of this app (before Alembic was introduced, via
    `create_all()`) is detected and stamped at `head` instead of replayed
    -- its schema already matches, since the initial migration is exactly
    that `create_all()` snapshot.
    """
    import app.models  # noqa: F401 - ensures every model is registered on Base
    from sqlalchemy import inspect

    alembic_cfg = Config(str(_ALEMBIC_INI))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    pre_alembic_db = bool(existing_tables) and "alembic_version" not in existing_tables

    if pre_alembic_db:
        command.stamp(alembic_cfg, "head")
    else:
        command.upgrade(alembic_cfg, "head")
