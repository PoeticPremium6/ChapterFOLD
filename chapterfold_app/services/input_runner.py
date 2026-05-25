from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

from core.schemas import ChapterfoldSettings
from core.pdf_binding_service import process_pdf_for_binding
from chapterfold_app.services.chapterfold_runner import run_processing


def detect_input_kind(path: str | Path) -> str:
    suffix = Path(path).suffix.lower()
    if suffix == ".epub":
        return "epub"
    if suffix == ".pdf":
        return "pdf"
    raise ValueError("Input file must be an .epub or .pdf file.")


def _payload_from_pdf_result(result) -> dict[str, Any]:
    return {
        "success": result.success,
        "input_type": "pdf",
        "input_pdf": str(result.input_pdf),
        "output_dir": str(result.output_dir),
        "page_count": result.page_count,
        "output_files": [str(path) for path in result.output_files],
        "interior_pdf": str(result.interior_pdf),
        "imposed_pdf": str(result.imposed_pdf) if result.imposed_pdf else "",
        "signature_plan_json": str(result.signature_plan_json) if result.signature_plan_json else "",
        "signature_plan_markdown": str(result.signature_plan_markdown) if result.signature_plan_markdown else "",
        "warnings": result.warnings,
        "error": result.error,
        "stage": "complete" if result.success else "error",
    }


def _filtered_run_processing_kwargs(input_path: Path, output_dir: Path, settings: ChapterfoldSettings) -> dict[str, Any]:
    raw = {
        "input_epub": input_path,
        "output_dir": output_dir,
        "variant": settings.variant,
        "export_docx": settings.export_docx,
        "export_markdown": settings.export_markdown,
        "paragraph_spacing_mode": settings.paragraph_spacing_mode,
        "contents_mode": getattr(settings, "contents_mode", "rebuild"),
        "page_number_start_mode": getattr(settings, "page_number_start_mode", "after-title-page"),
        "front_matter_page_number_style": getattr(settings, "front_matter_page_number_style", "hidden"),
        "page_size_preset": settings.page_size_preset,
        "custom_trim_width_cm": settings.custom_trim_width_cm,
        "custom_trim_height_cm": settings.custom_trim_height_cm,
        "margin_preset": settings.margin_preset,
        "custom_margin_top_cm": settings.custom_margin_top_cm,
        "custom_margin_bottom_cm": settings.custom_margin_bottom_cm,
        "custom_margin_inside_cm": settings.custom_margin_inside_cm,
        "custom_margin_outside_cm": settings.custom_margin_outside_cm,
        "imposition_mode": "also" if settings.create_imposed_pdf else "none",
        "imposed_pages_per_signature": settings.imposed_pages_per_signature,
        "binding_direction": settings.binding_direction,
        "max_end_padding": settings.max_end_padding,
        "output_font_key": getattr(settings, "output_font_key", "classic-serif"),
    }

    sig = inspect.signature(run_processing)
    return {key: value for key, value in raw.items() if key in sig.parameters}


def run_input_processing(
    input_path: str | Path,
    output_dir: str | Path,
    settings: ChapterfoldSettings,
) -> dict[str, Any]:
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    settings.validate()

    kind = detect_input_kind(input_path)

    if kind == "pdf":
        result = process_pdf_for_binding(
            input_path,
            output_dir,
            create_imposed_pdf=settings.create_imposed_pdf,
            pages_per_signature=int(settings.imposed_pages_per_signature or settings.signature_size),
            binding_direction=settings.binding_direction,
            max_end_padding=settings.max_end_padding,
        )
        return _payload_from_pdf_result(result)

    kwargs = _filtered_run_processing_kwargs(input_path, output_dir, settings)
    payload = run_processing(**kwargs)
    if isinstance(payload, dict):
        payload.setdefault("input_type", "epub")
    return payload
