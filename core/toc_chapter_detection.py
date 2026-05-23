from __future__ import annotations

from dataclasses import dataclass
import re


HEADING_RE = re.compile(r"^(#{2,6})\s+(.+?)\s*$")
CHAPTER_LINE_RE = re.compile(
    r"^\s*((?:CHAPTER|Chapter)\s+(?:\d+|[IVXLCDM]+|[A-Za-z]+)\.?\s+.+?|(?:EPILOGUE|Epilogue))\s*$"
)
INLINE_CHAPTER_RE = re.compile(
    r"(?<!#)\b((?:CHAPTER|Chapter)\s+(?:\d+|[IVXLCDM]+)\.?\s+[A-Z][^\n]{1,120}?\.)(?=\s+[A-Z“\"'])"
)


@dataclass(frozen=True)
class DetectedChapter:
    title: str
    line_number: int = 0
    source: str = "heading"
    slug: str = ""
    level: int = 2


@dataclass(frozen=True)
class ChapterPromotionResult:
    markdown: str
    promoted_count: int = 0


def slugify_title(title: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "-", title.strip().lower()).strip("-")
    return text or "section"


def normalise_chapter_title(title: str) -> str:
    title = re.sub(r"\s+", " ", title.strip())
    return title.strip("# ").strip()


def _is_toc_or_noise(title: str) -> bool:
    lowered = title.strip().lower()
    return lowered in {"contents", "table of contents", "toc"}


def _section_marker(title: str) -> str:
    return f"<!-- chapterfold-section: {title} -->"


def promote_inline_chapter_headings(markdown: str) -> str:
    return promote_detected_chapter_headings(markdown).markdown


def promote_detected_chapter_headings(markdown: str) -> ChapterPromotionResult:
    """Promote bare/inline chapter labels into Markdown H2 headings.

    If an exported section already has a Markdown heading and the first body
    line repeats the same chapter title, skip the repeated plain-text line.
    """
    out: list[str] = []
    promoted = 0
    last_heading_title = ""

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()

        if line.startswith("<!-- chapterfold-section:"):
            out.append(line)
            continue

        heading_match = HEADING_RE.match(line.strip())
        if heading_match:
            last_heading_title = normalise_chapter_title(heading_match.group(2))
            out.append(line)
            continue

        standalone = CHAPTER_LINE_RE.match(line)
        if standalone and len(line) <= 180:
            title = normalise_chapter_title(standalone.group(1))

            # Avoid:
            #   ## CHAPTER 1. Title
            #   CHAPTER 1. Title
            # becoming two identical headings.
            if last_heading_title and title.lower() == last_heading_title.lower():
                continue

            out.append(_section_marker(title))
            out.append(f"## {title}")
            last_heading_title = title
            promoted += 1
            continue

        def inline_repl(match: re.Match[str]) -> str:
            nonlocal promoted, last_heading_title
            title = normalise_chapter_title(match.group(1))
            if last_heading_title and title.lower() == last_heading_title.lower():
                return ""
            promoted += 1
            last_heading_title = title
            return f"\n\n{_section_marker(title)}\n## {title}\n\n"

        out.append(INLINE_CHAPTER_RE.sub(inline_repl, line))

    text = "\n".join(out)
    text = re.sub(r"\n{4,}", "\n\n\n", text).rstrip() + "\n"
    return ChapterPromotionResult(markdown=text, promoted_count=promoted)


def detect_chapters(markdown: str, *, include_inline: bool = True) -> list[DetectedChapter]:
    working = promote_inline_chapter_headings(markdown) if include_inline else markdown
    chapters: list[DetectedChapter] = []
    seen: set[str] = set()

    for idx, line in enumerate(working.splitlines()):
        match = HEADING_RE.match(line.strip())
        if not match:
            continue

        level = len(match.group(1))
        title = normalise_chapter_title(match.group(2))
        if not title or _is_toc_or_noise(title):
            continue

        key = title.lower()
        if key in seen:
            continue

        seen.add(key)
        source = "chapter-detection" if CHAPTER_LINE_RE.match(title) or title.lower() == "epilogue" else "heading"
        chapters.append(
            DetectedChapter(
                title=title,
                line_number=idx + 1,
                source=source,
                slug=slugify_title(title),
                level=level,
            )
        )

    return chapters


def collect_detected_chapter_titles(markdown: str) -> list[str]:
    return [chapter.title for chapter in detect_chapters(markdown, include_inline=True)]


__all__ = [
    "ChapterPromotionResult",
    "DetectedChapter",
    "collect_detected_chapter_titles",
    "detect_chapters",
    "normalise_chapter_title",
    "promote_detected_chapter_headings",
    "promote_inline_chapter_headings",
    "slugify_title",
]
