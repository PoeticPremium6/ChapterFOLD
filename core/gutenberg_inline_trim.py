from __future__ import annotations

"""Trim Project Gutenberg boilerplate that appears inside retained content.

This complements the spine-level Gutenberg selector. Some Gutenberg EPUBs put
copyright notices, usage text, START markers, and real content inside the same
HTML/text item. Dropping whole spine items is then too blunt, but keeping the
item preserves boilerplate. These helpers trim inside the first/last retained
section without touching normal fanfic/non-Gutenberg content.
"""

from dataclasses import replace, is_dataclass
import re
from typing import Any, Iterable, Sequence


START_RE = re.compile(
    r"(?is)^.*?\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK[^\r\n]*(?:\r?\n|$)",
)
END_RE = re.compile(
    r"(?is)\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK[^\r\n]*(?:\r?\n|$).*$",
)
GUTENBERG_EBOOK_TITLE_RE = re.compile(r"(?i)\bThe Project Gutenberg eBook of\b")


def contains_gutenberg_marker(text: str) -> bool:
    return "PROJECT GUTENBERG EBOOK" in (text or "").upper()


def trim_gutenberg_inline_boilerplate_text(text: str) -> tuple[str, list[str]]:
    """Return text with inline Gutenberg boilerplate removed plus actions."""

    if not text:
        return text, []

    actions: list[str] = []
    trimmed = text

    if START_RE.search(trimmed):
        trimmed = START_RE.sub("", trimmed, count=1).lstrip()
        actions.append("trimmed_before_start_marker")

    if END_RE.search(trimmed):
        trimmed = END_RE.sub("", trimmed, count=1).rstrip()
        actions.append("trimmed_after_end_marker")

    return trimmed, actions


def _trim_heading_if_boilerplate(heading: Any) -> Any:
    if isinstance(heading, str) and GUTENBERG_EBOOK_TITLE_RE.search(heading):
        return ""
    return heading


def _trim_tuple_section(section: tuple[Any, ...]) -> tuple[Any, ...]:
    if len(section) < 2:
        return section
    parts = list(section)
    parts[0] = _trim_heading_if_boilerplate(parts[0])
    if isinstance(parts[1], str):
        parts[1], _ = trim_gutenberg_inline_boilerplate_text(parts[1])
    return tuple(parts)


def _trim_list_section(section: list[Any]) -> list[Any]:
    if len(section) < 2:
        return section
    parts = list(section)
    parts[0] = _trim_heading_if_boilerplate(parts[0])
    if isinstance(parts[1], str):
        parts[1], _ = trim_gutenberg_inline_boilerplate_text(parts[1])
    return parts


def _trim_dict_section(section: dict[str, Any]) -> dict[str, Any]:
    updated = dict(section)
    for heading_key in ("title", "heading", "name"):
        if heading_key in updated:
            updated[heading_key] = _trim_heading_if_boilerplate(updated[heading_key])
    for text_key in ("text", "content", "html", "body"):
        if isinstance(updated.get(text_key), str):
            updated[text_key], _ = trim_gutenberg_inline_boilerplate_text(updated[text_key])
    return updated


def _trim_object_section(section: Any) -> Any:
    # Prefer immutable dataclass replacement when possible.
    changes: dict[str, Any] = {}
    for heading_attr in ("title", "heading", "name"):
        if hasattr(section, heading_attr):
            value = getattr(section, heading_attr)
            new_value = _trim_heading_if_boilerplate(value)
            if new_value != value:
                changes[heading_attr] = new_value
    for text_attr in ("text", "content", "html", "body"):
        if hasattr(section, text_attr):
            value = getattr(section, text_attr)
            if isinstance(value, str):
                new_value, _ = trim_gutenberg_inline_boilerplate_text(value)
                if new_value != value:
                    changes[text_attr] = new_value
    if not changes:
        return section
    if is_dataclass(section):
        try:
            return replace(section, **changes)
        except Exception:
            pass
    # Last resort: mutate copy-like object in place. This keeps compatibility
    # with simple project-specific section classes.
    for key, value in changes.items():
        try:
            setattr(section, key, value)
        except Exception:
            pass
    return section


def trim_gutenberg_boilerplate_from_sections(sections: Sequence[Any]) -> list[Any]:
    """Trim inline Gutenberg boilerplate from section-like objects.

    Handles the common ChapterFOLD section form `(title, text)`, plus dicts and
    simple objects/dataclasses. If no Gutenberg marker is present, the original
    content is returned unchanged apart from list materialisation.
    """

    trimmed_sections: list[Any] = []
    for section in sections:
        if isinstance(section, tuple):
            trimmed_sections.append(_trim_tuple_section(section))
        elif isinstance(section, list):
            trimmed_sections.append(_trim_list_section(section))
        elif isinstance(section, dict):
            trimmed_sections.append(_trim_dict_section(section))
        else:
            trimmed_sections.append(_trim_object_section(section))
    return trimmed_sections
