from __future__ import annotations

from pathlib import Path

from core.engine_api import EngineJobResult, run_engine_job
from core.job_manifest import build_job_manifest, load_job_manifest, write_job_manifest


def test_job_manifest_round_trip(tmp_path):
    result = EngineJobResult(
        success=True,
        stage="complete",
        input_path="input.pdf",
        output_dir="out",
        input_type="pdf",
        output_files=["out/book.pdf"],
    )

    manifest = build_job_manifest(
        job_id="abc123",
        input_path="input.pdf",
        output_dir="out",
        input_type="pdf",
        settings={"binding_direction": "rtl"},
        result=result,
    )

    path = write_job_manifest(manifest, tmp_path / "job_manifest.json")
    loaded = load_job_manifest(path)

    assert loaded.job_id == "abc123"
    assert loaded.status == "complete"
    assert loaded.stage == "complete"
    assert loaded.settings["binding_direction"] == "rtl"
    assert loaded.output_files == ["out/book.pdf"]


def test_workspace_engine_job_writes_manifest(tmp_path):
    source = Path("tests/fixtures/pdf/simple-binding.pdf")

    result = run_engine_job(
        input_path=source,
        workspace_root=tmp_path / "jobs",
        job_id="JOB123",
        settings={
            "create_imposed_pdf": False,
            "pages_per_signature": 16,
            "binding_direction": "ltr",
        },
        write_reports=True,
    )

    assert result.success is True
    assert result.manifest_json
    manifest_path = Path(result.manifest_json)
    assert manifest_path.exists()

    manifest = load_job_manifest(manifest_path)
    assert manifest.status == "complete"
    assert manifest.input_type == "pdf"
    assert manifest.output_files
