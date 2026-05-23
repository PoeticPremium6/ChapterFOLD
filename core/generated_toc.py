from __future__ import annotations

from dataclasses import dataclass
from html import escape
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

    upper = value.upper()
    if upper == "LIST OF ILLUSTRATIONS":
        return "List of Illustrations"
    if upper == "ILLUSTRATIONS":
        return "List of Illustrations"
    if upper == "PREFACE":
        return "Preface"

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


def collect_generated_toc_entries(sections: Iterable[tuple[str, str]]) -> list[TocEntry]:
    """Collect clean TOC entries from section headings and in-section headings."""
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

    for section_heading, html_fragment in sections:
        add(section_heading)

        soup = BeautifulSoup(html_fragment or "", "html.parser")
        for tag in soup.find_all(["h1", "h2", "h3"]):
            add(tag.get_text(" ", strip=True))

    return entries


def add_toc_anchors_to_sections(
    sections: list[tuple[str, str]],
    entries: list[TocEntry],
) -> list[tuple[str, str]]:
    """Add stable HTML anchors to headings/sections used by the generated TOC."""
    if not entries:
        return sections

    title_to_anchor = {entry.title.casefold(): entry.anchor for entry in entries}
    anchored: list[tuple[str, str]] = []

    for section_heading, html_fragment in sections:
        fragment = html_fragment or ""
        soup = BeautifulSoup(fragment, "html.parser")
        changed = False

        for tag in soup.find_all(["h1", "h2", "h3"]):
            title = _clean_toc_title(tag.get_text(" ", strip=True))
            anchor = title_to_anchor.get(title.casefold())
            if anchor:
                tag["id"] = anchor
                changed = True

        section_title = _clean_toc_title(section_heading)
        section_anchor = title_to_anchor.get(section_title.casefold())

        if section_anchor and f'id="{section_anchor}"' not in str(soup):
            marker = soup.new_tag("span")
            marker["id"] = section_anchor
            marker["class"] = "toc-anchor"
            soup.insert(0, marker)
            changed = True

        anchored.append((section_heading, str(soup) if changed else fragment))

    return anchored


def build_generated_toc_html(entries: list[TocEntry]) -> str:
    if not entries:
        return ""

    items = "\n".join(
        f'<li><a href="#{escape(entry.anchor)}">{escape(entry.title)}</a></li>'
        for entry in entries
    )

    return (
        '<section class="generated-contents">\n'
        "<h2>Contents</h2>\n"
        f"<ol>\n{items}\n</ol>\n"
        "</section>"
    )


def prepend_generated_toc_section(sections: list[tuple[str, str]]) -> list[tuple[str, str]]:
    entries = collect_generated_toc_entries(sections)
    if not entries:
        return sections

    anchored_sections = add_toc_anchors_to_sections(sections, entries)
    toc_html = build_generated_toc_html(entries)

    if anchored_sections and anchored_sections[0][0].strip().casefold() == "contents":
        return anchored_sections

    return [("Contents", toc_html)] + anchored_sections
