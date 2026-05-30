from __future__ import annotations

import pytest

from core.impose_service import build_signature_settings, signature_sheet_pairs


def test_build_signature_settings_accepts_rtl():
    settings = build_signature_settings(
        pages_per_signature=16,
        binding_direction="rtl",
    )

    assert settings.binding_direction == "rtl"


def test_ltr_16_page_signature_first_sheet_order():
    pairs = signature_sheet_pairs(16, binding_direction="ltr")

    assert pairs[0] == ((16, 1), (2, 15))
    assert pairs[1] == ((14, 3), (4, 13))


def test_rtl_16_page_signature_first_sheet_order():
    pairs = signature_sheet_pairs(16, binding_direction="rtl")

    assert pairs[0] == ((1, 16), (15, 2))
    assert pairs[1] == ((3, 14), (13, 4))


def test_signature_sheet_pairs_rejects_bad_direction():
    with pytest.raises(ValueError):
        signature_sheet_pairs(16, binding_direction="bad")
