from __future__ import annotations

from core.generated_toc import (
    build_generated_toc_html,
    build_generated_toc_text,
    collect_generated_toc_entries,
    prepend_generated_toc_section,
)


def test_collect_generated_toc_entries_from_front_matter_and_chapters():
    sections = [
        ("", "<h2>PREFACE.</h2><p>Intro.</p><h2>LIST OF ILLUSTRATIONS.</h2>"),
        ("CHAPTER I.", "<p>Body.</p>"),
        ("", "<h2>CHAPTER II.</h2><p>More body.</p>"),
    ]

    entries = collect_generated_toc_entries(sections)
    titles = [entry.title for entry in entries]

    assert titles == [
        "Preface",
        "List of Illustrations",
        "CHAPTER I",
        "CHAPTER II",
    ]


def test_build_generated_toc_text_is_markdown_friendly():
    sections = [
        ("CHAPTER I.", "<p>Body.</p>"),
        ("CHAPTER II.", "<p>More body.</p>"),
    ]
    entries = collect_generated_toc_entries(sections)

    text = build_generated_toc_text(entries)

    assert "- CHAPTER I" in text
    assert "- CHAPTER II" in text
    assert "<h2>" not in text


def test_build_generated_toc_html_still_available_for_future_pdf_toc():
    sections = [
        ("CHAPTER I.", "<p>Body.</p>"),
        ("CHAPTER II.", "<p>More body.</p>"),
    ]
    entries = collect_generated_toc_entries(sections)

    html = build_generated_toc_html(entries)

    assert "<h2>Contents</h2>" in html
    assert 'href="#chapter-i"' in html
    assert 'href="#chapter-ii"' in html


def test_prepend_generated_toc_section_uses_plain_text():
    sections = [
        ("CHAPTER I.", "<p>It is a truth universally acknowledged.</p>"),
        ("CHAPTER II.", "<p>Mr Bennet was among the earliest.</p>"),
    ]

    result = prepend_generated_toc_section(sections)

    assert result[0][0] == "Contents"
    assert "- CHAPTER I" in result[0][1]
    assert "- CHAPTER II" in result[0][1]
    assert "<section" not in result[0][1]


def test_caption_prefixed_heading_prefers_chapter_label():
    sections = [
        ("I hope Mr. Bingley will like it. CHAPTER II.", "<p>Body.</p>"),
    ]

    entries = collect_generated_toc_entries(sections)

    assert [entry.title for entry in entries] == ["CHAPTER II"]
