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
    load_epub_content,
    process_epub_to_pdf,
)
from core.impose_service import build_signature_settings, impose_pdf

LogCallback = Callable[[str], None]


PAGE_SIZE_PRESETS_CM: dict[str, tuple[str, float, float]] = {
    "default-trade": ("Default trade (6 x 9 in)", 15.24, 22.86),
    "a4": ("A4", 21.0, 29.7),
    "a5": ("A5", 14.8, 21.0),
    "a6": ("A6", 10.5, 14.8),
    "letter": ("US Letter", 21.59, 27.94),
    "half-letter": ("Half Letter", 13.97, 21.59),
    "trade-5x8": ("Trade 5 x 8 in", 12.70, 20.32),
    "trade-6x9": ("Trade 6 x 9 in", 15.24, 22.86),
}


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


def describe_margin_preset(margin_preset: str) -> str:
    preset = (margin_preset or "standard").strip().lower()

    mapping = {
        "standard": "Standard",
        "compact": "Compact",
        "wide": "Wide",
        "large-print": "Large print friendly",
        "custom": "Custom margins",
    }

    return mapping.get(preset, margin_preset)


def describe_page_size_preset(page_size_preset: str) -> str:
    key = (page_size_preset or "default-trade").strip().lower()
    if key == "custom":
        return "Custom size"
    if key in PAGE_SIZE_PRESETS_CM:
        return PAGE_SIZE_PRESETS_CM[key][0]
    return page_size_preset


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


def build_layout_settings(
    *,
    paragraph_spacing_mode: str,
    margin_preset: str,
    page_size_preset: str,
    custom_trim_width_cm: float | None,
    custom_trim_height_cm: float | None,
    custom_margin_top_cm: float | None,
    custom_margin_bottom_cm: float | None,
    custom_margin_inside_cm: float | None,
    custom_margin_outside_cm: float | None,
) -> LayoutSettings:
    layout = LayoutSettings(
        paragraph_spacing_mode=paragraph_spacing_mode,
    )

    size_key = (page_size_preset or "default-trade").strip().lower()
    if size_key == "custom":
        if custom_trim_width_cm is None or custom_trim_height_cm is None:
            raise ValueError("Custom page size selected but width/height were not provided.")
        if custom_trim_width_cm <= 0 or custom_trim_height_cm <= 0:
            raise ValueError("Custom page width and height must be greater than zero.")
        layout.trim_width_cm = custom_trim_width_cm
        layout.trim_height_cm = custom_trim_height_cm
    elif size_key in PAGE_SIZE_PRESETS_CM:
        _, width_cm, height_cm = PAGE_SIZE_PRESETS_CM[size_key]
        layout.trim_width_cm = width_cm
        layout.trim_height_cm = height_cm
    else:
        raise ValueError(f"Unknown page size preset: {page_size_preset}")

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
        layout.margin_inside_cm = 2.3
        layout.margin_outside_cm = 1.5
    elif preset == "custom":
        values = [
            custom_margin_top_cm,
            custom_margin_bottom_cm,
            custom_margin_inside_cm,
            custom_margin_outside_cm,
        ]
        if any(v is None for v in values):
            raise ValueError("Custom margins selected but one or more margin values were not provided.")
        if any(v <= 0 for v in values):
            raise ValueError("All custom margin values must be greater than zero.")

        layout.margin_top_cm = custom_margin_top_cm
        layout.margin_bottom_cm = custom_margin_bottom_cm
        layout.margin_inside_cm = custom_margin_inside_cm
        layout.margin_outside_cm = custom_margin_outside_cm
    elif preset != "standard":
        raise ValueError(f"Unknown margin preset: {margin_preset}")

    return layout


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
    page_size_preset: str,
) -> str:
    parts = [
        safe_filename_component(author),
        safe_filename_component(title),
        safe_filename_component(describe_variant(variant)),
    ]

    if spacing_mode and spacing_mode != "traditional":
        parts.append(safe_filename_component(describe_spacing_mode(spacing_mode)))

    if page_size_preset and page_size_preset != "default-trade":
        parts.append(safe_filename_component(describe_page_size_preset(page_size_preset)))

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
    page_size_preset: str,
) -> tuple[Path, Path, Path, str]:
    stem = build_file_stem(
        author=used_author or input_epub.stem,
        title=used_title or input_epub.stem,
        variant=variant,
        spacing_mode=spacing_mode,
        margin_preset=margin_preset,
        page_size_preset=page_size_preset,
    )

    output_pdf_path = output_dir / f"{stem} - Interior.pdf"
    output_docx_path = output_dir / f"{stem} - Editable.docx"
    output_markdown_path = output_dir / f"{stem} - Editable.md"
    return output_pdf_path, output_docx_path, output_markdown_path, stem


def render_baseline_pdf(
    *,
    input_epub: Path,
    output_dir: Path,
    used_title: str,
    used_author: str,
    spacing_mode: str,
    margin_preset: str,
    page_size_preset: str,
    settings: LayoutSettings,
    log: LogCallback | None = None,
) -> tuple[Path, int, float | None]:
    baseline_variant = "standard"
    baseline_cleanup = build_cleanup_settings(baseline_variant)

    baseline_pdf_path, _, _, _ = build_output_paths(
        input_epub=input_epub,
        output_dir=output_dir,
        used_title=used_title,
        used_author=used_author,
        variant=baseline_variant,
        spacing_mode=spacing_mode,
        margin_preset=margin_preset,
        page_size_preset=page_size_preset,
    )

    if log:
        log("Rendering baseline PDF for comparison...")

    process_epub_to_pdf(
        epub_path=input_epub,
        output_pdf_path=baseline_pdf_path,
        output_docx_path=None,
        output_markdown_path=None,
        export_docx=False,
        export_markdown=False,
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
    export_markdown: bool,
    paragraph_spacing_mode: str,
    margin_preset: str,
    page_size_preset: str,
    custom_trim_width_cm: float | None,
    custom_trim_height_cm: float | None,
    custom_margin_top_cm: float | None,
    custom_margin_bottom_cm: float | None,
    custom_margin_inside_cm: float | None,
    custom_margin_outside_cm: float | None,
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
        page_size_preset=page_size_preset,
        custom_trim_width_cm=custom_trim_width_cm,
        custom_trim_height_cm=custom_trim_height_cm,
        custom_margin_top_cm=custom_margin_top_cm,
        custom_margin_bottom_cm=custom_margin_bottom_cm,
        custom_margin_inside_cm=custom_margin_inside_cm,
        custom_margin_outside_cm=custom_margin_outside_cm,
    )

    create_imposed_pdf = (imposition_mode or "none").strip().lower() == "also"

    log("Reading EPUB metadata...")
    epub_content = load_epub_content(input_epub)

    used_title = epub_content.detected_title
    used_author = epub_content.detected_author

    output_pdf_path, output_docx_path, output_markdown_path, file_stem = build_output_paths(
        input_epub=input_epub,
        output_dir=output_dir,
        used_title=used_title,
        used_author=used_author,
        variant=variant,
        spacing_mode=paragraph_spacing_mode,
        margin_preset=margin_preset,
        page_size_preset=page_size_preset,
    )

    log(f"Detected title: {used_title}")
    log(f"Detected author: {used_author}")
    log(f"Selected variant: {describe_variant(variant)}")
    log(f"Paragraph spacing mode: {describe_spacing_mode(paragraph_spacing_mode)}")
    log(f"Page size: {describe_page_size_preset(page_size_preset)}")
    log(f"Trim size: {layout_settings.trim_width_cm:.2f} cm x {layout_settings.trim_height_cm:.2f} cm")
    log(f"Margin preset: {describe_margin_preset(margin_preset)}")
    log(
        "Margins (top / bottom / inside / outside): "
        f"{layout_settings.margin_top_cm:.2f} / "
        f"{layout_settings.margin_bottom_cm:.2f} / "
        f"{layout_settings.margin_inside_cm:.2f} / "
        f"{layout_settings.margin_outside_cm:.2f} cm"
    )
    log(f"Imposition mode: {describe_imposition_mode(imposition_mode)}")
    log(f"DOCX export: {'Yes (Word / LibreOffice)' if export_docx else 'No'}")
    log(f"Markdown export: {'Yes (Google Docs)' if export_markdown else 'No'}")

    baseline_pdf_path = None
    baseline_pages = None
    baseline_size_mb = None
    page_delta = None
    size_delta_mb = None

    baseline_pdf_path, baseline_pages, baseline_size_mb = render_baseline_pdf(
        input_epub=input_epub,
        output_dir=output_dir,
        used_title=used_title,
        used_author=used_author,
        spacing_mode=paragraph_spacing_mode,
        margin_preset=margin_preset,
        page_size_preset=page_size_preset,
        settings=layout_settings,
        log=log,
    )

    log("Rendering selected output files...")
    result: EpubToPdfResult = process_epub_to_pdf(
        epub_path=input_epub,
        output_pdf_path=output_pdf_path,
        output_docx_path=output_docx_path if export_docx else None,
        output_markdown_path=output_markdown_path if export_markdown else None,
        export_docx=export_docx,
        export_markdown=export_markdown,
        title=used_title,
        author=used_author,
        settings=layout_settings,
        cleanup_settings=cleanup_settings,
    )

    log("Calculating result stats...")
    input_size_mb = file_size_mb(input_epub)
    pdf_size_mb = file_size_mb(result.output_pdf)
    docx_size_mb = file_size_mb(result.output_docx) if result.output_docx else None
    markdown_size_mb = file_size_mb(result.output_markdown) if result.output_markdown else None
    output_pdf_pages = pdf_page_count(result.output_pdf)

    if baseline_pages is not None:
        page_delta = output_pdf_pages - baseline_pages
    if baseline_size_mb is not None and pdf_size_mb is not None:
        size_delta_mb = pdf_size_mb - baseline_size_mb

    preview_samples = []
    for title, section_html in epub_content.sections[:3]:
        preview_samples.append(
            {
                "heading": title,
                "before": trim_preview_text(section_html),
                "after": trim_preview_text(section_html),
            }
        )

    imposed_output_pdf = ""
    imposed_blank_pages_added = None
    imposed_total_signatures = None
    imposed_output_sheet_sides = None
    imposed_physical_sheets_total = None
    imposed_signature_settings_pages = None

    if create_imposed_pdf:
        log("Creating imposed signature PDF...")
        imposed_signature_settings_pages = imposed_pages_per_signature

        signature_settings = build_signature_settings(
            pages_per_signature=imposed_pages_per_signature,
            max_end_padding=max_end_padding,
            binding_direction=binding_direction,
        )

        imposed_path = output_dir / f"{file_stem} - Imposed.pdf"

        impose_result = impose_pdf(
            input_pdf=result.output_pdf,
            output_pdf=imposed_path,
            settings=signature_settings,
        )

        imposed_output_pdf = str(impose_result.output_pdf)
        imposed_blank_pages_added = impose_result.blank_pages_added
        imposed_total_signatures = impose_result.total_signatures
        imposed_output_sheet_sides = impose_result.output_sheet_sides
        imposed_physical_sheets_total = impose_result.physical_sheets_total

    return {
        "title": result.used_title,
        "author": result.used_author,
        "variant": variant,
        "variant_label": describe_variant(variant),
        "file_stem": file_stem,
        "input_epub": str(input_epub),
        "input_size_mb": input_size_mb,
        "pdf_size_mb": pdf_size_mb,
        "docx_size_mb": docx_size_mb,
        "markdown_size_mb": markdown_size_mb,
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
        "page_size_preset": page_size_preset,
        "page_size_preset_label": describe_page_size_preset(page_size_preset),
        "trim_width_cm": layout_settings.trim_width_cm,
        "trim_height_cm": layout_settings.trim_height_cm,
        "margin_preset": margin_preset,
        "margin_preset_label": describe_margin_preset(margin_preset),
        "margin_top_cm": layout_settings.margin_top_cm,
        "margin_bottom_cm": layout_settings.margin_bottom_cm,
        "margin_inside_cm": layout_settings.margin_inside_cm,
        "margin_outside_cm": layout_settings.margin_outside_cm,
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
        "output_pdf": str(result.output_pdf),
        "output_docx": str(result.output_docx) if result.output_docx else "",
        "output_markdown": str(result.output_markdown) if result.output_markdown else "",
        "output_dir": str(result.output_dir),
        "export_docx": export_docx,
        "export_markdown": export_markdown,
    }
