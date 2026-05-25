from __future__ import annotations

import importlib
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _app():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv[:1])
    return app


def test_markdown_render_dialog_imports():
    module = importlib.import_module("chapterfold_app.gui.markdown_render_dialog")
    assert hasattr(module, "MarkdownRenderDialog")


def test_markdown_render_dialog_can_be_constructed(tmp_path):
    _app()
    from chapterfold_app.gui.markdown_render_dialog import MarkdownRenderDialog

    md = tmp_path / "Edited.md"
    md.write_text("# Test Book\n\n## CHAPTER I.\n\nHello.", encoding="utf-8")

    dialog = MarkdownRenderDialog(initial_markdown_path=md)
    try:
        assert dialog.markdown_path.text() == str(md)
        assert dialog.output_dir.text().endswith("Edited_rendered")
        assert dialog.export_pdf.isChecked()
        assert not dialog.export_docx.isChecked()
    finally:
        dialog.close()
        dialog.deleteLater()


def test_markdown_render_dialog_toc_options():
    _app()
    from chapterfold_app.gui.markdown_render_dialog import MarkdownRenderDialog

    dialog = MarkdownRenderDialog()
    try:
        values = [dialog.toc_mode.itemData(i) for i in range(dialog.toc_mode.count())]
        assert values == ["keep", "remove", "rebuild"]
    finally:
        dialog.close()
        dialog.deleteLater()
