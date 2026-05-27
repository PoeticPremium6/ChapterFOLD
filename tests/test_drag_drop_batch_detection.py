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


def test_drop_path_line_edit_collects_multiple_supported_paths(tmp_path):
    _app()
    from chapterfold_app.gui.main_window import DropPathLineEdit

    epub = tmp_path / "story.epub"
    pdf = tmp_path / "book.pdf"
    txt = tmp_path / "notes.txt"

    epub.touch()
    pdf.touch()
    txt.touch()

    paths = DropPathLineEdit.accepted_paths_from_urls(
        [
            QUrl.fromLocalFile(str(epub)),
            QUrl.fromLocalFile(str(pdf)),
            QUrl.fromLocalFile(str(txt)),
        ]
    )

    assert paths == [str(epub), str(pdf)]


def test_main_window_has_batch_drop_handler():
    _app()
    from chapterfold_app.gui.main_window import MainWindow

    window = MainWindow()
    try:
        assert hasattr(window, "_handle_multiple_files_dropped")
    finally:
        window.close()
        window.deleteLater()
