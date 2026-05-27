from __future__ import annotations

from core.page_ornaments import (
    build_page_ornament_css,
    get_page_ornament_preset,
    ornamented_page_number_span,
    page_ornament_choices,
)


def test_page_ornament_choices_include_beautiful_presets():
    keys = [key for key, _, _ in page_ornament_choices()]

    assert "none" in keys
    assert "classic-rule" in keys
    assert "botanical-leaf" in keys
    assert "floral-corner" in keys
    assert "gothic-flourish" in keys
    assert "storybook" in keys


def test_unknown_page_ornament_falls_back_to_none():
    preset = get_page_ornament_preset("missing")

    assert preset.key == "none"


def test_build_page_ornament_css_for_none_is_empty():
    assert build_page_ornament_css("none") == ""


def test_build_page_ornament_css_contains_selected_class():
    css = build_page_ornament_css("botanical-leaf")

    assert "page-number-ornament" in css
    assert "ornament-botanical-leaf" in css
    assert "❦" in css


def test_ornamented_page_number_span_wraps_non_none_preset():
    html = ornamented_page_number_span("12", "floral-corner")

    assert 'class="page-number-ornament ornament-floral-corner"' in html
    assert ">12<" in html


def test_ornamented_page_number_span_leaves_none_plain():
    assert ornamented_page_number_span("12", "none") == "12"


def test_page_ornament_counter_content_wraps_counter():
    from core.page_ornaments import page_ornament_counter_content

    assert page_ornament_counter_content("counter(page)", "botanical-leaf") == '"❦ " counter(page) " ❦"'
    assert page_ornament_counter_content("counter(page)", "classic-rule") == '"— " counter(page) " —"'
    assert page_ornament_counter_content("counter(page)", "none") == "counter(page)"


def test_page_ornament_choices_include_richer_motifs():
    keys = [key for key, _, _ in page_ornament_choices()]

    for key in [
        "vine",
        "laurel",
        "victorian-dots",
        "celestial",
        "rose",
        "ivy",
        "acanthus",
        "minimal-divider",
    ]:
        assert key in keys


def test_page_ornament_choices_include_signature_motifs():
    keys = [key for key, _, _ in page_ornament_choices()]

    for key in [
        "poetic-vine",
        "moon-garden",
        "rose-window",
        "ivy-thorn",
        "asterism",
        "bookbinder-rule",
    ]:
        assert key in keys
