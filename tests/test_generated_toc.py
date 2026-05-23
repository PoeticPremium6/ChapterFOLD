from __future__ import annotations

from core.generated_toc import (
    add_toc_anchors_to_sections,
    build_generated_toc_html,
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


def test_build_generated_toc_html_uses_links():
    sections = [
        ("CHAPTER I.", "<p>Body.</p>"),
        ("CHAPTER II.", "<p>More body.</p>"),
    ]
    entries = collect_generated_toc_entries(sections)

    html = build_generated_toc_html(entries)

    assert "<h2>Contents</h2>" in html
    assert 'href="#chapter-i"' in html
    assert 'href="#chapter-ii"' in html


def test_add_toc_anchors_to_sections():
    sections = [
        ("", "<h2>CHAPTER I.</h2><p>Body.</p>"),
        ("CHAPTER II.", "<p>More body.</p>"),
    ]
    entries = collect_generated_toc_entries(sections)

    anchored = add_toc_anchors_to_sections(sections, entries)

    assert 'id="chapter-i"' in anchored[0][1]
    assert 'id="chapter-ii"' in anchored[1][1]


def test_prepend_generated_toc_section():
    sections = [
        ("CHAPTER I.", "<p>It is a truth universally acknowledged.</p>"),
        ("CHAPTER II.", "<p>Mr Bennet was among the earliest.</p>"),
    ]

    result = prepend_generated_toc_section(sections)

    assert result[0][0] == "Contents"
    assert "<h2>Contents</h2>" in result[0][1]
    assert 'href="#chapter-i"' in result[0][1]
    assert 'id="chapter-i"' in result[1][1]
    assert 'id="chapter-ii"' in result[2][1]
