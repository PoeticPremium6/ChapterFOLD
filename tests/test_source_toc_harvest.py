from __future__ import annotations

from core.source_toc_harvest import harvest_source_toc_entries, roman_to_int
from core.epub_service import build_clean_text_sections, CleanupSettings


def test_roman_to_int():
    assert roman_to_int("I") == 1
    assert roman_to_int("IV") == 4
    assert roman_to_int("LXI") == 61


def test_harvest_source_toc_entries_from_pride_style_links():
    html = """
    <p class="toc">
      <a href="#PREFACE">PREFACE.</a><br/>
      <a href="#ILLUSTRATIONS">List of Illustrations.</a><br/>
      <a href="#CHAPTER_I">I.</a><br/>
      <a href="#CHAPTER_II">II.</a><br/>
      <a href="#CHAPTER_III">III.</a><br/>
    </p>
    """

    assert harvest_source_toc_entries(html) == [
        "Preface",
        "List of Illustrations",
        "CHAPTER I",
        "CHAPTER II",
        "CHAPTER III",
    ]


def test_harvest_prefers_actual_toc_block_over_other_links():
    html = """
    <div>
      <a href="#illus_lxi">LXI.</a>
      <a href="#illus_iv">IV.</a>
    </div>
    <p class="toc">
      <a href="#PREFACE">PREFACE.</a><br/>
      <a href="#ILLUSTRATIONS">List of Illustrations.</a><br/>
      <a href="#CHAPTER_I">I.</a><br/>
      <a href="#CHAPTER_II">II.</a><br/>
      <a href="#CHAPTER_III">III.</a><br/>
    </p>
    """

    assert harvest_source_toc_entries(html) == [
        "Preface",
        "List of Illustrations",
        "CHAPTER I",
        "CHAPTER II",
        "CHAPTER III",
    ]


def test_generated_contents_uses_harvested_source_toc_seed():
    sections = [
        (
            "",
            """
            <p class="toc">
              <a href="#PREFACE">PREFACE.</a><br/>
              <a href="#ILLUSTRATIONS">List of Illustrations.</a><br/>
              <a href="#CHAPTER_I">I.</a><br/>
              <a href="#CHAPTER_II">II.</a><br/>
            </p>
            <p>Real title page text.</p>
            """,
        ),
        ("I hope Mr. Bingley will like it. CHAPTER II.", "<p>Body.</p>"),
    ]

    cleaned = build_clean_text_sections(
        sections,
        drop_notes=False,
        cleanup_settings=CleanupSettings(),
        contents_mode="rebuild",
    )

    assert cleaned[0][0] == "Contents"
    assert "- Preface" in cleaned[0][1]
    assert "- List of Illustrations" in cleaned[0][1]
    assert "- CHAPTER I" in cleaned[0][1]
    assert "- CHAPTER II" in cleaned[0][1]
    assert "__SOURCE_TOC_SEED__" not in [heading for heading, _ in cleaned]


def test_illustration_page_links_are_not_treated_as_chapters():
    html = """
    <div class="loi">
      <a href="#i_061">LXI.</a>
      <a href="#i_004">IV.</a>
      <a href="#i_025">XXV.</a>
    </div>
    """

    assert harvest_source_toc_entries(html) == []


def test_harvest_gutenberg_chapter_colon_and_comma_labels():
    html = """
    <p class="toc">
      <a href="#PREFACE">PREFACE.</a><br/>
      <a href="#LIST_OF_ILLUSTRATIONS">List of Illustrations.</a><br/>
      <a href="#Chapter_I">Chapter: I.,</a>
      <a href="#CHAPTER_II">II.,</a>
      <a href="#CHAPTER_III">III.,</a>
      <a href="#CHAPTER_LXI">LXI.</a>
    </p>
    """

    assert harvest_source_toc_entries(html) == [
        "Preface",
        "List of Illustrations",
        "CHAPTER I",
        "CHAPTER II",
        "CHAPTER III",
        "CHAPTER LXI",
    ]
