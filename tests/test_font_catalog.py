from __future__ import annotations

from core.font_catalog import FONT_CHOICES, font_css_stack, get_font_choice
from core.epub_service import LayoutSettings, build_css


def test_font_catalog_has_diverse_choices():
    keys = {choice.key for choice in FONT_CHOICES}

    for key in {
        "classic-serif",
        "eb-garamond",
        "cormorant",
        "libre-baskerville",
        "crimson-pro",
        "vollkorn",
        "literata",
        "source-serif",
        "gentium",
        "alegreya",
        "bookman",
        "palatino",
        "atkinson",
        "open-sans",
        "source-sans",
        "lora",
        "bitter",
        "merriweather",
        "fell-english",
        "typewriter",
        "caveat",
        "dancing-script",
        "playwrite",
        "readable-cursive",
        "unicode-global",
        "cjk-serif",
        "cjk-sans",
    }:
        assert key in keys


def test_font_choice_fallback():
    assert get_font_choice("not-real").key == "classic-serif"


def test_dropdown_labels_include_recommendations():
    choice = get_font_choice("libre-baskerville")
    assert "Libre Baskerville" in choice.dropdown_label
    assert "premium-looking printed books" in choice.dropdown_label


def test_unicode_global_contains_cjk_and_accent_sample():
    choice = get_font_choice("unicode-global")

    assert "你好" in choice.sample
    assert "ö ä å" in choice.sample
    assert "Noto Serif CJK SC" in choice.css_stack


def test_cursive_choices_exist_with_safe_fallbacks():
    assert "cursive" in get_font_choice("caveat").css_stack
    assert "cursive" in get_font_choice("dancing-script").css_stack
    assert "Segoe Print" in get_font_choice("readable-cursive").css_stack


def test_build_css_accepts_font_catalog_stack():
    css = build_css(LayoutSettings(font_family=font_css_stack("lora")))

    assert "Lora" in css
    assert "font-family:" in css
