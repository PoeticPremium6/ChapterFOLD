from __future__ import annotations

import json
from pathlib import Path

from tests.test_batch_anthology_service import build_tiny_epub
from scripts.run_batch_anthology import main as anthology_cli_main


def test_batch_anthology_cli_outputs_markdown_and_report(tmp_path):
    one = tmp_path / "one.epub"
    two = tmp_path / "two.epub"
    out = tmp_path / "out"
    report = tmp_path / "report.json"

    build_tiny_epub(one, title="Story One", author="Author A", body="First story body.")
    build_tiny_epub(two, title="Story Two", author="Author B", body="Second story body.")

    exit_code = anthology_cli_main(
        [
            str(one),
            str(two),
            "--output-dir",
            str(out),
            "--title",
            "Dropped Stories",
            "--author",
            "Editor",
            "--report-json",
            str(report),
        ]
    )

    assert exit_code == 0
    data = json.loads(report.read_text(encoding="utf-8"))

    assert data["success"]
    assert data["input_type"] == "batch-anthology"
    assert data["title"] == "Dropped Stories"
    assert len(data["inputs"]) == 2

    markdown_path = Path(data["markdown_path"])
    assert markdown_path.exists()

    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# Dropped Stories" in markdown
    assert "- Story One" in markdown
    assert "- Story Two" in markdown
    assert "First story body." in markdown
    assert "Second story body." in markdown
