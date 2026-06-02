from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.engine_api import EngineJobResult, run_engine_job, run_pdf_engine_job


def test_engine_result_is_json_serializable():
    result = EngineJobResult(
        success=True,
        stage="complete",
        input_path="input.pdf",
        output_dir="out",
        input_type="pdf",
        output_files=["out/book.pdf"],
    )

    data = json.loads(result.to_json())

    assert data["success"] is True
    assert data["input_type"] == "pdf"
    assert data["output_files"] == ["out/book.pdf"]


def test_engine_rejects_unsupported_extension(tmp_path):
    bad = tmp_path / "book.txt"
    bad.write_text("hello", encoding="utf-8")

    result = run_engine_job(
        input_path=bad,
        output_dir=tmp_path / "out",
        write_reports=False,
    )

    assert result.success is False
    assert result.user_error
    assert result.user_error["code"] == "unsupported_file_type"


def test_pdf_engine_job_runs_binding_only(tmp_path):
    source = Path("tests/fixtures/pdf/simple-binding.pdf")
    out = tmp_path / "pdf-engine"

    result = run_pdf_engine_job(
        input_pdf=source,
        output_dir=out,
        settings={
            "create_imposed_pdf": False,
            "pages_per_signature": 16,
            "binding_direction": "ltr",
        },
        write_reports=True,
    )

    assert result.success is True
    assert result.input_type == "pdf"
    assert result.stage == "complete"
    assert result.conversion_report_json
    assert Path(result.conversion_report_json).exists()
    assert result.manual_qa_log
    assert Path(result.manual_qa_log).exists()
    assert any(path.endswith("Interior.pdf") for path in result.output_files)


def test_pdf_engine_job_runs_rtl_imposition(tmp_path):
    source = Path("tests/fixtures/pdf/simple-binding.pdf")
    out = tmp_path / "pdf-engine-rtl"

    result = run_pdf_engine_job(
        input_pdf=source,
        output_dir=out,
        settings={
            "create_imposed_pdf": True,
            "pages_per_signature": 16,
            "binding_direction": "rtl",
        },
        write_reports=True,
    )

    assert result.success is True
    assert result.input_type == "pdf"
    assert any(path.endswith("Imposed.pdf") for path in result.output_files)


def test_engine_api_rejects_wrong_pdf_suffix(tmp_path):
    source = tmp_path / "not-a-pdf.txt"
    source.write_text("hello", encoding="utf-8")

    result = run_engine_job(
        input_path=source,
        output_dir=tmp_path / "out",
        write_reports=False,
    )

    assert result.success is False
    assert result.user_error
    assert result.user_error["code"] == "unsupported_file_type"


def test_run_engine_job_can_create_workspace_for_pdf(tmp_path):
    source = Path("tests/fixtures/pdf/simple-binding.pdf")
    workspace_root = tmp_path / "jobs"

    result = run_engine_job(
        input_path=source,
        workspace_root=workspace_root,
        settings={
            "create_imposed_pdf": False,
            "pages_per_signature": 16,
            "binding_direction": "ltr",
        },
        write_reports=True,
        job_id="TEST123",
    )

    assert result.success is True
    assert result.input_type == "pdf"
    assert "simple-binding-test123" in result.output_dir
    assert Path(result.output_dir).exists()
    assert result.report_json
    assert Path(result.report_json).exists()
    assert result.conversion_report_json
    assert Path(result.conversion_report_json).exists()


def test_run_engine_job_requires_output_or_workspace(tmp_path):
    source = Path("tests/fixtures/pdf/simple-binding.pdf")

    with pytest.raises(ValueError, match="output_dir is required"):
        run_engine_job(
            input_path=source,
            write_reports=False,
        )


def test_run_engine_job_can_validate_web_settings_for_pdf(tmp_path):
    source = Path("tests/fixtures/pdf/simple-binding.pdf")

    result = run_engine_job(
        input_path=source,
        output_dir=tmp_path / "validated-settings",
        settings={
            "create_imposed_pdf": "true",
            "imposed_pages_per_signature": "16",
            "binding_direction": "rtl",
        },
        validate_settings=True,
        write_reports=False,
    )

    assert result.success is True
    assert result.payload["input_type"] == "pdf"
    assert any(path.endswith("Imposed.pdf") for path in result.output_files)


def test_run_engine_job_returns_user_error_for_bad_web_setting(tmp_path):
    source = Path("tests/fixtures/pdf/simple-binding.pdf")

    result = run_engine_job(
        input_path=source,
        output_dir=tmp_path / "bad-settings",
        settings={"binding_direction": "sideways"},
        validate_settings=True,
        write_reports=False,
    )

    assert result.success is False
    assert result.user_error
    assert result.user_error["code"] in {"conversion_failed", "invalid_binding_direction"}
    assert "binding_direction" in result.error or "Invalid value" in result.error
