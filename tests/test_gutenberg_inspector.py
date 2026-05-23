from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_inspector_help_runs():
    result = subprocess.run(
        [sys.executable, "scripts/inspect_epub_structure.py", "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Inspect a Gutenberg EPUB" in result.stdout


def test_batch_inspector_help_runs():
    result = subprocess.run(
        [sys.executable, "scripts/inspect_gutenberg_batch.py", "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Inspect all EPUB" in result.stdout


def test_inspector_can_read_generated_fixture(tmp_path):
    subprocess.run([sys.executable, "scripts/build_sample_epubs.py"], check=True)
    fixture = Path("tests/fixtures/epubs/generated/scene-breaks.epub")
    assert fixture.exists()

    out_json = tmp_path / "scene_breaks.json"
    out_md = tmp_path / "scene_breaks.md"
    result = subprocess.run(
        [sys.executable, "scripts/inspect_epub_structure.py", str(fixture), str(out_json), "--markdown", str(out_md)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert out_json.exists()
    assert out_md.exists()
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data["html_item_count"] >= 1
    assert data["total_text_chars"] > 0
    assert "risk_flags" in data
