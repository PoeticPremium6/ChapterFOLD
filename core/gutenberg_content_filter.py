"""Gutenberg-aware content filtering for the conversion path.

This module bridges the Patch 009 inspector/selector work into the real EPUB
loading path. It is intentionally conservative:

- It only applies the spine selector when Project Gutenberg markers/boilerplate
  are detected.
- It falls back to keeping all records if selection would retain too little.
- It reports what was kept/dropped so the GUI/CLI/API can surface warnings.
"""

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

MIN_SAFE_GUTENBERG_RETENTION_RATIO = 0.25


def _norm_text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _clean_text_for_detection(html_fragment: str) -> str:
    soup = BeautifulSoup(html_fragment or "", "html.parser")
    for bad in soup(["script", "style"]):
        bad.decompose()
    return soup.get_text("\n", strip=True)


def _chapter_candidates_from_soup(soup: BeautifulSoup) -> list[str]:
    candidates: list[str] = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
        text = tag.get_text(" ", strip=True)
        if not text:
            continue
        upper = text.upper()
        if upper.startswith(("CHAPTER", "PART", "BOOK ", "VOLUME ", "THE PREFACE")):
            candidates.append(text)
    return candidates[:20]


def build_epub_html_record(
    *,
    index: int,
    href: str,
    spine_position: int | None,
    heading: str,
    body_html: str,
) -> dict[str, Any]:
    """Build a selector-compatible record from a loaded EPUB HTML body."""

    soup = BeautifulSoup(body_html or "", "html.parser")
    text = soup.get_text("\n", strip=True)
    lower = text.lower()
    link_count = len(soup.find_all("a"))
    paragraph_count = len(soup.find_all(["p", "blockquote", "li"]))
    heading_count = len(soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]))

    has_start = "start of the project gutenberg ebook" in lower or "start of this project gutenberg ebook" in lower
    has_end = "end of the project gutenberg ebook" in lower or "end of this project gutenberg ebook" in lower
    has_boilerplate = (
        "project gutenberg" in lower
        or "gutenberg.org" in lower
        or "project gutenberg license" in lower
    )
    has_toc = (
        "contents" in lower[:5000]
        or "table of contents" in lower[:5000]
        or (link_count >= 10 and paragraph_count <= 30)
    )

    first_text = text[:900]
    last_text = text[-900:] if len(text) > 900 else text

    return {
        "index": index,
        "href": href,
        "spine_position": spine_position,
        "heading": heading or "",
        "body_html": body_html or "",
        "text_chars": len(text),
        "paragraph_count": paragraph_count,
        "heading_count": heading_count,
        "link_count": link_count,
        "has_gutenberg_start": has_start,
        "has_gutenberg_end": has_end,
        "has_toc_hint": has_toc,
        "has_boilerplate_hint": has_boilerplate,
        "chapter_heading_candidates": _chapter_candidates_from_soup(soup),
        "first_text": first_text,
        "last_text": last_text,
    }


def _gutenberg_detected(records: list[dict[str, Any]]) -> bool:
    for record in records:
        if record.get("has_gutenberg_start") or record.get("has_gutenberg_end"):
            return True
        if record.get("has_boilerplate_hint"):
            text = (_norm_text(record.get("first_text")) + "\n" + _norm_text(record.get("last_text"))).lower()
            if "project gutenberg" in text:
                return True
    return False


def _fallback_report(records: list[dict[str, Any]], *, warning: str | None = None) -> dict[str, Any]:
    total = sum(_safe_int(record.get("text_chars")) for record in records)
    warnings = [warning] if warning else []
    return {
        "gutenberg_detected": False,
        "selection_applied": False,
        "total_html_items": len(records),
        "selected_html_items": len(records),
        "dropped_html_items": 0,
        "total_text_chars": total,
        "selected_text_chars": total,
        "selected_retention_ratio": 1.0 if total else 0.0,
        "selected_hrefs": [_norm_text(record.get("href")) for record in records],
        "dropped_hrefs": [],
        "drop_reasons_by_href": {},
        "risk_flags": [],
        "warnings": warnings,
    }


def apply_gutenberg_filter_to_records(
    records: list[dict[str, Any]],
    *,
    min_retention_ratio: float = MIN_SAFE_GUTENBERG_RETENTION_RATIO,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return selected records plus a retention report.

    Non-Gutenberg EPUBs are returned unchanged.
    """

    records = list(records)
    if not records:
        return records, _fallback_report(records)

    if not _gutenberg_detected(records):
        return records, _fallback_report(records)

    try:
        from core.gutenberg_selector import decide_gutenberg_body_items
    except Exception as exc:  # pragma: no cover - defensive for partial installs
        report = _fallback_report(records, warning=f"Could not import Gutenberg selector; kept all items: {exc}")
        report["gutenberg_detected"] = True
        return records, report

    total = sum(_safe_int(record.get("text_chars")) for record in records)
    selection = decide_gutenberg_body_items({"html_items": records, "total_text_chars": total})

    selected_hrefs = {decision.href for decision in selection.decisions if decision.selected}
    drop_reasons = {
        decision.href: decision.reason
        for decision in selection.decisions
        if not decision.selected
    }
    selected = [record for record in records if _norm_text(record.get("href")) in selected_hrefs]

    warnings: list[str] = []
    risk_flags: list[str] = []
    ratio = selection.selected_retention_ratio

    if selection.selected_item_count == 0:
        risk_flags.append("no_gutenberg_body_items_selected")
    if selection.selected_text_chars < 10_000:
        risk_flags.append("gutenberg_selected_body_text_very_short")
    if ratio < min_retention_ratio:
        risk_flags.append("gutenberg_selected_body_less_than_minimum_ratio")
        warnings.append(
            "Gutenberg selector retained too little text; fell back to keeping all EPUB spine items."
        )
        selected = records
        selected_hrefs = {_norm_text(record.get("href")) for record in records}
        drop_reasons = {}
        ratio = 1.0 if total else 0.0

    report = {
        "gutenberg_detected": True,
        "selection_applied": not warnings,
        "total_html_items": len(records),
        "selected_html_items": len(selected),
        "dropped_html_items": len(records) - len(selected),
        "total_text_chars": total,
        "selected_text_chars": sum(_safe_int(record.get("text_chars")) for record in selected),
        "selected_retention_ratio": round(ratio, 4),
        "selected_hrefs": [_norm_text(record.get("href")) for record in selected],
        "dropped_hrefs": [href for href in [_norm_text(record.get("href")) for record in records] if href not in selected_hrefs],
        "drop_reasons_by_href": drop_reasons,
        "risk_flags": sorted(set(risk_flags)),
        "warnings": warnings,
    }
    return selected, report


def retention_summary_line(report: dict[str, Any]) -> str:
    if not report or not report.get("gutenberg_detected"):
        return "Gutenberg selector: not detected"
    return (
        "Gutenberg selector: kept "
        f"{report.get('selected_html_items', 0)} / {report.get('total_html_items', 0)} HTML items, "
        f"{report.get('selected_text_chars', 0)} / {report.get('total_text_chars', 0)} chars "
        f"({report.get('selected_retention_ratio', 0):.4f})"
    )
