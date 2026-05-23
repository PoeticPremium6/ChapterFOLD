from __future__ import annotations

from core.toc_chapter_detection import (
    collect_detected_chapter_titles,
    promote_detected_chapter_headings,
)
from core.toc_rendering import apply_toc_mode_to_markdown


SAMPLE = """# Example

_By Tester_

## CHAPTER 1. First.

Opening text.

CHAPTER 2. Second.

More text.

Some paragraph ends here. CHAPTER 3. Third. The next chapter starts inline.

## Epilogue

Done.
"""


def test_promote_bare_chapter_lines_to_headings():
    result = promote_detected_chapter_headings(SAMPLE)

    assert result.promoted_count >= 2
    assert "## CHAPTER 2. Second." in result.markdown
    assert "## CHAPTER 3. Third." in result.markdown
    assert "<!-- chapterfold-section: CHAPTER 2. Second. -->" in result.markdown


def test_collect_detected_titles_includes_promoted_chapters():
    titles = collect_detected_chapter_titles(SAMPLE)

    assert "CHAPTER 1. First." in titles
    assert "CHAPTER 2. Second." in titles
    assert "CHAPTER 3. Third." in titles
    assert "Epilogue" in titles


def test_rebuild_toc_uses_promoted_chapters():
    result = apply_toc_mode_to_markdown(SAMPLE, "rebuild")

    assert "## Contents" in result.markdown
    assert "- CHAPTER 1. First." in result.markdown
    assert "- CHAPTER 2. Second." in result.markdown
    assert "- CHAPTER 3. Third." in result.markdown
    assert "## CHAPTER 2. Second." in result.markdown
    assert "## CHAPTER 3. Third." in result.markdown
