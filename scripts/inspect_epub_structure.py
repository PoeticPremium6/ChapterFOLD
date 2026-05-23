#!/usr/bin/env python3
"""Inspect a Gutenberg EPUB and report spine/body selection details."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bs4 import BeautifulSoup
from ebooklib import ITEM_DOCUMENT
from ebooklib import epub

try:
    from core.gutenberg_selector import select_gutenberg_body_items
except Exception:  # pragma: no cover - fallback for partial local states
    select_gutenberg_body_items = None  # type: ignore

START_RE = re.compile(r"\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK", re.I)
END_RE = re.compile(r"\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK", re.I)
TOC_RE = re.compile(r"\b(contents?|table of contents)\b", re.I)
BOILERPLATE_RE = re.compile(r"project gutenberg|gutenberg\.org|project gutenberg license", re.I)
CHAPTER_RE = re.compile(
    r"\b(?:chapter|book|part)\s+(?:[ivxlcdm]+|\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty)\b[\s\S]{0,120}",
    re.I,
)


def _clean_text(value: str) -> str:
    value = re.sub(r"\r\n?", "\n", value)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def _snippet(value: str, limit: int = 350) -> str:
    value = _clean_text(value)
    if len(value) <= limit:
        return value
    return value[:limit].rstrip() + " …"


def _metadata_first(book: epub.EpubBook, name: str) -> str:
    values = book.get_metadata("DC", name)
    if not values:
        return ""
    first = values[0]
    if isinstance(first, tuple) and first:
        return str(first[0])
    return str(first)


def _spine_positions(book: epub.EpubBook) -> dict[str, int]:
    positions: dict[str, int] = {}
    for pos, spine_entry in enumerate(book.spine):
        item_id = spine_entry[0] if isinstance(spine_entry, (tuple, list)) else spine_entry
        try:
            item = book.get_item_with_id(item_id)
        except Exception:
            item = None
        if item is not None:
            positions[item.get_name()] = pos
    return positions


def _chapter_candidates(soup: BeautifulSoup, text: str) -> list[str]:
    candidates: list[str] = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
        tag_text = _clean_text(tag.get_text("\n"))
        if tag_text and CHAPTER_RE.search(tag_text):
            candidates.append(tag_text[:160])
    if not candidates:
        for match in CHAPTER_RE.finditer(text):
            candidate = _clean_text(match.group(0))
            if candidate:
                candidates.append(candidate[:160])
            if len(candidates) >= 8:
                break
    return candidates[:12]


def _basic_select_items(html_items: list[dict[str, Any]]) -> tuple[list[str], dict[str, str]]:
    selected: list[str] = []
    drop_reasons: dict[str, str] = {}
    spine_items = sorted(html_items, key=lambda item: item.get("spine_position", 10**9))
    max_spine = max((int(item.get("spine_position") or 0) for item in spine_items), default=0)

    for item in spine_items:
        href = str(item.get("href", ""))
        text_chars = int(item.get("text_chars") or 0)
        link_count = int(item.get("link_count") or 0)
        spine_position = int(item.get("spine_position") or 0)
        has_start = bool(item.get("has_gutenberg_start"))
        has_end = bool(item.get("has_gutenberg_end"))
        has_toc = bool(item.get("has_toc_hint"))
        has_boilerplate = bool(item.get("has_boilerplate_hint"))
        has_chapter = bool(item.get("chapter_heading_candidates"))

        if not href or href.startswith("wrap") or text_chars <= 0:
            drop_reasons[href] = "empty_or_wrapper"
            continue
        if has_end and spine_position >= max_spine - 1:
            drop_reasons[href] = "gutenberg_end_license"
            continue
        if has_start and has_boilerplate and has_toc and spine_position <= 2:
            drop_reasons[href] = "gutenberg_frontmatter_toc"
            continue
        if has_toc and text_chars < 3500 and link_count >= 10 and not has_chapter:
            drop_reasons[href] = "short_link_heavy_toc"
            continue
        if text_chars >= 1500 or has_chapter:
            selected.append(href)
        else:
            drop_reasons[href] = "too_short_non_chapter"
    return selected, drop_reasons


def _selector_result(html_items: list[dict[str, Any]]) -> tuple[list[str], dict[str, str]]:
    if select_gutenberg_body_items is None:
        return _basic_select_items(html_items)
    try:
        result = select_gutenberg_body_items(html_items)  # type: ignore[misc]
        if isinstance(result, tuple) and len(result) == 2:
            selected, reasons = result
            selected_hrefs = [str(x.get("href", x)) if isinstance(x, dict) else str(x) for x in selected]
            return selected_hrefs, {str(k): str(v) for k, v in dict(reasons).items()}
        if isinstance(result, list):
            selected_hrefs = [str(x.get("href", x)) if isinstance(x, dict) else str(x) for x in result]
            all_hrefs = {str(item.get("href", "")) for item in html_items}
            return selected_hrefs, {href: "not_selected" for href in all_hrefs - set(selected_hrefs)}
    except Exception:
        pass
    return _basic_select_items(html_items)


def inspect_epub(epub_path: Path | str) -> dict[str, Any]:
    epub_path = Path(epub_path)
    book = epub.read_epub(str(epub_path))
    spine_positions = _spine_positions(book)

    html_items: list[dict[str, Any]] = []
    combined_parts: list[str] = []
    for index, item in enumerate(book.get_items_of_type(ITEM_DOCUMENT)):
        href = item.get_name()
        raw = item.get_content()
        try:
            html = raw.decode("utf-8", errors="replace")
        except AttributeError:
            html = str(raw)
        soup = BeautifulSoup(html, "html.parser")
        text = _clean_text(soup.get_text("\n"))
        combined_parts.append(text)
        links = soup.find_all("a")
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        paragraphs = soup.find_all("p")
        candidates = _chapter_candidates(soup, text)
        html_items.append(
            {
                "index": index,
                "href": href,
                "media_type": item.media_type,
                "spine_position": spine_positions.get(href, 10**9),
                "title": _clean_text(soup.title.get_text(" ")) if soup.title else "",
                "text_chars": len(text),
                "paragraph_count": len(paragraphs),
                "heading_count": len(headings),
                "link_count": len(links),
                "has_gutenberg_start": bool(START_RE.search(text)),
                "has_gutenberg_end": bool(END_RE.search(text)),
                "has_toc_hint": bool(TOC_RE.search(text)) or len(links) >= 20,
                "has_boilerplate_hint": bool(BOILERPLATE_RE.search(text)),
                "chapter_heading_candidates": candidates,
                "first_text": _snippet(text),
                "last_text": _snippet(text[-700:]),
            }
        )

    html_items.sort(key=lambda item: (item.get("spine_position", 10**9), item.get("index", 0)))
    total_text_chars = sum(int(item.get("text_chars") or 0) for item in html_items)

    combined = "\n\n".join(combined_parts)
    start_match = START_RE.search(combined)
    end_match = END_RE.search(combined)

    selected_hrefs, drop_reasons = _selector_result(html_items)
    selected_set = set(selected_hrefs)
    selected_body_text_chars = sum(int(item.get("text_chars") or 0) for item in html_items if item.get("href") in selected_set)
    selected_ratio = selected_body_text_chars / total_text_chars if total_text_chars else 0.0

    risk_flags: list[str] = []
    if selected_body_text_chars < 5000:
        risk_flags.append("selected_body_text_very_short")
    if total_text_chars and selected_ratio < 0.25:
        risk_flags.append("selected_body_less_than_25_percent_of_total")
    if total_text_chars and selected_ratio > 0.98:
        risk_flags.append("selected_body_may_include_boilerplate")

    return {
        "schema_version": 2,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "epub_path": str(epub_path),
        "filename": epub_path.name,
        "metadata_title": _metadata_first(book, "title"),
        "file_size_bytes": epub_path.stat().st_size if epub_path.exists() else None,
        "zip_file_count": None,
        "spine_hrefs": [href for href, _linear in [(book.get_item_with_id(e[0]).get_name(), e[1] if len(e) > 1 else None) for e in book.spine if book.get_item_with_id(e[0]) is not None]],
        "html_item_count": len(html_items),
        "total_text_chars": total_text_chars,
        "selected_body_text_chars": selected_body_text_chars,
        "selected_body_retention_ratio": round(selected_ratio, 4),
        "selected_body_hrefs": selected_hrefs,
        "drop_reasons_by_href": drop_reasons,
        "gutenberg_start": {
            "char_index": start_match.start(),
            "snippet": _snippet(combined[start_match.start(): start_match.start() + 500]),
        } if start_match else None,
        "gutenberg_end": {
            "char_index": end_match.start(),
            "snippet": _snippet(combined[end_match.start(): end_match.start() + 500]),
        } if end_match else None,
        "risk_flags": risk_flags,
        "html_items": html_items,
    }


def markdown_from_report(report: dict[str, Any]) -> str:
    selected = set(report.get("selected_body_hrefs", []))
    reasons = report.get("drop_reasons_by_href", {}) or {}
    lines = [
        f"# Gutenberg EPUB inspection: {report.get('filename', '')}",
        "",
        f"- Metadata title: {report.get('metadata_title', '')}",
        f"- HTML items: {report.get('html_item_count', 0)}",
        f"- Total text chars: {report.get('total_text_chars', 0)}",
        f"- Selected body chars: {report.get('selected_body_text_chars', 0)}",
        f"- Selected body retention ratio: {report.get('selected_body_retention_ratio', 0)}",
        f"- Risk flags: {', '.join(report.get('risk_flags', [])) or 'none'}",
        "",
        "## HTML item overview",
        "",
        "| # | Spine | Text chars | Headings | Paragraphs | TOC? | Start? | End? | Selected? | Drop reason | Href |",
        "|---:|---:|---:|---:|---:|:---:|:---:|:---:|:---:|---|---|",
    ]
    for item in report.get("html_items", []):
        href = item.get("href", "")
        lines.append(
            f"| {item.get('index', '')} | {item.get('spine_position', '')} | {item.get('text_chars', 0)} | "
            f"{item.get('heading_count', 0)} | {item.get('paragraph_count', 0)} | "
            f"{'Y' if item.get('has_toc_hint') else ''} | {'Y' if item.get('has_gutenberg_start') else ''} | "
            f"{'Y' if item.get('has_gutenberg_end') else ''} | {'Y' if href in selected else ''} | "
            f"{reasons.get(href, '')} | `{href}` |"
        )
    lines.append("")
    lines.append("## Chapter heading candidates")
    for item in report.get("html_items", []):
        candidates = item.get("chapter_heading_candidates") or []
        if not candidates:
            continue
        lines.append("")
        lines.append(f"### {item.get('href', '')}")
        for candidate in candidates:
            lines.append(f"- {_clean_text(str(candidate))}")
    lines.append("")
    return "\n".join(lines)


def write_report(epub_path: Path | str, output_json: Path | str, markdown: Path | str | None = None) -> dict[str, Any]:
    output_json = Path(output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    report = inspect_epub(Path(epub_path))
    output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if markdown is not None:
        md_path = Path(markdown)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown_from_report(report), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect a Gutenberg EPUB structure and body selection.")
    parser.add_argument("input_epub")
    parser.add_argument("output_json")
    parser.add_argument("--markdown", help="Optional path for a Markdown summary report.")
    args = parser.parse_args(argv)

    report = write_report(args.input_epub, args.output_json, args.markdown)
    print(f"Wrote {args.output_json}")
    if args.markdown:
        print(f"Wrote {args.markdown}")
    print(
        "Selected body chars:",
        report.get("selected_body_text_chars"),
        "ratio:",
        report.get("selected_body_retention_ratio"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
