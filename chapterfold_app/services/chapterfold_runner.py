from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Callable

from core.epub_service import (
    CleanupSettings,
    LayoutSettings,
    build_book_slug,
    editable_docx_name,
    interior_pdf_name,
    load_epub_content,
    markdown_name,
    process_epub_to_pdf,
)

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
        "aggressive-cleanup": "Aggressive Cleanup",
        "paragraph-dialogue-merge": "Dialogue Merge",
    }
    return mapping.get(variant, variant)


def describe_spacing_mode(mode: str) -> str:
    mapping = {
        "traditional": "Traditional",
        "uniform": "Uniform",
        "no-indents": "No indents",
        "indented-compact": "Indented compact",
    }
    return mapping.get(mode, mode)


def describe_margin_preset(margin_preset: str) -> str:
    mapping = {
        "standard": "Standard",
        "compact": "Compact",
        "wide": "Wide",
        "large-print": "Large print friendly",
        "custom": "Custom margins",
    }
    return mapping.get(margin_preset, margin_preset)


def describe_page_size_preset(page_size_preset: str) -> str:
    if page_size_preset == "custom":
        return "Custom size"
    if page_size_preset in PAGE_SIZE_PRESETS_CM:
        return PAGE_SIZE_PRESETS_CM[page_size_preset][0]
    return page_size_preset


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

    epub_content = load_epub_content(input_epub)
    used_title = epub_content.detected_title
    used_author = epub_content.detected_author

    book_slug = build_book_slug(
        title=used_title,
        author=used_author,
        fallback_stem=input_epub.stem,
    )

    variant_slug = variant.replace(" ", "-").replace("_", "-")
    pdf_name = interior_pdf_name(f"{book_slug}__{variant_slug}")
    docx_name = editable_docx_name(f"{book_slug}__{variant_slug}")
    md_name = markdown_name(f"{book_slug}__{variant_slug}")

    output_pdf_path = output_dir / pdf_name
    output_docx_path = output_dir / docx_name
    output_markdown_path = output_dir / md_name

    log("Starting ChapterFOLD processing...")
    log(f"Input EPUB: {input_epub}")
    log(f"Output folder: {output_dir}")
    log(f"Variant: {describe_variant(variant)}")
    log(f"Paragraph spacing: {describe_spacing_mode(paragraph_spacing_mode)}")
    log(f"Page size: {describe_page_size_preset(page_size_preset)}")
    log(
        f"Trim size: {layout_settings.trim_width_cm:.2f} x "
        f"{layout_settings.trim_height_cm:.2f} cm"
    )
    log(f"Margin preset: {describe_margin_preset(margin_preset)}")
    log(
        "Margins: "
        f"top {layout_settings.margin_top_cm:.2f}, "
        f"bottom {layout_settings.margin_bottom_cm:.2f}, "
        f"inside {layout_settings.margin_inside_cm:.2f}, "
        f"outside {layout_settings.margin_outside_cm:.2f} cm"
    )
    log(f"Export DOCX: {'Yes' if export_docx else 'No'}")
    log(f"Export Markdown: {'Yes' if export_markdown else 'No'}")
    log(f"Imposition mode: {imposition_mode}")
    log(f"Pages per signature: {imposed_pages_per_signature}")
    log(f"Binding direction: {binding_direction}")
    log(f"Max blank end pages: {max_end_padding}")

    result = process_epub_to_pdf(
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

    log(f"Detected title: {result.detected_title}")
    log(f"Detected author: {result.detected_author}")
    log(f"PDF created: {result.output_pdf}")

    if result.output_docx:
        log(f"DOCX created: {result.output_docx}")

    if result.output_markdown:
        log(f"Markdown created: {result.output_markdown}")

    return {
        "title": result.used_title,
        "author": result.used_author,
        "variant": variant,
        "variant_label": describe_variant(variant),
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
        "output_pdf": str(result.output_pdf),
        "output_docx": str(result.output_docx) if result.output_docx else "",
        "output_markdown": str(result.output_markdown) if result.output_markdown else "",
        "output_dir": str(result.output_dir),
    }
