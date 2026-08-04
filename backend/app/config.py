# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

import os
from pathlib import Path

from dotenv import load_dotenv

# Load backend/.env by an explicit, cwd-independent path -- the default
# load_dotenv() only searches upward from the current working directory, so
# it silently finds nothing if the app isn't launched from inside backend/.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./aletheia.db")
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "mock")

    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str | None = os.getenv("OPENAI_MODEL")

    ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")

    # Which backend the entity web-search tool uses. Valid values:
    # "mock" | "openai" | "anthropic" | "tavily". "openai"/"anthropic" reuse
    # the API keys/models above via each provider's hosted web-search tool;
    # "tavily" is a dedicated search API and needs TAVILY_API_KEY.
    SEARCH_PROVIDER: str = os.getenv("SEARCH_PROVIDER", "mock")
    TAVILY_API_KEY: str | None = os.getenv("TAVILY_API_KEY")

    # Dev-only default -- DO NOT use in production. Override via env var.
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "dev-only-insecure-secret-change-me-in-production"
    )
    ACCESS_TOKEN_EXPIRE_HOURS: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))


settings = Settings()
