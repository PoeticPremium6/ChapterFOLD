from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_preflight_script_exists():
    assert (ROOT / "scripts" / "preflight_check.py").exists()


def test_preflight_script_helpful_output():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "preflight_check.py")],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    assert "ChapterFOLD preflight check" in proc.stdout
    assert "core.schemas" in proc.stdout
    assert proc.returncode == 0
