"""Utilities for layout-heavy / ASCII-art-heavy source text.

Some Project Gutenberg books are not normal prose. They may contain ASCII
banners, boxes, diagrams, repeated separators, or old control-character
artifacts. The goal here is conservative: remove accidental junk/control
characters and tame repeated divider noise without destroying intentional text.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable

# Replacement/control artifacts seen in old ASCII/Gutenberg sources and PDF text.
CONTROL_REPLACEMENTS = {
    "\ufeff": "",   # BOM
    "\ufffd": "",   # replacement char
    "\ufffe": "-",  # often appears where a hyphen/line-break artifact was intended
    "\uffff": "",
    "\u200b": "",   # zero-width space
    "\u200c": "",
    "\u200d": "",
    "\u2060": "",
    "\u00ad": "",   # soft hyphen; usually accidental in body text
}

SYMBOL_CHARS = set("*=+_~#-|/\\.·•…:;<>[]{}()^vV!`'\" ")
REPEATED_SEPARATOR_CHARS = set("*=+_~#-—–·•….")


@dataclass(frozen=True)
class LayoutHeavyStats:
    total_lines: int
    ascii_separator_lines: int
    symbol_heavy_lines: int
    control_artifact_count: int

    @property
    def ascii_separator_ratio(self) -> float:
        if self.total_lines <= 0:
            return 0.0
        return self.ascii_separator_lines / self.total_lines

    @property
    def symbol_heavy_ratio(self) -> float:
        if self.total_lines <= 0:
            return 0.0
        return self.symbol_heavy_lines / self.total_lines

    @property
    def is_layout_heavy(self) -> bool:
        return (
            self.ascii_separator_ratio >= 0.08
            or self.symbol_heavy_ratio >= 0.12
            or self.control_artifact_count >= 3
        )


def sanitize_problem_characters(text: str) -> str:
    """Remove/normalise accidental Unicode control artifacts.

    Keeps normal newlines and tabs. Replaces the common U+FFFE artifact with a
    hyphen because it often appears in old line-broken compounds such as
    ``free\ufffemarket``.
    """
    if not text:
        return text

    for old, new in CONTROL_REPLACEMENTS.items():
        text = text.replace(old, new)

    out: list[str] = []
    for ch in text:
        if ch in "\n\r\t":
            out.append(ch)
            continue
        category = unicodedata.category(ch)
        if category.startswith("C"):
            # Drop remaining non-printing controls.
            continue
        out.append(ch)
    return "".join(out)


def _nonspace_chars(line: str) -> list[str]:
    return [ch for ch in line.strip() if not ch.isspace()]


def is_ascii_separator_line(line: str) -> bool:
    """True for decorative divider lines, not ordinary punctuation.

    Examples: ``******``, ``======``, ``++++ ----``. This deliberately avoids
    classifying prose with punctuation or dictionary entries as separator lines.
    """
    stripped = line.strip()
    if len(stripped) < 8:
        return False
    chars = _nonspace_chars(stripped)
    if not chars:
        return False
    if any(ch.isalnum() for ch in chars):
        return False
    if not all(ch in SYMBOL_CHARS for ch in chars):
        return False
    repeated = sum(1 for ch in chars if ch in REPEATED_SEPARATOR_CHARS)
    return repeated / max(1, len(chars)) >= 0.65


def is_symbol_heavy_line(line: str) -> bool:
    stripped = line.strip()
    if len(stripped) < 12:
        return False
    chars = _nonspace_chars(stripped)
    if not chars:
        return False
    symbol_count = sum(1 for ch in chars if ch in SYMBOL_CHARS or not ch.isalnum())
    alpha_count = sum(1 for ch in chars if ch.isalpha())
    return symbol_count / max(1, len(chars)) >= 0.55 and alpha_count <= 12


def estimate_layout_heavy_stats(text: str) -> LayoutHeavyStats:
    lines = text.splitlines()
    control_artifact_count = sum(text.count(ch) for ch in CONTROL_REPLACEMENTS)
    ascii_separator_lines = sum(1 for line in lines if is_ascii_separator_line(line))
    symbol_heavy_lines = sum(1 for line in lines if is_symbol_heavy_line(line))
    return LayoutHeavyStats(
        total_lines=len(lines),
        ascii_separator_lines=ascii_separator_lines,
        symbol_heavy_lines=symbol_heavy_lines,
        control_artifact_count=control_artifact_count,
    )


def compact_repeated_separator_blocks(text: str, replacement: str = "***") -> str:
    """Collapse consecutive decorative divider lines to a single divider.

    This reduces ugly multi-line ``*****`` / ``=====`` banners in PDF output while
    leaving prose and most ASCII diagrams alone.
    """
    lines = text.splitlines()
    out: list[str] = []
    in_separator_block = False

    for line in lines:
        if is_ascii_separator_line(line):
            if not in_separator_block:
                out.append(replacement)
                in_separator_block = True
            continue
        out.append(line)
        if line.strip():
            in_separator_block = False

    return "\n".join(out)


def clean_layout_heavy_text(text: str) -> str:
    """Apply conservative layout-heavy cleanup to text."""
    text = sanitize_problem_characters(text)
    text = compact_repeated_separator_blocks(text)
    # Remove accidental spaces before punctuation caused by OCR/EPUB splitting.
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    # Normalize excessive blank lines, but keep paragraph breaks.
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text
