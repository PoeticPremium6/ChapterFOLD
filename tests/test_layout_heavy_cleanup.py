from __future__ import annotations

from core.layout_heavy import (
    clean_layout_heavy_text,
    compact_repeated_separator_blocks,
    estimate_layout_heavy_stats,
    is_ascii_separator_line,
    sanitize_problem_characters,
)


def test_sanitize_problem_characters_repairs_fffe_hyphen_artifact():
    text = "free\ufffemarket and co\ufffeconspirators"
    assert sanitize_problem_characters(text) == "free-market and co-conspirators"


def test_separator_line_detection_is_conservative():
    assert is_ascii_separator_line("************************************************")
    assert is_ascii_separator_line("======== ======== ========")
    assert not is_ascii_separator_line("Chapter 1: CYBERPUNK: A CHALLENGING POSTMODERN LIFESTYLE")
    assert not is_ascii_separator_line("<<ASCII>>: keyboard characters")


def test_compact_repeated_separator_blocks():
    text = "Before\n**************\n**************\n==============\nAfter"
    assert compact_repeated_separator_blocks(text) == "Before\n***\nAfter"


def test_layout_heavy_stats_detects_artifacts():
    text = "Intro\n**************\n==============\nfree\ufffemarket\nNormal prose"
    stats = estimate_layout_heavy_stats(text)
    assert stats.ascii_separator_lines == 2
    assert stats.control_artifact_count == 1
    assert stats.is_layout_heavy


def test_clean_layout_heavy_text_keeps_prose_but_tames_noise():
    text = "free\ufffemarket\n**************\n**************\nUseful prose , with spacing ."
    cleaned = clean_layout_heavy_text(text)
    assert "free-market" in cleaned
    assert cleaned.count("***") == 1
    assert "prose," in cleaned
    assert "spacing." in cleaned
