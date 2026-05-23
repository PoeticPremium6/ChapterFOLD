#!/usr/bin/env python3
"""Print a ChapterFOLD diagnostic report from the command line."""
from __future__ import annotations

import sys
from pathlib import Path

# Allow direct execution from repo root: python scripts/<script>.py
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.diagnostics import build_diagnostic_report


if __name__ == "__main__":
    print(build_diagnostic_report(stage="command-line diagnostics"))
