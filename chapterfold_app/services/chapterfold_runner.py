from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path
from typing import Callable

from pypdf import PdfReader

from core.epub_service import (
    CleanupSettings,
    EpubToPdfResult,
    LayoutSettings,
    extract_clean_text_from_html,
    load_epub_content,
    process_epub_to_pdf,
)
from core.impose_service import build_signature_settings, impose_pdf

LogCallback = Callable[[str], None]


def build_cleanup_settings(variant: str) -> CleanupSettings:
    standard = CleanupSettings(
        join_soft_wrapped_lines=True,
        join_dialogue_continuations=True,
        merge_dialogue_paragraphs=False,
        aggressive_mode=False,
        collapse_extra_blank_lines=True,
        preserve_scene_breaks=True,
    )

    dialogue_merge = CleanupSettings(
        join_soft_wrapped_lines=True,
        join_dialogue_continuations=True,
        merge_dialogue_paragraphs=True,
        aggressive_mode=False,
        collapse_extra_blank_lines=True,
        preserve_scene_breaks=True,
    )

    aggressive = replace(
        dialogue_merge,
        aggressive_mode=True,
    )

    variants = {
        "standard": standard,
        "paragraph-dialogue-merge": dialogue_merge,
        "aggressive-cleanup": aggressive,
    }

    if variant not in variants:
        raise ValueError(f"Unknown variant: {variant}")

    return variants[variant]


def describe_variant(variant: str) -> str:
    mapping = {
        "standard": "Standard Cleanup",
        "paragraph-dialogue-merge": "Dialogue Merge",
        "aggressive-cleanup": "Aggressive Cleanup",
    }
    return mapping.get(variant, variant)


def describe_spacing_mode(mode: str) -> str:
    normalized = (mode or "traditional").strip().lower()
    if normalized == "uniform":
        return "Uniform (no paragraph gap, no indents)"
    if normalized == "no-indents":
        return "No indents (keep paragraph spacing)"
    if normalized == "indented-compact":
        return "Indented compact (minimal paragraph gap + indents)"
    return "Traditional (paragraph spacing + indents)"


def build_layout_settings(
    *,
    paragraph_spacing_mode: str,
    margin_preset: str,
) -> LayoutSettings:
    layout = LayoutSettings(
        paragraph_spacing_mode=paragraph_spacing_mode,
    )

    preset = (margin_preset or "standard").strip().lower()

    if preset == "compact":
        layout.margin_top_cm = 1.2
        layout.margin_bottom_cm = 1.2
        layout.margin_inside_cm = 1.5
        layout.margin_outside_cm = 0.8
    elif preset == "wide":
        layout.margin_top_cm = 1.8
        layout.margin_bottom_cm = 1.8
        layout.margin_inside_cm = 2.1
        layout.margin_outside_cm = 1.2
    elif preset == "large-print":
        layout.margin_top_cm = 2.0
        layout.margin_bottom_cm = 2.0
        layout.margin_inside_cm = 2.2
        layout.margin_outside_cm = 1.4
    else:
        layout.margin_top_cm = 1.5
        layout.margin_bottom_cm = 1.5
        layout.margin_inside_cm = 1.8
        layout.margin_outside_cm = 1.0

    return layout


def describe_margin_preset(margin_preset: str) -> str:
    preset = (margin_preset or "standard").strip().lower()
    mapping = {
        "standard": "Standard",
        "compact": "Compact",
        "wide": "Wide",
        "large-print": "Large print friendly",
    }
    return mapping.get(preset, margin_preset)


def describe_binding_direction(binding_direction: str) -> str:
    direction = (binding_direction or "ltr").strip().lower()
    if direction == "rtl":
        return "Right-to-left"
    return "Left-to-right"


def describe_imposition_mode(mode: str) -> str:
    normalized = (mode or "none").strip().lower()
    mapping = {
        "none": "Do not create imposed PDF",
        "also": "Also create imposed PDF",
    }
    return mapping.get(normalized, mode)


def describe_max_end_padding(max_end_padding: int | None) -> str:
    if max_end_padding is None:
        return "Unlimited"
    return str(max_end_padding)


def build_raw_preview_cleanup_settings() -> CleanupSettings:
    return CleanupSettings(
        join_soft_wrapped_lines=False,
        join_dialogue_continuations=False,
        merge_dialogue_paragraphs=False,
        aggressive_mode=False,
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


def safe_filename_component(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r'[<>:"/\\|?*]+', "", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip(" .")
    return text or "Unknown"


def build_file_stem(
    *,
    author: str,
    title: str,
    variant: str,
    spacing_mode: str,
    margin_preset: str,
) -> str:
    parts = [
        safe_filename_component(author),
        safe_filename_component(title),
        safe_filename_component(describe_variant(variant)),
    ]

    if spacing_mode and spacing_mode != "traditional":
        parts.append(safe_filename_component(describe_spacing_mode(spacing_mode)))

    if margin_preset and margin_preset != "standard":
        parts.append(safe_filename_component(describe_margin_preset(margin_preset)))

    return " - ".join(parts)


def build_output_paths(
    *,
    input_epub: Path,
    output_dir: Path,
    used_title: str,
    used_author: str,
    variant: str,
    spacing_mode: str,
    margin_preset: str,
) -> tuple[Path, Path, str]:
    stem = build_file_stem(
        author=used_author or input_epub.stem,
        title=used_title or input_epub.stem,
        variant=variant,
        spacing_mode=spacing_mode,
        margin_preset=margin_preset,
    )

    output_pdf_path = output_dir / f"{stem} - Interior.pdf"
    output_docx_path = output_dir / f"{stem} - Editable.docx"

    return output_pdf_path, output_docx_path, stem


def build_imposed_output_path(
    *,
    output_dir: Path,
    file_stem: str,
    pages_per_signature: int,
    binding_direction: str,
) -> Path:
    direction_label = "RTL" if binding_direction == "rtl" else "LTR"
    return output_dir / (
        f"{file_stem} - Imposed {pages_per_signature}pp {direction_label}.pdf"
    )


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


def render_baseline_pdf(
    *,
    input_epub: Path,
    output_dir: Path,
    used_title: str,
    used_author: str,
    spacing_mode: str,
    margin_preset: str,
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
        spacing_mode=spacing_mode,
        margin_preset=margin_preset,
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


def run_processing(
    *,
    input_epub: Path,
    output_dir: Path,
    variant: str,
    export_docx: bool,
    paragraph_spacing_mode: str,
    margin_preset: str,
    imposition_mode: str,
    imposed_pages_per_signature: int,
    binding_direction: str,
    max_end_padding: int | None,
    log_callback: LogCallback | None = None,
) -> dict:
    if not input_epub.exists():
        raise FileNotFoundError(f"Input EPUB not found: {input_epub}")

    output_dir.mkdir(parents=True, exist_ok=True)

    def log(message: str) -> None:
        if log_callback:
            log_callback(message)

    cleanup_settings = build_cleanup_settings(variant)
    layout_settings = build_layout_settings(
        paragraph_spacing_mode=paragraph_spacing_mode,
        margin_preset=margin_preset,
    )

    create_imposed_pdf = (imposition_mode or "none").strip().lower() == "also"

    log("Reading EPUB metadata...")
    epub_content = load_epub_content(input_epub)
    used_title = epub_content.detected_title
    used_author = epub_content.detected_author

    output_pdf_path, output_docx_path, file_stem = build_output_paths(
        input_epub=input_epub,
        output_dir=output_dir,
        used_title=used_title,
        used_author=used_author,
        variant=variant,
        spacing_mode=paragraph_spacing_mode,
        margin_preset=margin_preset,
    )

    log(f"Detected title: {used_title}")
    log(f"Detected author: {used_author}")
    log(f"Selected variant: {describe_variant(variant)}")
    log(f"Paragraph spacing mode: {describe_spacing_mode(paragraph_spacing_mode)}")
    log(f"Margin preset: {describe_margin_preset(margin_preset)}")
    log(f"Imposition mode: {describe_imposition_mode(imposition_mode)}")

    if create_imposed_pdf:
        log(f"Pages per signature: {imposed_pages_per_signature}")
        log(f"Binding direction: {describe_binding_direction(binding_direction)}")
        log(f"Max blank end pages: {describe_max_end_padding(max_end_padding)}")

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
            spacing_mode=paragraph_spacing_mode,
            margin_preset=margin_preset,
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

    imposed_output_pdf = ""
    imposed_blank_pages_added = None
    imposed_total_signatures = None
    imposed_output_sheet_sides = None
    imposed_physical_sheets_total = None
    imposed_signature_settings_pages = None

    if create_imposed_pdf:
        log("Creating imposed signature PDF...")
        signature_settings = build_signature_settings(
            pages_per_signature=imposed_pages_per_signature,
            binding_direction=binding_direction,
            max_end_padding=max_end_padding,
        )
        imposed_output_path = build_imposed_output_path(
            output_dir=output_dir,
            file_stem=file_stem,
            pages_per_signature=signature_settings.pages_per_signature,
            binding_direction=signature_settings.binding_direction,
        )
        imposed_result = impose_pdf(
            input_pdf=result.output_pdf,
            output_pdf=imposed_output_path,
            settings=signature_settings,
        )
        imposed_output_pdf = str(imposed_result.output_pdf)
        imposed_blank_pages_added = imposed_result.blank_pages_added
        imposed_total_signatures = imposed_result.total_signatures
        imposed_output_sheet_sides = imposed_result.output_sheet_sides
        imposed_physical_sheets_total = imposed_result.physical_sheets_total
        imposed_signature_settings_pages = signature_settings.pages_per_signature

        log(f"Imposed PDF created: {imposed_output_pdf}")
        log(
            f"Imposition: {signature_settings.pages_per_signature} pages/signature, "
            f"{describe_binding_direction(signature_settings.binding_direction)}"
        )

    return {
        "output_pdf": str(result.output_pdf),
        "output_docx": str(result.output_docx) if result.output_docx else "",
        "title": result.used_title,
        "author": result.used_author,
        "output_dir": str(result.output_dir),
        "variant": variant,
        "variant_label": describe_variant(variant),
        "file_stem": file_stem,
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
        "margin_preset": margin_preset,
        "margin_preset_label": describe_margin_preset(margin_preset),
        "imposition_mode": imposition_mode,
        "imposition_mode_label": describe_imposition_mode(imposition_mode),
        "create_imposed_pdf": create_imposed_pdf,
        "imposed_output_pdf": imposed_output_pdf,
        "imposed_pages_per_signature": imposed_signature_settings_pages,
        "binding_direction": binding_direction if create_imposed_pdf else "",
        "binding_direction_label": describe_binding_direction(binding_direction) if create_imposed_pdf else "",
        "max_end_padding": max_end_padding,
        "max_end_padding_label": describe_max_end_padding(max_end_padding),
        "imposed_blank_pages_added": imposed_blank_pages_added,
        "imposed_total_signatures": imposed_total_signatures,
        "imposed_output_sheet_sides": imposed_output_sheet_sides,
        "imposed_physical_sheets_total": imposed_physical_sheets_total,
    }
