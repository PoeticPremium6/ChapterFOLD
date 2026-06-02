from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_run_engine_job_cli_help_runs():
    result = subprocess.run(
        [sys.executable, "scripts/run_engine_job.py", "--help"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "web-worker-safe API" in result.stdout


def test_run_engine_job_cli_pdf_workspace(tmp_path):
    settings = tmp_path / "settings.json"
    settings.write_text(
        json.dumps(
            {
                "create_imposed_pdf": "true",
                "imposed_pages_per_signature": "16",
                "binding_direction": "rtl",
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_engine_job.py",
            "tests/fixtures/pdf/simple-binding.pdf",
            "--workspace-root",
            str(tmp_path / "jobs"),
            "--job-id",
            "CLI123",
            "--settings-json",
            str(settings),
            "--validate-settings",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout

    payload = json.loads(result.stdout)
    assert payload["success"] is True
    assert payload["input_type"] == "pdf"
    assert payload["manifest_json"]
    assert Path(payload["manifest_json"]).exists()
    assert any(path.endswith("Imposed.pdf") for path in payload["output_files"])


def test_run_engine_job_cli_rejects_bad_settings(tmp_path):
    settings = tmp_path / "settings.json"
    settings.write_text(
        json.dumps({"binding_direction": "sideways"}),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_engine_job.py",
            "tests/fixtures/pdf/simple-binding.pdf",
            str(tmp_path / "out"),
            "--settings-json",
            str(settings),
            "--validate-settings",
            "--no-reports",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["success"] is False
    assert payload["user_error"]
