from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from core.engine_errors import friendly_error_from_exception
from core.job import run_chapterfold_job as _legacy_run_chapterfold_job
from core.schemas import ChapterfoldJobInput, ChapterfoldSettings
from core.job_workspace import create_job_workspace, safe_slug, validate_input_file
from core.job_manifest import build_job_manifest, write_job_manifest
from core.job_stages import normalize_job_stage
from core.pdf_binding_service import process_pdf_for_binding
from core.settings_catalog import validate_web_settings
from core.product_hardening import (
    build_conversion_report,
    write_conversion_report,
    write_manual_qa_log_template,
)


def _chapterfold_settings_from_worker_settings(settings):
    """Convert web/worker settings into the legacy EPUB ChapterfoldSettings model."""
    if settings is None:
        return ChapterfoldSettings()

    if isinstance(settings, ChapterfoldSettings):
        return settings

    if not isinstance(settings, dict):
        return settings

    allowed = set(getattr(ChapterfoldSettings, "__dataclass_fields__", {}).keys())
    payload = {key: value for key, value in settings.items() if key in allowed}

    if (
        "imposed_pages_per_signature" in allowed
        and "imposed_pages_per_signature" not in payload
        and "pages_per_signature" in settings
    ):
        payload["imposed_pages_per_signature"] = settings["pages_per_signature"]

    return ChapterfoldSettings(**payload)


def run_chapterfold_job(*args, **kwargs):
    """Compatibility wrapper for the worker-safe engine API.

    core.job.run_chapterfold_job expects ChapterfoldJobInput, while the newer
    engine boundary may call it with explicit input_epub/output_dir/settings.
    """
    if "input_epub" in kwargs:
        input_epub = Path(kwargs.pop("input_epub"))
        output_dir = Path(kwargs.pop("output_dir"))
        settings = _chapterfold_settings_from_worker_settings(kwargs.pop("settings", None))

        job = ChapterfoldJobInput(
            input_epub=input_epub,
            output_dir=output_dir,
            settings=settings,
        )
        return _legacy_run_chapterfold_job(job)

    return _legacy_run_chapterfold_job(*args, **kwargs)


@dataclass
class EngineJobResult:
    """Web/CLI-safe result object for ChapterFOLD engine jobs."""

    success: bool
    stage: str
    input_path: str
    output_dir: str
    input_type: str
    output_files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error: str | None = None
    user_error: dict[str, Any] | None = None
    job_id: str | None = None
    report_json: str | None = None
    conversion_report_json: str | None = None
    manual_qa_log: str | None = None
    manifest_json: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


def _normalize_payload(payload: Any) -> dict[str, Any]:
    if payload is None:
        return {"success": False, "stage": "unknown", "error": "No result payload returned."}

    if isinstance(payload, dict):
        return dict(payload)

    if hasattr(payload, "to_dict"):
        data = payload.to_dict()
        if isinstance(data, dict):
            return data

    if hasattr(payload, "__dict__"):
        return dict(vars(payload))

    return {
        "success": False,
        "stage": "unknown",
        "error": f"Unsupported result payload type: {type(payload).__name__}",
    }


def _write_engine_reports(
    *,
    payload: dict[str, Any],
    input_path: str | Path,
    output_dir: str | Path,
    input_type: str,
    settings: dict[str, Any] | None = None,
) -> tuple[str | None, str | None]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    conversion_report = build_conversion_report(
        payload=payload,
        input_path=input_path,
        output_dir=output_dir,
        input_type=input_type,
        settings=settings or {},
    )
    conversion_report_path = write_conversion_report(conversion_report, output_dir)
    qa_log_path = write_manual_qa_log_template(output_dir)

    return str(conversion_report_path), str(qa_log_path)


def _engine_result_from_payload(
    *,
    payload: dict[str, Any],
    input_path: str | Path,
    output_dir: str | Path,
    input_type: str,
    report_json: str | Path | None = None,
    settings: dict[str, Any] | None = None,
    write_reports: bool = True,
) -> EngineJobResult:
    conversion_report_json: str | None = None
    manual_qa_log: str | None = None

    if write_reports:
        conversion_report_json, manual_qa_log = _write_engine_reports(
            payload=payload,
            input_path=input_path,
            output_dir=output_dir,
            input_type=input_type,
            settings=settings,
        )

    return EngineJobResult(
        success=bool(payload.get("success", False)),
        stage=normalize_job_stage(str(payload.get("stage", "")), success=bool(payload.get("success", False))),
        input_path=str(input_path),
        output_dir=str(output_dir),
        input_type=input_type,
        output_files=[str(path) for path in payload.get("output_files", [])],
        warnings=list(payload.get("warnings") or []),
        error=payload.get("error"),
        user_error=payload.get("user_error"),
        job_id=payload.get("job_id"),
        report_json=str(report_json) if report_json else None,
        conversion_report_json=conversion_report_json,
        manual_qa_log=manual_qa_log,
        manifest_json=None,
        payload=payload,
    )


def _failed_engine_result_from_exception(
    *,
    exc: BaseException,
    input_path: str | Path,
    output_dir: str | Path,
    input_type: str,
    stage: str = "validate",
) -> EngineJobResult:
    user_error = friendly_error_from_exception(exc)
    payload = {
        "success": False,
        "stage": stage,
        "input_type": input_type,
        "input_path": str(input_path),
        "output_dir": str(output_dir),
        "output_files": [],
        "warnings": [],
        "error": str(exc),
        "user_error": {
            "code": user_error.code,
            "message": user_error.message,
            "detail": user_error.detail,
            "retryable": user_error.retryable,
        },
    }

    return EngineJobResult(
        success=False,
        stage=normalize_job_stage(stage, success=False),
        input_path=str(input_path),
        output_dir=str(output_dir),
        input_type=input_type,
        output_files=[],
        warnings=[],
        error=str(exc),
        user_error=payload["user_error"],
        payload=payload,
    )


def _pdf_binding_settings_from_web_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Return only settings accepted by process_pdf_for_binding()."""

    allowed = {
        "create_imposed_pdf",
        "pages_per_signature",
        "binding_direction",
        "max_end_padding",
    }

    adapted = dict(settings)

    if "imposed_pages_per_signature" in adapted and "pages_per_signature" not in adapted:
        adapted["pages_per_signature"] = adapted.pop("imposed_pages_per_signature")

    return {key: value for key, value in adapted.items() if key in allowed}


def run_epub_engine_job(
    *,
    input_epub: str | Path,
    output_dir: str | Path,
    settings: dict[str, Any] | None = None,
    report_json: str | Path | None = None,
    write_reports: bool = True,
    validate_settings: bool = False,
) -> EngineJobResult:
    """Run the EPUB-to-book engine through a web-safe API boundary."""

    settings = dict(settings or {})
    if validate_settings:
        settings = validate_web_settings(settings)
    input_epub = Path(input_epub)
    validate_input_file(input_epub, allowed_suffixes={".epub"})
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = run_chapterfold_job(
        input_epub=input_epub,
        output_dir=output_dir,
        report_json=report_json,
        **settings,
    )
    payload = _normalize_payload(payload)

    return _engine_result_from_payload(
        payload=payload,
        input_path=input_epub,
        output_dir=output_dir,
        input_type="epub",
        report_json=report_json,
        settings=settings,
        write_reports=write_reports,
    )


def run_pdf_engine_job(
    *,
    input_pdf: str | Path,
    output_dir: str | Path,
    settings: dict[str, Any] | None = None,
    report_json: str | Path | None = None,
    write_reports: bool = True,
    validate_settings: bool = False,
) -> EngineJobResult:
    """Run the PDF binding/imposition engine through a web-safe API boundary."""

    settings = dict(settings or {})
    if validate_settings:
        settings = validate_web_settings(settings)
    input_pdf = Path(input_pdf)
    validate_input_file(input_pdf, allowed_suffixes={".pdf"})
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    settings = _pdf_binding_settings_from_web_settings(settings)

    result = process_pdf_for_binding(
        input_pdf=input_pdf,
        output_dir=output_dir,
        **settings,
    )

    payload = {
        "success": True,
        "stage": "complete",
        "input_type": "pdf",
        "input_pdf": str(input_pdf),
        "output_dir": str(output_dir),
        "page_count": result.page_count,
        "output_files": [str(path) for path in result.output_files],
        "interior_pdf": str(result.interior_pdf) if result.interior_pdf else "",
        "imposed_pdf": str(result.imposed_pdf) if result.imposed_pdf else "",
        "signature_plan_json": str(result.signature_plan_json) if result.signature_plan_json else "",
        "signature_plan_markdown": str(result.signature_plan_markdown) if result.signature_plan_markdown else "",
        "warnings": list(result.warnings or []),
        "error": None,
    }

    if report_json:
        Path(report_json).parent.mkdir(parents=True, exist_ok=True)
        Path(report_json).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return _engine_result_from_payload(
        payload=payload,
        input_path=input_pdf,
        output_dir=output_dir,
        input_type="pdf",
        report_json=report_json,
        settings=settings,
        write_reports=write_reports,
    )


def run_engine_job(
    *,
    input_path: str | Path,
    output_dir: str | Path | None = None,
    settings: dict[str, Any] | None = None,
    report_json: str | Path | None = None,
    write_reports: bool = True,
    workspace_root: str | Path | None = None,
    job_id: str | None = None,
    validate_settings: bool = False,
) -> EngineJobResult:
    """Dispatch a ChapterFOLD engine job based on file extension.

    If workspace_root is provided, an isolated job workspace is created and
    its output folder is used. This is intended for future web worker jobs.
    """

    input_path = Path(input_path)
    suffix = input_path.suffix.lower()
    manifest_json_path: Path | None = None

    if workspace_root is not None:
        workspace = create_job_workspace(
            workspace_root,
            job_id=job_id,
            label=safe_slug(input_path.stem, fallback="chapterfold"),
        )
        output_dir = workspace.output_dir
        manifest_json_path = workspace.reports_dir / "job_manifest.json"
        if report_json is None:
            report_json = workspace.reports_dir / "job_result.json"
    elif output_dir is None:
        raise ValueError("output_dir is required when workspace_root is not provided")

    try:
        if suffix == ".epub":
            result = run_epub_engine_job(
                input_epub=input_path,
                output_dir=output_dir,
                settings=settings,
                report_json=report_json,
                write_reports=write_reports,
                validate_settings=validate_settings,
            )
            if manifest_json_path is not None:
                manifest = build_job_manifest(
                    job_id=job_id or Path(output_dir).parent.name,
                    input_path=input_path,
                    output_dir=output_dir,
                    input_type="epub",
                    settings=dict(settings or {}),
                    result=result,
                )
                result.manifest_json = str(write_job_manifest(manifest, manifest_json_path))
            return result

        if suffix == ".pdf":
            result = run_pdf_engine_job(
                input_pdf=input_path,
                output_dir=output_dir,
                settings=settings,
                report_json=report_json,
                write_reports=write_reports,
                validate_settings=validate_settings,
            )
            if manifest_json_path is not None:
                manifest = build_job_manifest(
                    job_id=job_id or Path(output_dir).parent.name,
                    input_path=input_path,
                    output_dir=output_dir,
                    input_type="pdf",
                    settings=dict(settings or {}),
                    result=result,
                )
                result.manifest_json = str(write_job_manifest(manifest, manifest_json_path))
            return result

        raise ValueError(f"Unsupported input type for ChapterFOLD engine: {input_path.suffix}")

    except Exception as exc:
        result = _failed_engine_result_from_exception(
            exc=exc,
            input_path=input_path,
            output_dir=output_dir,
            input_type=suffix.lstrip(".") or "unknown",
            stage="validate",
        )
        if manifest_json_path is not None:
            manifest = build_job_manifest(
                job_id=job_id or Path(output_dir).parent.name,
                input_path=input_path,
                output_dir=output_dir,
                input_type=suffix.lstrip(".") or "unknown",
                settings=dict(settings or {}),
                result=result,
            )
            result.manifest_json = str(write_job_manifest(manifest, manifest_json_path))
        return result

# --- Worker result report compatibility guard ---
_run_engine_job_impl = run_engine_job


def _ensure_worker_result_report(result):
    """Ensure worker/API calls always materialize job_result.json when reported."""
    from pathlib import Path as _Path
    import json as _json

    report_json = getattr(result, "report_json", None)

    if not report_json:
        manifest_json = getattr(result, "manifest_json", None)
        if manifest_json:
            report_json = str(_Path(manifest_json).with_name("job_result.json"))
            try:
                result.report_json = report_json
            except Exception:
                pass

    if report_json:
        report_path = _Path(report_json)
        if not report_path.exists():
            report_path.parent.mkdir(parents=True, exist_ok=True)

            if hasattr(result, "to_json"):
                payload = result.to_json()
            elif hasattr(result, "to_dict"):
                payload = _json.dumps(result.to_dict(), indent=2, sort_keys=True)
            else:
                payload = _json.dumps(result, indent=2, sort_keys=True, default=str)

            report_path.write_text(payload + "\n", encoding="utf-8")

    return result


def run_engine_job(*args, **kwargs):
    result = _run_engine_job_impl(*args, **kwargs)
    return _ensure_worker_result_report(result)

