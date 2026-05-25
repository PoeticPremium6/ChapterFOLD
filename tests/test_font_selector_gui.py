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


def test_main_window_has_font_selector():
    _app()
    from chapterfold_app.gui.main_window import MainWindow

    window = MainWindow()
    try:
        assert hasattr(window, "font_combo")
        values = [window.font_combo.itemData(i) for i in range(window.font_combo.count())]
        labels = [window.font_combo.itemText(i) for i in range(window.font_combo.count())]

        assert "classic-serif" in values
        assert "unicode-global" in values
        assert "cjk-serif" in values
        assert "caveat" in values
        assert "dancing-script" in values
        assert any("traditional English classics" in label for label in labels)
        assert any("playful short editions" in label for label in labels)
    finally:
        window.close()
        window.deleteLater()


def test_font_choices_render_samples():
    from core.font_catalog import FONT_CHOICES

    samples = {choice.key: choice.sample for choice in FONT_CHOICES}
    assert "Pride" in samples["classic-serif"]
    assert "你好" in samples["unicode-global"]
    assert "Caveat" in samples["caveat"]
