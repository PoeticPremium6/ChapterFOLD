from __future__ import annotations

import re
from bs4 import BeautifulSoup, Tag

ROMAN_RE = re.compile(r"^[IVXLCDM]+[.,:]*$", re.IGNORECASE)
CHAPTER_COLON_RE = re.compile(r"^CHAPTER\s*:\s*([IVXLCDM]+)[.,:]*$", re.IGNORECASE)
CHAPTER_HREF_RE = re.compile(r"(?:^|[#/_-])chapter[_\-\s]*([ivxlcdm]+|\d+)\b", re.IGNORECASE)

FRONT_REMAP = {
    "PREFACE": "Preface",
    "PREFACE.": "Preface",
    "LIST OF ILLUSTRATIONS": "List of Illustrations",
    "LIST OF ILLUSTRATIONS.": "List of Illustrations",
    "ILLUSTRATIONS": "List of Illustrations",
    "ILLUSTRATIONS.": "List of Illustrations",
}


def roman_to_int(value: str) -> int:
    value = value.upper().strip().strip(".,:")
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    prev = 0
    for char in reversed(value):
        current = values.get(char, 0)
        if current < prev:
            total -= current
        else:
            total += current
            prev = current
    return total


def _chapter_from_href(href: str) -> str:
    match = CHAPTER_HREF_RE.search(href or "")
    if not match:
        return ""
    return match.group(1).upper()


def _target_looks_like_chapter(target: str) -> bool:
    return bool(_chapter_from_href(target))


def _clean_source_toc_label(value: str, *, href: str = "") -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    if not value:
        return ""

    upper = value.upper().strip()
    if upper in FRONT_REMAP:
        return FRONT_REMAP[upper]

    href_chapter = _chapter_from_href(href)

    # If the target is a chapter anchor, trust it. Gutenberg often uses labels
    # like "Chapter: I.," or "II.," where the href is cleaner than the text.
    if href_chapter and (
        ROMAN_RE.match(value)
        or CHAPTER_COLON_RE.match(value)
        or upper.startswith("CHAPTER")
    ):
        return f"CHAPTER {href_chapter}"

    chapter_colon = CHAPTER_COLON_RE.match(value)
    if chapter_colon and href_chapter:
        return f"CHAPTER {chapter_colon.group(1).upper()}"

    if ROMAN_RE.match(value):
        if href_chapter:
            return f"CHAPTER {value.strip('.,:').upper()}"
        return ""

    if upper.startswith("CHAPTER "):
        return upper.strip(" .,:")
        
    return ""


def _chapter_sort_key(label: str) -> tuple[int, int, str]:
    if label == "Preface":
        return (0, 0, label)
    if label == "List of Illustrations":
        return (1, 0, label)

    match = re.match(r"CHAPTER\s+([IVXLCDM]+)", label, re.IGNORECASE)
    if match:
        return (2, roman_to_int(match.group(1)), label)

    match = re.match(r"CHAPTER\s+(\d+)", label, re.IGNORECASE)
    if match:
        return (2, int(match.group(1)), label)

    return (9, 9999, label)


def _unique(entries: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for entry in entries:
        key = entry.casefold()
        if key not in seen:
            seen.add(key)
            result.append(entry)
    return result


def _entries_from_tag(tag: Tag) -> list[str]:
    entries: list[str] = []
    for link in tag.find_all("a"):
        href = str(link.get("href") or "")
        label = _clean_source_toc_label(link.get_text(" ", strip=True), href=href)
        if label:
            entries.append(label)
    return _unique(entries)


def _score_toc_candidate(tag: Tag, entries: list[str]) -> int:
    if not entries:
        return 0

    classes = " ".join(str(c).lower() for c in (tag.get("class") or []))
    tag_id = str(tag.get("id") or "").lower()
    text = tag.get_text(" ", strip=True).upper()

    chapter_count = sum(1 for e in entries if e.startswith("CHAPTER "))
    score = chapter_count * 10 + len(entries)

    if "toc" in classes or "toc" in tag_id or "contents" in classes or "contents" in tag_id:
        score += 100
    if "PREFACE" in text:
        score += 20
    if "ILLUSTRATIONS" in text:
        score += 20
    if any(e == "CHAPTER I" for e in entries):
        score += 50
    if chapter_count >= 10:
        score += 50

    return score


def harvest_source_toc_entries(html_fragment: str) -> list[str]:
    """Extract useful entries from the most likely source EPUB TOC block."""
    soup = BeautifulSoup(html_fragment or "", "html.parser")
    candidates: list[tuple[int, list[str]]] = []

    for tag in soup.find_all(["nav", "section", "div", "p", "ol", "ul"]):
        if not isinstance(tag, Tag) or getattr(tag, "attrs", None) is None:
            continue
        entries = _entries_from_tag(tag)
        score = _score_toc_candidate(tag, entries)
        if score:
            candidates.append((score, entries))

    if not candidates:
        entries = _entries_from_tag(soup)
    else:
        candidates.sort(key=lambda item: item[0], reverse=True)
        entries = candidates[0][1]

    entries = _unique(entries)
    return sorted(entries, key=_chapter_sort_key)
