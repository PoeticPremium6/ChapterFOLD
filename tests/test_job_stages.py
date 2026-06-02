from __future__ import annotations

from core.job_stages import (
    is_terminal_stage,
    job_stage_catalog,
    normalize_job_stage,
)


def test_normalize_job_stage_accepts_known_stage():
    assert normalize_job_stage("validating") == "validating"


def test_normalize_job_stage_maps_legacy_stage_names():
    assert normalize_job_stage("validate") == "validating"
    assert normalize_job_stage("run_processing") == "rendering"


def test_normalize_job_stage_uses_success_for_terminal_state():
    assert normalize_job_stage("anything", success=True) == "complete"
    assert normalize_job_stage("", success=False) == "failed"


def test_terminal_stage_detection():
    assert is_terminal_stage("complete") is True
    assert is_terminal_stage("failed") is True
    assert is_terminal_stage("rendering") is False


def test_job_stage_catalog_is_web_friendly():
    catalog = job_stage_catalog()
    values = {item["value"] for item in catalog}

    assert "queued" in values
    assert "complete" in values
    assert all("label" in item for item in catalog)
