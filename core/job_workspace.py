from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from pathlib import Path


SUPPORTED_INPUT_SUFFIXES = {".epub", ".pdf", ".md", ".markdown"}
DEFAULT_MAX_INPUT_SIZE_MB = 100


@dataclass(frozen=True)
class ValidatedInput:
    path: Path
    suffix: str
    size_bytes: int
    size_mb: float


@dataclass(frozen=True)
class JobWorkspace:
    root: Path
    job_id: str
    job_dir: Path
    input_dir: Path
    output_dir: Path
    reports_dir: Path


def safe_slug(value: str, *, fallback: str = "chapterfold-job") -> str:
    """Return a filesystem-safe slug suitable for job folders and filenames."""

    cleaned = value.strip().lower()
    cleaned = re.sub(r"[^a-z0-9._-]+", "-", cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    cleaned = cleaned.strip("-._")

    return cleaned or fallback


def validate_input_file(
    path: str | Path,
    *,
    allowed_suffixes: set[str] | None = None,
    max_size_mb: int | float = DEFAULT_MAX_INPUT_SIZE_MB,
) -> ValidatedInput:
    """Validate a user/job input file before processing."""

    input_path = Path(path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    if not input_path.is_file():
        raise ValueError(f"Input path is not a file: {input_path}")

    suffix = input_path.suffix.lower()
    allowed = allowed_suffixes or SUPPORTED_INPUT_SUFFIXES

    if suffix not in allowed:
        allowed_list = ", ".join(sorted(allowed))
        raise ValueError(f"Unsupported input file type: {suffix or '[none]'}. Expected one of: {allowed_list}")

    size_bytes = input_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)

    if size_mb > float(max_size_mb):
        raise ValueError(
            f"Input file is too large: {size_mb:.1f} MB. "
            f"Maximum allowed size is {float(max_size_mb):.1f} MB."
        )

    return ValidatedInput(
        path=input_path,
        suffix=suffix,
        size_bytes=size_bytes,
        size_mb=size_mb,
    )


def create_job_workspace(
    root: str | Path,
    *,
    job_id: str | None = None,
    label: str | None = None,
) -> JobWorkspace:
    """Create an isolated job workspace with input/output/report folders."""

    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)

    job_token = job_id or uuid.uuid4().hex
    prefix = safe_slug(label or "chapterfold")
    final_job_id = f"{prefix}-{safe_slug(job_token, fallback=uuid.uuid4().hex)}"

    job_dir = root_path / final_job_id
    input_dir = job_dir / "input"
    output_dir = job_dir / "output"
    reports_dir = job_dir / "reports"

    for directory in [input_dir, output_dir, reports_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    return JobWorkspace(
        root=root_path,
        job_id=final_job_id,
        job_dir=job_dir,
        input_dir=input_dir,
        output_dir=output_dir,
        reports_dir=reports_dir,
    )


def ensure_child_path(parent: str | Path, child: str | Path) -> Path:
    """Ensure child resolves inside parent, preventing path traversal."""

    parent_path = Path(parent).resolve()
    child_path = Path(child).resolve()

    if parent_path == child_path or parent_path in child_path.parents:
        return child_path

    raise ValueError(f"Path escapes allowed directory: {child}")
