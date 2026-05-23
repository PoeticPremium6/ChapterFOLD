from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable, List, Sequence

SECTION_MARKER_RE = re.compile(r"^<!--\s*chapterfold-section:\s*(.*?)\s*-->\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
AUTHOR_RE = re.compile(r"^_By\s+(.+?)_\s*$", re.MULTILINE)


def strip_markdown_title_block(markdown: str) -> str:
    """Remove a leading ChapterFOLD-style title/author block before combining books."""
    lines = markdown.splitlines()
    i = 0

    # Drop leading blank lines.
    while i < len(lines) and not lines[i].strip():
        i += 1

    # Drop leading H1 title.
    if i < len(lines) and lines[i].lstrip().startswith("# "):
        i += 1

        # Drop blank lines after title.
        while i < len(lines) and not lines[i].strip():
            i += 1

        # Drop optional "_By Author_" line.
        if i < len(lines) and re.match(r"^_By .+_$", lines[i].strip()):
            i += 1

        # Drop blank lines after author.
        while i < len(lines) and not lines[i].strip():
            i += 1

    return "\n".join(lines[i:]).strip() + "\n"


@dataclass(frozen=True)
class MarkdownSection:
    title: str
    body: str

    @property
    def body_chars(self) -> int:
        return len(self.body)


def slugify_title(title: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "-", title.strip().lower()).strip("-")
    return text or "section"


def extract_title(markdown: str, fallback: str = "Untitled") -> str:
    match = TITLE_RE.search(markdown)
    if match:
        return match.group(1).strip()
    return fallback


def extract_author(markdown: str, fallback: str = "") -> str:
    match = AUTHOR_RE.search(markdown)
    if match:
        return match.group(1).strip()
    return fallback


def strip_yaml_fence_noise(markdown: str) -> str:
    # Keep this deliberately conservative. Some users may edit Markdown manually.
    return markdown.replace("\ufeff", "").strip()


def add_section_markers(markdown: str) -> str:
    """Insert ChapterFOLD section comments before level-2+ headings.

    The title line (# Book Title) and author line are left untouched. Existing
    markers are preserved, making the function idempotent enough for repeated
    use in the pre-edit workflow.
    """
    markdown = strip_yaml_fence_noise(markdown)
    if "chapterfold-section:" in markdown:
        return markdown if markdown.endswith("\n") else markdown + "\n"

    lines = markdown.splitlines()
    out: list[str] = []
    for line in lines:
        heading = HEADING_RE.match(line)
        if heading and len(heading.group(1)) >= 2:
            title = heading.group(2).strip()
            if out and out[-1].strip():
                out.append("")
            out.append(f"<!-- chapterfold-section: {title} -->")
        out.append(line)
    return "\n".join(out).rstrip() + "\n"


def split_markdown_sections(markdown: str) -> list[MarkdownSection]:
    """Split Markdown into editable sections.

    Preferred split points are explicit ChapterFOLD section markers. If there
    are no markers, split on level-2+ headings. Any title/author/frontmatter
    before the first section becomes a Frontmatter section.
    """
    markdown = strip_yaml_fence_noise(markdown)
    lines = markdown.splitlines()
    sections: list[MarkdownSection] = []
    current_title = "Frontmatter"
    current_lines: list[str] = []
    saw_section = False

    def flush() -> None:
        nonlocal current_lines, current_title
        body = "\n".join(current_lines).strip()
        if body:
            sections.append(MarkdownSection(current_title.strip() or "Section", body + "\n"))
        current_lines = []

    for line in lines:
        marker = SECTION_MARKER_RE.match(line)
        if marker:
            flush()
            current_title = marker.group(1).strip() or "Section"
            saw_section = True
            continue

        heading = HEADING_RE.match(line)
        if not saw_section and heading and len(heading.group(1)) >= 2:
            flush()
            current_title = heading.group(2).strip() or "Section"
            saw_section = True

        current_lines.append(line)

    flush()
    return sections


def render_section_manifest(markdown: str) -> str:
    sections = split_markdown_sections(add_section_markers(markdown))
    lines = ["# ChapterFOLD section manifest", "", "| # | Title | Chars |", "|---:|---|---:|"]
    for idx, section in enumerate(sections, start=1):
        safe_title = section.title.replace("|", "\\|")
        lines.append(f"| {idx} | {safe_title} | {section.body_chars} |")
    return "\n".join(lines) + "\n"


def combine_markdown_books(
    markdown_documents: Sequence[str],
    *,
    title: str | None = None,
    author: str | None = None,
    include_source_titles: bool = False,
) -> str:
    """Combine multiple Editable.md documents into one clean Markdown book."""
    docs = [strip_yaml_fence_noise(doc) for doc in markdown_documents if strip_yaml_fence_noise(doc)]
    if not docs:
        raise ValueError("No Markdown documents were provided.")

    combined_title = title or "Combined ChapterFOLD Book"
    combined_author = author or "Various Authors"
    out: list[str] = [f"# {combined_title}", "", f"_By {combined_author}_", ""]

    for idx, doc in enumerate(docs, start=1):
        source_title = extract_title(doc, fallback=f"Book {idx}")
        source_author = extract_author(doc, fallback="")
        sections = split_markdown_sections(add_section_markers(doc))

        if include_source_titles:
            heading = source_title
            if source_author:
                heading += f" — {source_author}"
            out.extend([f"## {heading}", ""])

        # Skip duplicated top-level title/author frontmatter sections where possible.
        for section in sections:
            body = section.body.strip()
            if not body:
                continue
            if section.title == "Frontmatter":
                body_lines = [ln for ln in body.splitlines() if not ln.startswith("# ") and not ln.startswith("_By ")]
                body = "\n".join(body_lines).strip()
                if not body:
                    continue
            out.append(f"<!-- chapterfold-section: {section.title} -->")
            out.append(body)
            out.append("")

    return "\n".join(out).rstrip() + "\n"


def read_markdown_files(paths: Iterable[Path]) -> list[str]:
    docs: list[str] = []
    for path in paths:
        docs.append(Path(path).read_text(encoding="utf-8"))
    return docs
