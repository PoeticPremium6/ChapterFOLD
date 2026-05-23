from __future__ import annotations

from core.toc_rendering import apply_toc_mode_to_markdown


SAMPLE = """# Test Book

_By Tester_

## Contents

- Old Chapter

## CHAPTER 1. First

Text.

CHAPTER 2. Second

More text.
"""


def test_toc_rendering_keep_preserves_existing_contents():
    result = apply_toc_mode_to_markdown(SAMPLE, "keep")

    assert "## Contents" in result.markdown
    assert "- Old Chapter" in result.markdown
    assert result.removed_existing_toc is False


def test_toc_rendering_remove_deletes_existing_contents():
    result = apply_toc_mode_to_markdown(SAMPLE, "remove")

    assert "## Contents" not in result.markdown
    assert "- Old Chapter" not in result.markdown
    assert "## CHAPTER 1. First" in result.markdown
    assert result.removed_existing_toc is True


def test_toc_rendering_rebuild_inserts_clean_contents():
    result = apply_toc_mode_to_markdown(SAMPLE, "rebuild")

    assert "## Contents" in result.markdown
    assert "- CHAPTER 1. First" in result.markdown
    assert "- CHAPTER 2. Second" in result.markdown
    assert result.markdown.count("## Contents") == 1
    assert result.removed_existing_toc is True


def test_toc_rendering_rejects_unknown_mode():
    try:
        apply_toc_mode_to_markdown(SAMPLE, "bad-mode")
    except ValueError as exc:
        assert "Unknown TOC mode" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
