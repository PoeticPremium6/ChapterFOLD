import pytest

from core.impose_service import (
    build_signature_settings,
    pages_from_sheets,
    resolve_signature_size,
    signature_sheet_pairs,
)


def test_pages_from_sheets():
    assert pages_from_sheets(4) == 16


def test_resolve_signature_size_defaults():
    sheets, pages = resolve_signature_size(None, None)
    assert sheets == 4
    assert pages == 16


def test_resolve_signature_size_from_sheets():
    sheets, pages = resolve_signature_size(5, None)
    assert sheets == 5
    assert pages == 20


def test_resolve_signature_size_from_pages():
    sheets, pages = resolve_signature_size(None, 24)
    assert sheets == 6
    assert pages == 24


def test_resolve_signature_size_rejects_conflict():
    with pytest.raises(ValueError):
        resolve_signature_size(4, 20)


def test_build_signature_settings():
    settings = build_signature_settings(sheets_per_signature=4, max_end_padding=8)
    assert settings.sheets_per_signature == 4
    assert settings.pages_per_signature == 16
    assert settings.max_end_padding == 8


def test_signature_sheet_pairs_for_16_pages():
    pairs = signature_sheet_pairs(16)
    assert pairs == [
        ((16, 1), (2, 15)),
        ((14, 3), (4, 13)),
        ((12, 5), (6, 11)),
        ((10, 7), (8, 9)),
    ]


def test_signature_sheet_pairs_requires_multiple_of_four():
    with pytest.raises(ValueError):
        signature_sheet_pairs(10)
