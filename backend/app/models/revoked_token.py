# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

from sqlalchemy import Column, DateTime, String, func

from app.database.db import Base


class RevokedToken(Base):
    """A denylist entry for a logged-out access token, keyed by the token's
    `jti` claim. get_current_user() rejects any token whose jti shows up
    here, even if the JWT itself is still cryptographically valid and
    unexpired -- this is what makes POST /auth/logout actually invalidate
    the token server-side instead of relying on the client to discard it.

    `expires_at` mirrors the token's own `exp` claim so expired entries
    (which can no longer pass JWT validation anyway) can be purged instead
    of accumulating forever."""

    __tablename__ = "revoked_tokens"

    jti = Column(String, primary_key=True)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, server_default=func.now())
