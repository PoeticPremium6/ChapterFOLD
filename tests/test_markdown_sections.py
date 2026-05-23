from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from core.markdown_sections import (
    add_section_markers,
    combine_markdown_books,
    render_section_manifest,
    split_markdown_sections,
)


SAMPLE = """# Test Book

_By Tester_

## Chapter One

Opening text.

## Author Note

Remove me later.

## Chapter Two

More text.
"""


def test_add_section_markers_before_level_two_headings():
    marked = add_section_markers(SAMPLE)
    assert "<!-- chapterfold-section: Chapter One -->" in marked
    assert "<!-- chapterfold-section: Author Note -->" in marked
    assert marked.count("chapterfold-section:") == 3


def test_split_markdown_sections_detects_sections():
    sections = split_markdown_sections(add_section_markers(SAMPLE))
    titles = [section.title for section in sections]
    assert "Chapter One" in titles
    assert "Author Note" in titles
    assert "Chapter Two" in titles


def test_manifest_lists_detected_sections():
    manifest = render_section_manifest(add_section_markers(SAMPLE))
    assert "ChapterFOLD section manifest" in manifest
    assert "Chapter One" in manifest
    assert "Author Note" in manifest


def test_combine_markdown_books_removes_duplicate_titles():
    combined = combine_markdown_books([SAMPLE, SAMPLE], title="Combined", author="A. Person")
    assert combined.startswith("# Combined")
    assert "_By A. Person_" in combined
    assert combined.count("# Test Book") == 0
    assert combined.count("Chapter One") >= 2


def test_sectionize_script_help_runs():
    result = subprocess.run(
        [sys.executable, "scripts/sectionize_markdown_book.py", "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "section markers" in result.stdout


def test_combine_script_writes_output(tmp_path):
    one = tmp_path / "one.md"
    two = tmp_path / "two.md"
    out = tmp_path / "combined.md"
    one.write_text(SAMPLE, encoding="utf-8")
    two.write_text(SAMPLE.replace("Test Book", "Second Book"), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/combine_markdown_books.py",
            str(one),
            str(two),
            "--title",
            "My Omnibus",
            "--author",
            "Various",
            "--output",
            str(out),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    text = out.read_text(encoding="utf-8")
    assert "# My Omnibus" in text
    assert "Test Book" in text
    assert "Second Book" in text
