# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

import re

AMOUNT_RE = re.compile(r"\$\d[\d,]*(?:\.\d{2})?\b")
ACCOUNT_RE = re.compile(r"\b(?:acct|account)\s*#?\s*(\d{4,})\b", re.IGNORECASE)
GENERIC_NUMBER_RE = re.compile(r"\b\d{8,}\b")
# Matches either an "acct #..." prefixed number or a bare 8+ digit number in
# a single pass, so a substitution can't accidentally re-match text produced
# by an earlier substitution (which sequential ACCOUNT_RE/GENERIC_NUMBER_RE
# passes would do, since a fake account number is itself an 8+ digit run).
ACCOUNT_OR_NUMBER_RE = re.compile(
    r"\b(?:acct|account)\s*#?\s*(\d{4,})\b|\b(\d{8,})\b", re.IGNORECASE
)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
ORG_RE = re.compile(r"\b[A-Z][\w&]*(?:\s+[A-Z][\w&]*)*\s+(?:Inc|LLC|Ltd|Corp|Co)\.?\b")
NAME_RE = re.compile(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b")
