# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

import os
import tempfile

# Must run before anything imports app.config -- the engine is created at
# import time from DATABASE_URL, and tests must never touch the dev database.
_TEST_DB = os.path.join(tempfile.gettempdir(), "aletheia_test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"

# Tests must never call a real AI provider (cost, network, non-determinism),
# regardless of what's configured in backend/.env for local dev use. This
# only fills in a default -- python-dotenv's load_dotenv() never overrides
# a variable that's already set in the environment, so this wins.
os.environ["AI_PROVIDER"] = "mock"

# Same reasoning as AI_PROVIDER above -- tests must never call a real search
# provider.
os.environ["SEARCH_PROVIDER"] = "mock"

# Evidence attachment uploads must land in a throwaway directory, not the
# real backend/data/evidence_attachments used by local dev.
_TEST_UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "aletheia_test_attachments")
os.environ["EVIDENCE_UPLOAD_DIR"] = _TEST_UPLOAD_DIR

import shutil  # noqa: E402

import pytest  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _fresh_test_db():
    if os.path.exists(_TEST_DB):
        os.remove(_TEST_DB)
    if os.path.exists(_TEST_UPLOAD_DIR):
        shutil.rmtree(_TEST_UPLOAD_DIR)
    yield
    if os.path.exists(_TEST_DB):
        os.remove(_TEST_DB)
    if os.path.exists(_TEST_UPLOAD_DIR):
        shutil.rmtree(_TEST_UPLOAD_DIR)
