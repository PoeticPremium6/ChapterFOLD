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


def test_main_window_has_page_number_start_selector():
    _app()
    from chapterfold_app.gui.main_window import MainWindow

    window = MainWindow()
    try:
        assert hasattr(window, "page_number_start_combo")
        values = [window.page_number_start_combo.itemData(i) for i in range(window.page_number_start_combo.count())]
        assert values == ["after-title-page", "main-text", "first-page", "none"]
    finally:
        window.close()
        window.deleteLater()
