from __future__ import annotations

from core.toc_policy import TocPolicyResult, apply_toc_policy
from core.toc_chapter_detection import promote_detected_chapter_headings


def apply_toc_mode_to_markdown(markdown: str, toc_mode: str = "keep") -> TocPolicyResult:
    """Apply the requested TOC mode for Markdown render workflows."""
    return apply_toc_policy(markdown, mode=toc_mode)
