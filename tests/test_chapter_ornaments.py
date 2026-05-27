from __future__ import annotations

from core.page_ornaments import (
    build_chapter_ornament_css,
    chapter_ornament_choices,
    chapter_ornament_text,
    normalize_chapter_ornament,
)
from core.schemas import ChapterfoldSettings


def test_chapter_ornament_choices_include_signature_options():
    keys = [key for key, _, _ in chapter_ornament_choices()]

    assert keys == [
        "none",
        "classic-rule",
        "botanical-divider",
        "poetic-vine",
        "moon-garden",
        "rose-window",
        "bookbinder-rule",
    ]


def test_chapter_ornament_text_for_signature_motifs():
    assert chapter_ornament_text("poetic-vine") == "❧ ❦ ❧"
    assert chapter_ornament_text("moon-garden") == "☾ ✦ ☽"
    assert chapter_ornament_text("bookbinder-rule") == "─ ❧ ☙ ─"


def test_chapter_ornament_css_none_is_empty():
    assert build_chapter_ornament_css("none") == ""


def test_chapter_ornament_css_targets_chapter_headings():
    css = build_chapter_ornament_css("rose-window")

    assert ".chapter > h1:first-child::after" in css
    assert "✿ ❈ ✿" in css


def test_settings_accept_chapter_ornament():
    settings = ChapterfoldSettings(chapter_ornament="poetic-vine")
    settings.validate()

    assert settings.chapter_ornament == "poetic-vine"


def test_settings_reject_bad_chapter_ornament():
    settings = ChapterfoldSettings(chapter_ornament="bad")

    try:
        settings.validate()
    except ValueError as exc:
        assert "chapter_ornament" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_normalize_chapter_ornament_defaults_to_none():
    assert normalize_chapter_ornament(None) == "none"
