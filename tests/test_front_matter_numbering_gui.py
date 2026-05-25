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


def test_main_window_has_front_matter_number_selector():
    _app()
    from chapterfold_app.gui.main_window import MainWindow

    window = MainWindow()
    try:
        assert hasattr(window, "front_matter_numbers_combo")
        values = [window.front_matter_numbers_combo.itemData(i) for i in range(window.front_matter_numbers_combo.count())]
        assert values == ["hidden", "roman-lower", "roman-upper", "arabic"]
    finally:
        window.close()
        window.deleteLater()
