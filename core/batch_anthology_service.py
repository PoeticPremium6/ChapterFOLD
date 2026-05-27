from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.epub_service import (
    CleanupSettings,
    build_clean_text_sections,
    export_epub_image_assets,
    load_epub_content,
)


@dataclass
class AnthologyInputRecord:
    input_path: Path
    title: str
    author: str
    section_count: int
    char_count: int
    image_marker_count: int = 0
    image_asset_count: int = 0
    image_asset_files: list[str] = field(default_factory=list)


@dataclass
class AnthologyBuildResult:
    success: bool
    title: str
    author: str
    output_dir: Path
    markdown_path: Path
    manifest_json_path: Path
    input_records: list[AnthologyInputRecord] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    externalized_image_files: list[str] = field(default_factory=list)


def _safe_filename(value: str) -> str:
    value = (value or "Anthology").strip()
    for char in '<>:"/\\|?*':
        value = value.replace(char, "-")
    return " ".join(value.split())


def _clean_heading(value: str | None, fallback: str) -> str:
    value = " ".join((value or "").strip().split())
    return value or fallback


IMAGE_MARKER_PATTERN = re.compile(r"\[\[CHAPTERFOLD_IMAGE:[A-Za-z0-9_\-=]+\]\]")


def _extract_image_markers(value: str) -> list[str]:
    return IMAGE_MARKER_PATTERN.findall(value or "")


def _prepend_missing_image_markers(cleaned: str, raw_markers: list[str]) -> str:
    if not raw_markers:
        return cleaned

    missing = [marker for marker in raw_markers if marker not in cleaned]
    if not missing:
        return cleaned

    if cleaned.strip():
        return "\n\n".join(missing) + "\n\n" + cleaned.strip()

    return "\n\n".join(missing)


def _decode_image_marker_payload(marker: str) -> dict[str, Any]:
    prefix = "[[CHAPTERFOLD_IMAGE:"
    suffix = "]]"
    if not marker.startswith(prefix) or not marker.endswith(suffix):
        return {}

    encoded = marker[len(prefix):-len(suffix)]
    padding = "=" * (-len(encoded) % 4)

    try:
        raw = base64.urlsafe_b64decode((encoded + padding).encode("ascii"))
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        return {}

    return data if isinstance(data, dict) else {}


def _safe_asset_name(value: str, fallback: str) -> str:
    name = Path(value or fallback).name.strip() or fallback
    for char in '<>:"/\\|?*':
        name = name.replace(char, "-")
    return " ".join(name.split())


def _extension_from_data_uri(src: str) -> str:
    if src.startswith("data:image/jpeg") or src.startswith("data:image/jpg"):
        return ".jpg"
    if src.startswith("data:image/png"):
        return ".png"
    if src.startswith("data:image/gif"):
        return ".gif"
    if src.startswith("data:image/webp"):
        return ".webp"
    if src.startswith("data:image/svg"):
        return ".svg"
    return ".img"


def _write_data_uri_image(src: str, output_path: Path) -> bool:
    if not src.startswith("data:image/") or "," not in src:
        return False

    _, encoded = src.split(",", 1)
    try:
        payload = base64.b64decode(encoded)
    except Exception:
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(payload)
    return True


def externalize_anthology_image_markers(
    markdown: str,
    output_dir: str | Path,
    *,
    anthology_slug: str,
) -> tuple[str, list[str]]:
    """Replace embedded ChapterFOLD image markers with normal Markdown image links.

    This keeps anthology Markdown editable instead of filling it with large
    base64 marker payloads.
    """

    output_dir = Path(output_dir)
    assets_dir = output_dir / f"{anthology_slug}-anthology-assets"
    written_files: list[str] = []
    seen_by_digest: dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        marker = match.group(0)
        data = _decode_image_marker_payload(marker)
        src = str(data.get("src") or "")
        alt = str(data.get("alt") or "")
        original_name = str(data.get("name") or "")

        if not src.startswith("data:image/"):
            return marker

        digest = hashlib.sha256(src.encode("utf-8")).hexdigest()[:16]
        if digest in seen_by_digest:
            rel = seen_by_digest[digest]
            return f"![{alt}]({rel})"

        suffix = Path(original_name).suffix or _extension_from_data_uri(src)
        safe_name = _safe_asset_name(original_name, f"image-{len(written_files) + 1:04d}{suffix}")
        if not Path(safe_name).suffix:
            safe_name = f"{safe_name}{suffix}"

        output_path = assets_dir / f"{len(written_files) + 1:04d}-{safe_name}"
        if not _write_data_uri_image(src, output_path):
            return marker

        rel = output_path.relative_to(output_dir).as_posix()
        seen_by_digest[digest] = rel
        written_files.append(str(output_path))
        return f"![{alt}]({rel})"

    rewritten = IMAGE_MARKER_PATTERN.sub(replace, markdown)
    return rewritten, written_files


def _markdown_page_break() -> str:
    return '<div class="chapterfold-page-break"></div>'


def _markdown_title_page(title: str, author: str) -> list[str]:
    return [
        '<section class="chapterfold-title-page">',
        "",
        f"# {title}",
        "",
        f"_By {author}_",
        "",
        "</section>",
    ]


def _markdown_source_divider(title: str, author: str, index: int) -> list[str]:
    return [
        _markdown_page_break(),
        "",
        f"# {title}",
        "",
        f"_By {author}_",
        "",
        f"<!-- ANTHOLOGY_SOURCE_INDEX: {index} -->",
        "",
    ]


def _clean_section_text(value: str) -> str:
    lines = [line.rstrip() for line in (value or "").splitlines()]
    compact: list[str] = []
    blank_seen = False

    for line in lines:
        if not line.strip():
            if not blank_seen:
                compact.append("")
            blank_seen = True
        else:
            compact.append(line)
            blank_seen = False

    return "\n".join(compact).strip()


def _load_epub_as_anthology_item(
    input_path: Path,
    *,
    cleanup_settings: CleanupSettings | None = None,
) -> tuple[AnthologyInputRecord, list[tuple[str, str]]]:
    content = load_epub_content(input_path)

    raw_image_markers_by_section = [
        _extract_image_markers(raw_html)
        for _, raw_html in content.sections
    ]

    title = _clean_heading(
        getattr(content, "detected_title", None),
        input_path.stem,
    )
    author = _clean_heading(
        getattr(content, "detected_author", None),
        "Unknown author",
    )

    sections = build_clean_text_sections(
        content.sections,
        drop_notes=False,
        cleanup_settings=cleanup_settings or CleanupSettings(),
        contents_mode="remove",
    )

    cleaned_sections: list[tuple[str, str]] = []
    total_chars = 0

    image_marker_count = 0

    for index, (heading, text) in enumerate(sections, start=1):
        cleaned = _clean_section_text(text)
        raw_markers = raw_image_markers_by_section[index - 1] if index - 1 < len(raw_image_markers_by_section) else []
        cleaned = _prepend_missing_image_markers(cleaned, raw_markers)

        markers_in_section = _extract_image_markers(cleaned)
        if raw_markers and not markers_in_section:
            markers_in_section = raw_markers

        if not cleaned:
            continue

        section_heading = _clean_heading(heading, f"Section {index}")
        cleaned_sections.append((section_heading, cleaned))
        total_chars += len(cleaned)
        image_marker_count += len(markers_in_section)

    record = AnthologyInputRecord(
        input_path=input_path,
        title=title,
        author=author,
        section_count=len(cleaned_sections),
        char_count=total_chars,
        image_marker_count=image_marker_count,
    )

    return record, cleaned_sections


def build_anthology_markdown(
    inputs: list[str | Path],
    *,
    anthology_title: str = "Collected Works",
    anthology_author: str = "Various Authors",
    cleanup_settings: CleanupSettings | None = None,
) -> tuple[str, list[AnthologyInputRecord], list[str]]:
    input_paths = [Path(path) for path in inputs]
    if not input_paths:
        raise ValueError("At least one EPUB input is required.")

    warnings: list[str] = []
    records: list[AnthologyInputRecord] = []

    lines: list[str] = []
    lines.extend(_markdown_title_page(anthology_title, anthology_author))
    lines.extend([
        "",
        _markdown_page_break(),
        "",
        "## Contents",
        "",
    ])

    loaded_items: list[tuple[AnthologyInputRecord, list[tuple[str, str]]]] = []

    for input_path in input_paths:
        if input_path.suffix.lower() != ".epub":
            raise ValueError(f"Batch anthology currently supports EPUB inputs only: {input_path}")
        if not input_path.exists():
            raise FileNotFoundError(f"Input EPUB does not exist: {input_path}")

        record, sections = _load_epub_as_anthology_item(
            input_path,
            cleanup_settings=cleanup_settings,
        )

        if not sections:
            warnings.append(f"No extractable sections found: {input_path}")

        loaded_items.append((record, sections))
        records.append(record)
        lines.append(f"- {record.title}")

    lines.extend(["", _markdown_page_break(), ""])

    for source_index, (record, sections) in enumerate(loaded_items, start=1):
        lines.extend(_markdown_source_divider(record.title, record.author, source_index))

        for section_index, (heading, text) in enumerate(sections, start=1):
            # Avoid repeating the source title immediately as the first section heading.
            if section_index == 1 and heading.strip().casefold() == record.title.strip().casefold():
                lines.append(text)
                lines.append("")
                continue

            lines.append(f"## {heading}")
            lines.append("")
            lines.append(text)
            lines.append("")

    lines.append("")

    return "\n".join(lines).rstrip() + "\n", records, warnings


def write_anthology_markdown(
    inputs: list[str | Path],
    output_dir: str | Path,
    *,
    anthology_title: str = "Collected Works",
    anthology_author: str = "Various Authors",
    cleanup_settings: CleanupSettings | None = None,
) -> AnthologyBuildResult:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    markdown, records, warnings = build_anthology_markdown(
        inputs,
        anthology_title=anthology_title,
        anthology_author=anthology_author,
        cleanup_settings=cleanup_settings,
    )

    stem = _safe_filename(anthology_title)
    markdown_path = output_dir / f"{stem} - Anthology.md"
    manifest_json_path = output_dir / f"{stem} - Anthology Manifest.json"

    markdown, externalized_image_files = externalize_anthology_image_markers(
        markdown,
        output_dir,
        anthology_slug=stem.lower().replace(" ", "-"),
    )

    for index, record in enumerate(records, start=1):
        book_slug = f"{stem.lower().replace(' ', '-')}-source-{index}"
        try:
            asset_files = export_epub_image_assets(record.input_path, output_dir, book_slug=book_slug)
        except Exception as exc:
            warnings.append(f"Image asset export failed for {record.input_path}: {exc}")
            asset_files = []

        record.image_asset_files = asset_files
        record.image_asset_count = len(asset_files)

    markdown_path.write_text(markdown, encoding="utf-8")

    manifest = {
        "success": True,
        "title": anthology_title,
        "author": anthology_author,
        "input_count": len(records),
        "output_markdown": str(markdown_path),
        "externalized_image_count": len(externalized_image_files),
        "externalized_image_files": externalized_image_files,
        "warnings": warnings,
        "inputs": [
            {
                "input_path": str(record.input_path),
                "title": record.title,
                "author": record.author,
                "section_count": record.section_count,
                "char_count": record.char_count,
                "image_marker_count": record.image_marker_count,
                "image_asset_count": record.image_asset_count,
                "image_asset_files": record.image_asset_files,
            }
            for record in records
        ],
    }
    manifest_json_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    return AnthologyBuildResult(
        success=True,
        title=anthology_title,
        author=anthology_author,
        output_dir=output_dir,
        markdown_path=markdown_path,
        manifest_json_path=manifest_json_path,
        input_records=records,
        warnings=warnings,
        externalized_image_files=externalized_image_files,
    )


def anthology_result_to_dict(result: AnthologyBuildResult) -> dict[str, Any]:
    return {
        "success": result.success,
        "title": result.title,
        "author": result.author,
        "output_dir": str(result.output_dir),
        "markdown_path": str(result.markdown_path),
        "manifest_json_path": str(result.manifest_json_path),
        "externalized_image_count": len(result.externalized_image_files),
        "externalized_image_files": result.externalized_image_files,
        "warnings": result.warnings,
        "inputs": [
            {
                "input_path": str(record.input_path),
                "title": record.title,
                "author": record.author,
                "section_count": record.section_count,
                "char_count": record.char_count,
                "image_marker_count": record.image_marker_count,
                "image_asset_count": record.image_asset_count,
                "image_asset_files": record.image_asset_files,
            }
            for record in result.input_records
        ],
    }
