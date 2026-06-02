from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.job_cleanup import cleanup_job_workspaces, find_cleanup_candidates
from core.job_manifest import JobManifest


def _write_manifest(job_dir: Path, *, status: str, updated_at_utc: str):
    reports = job_dir / "reports"
    reports.mkdir(parents=True)

    manifest = JobManifest(
        job_id=job_dir.name,
        status=status,
        stage=status,
        input_path="input.pdf",
        output_dir=str(job_dir / "output"),
        input_type="pdf",
        updated_at_utc=updated_at_utc,
    )
    (reports / "job_manifest.json").write_text(manifest.to_json(), encoding="utf-8")


def test_find_cleanup_candidates_includes_old_failed_job(tmp_path):
    now = datetime.now(timezone.utc)
    job = tmp_path / "failed-job"
    job.mkdir()
    _write_manifest(
        job,
        status="failed",
        updated_at_utc=(now - timedelta(hours=30)).isoformat(timespec="seconds"),
    )

    candidates = find_cleanup_candidates(
        tmp_path,
        failed_max_age_hours=24,
        now=now,
    )

    assert len(candidates) == 1
    assert candidates[0].path == job
    assert candidates[0].status == "failed"


def test_find_cleanup_candidates_preserves_completed_by_default(tmp_path):
    now = datetime.now(timezone.utc)
    job = tmp_path / "complete-job"
    job.mkdir()
    _write_manifest(
        job,
        status="complete",
        updated_at_utc=(now - timedelta(hours=100)).isoformat(timespec="seconds"),
    )

    candidates = find_cleanup_candidates(
        tmp_path,
        max_age_hours=72,
        include_completed=False,
        now=now,
    )

    assert candidates == []


def test_find_cleanup_candidates_can_include_completed(tmp_path):
    now = datetime.now(timezone.utc)
    job = tmp_path / "complete-job"
    job.mkdir()
    _write_manifest(
        job,
        status="complete",
        updated_at_utc=(now - timedelta(hours=100)).isoformat(timespec="seconds"),
    )

    candidates = find_cleanup_candidates(
        tmp_path,
        max_age_hours=72,
        include_completed=True,
        now=now,
    )

    assert len(candidates) == 1
    assert candidates[0].path == job


def test_cleanup_job_workspaces_dry_run_does_not_delete(tmp_path):
    now = datetime.now(timezone.utc)
    job = tmp_path / "failed-job"
    job.mkdir()
    _write_manifest(
        job,
        status="failed",
        updated_at_utc=(now - timedelta(hours=30)).isoformat(timespec="seconds"),
    )

    result = cleanup_job_workspaces(
        tmp_path,
        failed_max_age_hours=24,
        dry_run=True,
    )

    assert len(result.candidates) == 1
    assert result.deleted == []
    assert job.exists()


def test_cleanup_job_workspaces_deletes_when_not_dry_run(tmp_path):
    now = datetime.now(timezone.utc)
    job = tmp_path / "failed-job"
    job.mkdir()
    _write_manifest(
        job,
        status="failed",
        updated_at_utc=(now - timedelta(hours=30)).isoformat(timespec="seconds"),
    )

    result = cleanup_job_workspaces(
        tmp_path,
        failed_max_age_hours=24,
        dry_run=False,
    )

    assert len(result.candidates) == 1
    assert result.deleted == [job]
    assert not job.exists()
