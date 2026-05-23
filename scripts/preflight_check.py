#!/usr/bin/env python3
"""Run quick ChapterFOLD preflight checks before deeper manual testing."""

from __future__ import annotations

import importlib
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _status(name: str, ok: bool, detail: str = "") -> bool:
    mark = "OK" if ok else "FAIL"
    suffix = f" - {detail}" if detail else ""
    print(f"{name:<32} {mark}{suffix}")
    return ok


def check_import(module_name: str, import_name: str | None = None) -> bool:
    try:
        module = importlib.import_module(module_name)
        if import_name:
            getattr(module, import_name)
        return _status(module_name, True)
    except Exception as exc:
        return _status(module_name, False, str(exc))


def check_qt() -> bool:
    try:
        from PySide6.QtWidgets import QApplication
        if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
            os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])
        _ = app
        return _status("PySide6 QApplication", True)
    except Exception as exc:
        return _status("PySide6 QApplication", False, str(exc))


def check_cli_help() -> bool:
    script = ROOT / "scripts" / "run_chapterfold_job.py"
    if not script.exists():
        return _status("CLI runner help", False, "scripts/run_chapterfold_job.py missing")
    proc = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    ok = proc.returncode == 0 and "Run a ChapterFOLD EPUB conversion" in proc.stdout
    detail = "" if ok else (proc.stderr.strip() or proc.stdout.strip())[:300]
    return _status("CLI runner help", ok, detail)


def check_fixture_builder() -> bool:
    script = ROOT / "scripts" / "build_sample_epubs.py"
    if not script.exists():
        return _status("EPUB fixture builder", True, "not present yet; skipping")
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    ok = proc.returncode == 0
    detail = "" if ok else (proc.stderr.strip() or proc.stdout.strip())[:300]
    return _status("EPUB fixture builder", ok, detail)


def check_api_import() -> bool:
    api_file = ROOT / "api" / "main.py"
    if not api_file.exists():
        return _status("FastAPI app import", True, "not present yet; skipping")
    try:
        from api.main import app
        _ = app
        return _status("FastAPI app import", True)
    except Exception as exc:
        return _status("FastAPI app import", False, str(exc))


def main() -> int:
    print("ChapterFOLD preflight check")
    print("===========================")
    print(f"Python: {platform.python_version()}  ({sys.executable})")
    print(f"OS:     {platform.platform()}")
    print(f"Root:   {ROOT}")
    print()
    checks = [
        check_import("core.schemas", "ChapterfoldSettings"),
        check_import("core.job", "run_chapterfold_job"),
        check_import("core.diagnostics", "build_diagnostic_report"),
        check_import("ebooklib"),
        check_import("weasyprint"),
        check_import("pypdf"),
        check_import("docx"),
        check_import("bs4"),
        check_qt(),
        check_cli_help(),
        check_fixture_builder(),
        check_api_import(),
    ]
    print()
    if all(checks):
        print("Preflight passed. You can move on to focused conversion testing.")
        return 0
    print("Preflight failed. Fix the failing checks before deeper manual testing.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
