from __future__ import annotations

import os
import sys
from pathlib import Path


def configure_weasyprint_dlls() -> None:
    """
    Configure DLL lookup paths for WeasyPrint on Windows.

    Order:
    1. Existing WEASYPRINT_DLL_DIRECTORIES env var
    2. Bundled gtk_runtime folder inside packaged app
    3. Common local MSYS2 install path for development
    """
    existing = os.environ.get("WEASYPRINT_DLL_DIRECTORIES", "").strip()
    candidates: list[Path] = []

    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.append(exe_dir / "gtk_runtime")

    repo_local_msys = Path(r"C:\msys64\ucrt64\bin")
    candidates.append(repo_local_msys)

    valid_dirs: list[str] = []
    if existing:
        for part in existing.split(os.pathsep):
            part = part.strip()
            if part and Path(part).exists():
                valid_dirs.append(part)

    for candidate in candidates:
        if candidate.exists():
            value = str(candidate)
            if value not in valid_dirs:
                valid_dirs.append(value)

    if valid_dirs:
        os.environ["WEASYPRINT_DLL_DIRECTORIES"] = os.pathsep.join(valid_dirs)

        if hasattr(os, "add_dll_directory"):
            for dll_dir in valid_dirs:
                try:
                    os.add_dll_directory(dll_dir)
                except OSError:
                    pass


configure_weasyprint_dlls()

# Make the repo root importable so `core` can be found when running
# from inside chapterfold_app/.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("ChapterFOLD")
    app.setOrganizationName("ChapterFOLD")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
