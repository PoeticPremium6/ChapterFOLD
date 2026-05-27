from __future__ import annotations

import json
import platform
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class ConversionArtifact:
    label: str
    path: str
    exists: bool
    size_bytes: int | None = None


@dataclass
class ConversionReport:
    success: bool
    stage: str
    input_path: str
    output_dir: str
    input_type: str = "unknown"
    job_id: str | None = None
    warnings: list[str] = field(default_factory=list)
    error: str | None = None
    output_files: list[str] = field(default_factory=list)
    artifacts: list[ConversionArtifact] = field(default_factory=list)
    environment: dict[str, str] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)
    created_at_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


def artifact_from_path(path: str | Path, label: str | None = None) -> ConversionArtifact:
    p = Path(path)
    return ConversionArtifact(
        label=label or p.name,
        path=str(p),
        exists=p.exists(),
        size_bytes=p.stat().st_size if p.exists() else None,
    )


def build_environment_summary() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
    }


def build_conversion_report(
    *,
    payload: dict[str, Any],
    input_path: str | Path,
    output_dir: str | Path,
    input_type: str = "unknown",
    settings: dict[str, Any] | None = None,
) -> ConversionReport:
    output_files = [str(path) for path in payload.get("output_files", [])]
    artifacts = [artifact_from_path(path) for path in output_files]

    return ConversionReport(
        success=bool(payload.get("success", False)),
        stage=str(payload.get("stage", "")),
        input_path=str(input_path),
        output_dir=str(output_dir),
        input_type=input_type,
        job_id=payload.get("job_id"),
        warnings=list(payload.get("warnings") or []),
        error=payload.get("error"),
        output_files=output_files,
        artifacts=artifacts,
        environment=build_environment_summary(),
        settings=settings or {},
    )


def write_conversion_report(
    report: ConversionReport,
    output_dir: str | Path,
    *,
    filename: str = "conversion_report.json",
) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    path = output_dir / filename
    path.write_text(
        json.dumps(asdict(report), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def write_manual_qa_log_template(
    output_dir: str | Path,
    *,
    filename: str = "manual_qa_log.md",
) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    path = output_dir / filename
    if path.exists():
        return path

    path.write_text(
        """# ChapterFOLD Manual QA Log

## Build / Environment

- Date:
- OS:
- Python:
- ChapterFOLD version / commit:
- Input file:
- Output folder:

## Settings Checked

- Variant:
- Contents mode:
- Page numbers:
- Page ornament:
- Ornament amount:
- Chapter ornament:
- Page size:
- Margins:
- Imposition:

## Output Files

- Interior PDF:
- Editable Markdown:
- DOCX:
- Imposed PDF:
- Signature plan:

## Visual QA Checklist

- [ ] Title page looks correct.
- [ ] Contents page looks correct.
- [ ] First main-text chapter starts correctly.
- [ ] Page numbers start where expected.
- [ ] Front matter numbering is correct, if enabled.
- [ ] Page ornaments render correctly.
- [ ] Chapter ornaments render correctly.
- [ ] Images are retained where expected.
- [ ] Paragraph spacing and indentation are acceptable.
- [ ] Unicode/special characters render correctly.
- [ ] Final PDF opens without errors.
- [ ] DOCX opens without errors, if exported.
- [ ] Imposed PDF opens without errors, if exported.

## Notes

-

## Verdict

- [ ] Pass
- [ ] Pass with notes
- [ ] Fail
""",
        encoding="utf-8",
    )
    return path


def write_sample_gallery_manifest(
    output_dir: str | Path,
    samples: list[dict[str, Any]],
    *,
    filename: str = "sample_gallery_manifest.json",
) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    path = output_dir / filename
    path.write_text(
        json.dumps(
            {
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "samples": samples,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path
