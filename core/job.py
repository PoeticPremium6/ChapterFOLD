"""UI-independent ChapterFOLD job runner.

This module adapts the shared CLI/API job schema to the existing desktop
runner. The desktop runner currently exposes a keyword-only run_processing(...)
function, so positional calls will fail. Keep this adapter thin and conservative.
"""
from __future__ import annotations

import inspect
import traceback
from pathlib import Path
from typing import Any

from core.schemas import ChapterfoldJobInput, ChapterfoldJobResult


def _job_id(job: ChapterfoldJobInput) -> str | None:
    return getattr(job, "job_id", None)


def _runner_kwargs(job: ChapterfoldJobInput) -> dict[str, Any]:
    settings = job.settings
    signature_pages = (
        getattr(settings, "imposed_pages_per_signature", None)
        or getattr(settings, "signature_size", None)
        or 16
    )

    return {
        "input_epub": Path(job.input_epub),
        "output_dir": Path(job.output_dir),
        "variant": getattr(settings, "variant", "standard"),
        "export_docx": bool(getattr(settings, "export_docx", False)),
        "export_markdown": bool(getattr(settings, "export_markdown", False)),
        "paragraph_spacing_mode": getattr(settings, "paragraph_spacing_mode", "traditional"),
        "margin_preset": getattr(settings, "margin_preset", "standard"),
        "page_size_preset": getattr(settings, "page_size_preset", "default-trade"),
        "custom_trim_width_cm": getattr(settings, "custom_trim_width_cm", None),
        "custom_trim_height_cm": getattr(settings, "custom_trim_height_cm", None),
        "custom_margin_top_cm": getattr(settings, "custom_margin_top_cm", None),
        "custom_margin_bottom_cm": getattr(settings, "custom_margin_bottom_cm", None),
        "custom_margin_inside_cm": getattr(settings, "custom_margin_inside_cm", None),
        "custom_margin_outside_cm": getattr(settings, "custom_margin_outside_cm", None),
        "imposition_mode": "also" if bool(getattr(settings, "create_imposed_pdf", False)) else "none",
        "imposed_pages_per_signature": int(signature_pages),
        "binding_direction": getattr(settings, "binding_direction", "ltr"),
        "max_end_padding": getattr(settings, "max_end_padding", None),
        "log_callback": None,
    }


def _filter_kwargs_for_callable(func: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Pass only supported kwargs unless the callable accepts **kwargs."""
    try:
        signature = inspect.signature(func)
    except (TypeError, ValueError):
        return kwargs

    parameters = signature.parameters
    if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in parameters.values()):
        return kwargs
    return {key: value for key, value in kwargs.items() if key in parameters}


def _output_files_from_runner_result(result: Any, output_dir: Path) -> list[Path]:
    if isinstance(result, dict):
        files: list[Path] = []
        for key in (
            "output_pdf",
            "output_docx",
            "output_markdown",
            "imposed_output_pdf",
            "baseline_pdf",
        ):
            value = result.get(key)
            if value:
                files.append(Path(value))
        for value in result.get("output_files", []) or []:
            if value:
                files.append(Path(value))
        # Preserve order while de-duplicating.
        seen: set[str] = set()
        unique: list[Path] = []
        for path in files:
            key = str(path)
            if key not in seen:
                seen.add(key)
                unique.append(path)
        return unique

    if isinstance(result, (list, tuple)):
        return [Path(p) for p in result]

    return sorted(output_dir.glob("*"))


def run_chapterfold_job(job: ChapterfoldJobInput) -> ChapterfoldJobResult:
    """Run a ChapterFOLD conversion job without importing GUI modules."""

    stage = "validate"
    try:
        job.validate()

        stage = "import_runner"
        try:
            from chapterfold_app.services.chapterfold_runner import run_processing  # type: ignore
        except Exception as exc:  # pragma: no cover - depends on local app state
            return ChapterfoldJobResult(
                success=False,
                error=f"Could not import existing ChapterFOLD runner: {exc}",
                stage=stage,
                job_id=_job_id(job),
            )

        stage = "run_processing"
        kwargs = _filter_kwargs_for_callable(run_processing, _runner_kwargs(job))
        result = run_processing(**kwargs)

        output_files = _output_files_from_runner_result(result, Path(job.output_dir))
        warnings: list[str] = []
        error = None
        success = True

        if isinstance(result, dict):
            warnings = list(result.get("warnings", []) or [])
            error = result.get("error")
            success = bool(result.get("success", True)) and error in (None, "")

        return ChapterfoldJobResult(
            success=success,
            output_files=output_files,
            warnings=warnings,
            error=error,
            stage="complete",
            job_id=_job_id(job),
        )

    except Exception as exc:
        return ChapterfoldJobResult(
            success=False,
            error=f"{exc}\n\n{traceback.format_exc()}",
            stage=stage,
            job_id=_job_id(job),
        )
