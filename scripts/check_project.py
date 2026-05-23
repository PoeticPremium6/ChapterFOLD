#!/usr/bin/env python3
from __future__ import annotations

import importlib
import platform
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


REQUIRED_IMPORTS = [
    ("bs4", "bs4"),
    ("ebooklib", "ebooklib"),
    ("lxml", "lxml"),
    ("pypdf", "pypdf"),
    ("pytest", "pytest"),
    ("docx", "docx"),
    ("PySide6", "PySide6"),
    ("core.schemas", "core.schemas"),
    ("core.job", "core.job"),
    ("core.diagnostics", "core.diagnostics"),
    ("core.gutenberg_selector", "core.gutenberg_selector"),
    ("core.gutenberg_content_filter", "core.gutenberg_content_filter"),
    ("core.gutenberg_inline_trim", "core.gutenberg_inline_trim"),
    ("weasyprint", "weasyprint"),
]


def check_imports() -> bool:
    ok = True
    for label, module_name in REQUIRED_IMPORTS:
        try:
            importlib.import_module(module_name)
            print(f"{label:<32} OK")
        except Exception as exc:
            ok = False
            print(f"{label:<32} FAIL: {exc}")
    return ok


def run_tests() -> int:
    print("\nRunning tests...")
    return subprocess.call([sys.executable, "-m", "pytest"], cwd=ROOT)


def main() -> int:
    print("ChapterFOLD project check")
    print(f"Python: {platform.python_version()}")
    print(f"OS:     {platform.platform()}")
    print(f"Root:   {ROOT}")
    print()

    imports_ok = check_imports()
    if not imports_ok:
        return 1

    return run_tests()


if __name__ == "__main__":
    raise SystemExit(main())
