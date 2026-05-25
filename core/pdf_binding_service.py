from __future__ import annotations

import inspect
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from core.impose_service import build_signature_settings, impose_pdf
from core.signature_exports import (
    calculate_signature_groups,
    write_signature_plan_json,
    write_signature_plan_markdown,
)


@dataclass
class PdfBindingResult:
    success: bool
    input_pdf: Path
    output_dir: Path
    interior_pdf: Path
    page_count: int
    output_files: list[Path] = field(default_factory=list)
    imposed_pdf: Path | None = None
    signature_plan_json: Path | None = None
    signature_plan_markdown: Path | None = None
    warnings: list[str] = field(default_factory=list)
    error: str | None = None


def safe_pdf_stem(path: Path) -> str:
    stem = path.stem.strip() or "book"
    for char in '<>:"/\\|?*':
        stem = stem.replace(char, "-")
    return " ".join(stem.split())


def count_pdf_pages(path: Path) -> int:
    reader = PdfReader(str(path))
    return len(reader.pages)


def copy_pdf_as_interior(input_pdf: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_pdf_stem(input_pdf)} - Interior.pdf"
    shutil.copy2(input_pdf, output_path)
    return output_path


def _call_impose_pdf_compat(*, input_pdf: Path, output_pdf: Path, signature_settings: Any) -> Any:
    """Call impose_pdf while tolerating minor local signature differences."""
    sig = inspect.signature(impose_pdf)
    params = sig.parameters

    kwargs: dict[str, Any] = {}

    for name in params:
        if name in {"input_pdf", "input_pdf_path", "source_pdf", "source_pdf_path", "src_pdf"}:
            kwargs[name] = input_pdf
        elif name in {"output_pdf", "output_pdf_path", "target_pdf", "target_pdf_path", "dst_pdf"}:
            kwargs[name] = output_pdf
        elif name in {"settings", "signature_settings", "impose_settings"}:
            kwargs[name] = signature_settings

    if len(kwargs) == len(params):
        return impose_pdf(**kwargs)

    # Fallback for the most likely positional shape.
    return impose_pdf(input_pdf, output_pdf, signature_settings)


def process_pdf_for_binding(
    input_pdf: str | Path,
    output_dir: str | Path,
    *,
    create_imposed_pdf: bool = False,
    pages_per_signature: int = 16,
    binding_direction: str = "ltr",
    max_end_padding: int | None = None,
) -> PdfBindingResult:
    input_pdf = Path(input_pdf)
    output_dir = Path(output_dir)

    if input_pdf.suffix.lower() != ".pdf":
        raise ValueError("Input file must be a .pdf file.")
    if not input_pdf.exists():
        raise FileNotFoundError(f"Input PDF does not exist: {input_pdf}")

    output_dir.mkdir(parents=True, exist_ok=True)

    page_count = count_pdf_pages(input_pdf)
    interior_pdf = copy_pdf_as_interior(input_pdf, output_dir)

    result = PdfBindingResult(
        success=True,
        input_pdf=input_pdf,
        output_dir=output_dir,
        interior_pdf=interior_pdf,
        page_count=page_count,
        output_files=[interior_pdf],
    )

    if not create_imposed_pdf:
        return result

    signature_settings = build_signature_settings(
        pages_per_signature=pages_per_signature,
        binding_direction=binding_direction,
        max_end_padding=max_end_padding,
    )

    imposed_pdf = output_dir / f"{safe_pdf_stem(input_pdf)} - Imposed.pdf"
    _call_impose_pdf_compat(
        input_pdf=interior_pdf,
        output_pdf=imposed_pdf,
        signature_settings=signature_settings,
    )

    groups = calculate_signature_groups(
        total_pages=page_count,
        pages_per_signature=pages_per_signature,
    )

    plan_json = write_signature_plan_json(
        output_path=output_dir / f"{safe_pdf_stem(input_pdf)} - Signature Plan.json",
        total_pages=page_count,
        pages_per_signature=pages_per_signature,
        groups=groups,
    )
    plan_md = write_signature_plan_markdown(
        output_path=output_dir / f"{safe_pdf_stem(input_pdf)} - Signature Plan.md",
        title=safe_pdf_stem(input_pdf),
        total_pages=page_count,
        pages_per_signature=pages_per_signature,
        groups=groups,
    )

    result.imposed_pdf = imposed_pdf
    result.signature_plan_json = plan_json
    result.signature_plan_markdown = plan_md
    result.output_files.extend([imposed_pdf, plan_json, plan_md])

    return result
