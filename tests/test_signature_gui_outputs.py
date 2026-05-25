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


def test_main_window_has_signature_output_buttons():
    _app()
    from chapterfold_app.gui.main_window import MainWindow

    window = MainWindow()
    try:
        assert hasattr(window, "open_signature_plan_btn")
        assert hasattr(window, "open_signature_batches_btn")
        assert window.open_signature_plan_btn.text() == "Open Signature Plan"
        assert window.open_signature_batches_btn.text() == "Open Signature Batches"
    finally:
        window.close()
        window.deleteLater()
