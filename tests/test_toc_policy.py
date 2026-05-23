from __future__ import annotations

from core.toc_policy import apply_toc_policy, collect_toc_entries, remove_existing_toc


SAMPLE = """# Test Book

_By Tester_

## Contents

- Chapter One
- Chapter Two

## Chapter One

First chapter text.

## Chapter Two

Second chapter text.
"""


def test_collect_toc_entries_uses_chapter_headings():
    entries = collect_toc_entries(SAMPLE)
    titles = [entry.title for entry in entries]

    assert "Chapter One" in titles
    assert "Chapter Two" in titles
    assert "Contents" not in titles


def test_remove_existing_toc_removes_contents_block():
    cleaned, removed = remove_existing_toc(SAMPLE)

    assert removed is True
    assert "## Contents" not in cleaned
    assert "- Chapter One" not in cleaned
    assert "## Chapter One" in cleaned
    assert "First chapter text." in cleaned


def test_apply_toc_policy_keep_leaves_text_unchanged():
    result = apply_toc_policy(SAMPLE, mode="keep")

    assert result.markdown == SAMPLE
    assert result.removed_existing_toc is False


def test_apply_toc_policy_remove_deletes_contents():
    result = apply_toc_policy(SAMPLE, mode="remove")

    assert "## Contents" not in result.markdown
    assert "## Chapter One" in result.markdown
    assert result.removed_existing_toc is True


def test_apply_toc_policy_rebuild_adds_clean_contents():
    result = apply_toc_policy(SAMPLE, mode="rebuild")

    assert "## Contents" in result.markdown
    assert "- Chapter One" in result.markdown
    assert "- Chapter Two" in result.markdown
    assert result.markdown.count("## Contents") == 1
    assert result.removed_existing_toc is True


def test_apply_toc_policy_rejects_unknown_mode():
    try:
        apply_toc_policy(SAMPLE, mode="nonsense")
    except ValueError as exc:
        assert "Unknown TOC mode" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
