from __future__ import annotations

from dataclasses import dataclass
import re

from core.toc_chapter_detection import DetectedChapter, detect_chapters, promote_inline_chapter_headings


TOC_HEADING_RE = re.compile(r"^#{1,6}\s+(?:contents|table of contents)\s*$", re.I)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@dataclass(frozen=True)
class TocEntry:
    level: int
    title: str
    line_number: int = 0
    source: str = "heading"
    slug: str = ""


@dataclass(frozen=True)
class TocPolicyResult:
    markdown: str
    mode: str
    entries: list[TocEntry]
    removed_existing_toc: bool = False
    warning: str = ""


def _entry_from_detected(chapter: DetectedChapter) -> TocEntry:
    return TocEntry(
        level=chapter.level,
        title=chapter.title,
        line_number=chapter.line_number,
        source=chapter.source,
        slug=chapter.slug,
    )


def collect_toc_entries(markdown: str, *, include_inline_chapters: bool = True) -> list[TocEntry]:
    """Collect TOC entries from headings plus inline chapter starts.

    This fixes books such as Moby Dick where not every chapter became a Markdown
    heading during EPUB extraction.
    """
    chapters = detect_chapters(markdown, include_inline=include_inline_chapters)
    return [_entry_from_detected(chapter) for chapter in chapters]


def remove_existing_toc(markdown: str) -> tuple[str, bool]:
    """Remove a clear existing Contents/Table of Contents block.

    Removal starts at a Contents heading and continues until the next Markdown
    heading of the same or higher level. This intentionally avoids trying to
    remove vague prose paragraphs that merely mention contents.
    """
    lines = markdown.splitlines()
    out: list[str] = []
    i = 0
    removed = False

    while i < len(lines):
        line = lines[i]
        toc_heading = TOC_HEADING_RE.match(line.strip())
        if not toc_heading:
            out.append(line)
            i += 1
            continue

        removed = True
        heading_match = HEADING_RE.match(line)
        toc_level = len(heading_match.group(1)) if heading_match else 2
        i += 1

        # Skip the TOC body until the next same/higher-level heading.
        while i < len(lines):
            next_heading = HEADING_RE.match(lines[i])
            if next_heading and len(next_heading.group(1)) <= toc_level:
                break
            i += 1

    cleaned = "\n".join(out).strip() + "\n"
    return cleaned, removed


def build_rebuilt_toc(entries: list[TocEntry], *, linked: bool = False) -> str:
    lines = ["## Contents", ""]
    for entry in entries:
        indent = "  " * max(0, entry.level - 2)
        if linked and entry.slug:
            lines.append(f"{indent}- [{entry.title}](#{entry.slug})")
        else:
            lines.append(f"{indent}- {entry.title}")
    return "\n".join(lines).rstrip() + "\n"


def _insert_toc_after_title_block(markdown: str, toc_block: str) -> str:
    lines = markdown.splitlines()
    insert_at = 0

    # Keep leading title and optional author together before Contents.
    if lines and lines[0].startswith("# "):
        insert_at = 1
        while insert_at < len(lines) and not lines[insert_at].strip():
            insert_at += 1
        if insert_at < len(lines) and re.match(r"^_By .+_$", lines[insert_at].strip()):
            insert_at += 1
        while insert_at < len(lines) and not lines[insert_at].strip():
            insert_at += 1

    before = "\n".join(lines[:insert_at]).rstrip()
    after = "\n".join(lines[insert_at:]).lstrip()
    parts = [part for part in [before, toc_block.strip(), after] if part]
    return "\n\n".join(parts).rstrip() + "\n"


def apply_toc_policy(
    markdown: str,
    *,
    mode: str = "keep",
    include_inline_chapters: bool = True,
    promote_inline_headings: bool = True,
    linked: bool = False,
) -> TocPolicyResult:
    """Apply keep/remove/rebuild TOC policy to Markdown.

    Modes:
      keep    - leave existing TOC alone, but optionally promote inline chapters
      remove  - remove an existing TOC block
      rebuild - remove existing TOC and insert a generated Contents section
    """
    if mode not in {"keep", "remove", "rebuild"}:
        raise ValueError(f"Unknown TOC mode: {mode}")

    working = markdown
    if promote_inline_headings:
        working = promote_inline_chapter_headings(working)

    entries = collect_toc_entries(working, include_inline_chapters=include_inline_chapters)

    if mode == "keep":
        return TocPolicyResult(
            markdown=working,
            mode=mode,
            entries=entries,
            removed_existing_toc=False,
        )

    cleaned, removed = remove_existing_toc(working)

    if mode == "remove":
        return TocPolicyResult(
            markdown=cleaned,
            mode=mode,
            entries=entries,
            removed_existing_toc=removed,
        )

    toc_block = build_rebuilt_toc(entries, linked=linked)
    rebuilt = _insert_toc_after_title_block(cleaned, toc_block)
    warning = "" if entries else "No chapter headings were detected for rebuilt TOC."
    return TocPolicyResult(
        markdown=rebuilt,
        mode=mode,
        entries=entries,
        removed_existing_toc=removed,
        warning=warning,
    )
