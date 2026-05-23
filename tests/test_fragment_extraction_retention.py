from __future__ import annotations

from pathlib import Path

import pytest

from core.epub_service import (
    CleanupSettings,
    build_clean_text_sections,
    build_clean_text_sections_with_retention_guard,
    estimate_cleaned_text_chars,
    extract_clean_items_from_html,
    load_epub_content,
)


def test_multi_root_html_fragment_keeps_all_top_level_paragraphs():
    # Gutenberg/Moby-style spine files often contain many top-level <p> tags.
    # Parsing those fragments as XML silently kept only the first top-level tag.
    fragment = """
    <p>First paragraph before a chapter heading.</p>
    <h2>CHAPTER 17. The Ramadan.</h2>
    <p>Second paragraph after the heading.</p>
    <p>Third paragraph after the heading.</p>
    """

    items = extract_clean_items_from_html(fragment, cleanup_settings=CleanupSettings())
    text = "\n\n".join(t for kind, t in items if kind == "p")

    assert "First paragraph before" in text
    assert "Second paragraph after" in text
    assert "Third paragraph after" in text


def test_cleanup_retention_guard_reports_healthy_cleaning():
    sections = [
        ("CHAPTER 1", "<p>Call me Ishmael. Some years ago.</p><p>Another long paragraph follows.</p>"),
        ("CHAPTER 2", "<p>The carpet-bag was packed.</p>"),
    ]

    cleaned, report = build_clean_text_sections_with_retention_guard(
        sections,
        drop_notes=False,
        cleanup_settings=CleanupSettings(),
        gutenberg_report={
            "gutenberg_detected": True,
            "selected_text_chars": 500,
            "selected_retention_ratio": 0.95,
        },
    )

    assert cleaned
    assert report["cleaned_text_chars"] == estimate_cleaned_text_chars(cleaned)
    assert report["cleanup_retention_ratio"] > 0
    assert report["failed"] is False


@pytest.mark.local_gutenberg
def test_local_moby_dick_cleanup_retains_body_if_fixture_exists():
    fixture = Path("tests/fixtures/gutenberg/raw/Moby Dick.epub")
    if not fixture.exists():
        pytest.skip("Local Gutenberg Moby Dick fixture is not present.")

    content = load_epub_content(fixture)
    gutenberg_report = getattr(content, "gutenberg_report", {})
    assert gutenberg_report.get("gutenberg_detected") is True
    assert gutenberg_report.get("selected_text_chars", 0) > 1_000_000

    cleaned = build_clean_text_sections(
        content.sections,
        drop_notes=False,
        cleanup_settings=CleanupSettings(),
    )
    cleaned_chars = estimate_cleaned_text_chars(cleaned)
    joined = "\n\n".join(text for _, text in cleaned)

    assert cleaned_chars > 500_000
    assert "Call me Ishmael" in joined
    assert "Queequeg" in joined
    assert "another orphan" in joined
