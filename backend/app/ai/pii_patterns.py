# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

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

# US Social Security number, e.g. "123-45-6789". Requires the dashes so it
# doesn't overlap with GENERIC_NUMBER_RE (which only matches unbroken digit
# runs) or PHONE_RE (different grouping: 3-2-4 vs 3-3-4).
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

# US/NANP-style phone numbers with an explicit separator between groups, e.g.
# "555-123-4567", "(555) 123-4567", "555.123.4567", "+1 555-123-4567". Bare
# unseparated 10-digit runs are intentionally left to GENERIC_NUMBER_RE
# (ambiguous with account numbers either way).
PHONE_RE = re.compile(
    r"(?<!\d)(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}(?!\d)"
)

# One IPv4 octet, 0-255.
_OCTET = r"(?:25[0-5]|2[0-4]\d|1?\d?\d)"
IP_RE = re.compile(rf"\b{_OCTET}\.{_OCTET}\.{_OCTET}\.{_OCTET}\b")

# A street address: a leading house number, a handful of words, and a
# recognizable street-type suffix. Naive (no unit/apartment or PO box
# handling) but catches the common "123 Main Street" shape.
_STREET_SUFFIXES = (
    r"Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|"
    r"Court|Ct|Way|Place|Pl|Circle|Cir|Terrace|Ter|Highway|Hwy|Parkway|Pkwy"
)
ADDRESS_RE = re.compile(
    rf"\b\d{{1,6}}\s+(?:[A-Za-z0-9.'-]+\s+){{0,4}}(?:{_STREET_SUFFIXES})\.?\b",
    re.IGNORECASE,
)
