from __future__ import annotations

import pytest

from core.page_numbering import build_page_number_css, normalize_front_matter_number_style
from core.epub_service import LayoutSettings, build_css
from core.schemas import ChapterfoldSettings


def test_front_matter_number_style_validation():
    assert normalize_front_matter_number_style(None) == "hidden"
    assert normalize_front_matter_number_style("roman-lower") == "roman-lower"

    with pytest.raises(ValueError):
        normalize_front_matter_number_style("bad")


def test_settings_validate_front_matter_number_style():
    ChapterfoldSettings(front_matter_page_number_style="roman-lower").validate()

    with pytest.raises(ValueError):
        ChapterfoldSettings(front_matter_page_number_style="bad").validate()


def test_main_text_roman_lower_frontmatter_css():
    css = build_page_number_css("main-text", "roman-lower")

    assert "chapterfold-frontmatter" in css
    assert "counter(page, lower-roman)" in css
    assert "counter-reset: page 1" in css


def test_main_text_roman_upper_frontmatter_css():
    css = build_page_number_css("main-text", "roman-upper")

    assert "counter(page, upper-roman)" in css


def test_build_css_includes_front_matter_number_style():
    css = build_css(
        LayoutSettings(
            page_number_start_mode="main-text",
            front_matter_page_number_style="roman-lower",
        )
    )

    assert "counter(page, lower-roman)" in css
