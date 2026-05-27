from __future__ import annotations

import json
from pathlib import Path

from core.product_hardening import (
    artifact_from_path,
    build_conversion_report,
    write_conversion_report,
    write_manual_qa_log_template,
    write_sample_gallery_manifest,
)


def test_artifact_from_path_records_existing_file(tmp_path):
    output = tmp_path / "book.pdf"
    output.write_bytes(b"pdf")

    artifact = artifact_from_path(output, label="Interior PDF")

    assert artifact.label == "Interior PDF"
    assert artifact.exists is True
    assert artifact.size_bytes == 3


def test_build_conversion_report_records_outputs_and_environment(tmp_path):
    output = tmp_path / "book.pdf"
    output.write_bytes(b"pdf")

    report = build_conversion_report(
        payload={
            "success": True,
            "stage": "complete",
            "job_id": "abc",
            "output_files": [str(output)],
            "warnings": [],
            "error": None,
        },
        input_path="input.epub",
        output_dir=tmp_path,
        input_type="epub",
        settings={"variant": "standard"},
    )

    assert report.success is True
    assert report.input_type == "epub"
    assert report.artifacts[0].exists is True
    assert report.settings["variant"] == "standard"
    assert "python" in report.environment


def test_write_conversion_report(tmp_path):
    report = build_conversion_report(
        payload={"success": True, "stage": "complete", "output_files": []},
        input_path="input.epub",
        output_dir=tmp_path,
        input_type="epub",
    )

    path = write_conversion_report(report, tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["success"] is True
    assert data["stage"] == "complete"


def test_write_manual_qa_log_template(tmp_path):
    path = write_manual_qa_log_template(tmp_path)
    text = path.read_text(encoding="utf-8")

    assert "Manual QA Log" in text
    assert "Visual QA Checklist" in text
    assert "Page ornaments render correctly" in text
    assert "Chapter ornaments render correctly" in text


def test_write_sample_gallery_manifest(tmp_path):
    path = write_sample_gallery_manifest(
        tmp_path,
        [
            {
                "title": "Unicode Smoke",
                "before": "input.epub",
                "after": "output.pdf",
                "notes": "Basic multilingual fixture.",
            }
        ],
    )

    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["samples"][0]["title"] == "Unicode Smoke"
