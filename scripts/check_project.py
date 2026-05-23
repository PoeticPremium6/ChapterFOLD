#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def check_import(module: str) -> bool:
    ok = importlib.util.find_spec(module) is not None
    print(f"{module:20} {'OK' if ok else 'MISSING'}")
    return ok


def main() -> int:
    print("ChapterFOLD project check")
    print(f"Python: {sys.version.split()[0]}")
    print(f"OS:     {platform.platform()}")
    print(f"Root:   {ROOT}")
    print()

    required = [
        "bs4",
        "ebooklib",
        "lxml",
        "pypdf",
        "pytest",
        "docx",
        "PySide6",
        "core.schemas",
        "core.job",
        "core.diagnostics",
    ]
    optional_native = ["weasyprint"]

    missing = [module for module in required if not check_import(module)]
    for module in optional_native:
        check_import(module)

    print()
    if missing:
        print("Missing required packages/modules. Try:")
        print("  python -m pip install --default-timeout=300 -r requirements.txt")
        return 1

    print("Running tests...")
    return subprocess.call([sys.executable, "-m", "pytest", "-q"], cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())

# Patch 005 dependency note: fastapi should import successfully for API prototype.

# Patch 005 dependency note: uvicorn should import successfully for API prototype.
