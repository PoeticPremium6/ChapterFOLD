from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from bs4 import BeautifulSoup


CHAPTER_HEADING_RE = re.compile(
    r"^\s*(CHAPTER\s+[IVXLCDM0-9]+\.?.*|Chapter\s+[IVXLCDM0-9]+\.?.*)\s*$"
)

FRONT_MATTER_HEADING_RE = re.compile(
    r"^\s*(PREFACE\.?|LIST OF ILLUSTRATIONS\.?|ILLUSTRATIONS\.?)\s*$",
    re.IGNORECASE,
)

INLINE_CHAPTER_RE = re.compile(
    r"\b(CHAPTER\s+[IVXLCDM0-9]+\.?(?:\s+[A-Z][A-Za-z’'—,:;\-\s]+?)?)(?=\n|$|<|\.?\s{2,})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class TocEntry:
    title: str
    anchor: str


def slugify_anchor(value: str, *, fallback: str = "section") -> str:
    value = re.sub(r"\s+", " ", value or "").strip().lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or fallback


def _clean_toc_title(value: str) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    value = value.strip(" .")
    if not value:
        return ""

    # If a caption/prose fragment was accidentally joined before a chapter label,
    # prefer the chapter label.
    chapter_match = re.search(r"\bCHAPTER\s+[IVXLCDM0-9]+\.?.*$", value, re.IGNORECASE)
    if chapter_match:
        value = chapter_match.group(0).strip(" .")

    upper = value.upper()
    if upper == "LIST OF ILLUSTRATIONS":
        return "List of Illustrations"
    if upper == "ILLUSTRATIONS":
        return "List of Illustrations"
    if upper == "PREFACE":
        return "Preface"

    if upper.startswith("CHAPTER "):
        return upper

    return value


def _looks_like_toc_entry(value: str) -> bool:
    value = _clean_toc_title(value)
    if not value:
        return False
    if FRONT_MATTER_HEADING_RE.match(value):
        return True
    if CHAPTER_HEADING_RE.match(value):
        return True
    return False


def _unique_anchor(title: str, used: set[str]) -> str:
    base = slugify_anchor(title)
    anchor = base
    i = 2
    while anchor in used:
        anchor = f"{base}-{i}"
        i += 1
    used.add(anchor)
    return anchor


def _candidate_lines_from_fragment(fragment: str) -> list[str]:
    soup = BeautifulSoup(fragment or "", "html.parser")
    lines: list[str] = []

    for tag in soup.find_all(["h1", "h2", "h3"]):
        lines.append(tag.get_text(" ", strip=True))

    text = soup.get_text("\n", strip=True)
    for line in text.splitlines():
        clean = line.strip()
        if clean:
            lines.append(clean)

    # Also scan raw fragments because some Project Gutenberg chapter labels are
    # adjacent to image/caption markup before normal text extraction.
    raw = re.sub(r"<br\s*/?>", "\n", fragment or "", flags=re.I)
    raw = re.sub(r"<[^>]+>", "\n", raw)
    for line in raw.splitlines():
        clean = line.strip()
        if clean:
            lines.append(clean)

    return lines


def collect_generated_toc_entries(sections: Iterable[tuple[str, str]]) -> list[TocEntry]:
    """Collect clean TOC entries from section headings and in-section labels."""
    entries: list[TocEntry] = []
    seen_titles: set[str] = set()
    used_anchors: set[str] = set()

    def add(title: str) -> None:
        clean = _clean_toc_title(title)
        if not clean or not _looks_like_toc_entry(clean):
            return

        key = clean.casefold()
        if key in seen_titles:
            return

        seen_titles.add(key)
        entries.append(TocEntry(clean, _unique_anchor(clean, used_anchors)))

    for section_heading, fragment in sections:
        add(section_heading)

        for line in _candidate_lines_from_fragment(fragment):
            add(line)
            for match in INLINE_CHAPTER_RE.finditer(line):
                add(match.group(1))

    return entries


def build_generated_toc_text(entries: list[TocEntry]) -> str:
    if not entries:
        return ""
    return "\n".join(f"- {entry.title}" for entry in entries)


def build_generated_toc_html(entries: list[TocEntry]) -> str:
    """Kept for future PDF page-aware TOC work; current clean sections use text."""
    if not entries:
        return ""

    items = "\n".join(
        f'<li><a href="#{entry.anchor}">{entry.title}</a></li>'
        for entry in entries
    )
    return (
        '<section class="generated-contents">\n'
        "<h2>Contents</h2>\n"
        f"<ol>\n{items}\n</ol>\n"
        "</section>"
    )


def add_toc_anchors_to_sections(
    sections: list[tuple[str, str]],
    entries: list[TocEntry],
) -> list[tuple[str, str]]:
    # Plain text clean sections do not currently carry stable HTML anchors.
    # This remains a no-op foundation for the later PDF page-numbered TOC pass.
    return sections


def prepend_generated_toc_section(sections: list[tuple[str, str]]) -> list[tuple[str, str]]:
    entries = collect_generated_toc_entries(sections)
    if not entries:
        return sections

    toc_text = build_generated_toc_text(entries)
    if not toc_text:
        return sections

    if sections and sections[0][0].strip().casefold() == "contents":
        return sections

    return [("Contents", toc_text)] + sections
