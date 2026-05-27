from __future__ import annotations

from core.page_numbering import build_page_number_css
from core.page_ornaments import (
    normalize_page_ornament_amount,
    page_ornament_amount_choices,
    page_ornament_counter_content,
)


def test_page_ornament_amount_choices():
    keys = [key for key, _, _ in page_ornament_amount_choices()]
    assert keys == ["subtle", "balanced", "ornate"]


def test_page_ornament_amount_changes_counter_content():
    assert page_ornament_counter_content("counter(page)", "botanical-leaf", "subtle") == '"❦ " counter(page) " ❦"'
    assert page_ornament_counter_content("counter(page)", "botanical-leaf", "balanced") == '"❦ ❦ " counter(page) " ❦ ❦"'
    assert page_ornament_counter_content("counter(page)", "botanical-leaf", "ornate") == '"❦ ❦ ❦ " counter(page) " ❦ ❦ ❦"'


def test_invalid_page_ornament_amount_rejected():
    try:
        normalize_page_ornament_amount("huge")
    except ValueError as exc:
        assert "page ornament amount" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_page_number_css_uses_ornate_amount():
    css = build_page_number_css(
        "after-title-page",
        page_ornament="floral-corner",
        page_ornament_amount="ornate",
    )

    assert '"❧ ❧ ❧ " counter(page) " ☙ ☙ ☙"' in css


def test_new_page_ornament_motifs_generate_content():
    assert page_ornament_counter_content("counter(page)", "rose", "balanced") == '"✿ ✿ " counter(page) " ✿ ✿"'
    assert page_ornament_counter_content("counter(page)", "celestial", "subtle") == '"☾ " counter(page) " ✦"'
    assert page_ornament_counter_content("counter(page)", "minimal-divider", "ornate") == '"– – – " counter(page) " – – –"'


def test_signature_motifs_scale_as_sequences():
    assert page_ornament_counter_content("counter(page)", "poetic-vine", "subtle") == '"❧ ❦ " counter(page) " ❦ ☙"'
    assert page_ornament_counter_content("counter(page)", "moon-garden", "balanced") == '"☾ ✦ ☾ ✦ " counter(page) " ✦ ☽ ✦ ☽"'
    assert page_ornament_counter_content("counter(page)", "bookbinder-rule", "ornate") == '"─ ❧ ─ ❧ ─ ❧ " counter(page) " ☙ ─ ☙ ─ ☙ ─"'
