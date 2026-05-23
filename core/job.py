
"""UI-independent ChapterFOLD job runner."""
from __future__ import annotations

import traceback
from pathlib import Path
from typing import List

from core.schemas import ChapterfoldJobInput, ChapterfoldJobResult


def _job_id(job: ChapterfoldJobInput) -> str | None:
    return getattr(job, "job_id", None)


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
        settings_dict = job.settings.to_dict()

        result = None
        call_errors: List[str] = []
        call_attempts = [
            lambda: run_processing(str(job.input_epub), str(job.output_dir), settings_dict),
            lambda: run_processing(job.input_epub, job.output_dir, job.settings),
            lambda: run_processing(input_epub=job.input_epub, output_dir=job.output_dir, settings=job.settings),
        ]

        for attempt in call_attempts:
            try:
                result = attempt()
                break
            except TypeError as exc:
                call_errors.append(str(exc))

        if result is None and call_errors:
            return ChapterfoldJobResult(
                success=False,
                error="Existing run_processing signature is not yet compatible with core.job. "
                + " | ".join(call_errors),
                stage=stage,
                job_id=_job_id(job),
            )

        output_files: List[Path] = []
        if isinstance(result, dict):
            for value in result.get("output_files", []) or []:
                output_files.append(Path(value))
            success = bool(result.get("success", True))
            warnings = list(result.get("warnings", []) or [])
            error = result.get("error")
        elif isinstance(result, (list, tuple)):
            output_files = [Path(p) for p in result]
            success = True
            warnings = []
            error = None
        else:
            output_files = sorted(job.output_dir.glob("*"))
            success = True
            warnings = []
            error = None

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
