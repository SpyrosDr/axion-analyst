# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings

ALGORITHM = "HS256"

# Name of the httpOnly cookie the browser frontend authenticates with. API
# clients/tools may keep using a plain `Authorization: Bearer <token>`
# header instead -- see auth/dependencies.py, which accepts either.
ACCESS_TOKEN_COOKIE_NAME = "access_token"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(*, subject: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        # Unique per-token id so a single issued token can be revoked
        # (POST /auth/logout) without invalidating every other token the
        # same user holds (e.g. a second browser tab/device).
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Returns the full decoded payload (sub/iat/exp/jti), or None if the
    token is missing, malformed, expired, or signed with a different key."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
