from __future__ import annotations

import re
from bs4 import BeautifulSoup, Tag


ROMAN_LINE_RE = re.compile(
    r"^\s*(PREFACE\.?|CONTENTS\.?|ILLUSTRATIONS\.?|LIST OF ILLUSTRATIONS\.?|"
    r"[IVXLCDM]+\.?)\s*$",
    re.IGNORECASE,
)


def _link_count(tag: Tag) -> int:
    return len(tag.find_all("a"))


def _text_lines(tag: Tag) -> list[str]:
    return [line.strip() for line in tag.get_text("\n", strip=True).splitlines() if line.strip()]


def _looks_like_cramped_original_toc(tag: Tag) -> bool:
    """Detect source EPUB/Gutenberg TOC blocks that should be rebuilt by ChapterFOLD."""
    # BeautifulSoup tags can remain in a precomputed list after an ancestor has
    # been decomposed. In that state attrs may be None and tag.get() can fail.
    if not isinstance(tag, Tag) or getattr(tag, "attrs", None) is None:
        return False

    classes = {str(cls).lower() for cls in (tag.get("class") or [])}
    role = str(tag.get("role") or "").lower()
    tag_id = str(tag.get("id") or "").lower()

    if role in {"doc-toc", "navigation"}:
        return True

    if tag.name == "nav":
        return True

    if "toc" in classes or "contents" in classes:
        return True

    if "toc" in tag_id or "contents" in tag_id:
        return True

    links = _link_count(tag)
    lines = _text_lines(tag)

    if links >= 8:
        return True

    if len(lines) >= 8:
        romanish = sum(1 for line in lines if ROMAN_LINE_RE.match(line))
        if romanish >= 6:
            return True

    return False


def strip_original_toc_blocks(html_fragment: str) -> str:
    """Remove cramped source TOC/list blocks while preserving real prose front matter."""
    if not html_fragment:
        return ""

    soup = BeautifulSoup(html_fragment, "html.parser")

    # Remove obvious nav/toc containers first. Iterate from deepest to shallowest
    # so removing a parent does not invalidate children that are still queued.
    tags = list(soup.find_all(["nav", "div", "section", "p", "ol", "ul"]))
    tags.sort(key=lambda tag: len(list(tag.parents)) if isinstance(tag, Tag) else 0, reverse=True)

    for tag in tags:
        if not isinstance(tag, Tag) or getattr(tag, "attrs", None) is None:
            continue

        if _looks_like_cramped_original_toc(tag):
            tag.decompose()

    # Gutenberg Pride-style fallback: standalone runs of many roman numeral lines.
    text = str(soup)
    text = re.sub(
        r"(?is)(<p[^>]*>\s*)?"
        r"(PREFACE\.?\s*<br\s*/?>\s*)?"
        r"(LIST OF ILLUSTRATIONS\.?\s*<br\s*/?>\s*)?"
        r"((?:[IVXLCDM]+\.?\s*<br\s*/?>\s*){8,})"
        r"(</p>)?",
        "",
        text,
    )

    return text
