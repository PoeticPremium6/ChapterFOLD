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


def test_main_window_has_page_ornament_selector():
    _app()
    from chapterfold_app.gui.main_window import MainWindow

    window = MainWindow()
    try:
        assert hasattr(window, "page_ornament_combo")
        assert hasattr(window, "page_ornament_amount_combo")

        values = [
            window.page_ornament_combo.itemData(i)
            for i in range(window.page_ornament_combo.count())
        ]

        assert "none" in values
        assert "classic-rule" in values
        assert "botanical-leaf" in values
        assert "floral-corner" in values
        assert "gothic-flourish" in values
        assert "storybook" in values

        amount_values = [
            window.page_ornament_amount_combo.itemData(i)
            for i in range(window.page_ornament_amount_combo.count())
        ]
        assert amount_values == ["subtle", "balanced", "ornate"]
    finally:
        window.close()
        window.deleteLater()


def test_page_ornament_result_text_displays_payload_value():
    _app()
    from chapterfold_app.gui.main_window import MainWindow

    window = MainWindow()
    try:
        text = window._build_results_text(
            {
                "success": True,
                "input_type": "epub",
                "page_number_start_mode": "after-title-page",
                "front_matter_page_number_style": "hidden",
                "page_ornament": "botanical-leaf",
                "output_files": [],
                "warnings": [],
            }
        )

        assert "Page ornament: botanical-leaf" in text
    finally:
        window.close()
        window.deleteLater()


def test_page_ornament_selector_promotes_signature_motifs():
    _app()
    from chapterfold_app.gui.main_window import MainWindow

    window = MainWindow()
    try:
        labels = [
            window.page_ornament_combo.itemText(i)
            for i in range(window.page_ornament_combo.count())
        ]

        assert labels[0] == "None"
        assert any(label.startswith("Signature — Poetic Vine") for label in labels[:8])
        assert any(label.startswith("Signature — Moon Garden") for label in labels[:8])
        assert any(label.startswith("Signature — Bookbinder") for label in labels[:8])
    finally:
        window.close()
        window.deleteLater()
