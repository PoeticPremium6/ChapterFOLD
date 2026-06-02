from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.job_manifest import JobManifest, load_job_manifest


@dataclass(frozen=True)
class CleanupCandidate:
    path: Path
    reason: str
    age_hours: float
    status: str | None = None


@dataclass(frozen=True)
class CleanupResult:
    root: Path
    dry_run: bool
    candidates: list[CleanupCandidate]
    deleted: list[Path]
    errors: dict[str, str]


def _parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _age_hours(path: Path, *, now: datetime) -> float:
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return max(0.0, (now - modified).total_seconds() / 3600)


def _manifest_for_job_dir(job_dir: Path) -> JobManifest | None:
    manifest_path = job_dir / "reports" / "job_manifest.json"
    if not manifest_path.exists():
        return None
    try:
        return load_job_manifest(manifest_path)
    except Exception:
        return None


def find_cleanup_candidates(
    root: str | Path,
    *,
    max_age_hours: float = 72,
    failed_max_age_hours: float = 24,
    include_completed: bool = False,
    now: datetime | None = None,
) -> list[CleanupCandidate]:
    """Find job directories that are old enough to remove.

    Failed jobs can have a shorter retention period than completed jobs.
    Completed jobs are preserved unless include_completed=True.
    """

    root_path = Path(root)
    if not root_path.exists():
        return []

    current = now or datetime.now(timezone.utc)
    candidates: list[CleanupCandidate] = []

    for job_dir in root_path.iterdir():
        if not job_dir.is_dir():
            continue

        manifest = _manifest_for_job_dir(job_dir)
        status = manifest.status if manifest else None

        updated = _parse_utc(manifest.updated_at_utc if manifest else None)
        if updated is not None:
            age = max(0.0, (current - updated).total_seconds() / 3600)
        else:
            age = _age_hours(job_dir, now=current)

        if status == "failed" and age >= failed_max_age_hours:
            candidates.append(
                CleanupCandidate(
                    path=job_dir,
                    reason="failed job exceeded retention window",
                    age_hours=age,
                    status=status,
                )
            )
            continue

        if status == "complete" and include_completed and age >= max_age_hours:
            candidates.append(
                CleanupCandidate(
                    path=job_dir,
                    reason="completed job exceeded retention window",
                    age_hours=age,
                    status=status,
                )
            )
            continue

        if status not in {"complete", "failed"} and age >= max_age_hours:
            candidates.append(
                CleanupCandidate(
                    path=job_dir,
                    reason="non-terminal job exceeded retention window",
                    age_hours=age,
                    status=status,
                )
            )

    return candidates


def cleanup_job_workspaces(
    root: str | Path,
    *,
    max_age_hours: float = 72,
    failed_max_age_hours: float = 24,
    include_completed: bool = False,
    dry_run: bool = True,
) -> CleanupResult:
    """Delete old job workspaces, or report what would be deleted."""

    root_path = Path(root)
    candidates = find_cleanup_candidates(
        root_path,
        max_age_hours=max_age_hours,
        failed_max_age_hours=failed_max_age_hours,
        include_completed=include_completed,
    )

    deleted: list[Path] = []
    errors: dict[str, str] = {}

    if not dry_run:
        for candidate in candidates:
            try:
                shutil.rmtree(candidate.path)
                deleted.append(candidate.path)
            except Exception as exc:
                errors[str(candidate.path)] = f"{exc.__class__.__name__}: {exc}"

    return CleanupResult(
        root=root_path,
        dry_run=dry_run,
        candidates=candidates,
        deleted=deleted,
        errors=errors,
    )
