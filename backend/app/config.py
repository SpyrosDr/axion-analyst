# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

import os
from pathlib import Path

from dotenv import load_dotenv

# Load backend/.env by an explicit, cwd-independent path -- the default
# load_dotenv() only searches upward from the current working directory, so
# it silently finds nothing if the app isn't launched from inside backend/.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Shared with the SECRET_KEY default below and with the production-boot
# check in app.main, so there is exactly one place this string is defined.
DEFAULT_INSECURE_SECRET_KEY = "dev-only-insecure-secret-change-me-in-production"


class Settings:
    # "development" (default) | "production". Only gates the startup check
    # that refuses to boot with the default SECRET_KEY -- it does not
    # change any other app behavior.
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./aletheia.db")
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "mock")

    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str | None = os.getenv("OPENAI_MODEL")

    ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")

    # Which backend the entity web-search tool uses. Valid values:
    # "mock" | "openai" | "anthropic" | "tavily". "openai"/"anthropic" reuse
    # the API keys/models above via each provider's hosted web-search tool;
    # "tavily" is a dedicated search API and needs TAVILY_API_KEY.
    SEARCH_PROVIDER: str = os.getenv("SEARCH_PROVIDER", "mock")
    TAVILY_API_KEY: str | None = os.getenv("TAVILY_API_KEY")

    # How long a previous entity-search result may be reused for an
    # identical (query, entity_type) pair instead of re-hitting the search
    # provider. Repeats are common -- the same entity gets looked up across
    # cases/analysts -- and the provider call is the slow, potentially
    # metered/rate-limited part. 0 disables caching entirely. A fresh
    # EntitySearch row is still written on every call (for per-case/user
    # ownership and audit history); only the provider call is skipped.
    SEARCH_CACHE_TTL_SECONDS: int = int(
        os.getenv("SEARCH_CACHE_TTL_SECONDS", str(60 * 60))
    )

    # Where evidence attachment files (screenshots, PDFs, statements) are
    # stored on disk. Defaults under backend/data/ (anchored on this file's
    # location, not cwd, unlike DATABASE_URL, so it doesn't silently move if
    # the app is launched from a different directory) -- override for a
    # separate volume/mount in production.
    EVIDENCE_UPLOAD_DIR: str = os.getenv(
        "EVIDENCE_UPLOAD_DIR",
        str(Path(__file__).resolve().parent.parent / "data" / "evidence_attachments"),
    )
    EVIDENCE_MAX_ATTACHMENT_SIZE_BYTES: int = int(
        os.getenv("EVIDENCE_MAX_ATTACHMENT_SIZE_BYTES", str(20 * 1024 * 1024))
    )
    # Extensions allowed for evidence attachments, lowercase, without the
    # dot. Deliberately excludes anything executable or that a browser might
    # render/execute (html, svg, js, ...) -- an uploaded attachment is meant
    # to be evidence, not content the app or a viewer's browser interprets.
    EVIDENCE_ALLOWED_ATTACHMENT_EXTENSIONS: set[str] = {
        ext.strip().lower().lstrip(".")
        for ext in os.getenv(
            "EVIDENCE_ALLOWED_ATTACHMENT_EXTENSIONS",
            "png,jpg,jpeg,gif,webp,pdf,txt,csv,eml,docx,xlsx",
        ).split(",")
        if ext.strip()
    }

    # Dev-only default -- DO NOT use in production. Override via env var.
    SECRET_KEY: str = os.getenv("SECRET_KEY", DEFAULT_INSECURE_SECRET_KEY)
    ACCESS_TOKEN_EXPIRE_HOURS: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))

    # Origins allowed to make cross-origin requests to the API (e.g. a
    # frontend served from a different host/port than this backend).
    # Comma-separated. Defaults cover the Vite dev server; the dev workflow
    # in README.md normally never hits this because Vite proxies /api/* to
    # the backend same-origin, but it matters for anything hitting the API
    # directly (Swagger UI on a different port, a separately hosted
    # frontend build, etc).
    CORS_ALLOWED_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ]

    # Login brute-force throttling. A given *account* locks out after
    # LOGIN_RATE_LIMIT_ATTEMPTS failures within the window; a given *client
    # IP* gets a much larger allowance (LOGIN_RATE_LIMIT_IP_ATTEMPTS) so one
    # IP spraying many usernames also gets caught, without a single
    # legitimate account's failures ever locking out its whole IP (e.g. an
    # office NAT).
    LOGIN_RATE_LIMIT_ATTEMPTS: int = int(os.getenv("LOGIN_RATE_LIMIT_ATTEMPTS", "5"))
    LOGIN_RATE_LIMIT_IP_ATTEMPTS: int = int(
        os.getenv("LOGIN_RATE_LIMIT_IP_ATTEMPTS", "20")
    )
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = int(
        os.getenv("LOGIN_RATE_LIMIT_WINDOW_SECONDS", "300")
    )
    LOGIN_RATE_LIMIT_LOCKOUT_SECONDS: int = int(
        os.getenv("LOGIN_RATE_LIMIT_LOCKOUT_SECONDS", "300")
    )


settings = Settings()


def check_boot_safety() -> None:
    """Refuse to start with ENVIRONMENT=production and the default,
    publicly-known insecure SECRET_KEY -- that combination would let anyone
    forge login tokens for any user. Does nothing outside production, so
    local dev keeps working with no setup."""
    if (
        settings.ENVIRONMENT == "production"
        and settings.SECRET_KEY == DEFAULT_INSECURE_SECRET_KEY
    ):
        raise RuntimeError(
            "Refusing to start: ENVIRONMENT=production but SECRET_KEY is "
            "still the default insecure value. Set a real SECRET_KEY in "
            "backend/.env, e.g.:\n"
            "  python -c \"import secrets; print(secrets.token_hex(32))\""
        )
