from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path


WORKER_SAFE_FILES = [
    Path("core/engine_api.py"),
    Path("core/job_workspace.py"),
    Path("core/job_manifest.py"),
    Path("core/job_stages.py"),
    Path("core/job_cleanup.py"),
    Path("core/engine_errors.py"),
    Path("core/settings_catalog.py"),
    Path("scripts/run_engine_job.py"),
]

BANNED_IMPORT_PREFIXES = (
    "PySide6",
    "chapterfold_app",
)


def _imports_from_file(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return imports


def test_worker_safe_files_do_not_import_gui_modules() -> None:
    failures: list[str] = []

    for path in WORKER_SAFE_FILES:
        assert path.exists(), f"Missing expected worker-safe file: {path}"

        for imported in _imports_from_file(path):
            if imported.startswith(BANNED_IMPORT_PREFIXES):
                failures.append(f"{path}: imports {imported}")

    assert not failures, "GUI dependencies found in worker-safe files:\n" + "\n".join(failures)


def test_engine_api_import_does_not_load_gui_modules() -> None:
    code = """
import sys
import core.engine_api
bad = [
    name for name in sys.modules
    if name == 'PySide6'
    or name.startswith('PySide6.')
    or name == 'chapterfold_app'
    or name.startswith('chapterfold_app.')
]
if bad:
    raise SystemExit('GUI modules loaded during engine_api import: ' + ', '.join(sorted(bad)))
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
