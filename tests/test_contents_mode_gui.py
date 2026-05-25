from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _app():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv[:1])
    return app


def test_main_window_has_contents_mode_selector():
    _app()
    from chapterfold_app.gui.main_window import MainWindow

    window = MainWindow()
    try:
        assert hasattr(window, "contents_mode_combo")
        values = [window.contents_mode_combo.itemData(i) for i in range(window.contents_mode_combo.count())]
        assert values == ["rebuild", "rebuild-paged", "remove", "keep"]
    finally:
        window.close()
        window.deleteLater()
