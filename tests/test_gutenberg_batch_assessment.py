from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_gutenberg_batch_assessment_help_runs():
    result = subprocess.run(
        [sys.executable, "scripts/assess_gutenberg_batch.py", "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Batch convert and assess Gutenberg EPUB outputs" in result.stdout


def test_gutenberg_batch_assessment_empty_dir_fails_cleanly(tmp_path):
    output_dir = tmp_path / "out"
    result = subprocess.run(
        [sys.executable, "scripts/assess_gutenberg_batch.py", str(tmp_path), str(output_dir), "--no-convert"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert "No EPUB files found" in result.stderr
