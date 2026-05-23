from __future__ import annotations

import importlib
import subprocess
import sys


def test_markdown_render_dialog_imports():
    module = importlib.import_module("chapterfold_app.gui.markdown_render_dialog")
    assert hasattr(module, "MarkdownRenderDialog")


def test_markdown_render_gui_launcher_help_imports():
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", "scripts/render_markdown_gui.py"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
