from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Callable

from core.epub_service import (
    CleanupSettings,
    EpubToPdfResult,
    LayoutSettings,
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


def run_processing(
    *,
    input_epub: Path,
    output_dir: Path,
    variant: str,
    export_docx: bool,
    log_callback: LogCallback | None = None,
) -> EpubToPdfResult:
    if not input_epub.exists():
        raise FileNotFoundError(f"Input EPUB not found: {input_epub}")

    output_dir.mkdir(parents=True, exist_ok=True)

    def log(message: str) -> None:
        if log_callback:
            log_callback(message)

    cleanup_settings = build_cleanup_settings(variant)
    layout_settings = LayoutSettings()

    log("Starting ChapterFOLD processing...")
    log(f"Input EPUB: {input_epub}")
    log(f"Output folder: {output_dir}")
    log(f"Variant: {variant}")
    log(f"Export DOCX: {'Yes' if export_docx else 'No'}")

    result = process_epub_to_pdf(
        epub_path=input_epub,
        output_pdf_path=None,
        output_docx_path=None,
        export_docx=export_docx,
        title=None,
        author=None,
        settings=layout_settings,
        cleanup_settings=cleanup_settings,
    )

    log(f"Detected title: {result.detected_title}")
    log(f"Detected author: {result.detected_author}")
    log(f"PDF created: {result.output_pdf}")

    if result.output_docx:
        log(f"DOCX created: {result.output_docx}")

    return result
