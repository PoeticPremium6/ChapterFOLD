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


def test_cli_scripts_expose_chapter_ornament_flag():
    for script in ["scripts/run_chapterfold_job.py", "scripts/run_chapterfold_input_job.py"]:
        text = open(script, encoding="utf-8").read()
        assert "--chapter-ornament" in text
        assert "poetic-vine" in text
        assert "bookbinder-rule" in text


def test_main_window_has_chapter_ornament_selector():
    _app()
    from chapterfold_app.gui.main_window import MainWindow

    window = MainWindow()
    try:
        assert hasattr(window, "chapter_ornament_combo")
        values = [
            window.chapter_ornament_combo.itemData(i)
            for i in range(window.chapter_ornament_combo.count())
        ]
        assert values == [
            "none",
            "classic-rule",
            "botanical-divider",
            "poetic-vine",
            "moon-garden",
            "rose-window",
            "bookbinder-rule",
        ]
    finally:
        window.close()
        window.deleteLater()


def test_result_text_can_show_chapter_ornament():
    _app()
    from chapterfold_app.gui.main_window import MainWindow

    window = MainWindow()
    try:
        text = window._build_results_text(
            {
                "success": True,
                "input_type": "epub",
                "page_ornament": "poetic-vine",
                "page_ornament_amount": "balanced",
                "chapter_ornament": "rose-window",
                "output_files": [],
                "warnings": [],
            }
        )
        assert "Chapter ornament: rose-window" in text
    finally:
        window.close()
        window.deleteLater()
