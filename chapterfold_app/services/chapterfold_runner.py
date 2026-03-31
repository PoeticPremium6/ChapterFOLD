from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Callable

from pypdf import PdfReader

from core.epub_service import (
    CleanupSettings,
    EpubToPdfResult,
    LayoutSettings,
    build_book_slug,
    editable_docx_name,
    extract_clean_text_from_html,
    interior_pdf_name,
    load_epub_content,
    process_epub_to_pdf,
)

LogCallback = Callable[[str], None]


def build_cleanup_settings(variant: str) -> CleanupSettings:
    standard = CleanupSettings(
        join_soft_wrapped_lines=True,
        join_dialogue_continuations=True,
        merge_dialogue_paragraphs=False,
        collapse_extra_blank_lines=True,
        preserve_scene_breaks=True,
    )

    aggressive = CleanupSettings(
        join_soft_wrapped_lines=True,
        join_dialogue_continuations=True,
        merge_dialogue_paragraphs=False,
        collapse_extra_blank_lines=True,
        preserve_scene_breaks=True,
    )

    paragraph_dialogue_merge = replace(
        aggressive,
        merge_dialogue_paragraphs=True,
    )

    variants = {
        "standard": standard,
        "aggressive-cleanup": aggressive,
        "paragraph-dialogue-merge": paragraph_dialogue_merge,
    }

    if variant not in variants:
        raise ValueError(f"Unknown variant: {variant}")

    return variants[variant]


def build_raw_preview_cleanup_settings() -> CleanupSettings:
    return CleanupSettings(
        join_soft_wrapped_lines=False,
        join_dialogue_continuations=False,
        merge_dialogue_paragraphs=False,
        collapse_extra_blank_lines=False,
        preserve_scene_breaks=True,
    )


def file_size_mb(path: Path | None) -> float | None:
    if path is None or not path.exists():
        return None
    return path.stat().st_size / (1024 * 1024)


def pdf_page_count(path: Path) -> int:
    reader = PdfReader(str(path))
    return len(reader.pages)


def trim_preview_text(text: str, limit: int = 1400) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def build_preview_samples(
    *,
    sections: list[tuple[str, str]],
    cleanup_settings: CleanupSettings,
    max_samples: int = 3,
) -> list[dict[str, str]]:
    samples: list[dict[str, str]] = []
    raw_settings = build_raw_preview_cleanup_settings()

    for heading, raw_html in sections:
        before = extract_clean_text_from_html(
            raw_html,
            drop_notes=False,
            cleanup_settings=raw_settings,
        ).strip()

        after = extract_clean_text_from_html(
            raw_html,
            drop_notes=False,
            cleanup_settings=cleanup_settings,
        ).strip()

        if not before or not after or before == after:
            continue

        samples.append(
            {
                "heading": (heading or "(Untitled section)").strip(),
                "before": trim_preview_text(before),
                "after": trim_preview_text(after),
            }
        )

        if len(samples) >= max_samples:
            break

    return samples


def build_output_paths(
    *,
    input_epub: Path,
    output_dir: Path,
    used_title: str,
    used_author: str,
    variant: str,
) -> tuple[Path, Path, str]:
    book_slug = build_book_slug(
        title=used_title,
        author=used_author,
        fallback_stem=input_epub.stem,
    )

    variant_slug = variant.replace(" ", "-").replace("_", "-")
    full_slug = f"{book_slug}__{variant_slug}"

    output_pdf_path = output_dir / interior_pdf_name(full_slug)
    output_docx_path = output_dir / editable_docx_name(full_slug)

    return output_pdf_path, output_docx_path, full_slug


def render_baseline_pdf(
    *,
    input_epub: Path,
    output_dir: Path,
    used_title: str,
    used_author: str,
    settings: LayoutSettings,
    log: LogCallback | None = None,
) -> tuple[Path, int, float | None]:
    baseline_variant = "standard"
    baseline_cleanup = build_cleanup_settings(baseline_variant)

    baseline_pdf_path, _, _ = build_output_paths(
        input_epub=input_epub,
        output_dir=output_dir,
        used_title=used_title,
        used_author=used_author,
        variant=baseline_variant,
    )

    if log:
        log("Rendering baseline PDF for comparison...")

    process_epub_to_pdf(
        epub_path=input_epub,
        output_pdf_path=baseline_pdf_path,
        output_docx_path=None,
        export_docx=False,
        title=used_title,
        author=used_author,
        settings=settings,
        cleanup_settings=baseline_cleanup,
    )

    baseline_pages = pdf_page_count(baseline_pdf_path)
    baseline_size_mb = file_size_mb(baseline_pdf_path)
    return baseline_pdf_path, baseline_pages, baseline_size_mb


def describe_spacing_mode(mode: str) -> str:
    normalized = (mode or "traditional").strip().lower()
    if normalized == "uniform":
        return "Uniform (no paragraph gap, no indents)"
    if normalized == "no-indents":
        return "No indents (keep paragraph spacing)"
    return "Traditional (paragraph spacing + indents)"


def run_processing(
    *,
    input_epub: Path,
    output_dir: Path,
    variant: str,
    export_docx: bool,
    paragraph_spacing_mode: str,
    log_callback: LogCallback | None = None,
) -> dict:
    if not input_epub.exists():
        raise FileNotFoundError(f"Input EPUB not found: {input_epub}")

    output_dir.mkdir(parents=True, exist_ok=True)

    def log(message: str) -> None:
        if log_callback:
            log_callback(message)

    cleanup_settings = build_cleanup_settings(variant)
    layout_settings = LayoutSettings(
        paragraph_spacing_mode=paragraph_spacing_mode,
    )

    log("Reading EPUB metadata...")
    epub_content = load_epub_content(input_epub)
    used_title = epub_content.detected_title
    used_author = epub_content.detected_author

    output_pdf_path, output_docx_path, full_slug = build_output_paths(
        input_epub=input_epub,
        output_dir=output_dir,
        used_title=used_title,
        used_author=used_author,
        variant=variant,
    )

    log(f"Detected title: {used_title}")
    log(f"Detected author: {used_author}")
    log(f"Selected variant: {variant}")
    log(f"Paragraph spacing mode: {describe_spacing_mode(paragraph_spacing_mode)}")
    log("Building text cleanup preview samples...")

    preview_samples = build_preview_samples(
        sections=epub_content.sections,
        cleanup_settings=cleanup_settings,
        max_samples=3,
    )

    baseline_pdf_path = None
    baseline_pages = None
    baseline_size_mb = None

    if variant != "standard":
        baseline_pdf_path, baseline_pages, baseline_size_mb = render_baseline_pdf(
            input_epub=input_epub,
            output_dir=output_dir,
            used_title=used_title,
            used_author=used_author,
            settings=layout_settings,
            log=log,
        )

    log("Rendering selected output files...")
    result: EpubToPdfResult = process_epub_to_pdf(
        epub_path=input_epub,
        output_pdf_path=output_pdf_path,
        output_docx_path=output_docx_path if export_docx else None,
        export_docx=export_docx,
        title=used_title,
        author=used_author,
        settings=layout_settings,
        cleanup_settings=cleanup_settings,
    )

    log("Calculating result stats...")
    input_size_mb = file_size_mb(input_epub)
    pdf_size_mb = file_size_mb(result.output_pdf)
    docx_size_mb = file_size_mb(result.output_docx) if result.output_docx else None
    output_pdf_pages = pdf_page_count(result.output_pdf)

    page_delta = None
    size_delta_mb = None
    if baseline_pages is not None:
        page_delta = output_pdf_pages - baseline_pages
    if baseline_size_mb is not None and pdf_size_mb is not None:
        size_delta_mb = pdf_size_mb - baseline_size_mb

    return {
        "output_pdf": str(result.output_pdf),
        "output_docx": str(result.output_docx) if result.output_docx else "",
        "title": result.used_title,
        "author": result.used_author,
        "output_dir": str(result.output_dir),
        "variant": variant,
        "book_slug": full_slug,
        "input_epub": str(input_epub),
        "input_size_mb": input_size_mb,
        "pdf_size_mb": pdf_size_mb,
        "docx_size_mb": docx_size_mb,
        "output_pdf_pages": output_pdf_pages,
        "preview_samples": preview_samples,
        "preview_sample_count": len(preview_samples),
        "baseline_pdf": str(baseline_pdf_path) if baseline_pdf_path else "",
        "baseline_pdf_pages": baseline_pages,
        "baseline_pdf_size_mb": baseline_size_mb,
        "page_delta_vs_baseline": page_delta,
        "size_delta_mb_vs_baseline": size_delta_mb,
        "paragraph_spacing_mode": paragraph_spacing_mode,
        "paragraph_spacing_mode_label": describe_spacing_mode(paragraph_spacing_mode),
    }
