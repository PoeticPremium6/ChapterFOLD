from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_pdf_worker_cli_smoke_creates_outputs_and_reports(tmp_path: Path) -> None:
    input_pdf = Path("tests/fixtures/pdf/simple-binding.pdf")
    assert input_pdf.exists(), "Missing PDF smoke fixture"

    settings_json = tmp_path / "settings.json"
    settings_json.write_text(
        json.dumps(
            {
                "create_imposed_pdf": True,
                "imposed_pages_per_signature": 16,
                "binding_direction": "ltr",
            }
        ),
        encoding="utf-8",
    )

    workspace_root = tmp_path / "jobs"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_engine_job.py",
            str(input_pdf),
            "--workspace-root",
            str(workspace_root),
            "--job-id",
            "pdf-worker-smoke",
            "--settings-json",
            str(settings_json),
            "--validate-settings",
        ],
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout

    payload = json.loads(result.stdout)
    assert payload["success"] is True
    assert payload["input_type"] == "pdf"
    assert payload["output_files"], payload

    output_files = [Path(path) for path in payload["output_files"]]
    assert any(path.name.endswith("- Interior.pdf") for path in output_files)
    assert any(path.name.endswith("- Imposed.pdf") for path in output_files)

    manifest_json = Path(payload["manifest_json"])
    job_result_json = Path(payload["report_json"])

    assert manifest_json.exists(), payload
    assert job_result_json.exists(), payload

    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    job_result = json.loads(job_result_json.read_text(encoding="utf-8"))

    assert manifest["status"] == "complete"
    assert manifest["stage"] == "complete"
    assert manifest["output_files"]

    assert job_result["success"] is True
    assert job_result["output_files"]
