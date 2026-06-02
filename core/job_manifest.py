from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.job_stages import normalize_job_stage


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class JobManifest:
    job_id: str
    status: str
    stage: str
    input_path: str
    output_dir: str
    input_type: str
    settings: dict[str, Any] = field(default_factory=dict)
    output_files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error: str | None = None
    user_error: dict[str, Any] | None = None
    created_at_utc: str = field(default_factory=utc_now_iso)
    updated_at_utc: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


def status_from_success(success: bool | None) -> str:
    if success is True:
        return "complete"
    if success is False:
        return "failed"
    return "pending"


def build_job_manifest(
    *,
    job_id: str,
    input_path: str | Path,
    output_dir: str | Path,
    input_type: str,
    settings: dict[str, Any] | None = None,
    result: Any | None = None,
    stage: str = "created",
    status: str | None = None,
) -> JobManifest:
    success = getattr(result, "success", None)
    normalized_stage = normalize_job_stage(str(getattr(result, "stage", stage)), success=success)
    resolved_status = status or status_from_success(success)

    return JobManifest(
        job_id=job_id,
        status=resolved_status,
        stage=normalized_stage,
        input_path=str(input_path),
        output_dir=str(output_dir),
        input_type=input_type,
        settings=dict(settings or {}),
        output_files=[str(path) for path in getattr(result, "output_files", [])],
        warnings=list(getattr(result, "warnings", []) or []),
        error=getattr(result, "error", None),
        user_error=getattr(result, "user_error", None),
    )


def write_job_manifest(
    manifest: JobManifest,
    path: str | Path,
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest.updated_at_utc = utc_now_iso()
    path.write_text(manifest.to_json(), encoding="utf-8")
    return path


def load_job_manifest(path: str | Path) -> JobManifest:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return JobManifest(**data)
