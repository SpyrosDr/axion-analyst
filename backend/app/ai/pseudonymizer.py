# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

from app.ai.pii_patterns import (
    ACCOUNT_OR_NUMBER_RE,
    ADDRESS_RE,
    EMAIL_RE,
    IP_RE,
    NAME_RE,
    PHONE_RE,
    SSN_RE,
)

_NAME_POOL = [
    "John Doe",
    "Jane Roe",
    "Alex Smith",
    "Morgan Lee",
    "Taylor Brown",
    "Jordan Clark",
    "Casey Wright",
    "Riley Adams",
]


class Pseudonymizer:
    """Swaps person names, emails, account numbers, SSNs, phone numbers, IP
    addresses, and street addresses for consistent fake stand-ins before
    case text is sent to a third-party AI provider, and restores the real
    values in the provider's response afterward. State is scoped to a single
    analyze_case() call so the same real value always maps to the same fake
    value across the context/description/evidence texts of that call,
    keeping the AI's entity correlation intact."""

    def __init__(self):
        self._real_to_fake: dict[str, str] = {}
        self._fake_to_real: dict[str, str] = {}
        self._name_count = 0
        self._email_count = 0
        self._account_count = 0
        self._ssn_count = 0
        self._phone_count = 0
        self._ip_count = 0
        self._address_count = 0

    def _fake_name(self, real: str) -> str:
        if real in self._real_to_fake:
            return self._real_to_fake[real]
        cycle, index = divmod(self._name_count, len(_NAME_POOL))
        fake = _NAME_POOL[index] if cycle == 0 else f"{_NAME_POOL[index]} {cycle + 1}"
        self._name_count += 1
        self._register(real, fake)
        return fake

    def _fake_email(self, real: str) -> str:
        if real in self._real_to_fake:
            return self._real_to_fake[real]
        self._email_count += 1
        fake = f"person{self._email_count}@example.com"
        self._register(real, fake)
        return fake

    def _fake_account(self, real_digits: str) -> str:
        if real_digits in self._real_to_fake:
            return self._real_to_fake[real_digits]
        self._account_count += 1
        fake = str(self._account_count).rjust(len(real_digits), "9")
        self._register(real_digits, fake)
        return fake

    def _fake_digits_preserving_format(self, real: str, counter_name: str) -> str:
        """Replaces only the digit characters of `real` with a counter-based
        fake number, padded and interleaved so separators (dashes, dots,
        spaces, parens) stay exactly where they were -- e.g. "555-123-4567"
        -> "555-000-0001". Used for SSNs and phone numbers, whose formatting
        the AI provider may otherwise use to infer the field is genuine."""
        if real in self._real_to_fake:
            return self._real_to_fake[real]
        count = getattr(self, counter_name) + 1
        setattr(self, counter_name, count)
        digit_positions = sum(1 for ch in real if ch.isdigit())
        fake_digits = iter(str(count).rjust(digit_positions, "0"))
        fake = "".join(
            next(fake_digits) if ch.isdigit() else ch for ch in real
        )
        self._register(real, fake)
        return fake

    def _fake_ip(self, real: str) -> str:
        if real in self._real_to_fake:
            return self._real_to_fake[real]
        self._ip_count += 1
        # 203.0.113.0/24 (TEST-NET-3, RFC 5737) is reserved for
        # documentation/examples and never routable, so it can't collide
        # with a real address.
        fake = f"203.0.113.{self._ip_count % 256}"
        self._register(real, fake)
        return fake

    def _fake_address(self, real: str) -> str:
        if real in self._real_to_fake:
            return self._real_to_fake[real]
        self._address_count += 1
        # Lowercase so the placeholder can't itself be re-matched by
        # NAME_RE, which runs after ADDRESS_RE and requires capitalized
        # words.
        fake = f"{self._address_count} placeholder ave"
        self._register(real, fake)
        return fake

    def _register(self, real: str, fake: str) -> None:
        self._real_to_fake[real] = fake
        self._fake_to_real[fake] = real

    def _replace_number(self, match) -> str:
        digits = match.group(1) or match.group(2)
        return match.group(0).replace(digits, self._fake_account(digits))

    def pseudonymize(self, text: str) -> str:
        if not text:
            return text
        text = EMAIL_RE.sub(lambda m: self._fake_email(m.group(0)), text)
        text = IP_RE.sub(lambda m: self._fake_ip(m.group(0)), text)
        text = SSN_RE.sub(lambda m: self._fake_digits_preserving_format(m.group(0), "_ssn_count"), text)
        text = PHONE_RE.sub(lambda m: self._fake_digits_preserving_format(m.group(0), "_phone_count"), text)
        text = ACCOUNT_OR_NUMBER_RE.sub(self._replace_number, text)
        text = ADDRESS_RE.sub(lambda m: self._fake_address(m.group(0)), text)
        text = NAME_RE.sub(lambda m: self._fake_name(m.group(0)), text)
        return text

    def restore(self, text: str) -> str:
        if not text:
            return text
        for fake in sorted(self._fake_to_real, key=len, reverse=True):
            if fake in text:
                text = text.replace(fake, self._fake_to_real[fake])
        return text
