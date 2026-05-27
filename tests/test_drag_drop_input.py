from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QUrl

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _app():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv[:1])
    return app


def test_drop_path_line_edit_accepts_epub_and_pdf_paths(tmp_path):
    _app()
    from chapterfold_app.gui.main_window import DropPathLineEdit

    epub = tmp_path / "book.epub"
    pdf = tmp_path / "book.pdf"
    txt = tmp_path / "notes.txt"

    epub.touch()
    pdf.touch()
    txt.touch()

    assert DropPathLineEdit.accepted_path_from_urls([QUrl.fromLocalFile(str(epub))]) == str(epub)
    assert DropPathLineEdit.accepted_path_from_urls([QUrl.fromLocalFile(str(pdf))]) == str(pdf)
    assert DropPathLineEdit.accepted_path_from_urls([QUrl.fromLocalFile(str(txt))]) == ""


def test_main_window_uses_drop_path_input_widget():
    _app()
    from chapterfold_app.gui.main_window import DropPathLineEdit, MainWindow

    window = MainWindow()
    try:
        assert isinstance(window.input_edit, DropPathLineEdit)
        assert window.input_edit.acceptDrops()
    finally:
        window.close()
        window.deleteLater()


def test_dragged_pdf_path_triggers_pdf_mode(tmp_path):
    _app()
    from chapterfold_app.gui.main_window import DropPathLineEdit, MainWindow

    pdf = tmp_path / "book.pdf"
    pdf.touch()

    window = MainWindow()
    try:
        path = DropPathLineEdit.accepted_path_from_urls([QUrl.fromLocalFile(str(pdf))])
        window.input_edit.setText(path)
        window._sync_input_mode()

        assert window.process_btn.text() == "Process PDF"
        assert not window.variant_combo.isEnabled()
        assert window.imposition_mode_combo.isEnabled()
    finally:
        window.close()
        window.deleteLater()
