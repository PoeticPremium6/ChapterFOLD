"""Gutenberg-aware EPUB spine body selection.

This module is independent from the GUI and conversion engine. It selects likely
book-body HTML spine items from an EPUB inspection report.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import re
from typing import Any, Iterable

SUBSTANTIAL_TEXT_CHARS = 1500
MIN_BODYISH_TEXT_CHARS = 200


@dataclass(frozen=True)
class GutenbergItemDecision:
    index: int
    href: str
    spine_position: int | None
    text_chars: int
    selected: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GutenbergSelectionSummary:
    selected_item_count: int
    dropped_item_count: int
    selected_text_chars: int
    total_text_chars: int
    selected_retention_ratio: float
    decisions: list[GutenbergItemDecision]

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_item_count": self.selected_item_count,
            "dropped_item_count": self.dropped_item_count,
            "selected_text_chars": self.selected_text_chars,
            "total_text_chars": self.total_text_chars,
            "selected_retention_ratio": self.selected_retention_ratio,
            "decisions": [decision.to_dict() for decision in self.decisions],
        }


REAL_FRONT_MATTER_RE = re.compile(
    r"\b(PREFACE|CONTENTS|LIST OF ILLUSTRATIONS|ILLUSTRATIONS|CHAPTER\s+I\.?|Chapter\s+I\.?)\b",
    re.IGNORECASE,
)


def contains_real_front_matter_or_chapter_one(text: str) -> bool:
    """Return True when a front Gutenberg-ish item also contains real book matter."""
    return bool(REAL_FRONT_MATTER_RE.search(text or ""))



def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_bool(value: Any) -> bool:
    return bool(value)


def _text(item: dict[str, Any], key: str) -> str:
    value = item.get(key, "")
    return value if isinstance(value, str) else ""


def _spine_position(item: dict[str, Any]) -> int | None:
    value = item.get("spine_position")
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _sort_items_by_spine(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(item: dict[str, Any]) -> tuple[int, int]:
        spine = _spine_position(item)
        index = _as_int(item.get("index"), 10_000)
        if spine is None or spine <= 0:
            return (10_000 + index, index)
        return (spine, index)

    return sorted(items, key=key)


def _href(item: dict[str, Any]) -> str:
    return _text(item, "href")


def _is_wrap_or_empty(item: dict[str, Any]) -> bool:
    href = _href(item).lower()
    text_chars = _as_int(item.get("text_chars"))
    spine = _spine_position(item)
    if text_chars <= 0:
        return True
    if spine == 0:
        return True
    if href.startswith("wrap") and text_chars <= 10:
        return True
    return False


def _is_end_license_item(item: dict[str, Any]) -> bool:
    if _as_bool(item.get("has_gutenberg_end")):
        return True

    combined = (_text(item, "first_text") + "\n" + _text(item, "last_text")).lower()
    if "end of the project gutenberg ebook" in combined:
        return True
    if "project gutenberg license" in combined and "creating the works from print editions" in combined:
        return True
    return False


def _is_front_boilerplate_or_contents(item: dict[str, Any], position_in_spine: int) -> bool:
    if position_in_spine > 2:
        return False

    text_chars = _as_int(item.get("text_chars"))
    link_count = _as_int(item.get("link_count"))
    has_start = _as_bool(item.get("has_gutenberg_start"))
    has_toc = _as_bool(item.get("has_toc_hint"))
    has_boilerplate = _as_bool(item.get("has_boilerplate_hint"))
    combined_text = _text(item, "first_text") + "\n" + _text(item, "last_text")
    combined = combined_text.lower()

    # Issue #17D:
    # Some illustrated Gutenberg EPUBs put the Gutenberg header/title matter,
    # Preface, List of Illustrations/Contents, and Chapter I in the same first
    # spine file. Do not drop that file wholesale when it is substantial.
    #
    # Keep the old behaviour for tiny pure boilerplate/contents files.
    if text_chars >= 10_000 and contains_real_front_matter_or_chapter_one(combined_text):
        return False

    if has_start and (has_boilerplate or has_toc):
        return True
    if "the project gutenberg ebook of" in combined and text_chars < 10_000:
        return True
    if has_toc and link_count >= 10 and text_chars < 8_000:
        return True
    return False


def _is_pure_toc_item(item: dict[str, Any]) -> bool:
    text_chars = _as_int(item.get("text_chars"))
    link_count = _as_int(item.get("link_count"))
    paragraph_count = _as_int(item.get("paragraph_count"))
    has_toc = _as_bool(item.get("has_toc_hint"))

    if not has_toc:
        return False
    if text_chars >= 10_000:
        return False
    if link_count >= 10 and paragraph_count <= 25:
        return True
    return False


def _looks_like_body_item(item: dict[str, Any]) -> bool:
    text_chars = _as_int(item.get("text_chars"))
    if text_chars >= SUBSTANTIAL_TEXT_CHARS:
        return True
    if item.get("chapter_heading_candidates"):
        return True
    if text_chars >= MIN_BODYISH_TEXT_CHARS:
        return True
    return False


def decide_gutenberg_body_items(report_or_items: dict[str, Any] | list[dict[str, Any]]) -> GutenbergSelectionSummary:
    if isinstance(report_or_items, dict):
        raw_items = list(report_or_items.get("html_items", []) or [])
        total_text_chars = _as_int(report_or_items.get("total_text_chars"))
        if total_text_chars <= 0:
            total_text_chars = sum(_as_int(item.get("text_chars")) for item in raw_items)
    else:
        raw_items = list(report_or_items)
        total_text_chars = sum(_as_int(item.get("text_chars")) for item in raw_items)

    spine_items = _sort_items_by_spine(raw_items)
    decisions: list[GutenbergItemDecision] = []

    for pos, item in enumerate(spine_items):
        index = _as_int(item.get("index"), len(decisions))
        href = _href(item)
        spine = _spine_position(item)
        text_chars = _as_int(item.get("text_chars"))

        if _is_wrap_or_empty(item):
            selected, reason = False, "empty_or_non_content_spine_item"
        elif _is_end_license_item(item):
            selected, reason = False, "gutenberg_end_license"
        elif _is_front_boilerplate_or_contents(item, pos):
            selected, reason = False, "front_gutenberg_notice_or_contents"
        elif _is_pure_toc_item(item):
            selected, reason = False, "short_link_heavy_contents"
        elif _looks_like_body_item(item):
            selected, reason = True, "body_spine_item"
        else:
            selected, reason = False, "too_short_for_body"

        decisions.append(
            GutenbergItemDecision(
                index=index,
                href=href,
                spine_position=spine,
                text_chars=text_chars,
                selected=selected,
                reason=reason,
            )
        )

    selected_text_chars = sum(decision.text_chars for decision in decisions if decision.selected)
    selected_item_count = sum(1 for decision in decisions if decision.selected)
    dropped_item_count = len(decisions) - selected_item_count
    ratio = selected_text_chars / total_text_chars if total_text_chars else 0.0

    return GutenbergSelectionSummary(
        selected_item_count=selected_item_count,
        dropped_item_count=dropped_item_count,
        selected_text_chars=selected_text_chars,
        total_text_chars=total_text_chars,
        selected_retention_ratio=round(ratio, 4),
        decisions=decisions,
    )


def apply_gutenberg_selection_to_report(report: dict[str, Any]) -> dict[str, Any]:
    updated = dict(report)
    selection = decide_gutenberg_body_items(updated)

    updated["spine_selected_body_item_count"] = selection.selected_item_count
    updated["spine_dropped_item_count"] = selection.dropped_item_count
    updated["spine_selected_body_text_chars"] = selection.selected_text_chars
    updated["spine_selected_body_retention_ratio"] = selection.selected_retention_ratio
    updated["gutenberg_body_selection"] = selection.to_dict()

    # Keep legacy inspector fields, but make them reflect the spine selector.
    updated["estimated_body_text_chars_between_gutenberg_markers"] = selection.selected_text_chars
    updated["estimated_body_retention_ratio"] = selection.selected_retention_ratio

    risk_flags = list(updated.get("risk_flags", []) or [])
    risk_flags = [
        flag for flag in risk_flags
        if flag not in {"estimated_body_text_very_short", "estimated_body_less_than_25_percent_of_total"}
    ]

    if selection.selected_text_chars < 10_000:
        risk_flags.append("spine_selected_body_text_very_short")
    if selection.selected_retention_ratio < 0.25:
        risk_flags.append("spine_selected_body_less_than_25_percent_of_total")
    if selection.selected_item_count == 0:
        risk_flags.append("no_spine_body_items_selected")

    updated["risk_flags"] = sorted(set(risk_flags))
    return updated
