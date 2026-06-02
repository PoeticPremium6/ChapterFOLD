from __future__ import annotations

import pytest

from core.settings_catalog import (
    settings_catalog,
    settings_defaults,
    validate_web_settings,
)


def test_settings_catalog_contains_web_visible_book_design_settings():
    catalog = settings_catalog()
    keys = {item["key"] for item in catalog}

    assert "page_ornament" in keys
    assert "chapter_ornament" in keys
    assert "binding_direction" in keys
    assert "page_size_preset" in keys


def test_settings_defaults_are_json_friendly():
    defaults = settings_defaults()

    assert defaults["variant"] == "standard"
    assert defaults["page_ornament"] == "none"
    assert defaults["chapter_ornament"] == "none"
    assert defaults["binding_direction"] == "ltr"


def test_validate_web_settings_accepts_known_values():
    settings = validate_web_settings(
        {
            "variant": "standard",
            "page_ornament": "poetic-vine",
            "chapter_ornament": "rose-window",
            "create_imposed_pdf": "true",
            "imposed_pages_per_signature": "16",
            "binding_direction": "rtl",
        }
    )

    assert settings["page_ornament"] == "poetic-vine"
    assert settings["chapter_ornament"] == "rose-window"
    assert settings["create_imposed_pdf"] is True
    assert settings["imposed_pages_per_signature"] == 16
    assert settings["binding_direction"] == "rtl"


def test_validate_web_settings_rejects_unknown_key():
    with pytest.raises(ValueError, match="Unknown setting"):
        validate_web_settings({"bad_setting": "x"})


def test_validate_web_settings_rejects_bad_choice():
    with pytest.raises(ValueError, match="Invalid value"):
        validate_web_settings({"binding_direction": "sideways"})


def test_catalog_can_hide_advanced_settings():
    catalog = settings_catalog(include_advanced=False)
    keys = {item["key"] for item in catalog}

    assert "binding_direction" not in keys
    assert "page_ornament" in keys
