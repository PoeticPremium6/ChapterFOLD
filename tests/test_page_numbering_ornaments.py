from __future__ import annotations

from core.page_numbering import build_page_number_css


def test_after_title_page_can_use_botanical_page_number_ornament():
    css = build_page_number_css("after-title-page", page_ornament="botanical-leaf")

    assert '"❦ " counter(page) " ❦"' in css
    assert "@page chapterfold-titlepage" in css


def test_main_text_can_use_roman_front_matter_with_ornaments():
    css = build_page_number_css(
        "main-text",
        front_matter_style="roman-lower",
        page_ornament="floral-corner",
    )

    assert '"❧ " counter(page, lower-roman) " ☙"' in css
    assert '"❧ " counter(page) " ☙"' in css


def test_page_number_none_still_disables_numbers_even_with_ornament():
    css = build_page_number_css("none", page_ornament="gothic-flourish")

    assert "content: none" in css
    assert "✦" not in css
