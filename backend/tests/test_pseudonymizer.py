# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

from app.ai.pseudonymizer import Pseudonymizer


def test_pseudonymize_and_restore_round_trip_covers_all_pii_types():
    text = (
        "Contact John Smith at john.smith@example.com or 555-123-4567. "
        "SSN 123-45-6789, account #12345678, lives at 42 Main Street, "
        "logged in from 8.8.8.8."
    )
    p = Pseudonymizer()
    pseudonymized = p.pseudonymize(text)

    assert "John Smith" not in pseudonymized
    assert "john.smith@example.com" not in pseudonymized
    assert "555-123-4567" not in pseudonymized
    assert "123-45-6789" not in pseudonymized
    assert "12345678" not in pseudonymized
    assert "42 Main Street" not in pseudonymized
    assert "8.8.8.8" not in pseudonymized

    restored = p.restore(pseudonymized)
    assert restored == text


def test_ssn_and_phone_use_distinct_formats_and_do_not_collide():
    text = "SSN 123-45-6789 and phone 555-123-4567 for the same person."
    p = Pseudonymizer()
    pseudonymized = p.pseudonymize(text)
    restored = p.restore(pseudonymized)
    assert restored == text
    # SSN keeps 3-2-4 grouping, phone keeps 3-3-4 -- formats must not merge.
    assert "-" in pseudonymized


def test_repeated_value_maps_to_same_fake_consistently():
    text = "Ping 10.20.30.40 then ping 10.20.30.40 again."
    p = Pseudonymizer()
    pseudonymized = p.pseudonymize(text)
    fakes = set(pseudonymized.replace("Ping ", "").replace(" then ping ", "|").replace(" again.", "").split("|"))
    assert len(fakes) == 1


def test_address_placeholder_is_not_remangled_by_name_pattern():
    text = "Suspect resides at 100 Oak Avenue in the city."
    p = Pseudonymizer()
    pseudonymized = p.pseudonymize(text)
    assert "100 Oak Avenue" not in pseudonymized
    # The lowercase fake address placeholder must survive the later NAME_RE
    # pass unmodified, or restore() won't find it as a key.
    assert p.restore(pseudonymized) == text


def test_plain_bare_digit_number_still_treated_as_account_number():
    text = "Wire reference 87654321 was flagged."
    p = Pseudonymizer()
    pseudonymized = p.pseudonymize(text)
    assert "87654321" not in pseudonymized
    assert p.restore(pseudonymized) == text
