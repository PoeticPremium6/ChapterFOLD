from __future__ import annotations

import pytest

from core.page_numbering import build_page_number_css, normalize_page_number_start_mode
from core.epub_service import LayoutSettings, build_css
from core.schemas import ChapterfoldSettings


def test_page_number_mode_validation():
    assert normalize_page_number_start_mode(None) == "after-title-page"
    assert normalize_page_number_start_mode("main-text") == "main-text"

    with pytest.raises(ValueError):
        normalize_page_number_start_mode("bad")


def test_settings_validate_page_number_start_mode():
    settings = ChapterfoldSettings(page_number_start_mode="main-text")
    settings.validate()

    bad = ChapterfoldSettings(page_number_start_mode="bad")
    with pytest.raises(ValueError):
        bad.validate()


def test_after_title_page_css_suppresses_title_page():
    css = build_page_number_css("after-title-page")

    assert "chapterfold-titlepage" in css
    assert "content: none" in css


def test_main_text_css_suppresses_frontmatter_and_numbers_maintext():
    css = build_page_number_css("main-text")

    assert "chapterfold-frontmatter" in css
    assert "chapterfold-maintext" in css
    assert "counter-reset: page 1" in css
    assert "content: counter(page)" in css


def test_build_css_includes_page_number_mode_css():
    css = build_css(LayoutSettings(page_number_start_mode="none"))

    assert "Page numbering: disabled" in css
    assert "content: none" in css
