from __future__ import annotations

import os
import sys

from PySide6.QtCore import QUrl

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _app():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv[:1])
    return app


def test_drop_markdown_line_edit_accepts_markdown_paths(tmp_path):
    _app()
    from chapterfold_app.gui.markdown_render_dialog import DropMarkdownLineEdit

    md = tmp_path / "book.md"
    markdown = tmp_path / "book.markdown"
    txt = tmp_path / "book.txt"
    pdf = tmp_path / "book.pdf"

    for path in [md, markdown, txt, pdf]:
        path.touch()

    assert DropMarkdownLineEdit.accepted_path_from_urls([QUrl.fromLocalFile(str(md))]) == str(md)
    assert DropMarkdownLineEdit.accepted_path_from_urls([QUrl.fromLocalFile(str(markdown))]) == str(markdown)
    assert DropMarkdownLineEdit.accepted_path_from_urls([QUrl.fromLocalFile(str(txt))]) == str(txt)
    assert DropMarkdownLineEdit.accepted_path_from_urls([QUrl.fromLocalFile(str(pdf))]) == ""


def test_markdown_render_dialog_uses_drop_markdown_input(tmp_path):
    _app()
    from chapterfold_app.gui.markdown_render_dialog import DropMarkdownLineEdit, MarkdownRenderDialog

    md = tmp_path / "Editable.md"
    md.write_text("# Test\\n", encoding="utf-8")

    dialog = MarkdownRenderDialog()
    try:
        assert isinstance(dialog.markdown_path, DropMarkdownLineEdit)

        dialog.set_markdown_path(md)

        assert dialog.markdown_path.text() == str(md)
        assert dialog.output_dir.text().endswith("Editable_rendered")
        assert "Editable.md" in dialog.windowTitle()
    finally:
        dialog.close()
        dialog.deleteLater()
