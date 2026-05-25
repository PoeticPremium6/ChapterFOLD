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


def test_main_window_pdf_mode_disables_epub_only_controls():
    _app()
    from chapterfold_app.gui.main_window import MainWindow

    window = MainWindow()
    try:
        window.input_edit.setText("/tmp/example.pdf")
        window._sync_input_mode()

        assert window.process_btn.text() == "Process PDF"
        assert not window.variant_combo.isEnabled()
        assert not window.export_docx_btn.isEnabled()
        assert not window.export_markdown_btn.isEnabled()
        assert not window.spacing_mode_combo.isEnabled()
        assert not window.contents_mode_combo.isEnabled()
        assert not window.font_combo.isEnabled()

        assert window.imposition_mode_combo.isEnabled()
        assert window.signature_pages_combo.isEnabled()
        assert window.binding_direction_combo.isEnabled()
    finally:
        window.close()
        window.deleteLater()


def test_main_window_epub_mode_enables_epub_controls():
    _app()
    from chapterfold_app.gui.main_window import MainWindow

    window = MainWindow()
    try:
        window.input_edit.setText("/tmp/example.epub")
        window._sync_input_mode()

        assert window.process_btn.text() == "Process EPUB"
        assert window.variant_combo.isEnabled()
        assert window.export_docx_btn.isEnabled()
        assert window.export_markdown_btn.isEnabled()
        assert window.spacing_mode_combo.isEnabled()
        assert window.contents_mode_combo.isEnabled()
        assert window.font_combo.isEnabled()
    finally:
        window.close()
        window.deleteLater()


def test_pdf_result_text_is_binding_only():
    _app()
    from chapterfold_app.gui.main_window import MainWindow

    window = MainWindow()
    try:
        text = window._build_results_text(
            {
                "input_type": "pdf",
                "input_pdf": "in.pdf",
                "interior_pdf": "out/Interior.pdf",
                "page_count": 12,
                "create_imposed_pdf": True,
                "imposed_output_pdf": "out/Imposed.pdf",
                "imposed_pages_per_signature": 16,
                "binding_direction_label": "LTR",
                "max_end_padding_label": "Default",
                "signature_plan_markdown": "out/Signature Plan.md",
            }
        )

        assert "Input type: PDF" in text
        assert "binding/imposition only" in text
        assert "Interior.pdf" in text
        assert "Imposed.pdf" in text
        assert "does not run EPUB cleanup" in text
    finally:
        window.close()
        window.deleteLater()


def test_pdf_mode_defaults_to_imposed_output():
    _app()
    from chapterfold_app.gui.main_window import MainWindow

    window = MainWindow()
    try:
        none_index = window.imposition_mode_combo.findData("none")
        window.imposition_mode_combo.setCurrentIndex(none_index)

        window.input_edit.setText("/tmp/example.pdf")
        window._sync_input_mode()

        assert window.imposition_mode_combo.currentData() == "also"
        assert "PDF mode" in window.status_label.text()
    finally:
        window.close()
        window.deleteLater()


def test_pdf_result_payload_text_has_openable_paths_without_modal_success_dialog():
    _app()
    from chapterfold_app.gui.main_window import MainWindow

    window = MainWindow()
    try:
        payload = {
            "input_type": "pdf",
            "output_dir": "/tmp/out",
            "output_pdf": "/tmp/out/book - Interior.pdf",
            "interior_pdf": "/tmp/out/book - Interior.pdf",
            "imposed_output_pdf": "/tmp/out/book - Imposed.pdf",
            "signature_plan_markdown": "/tmp/out/book - Signature Plan.md",
            "signature_batches_markdown": "",
            "preview_samples": [],
            "create_imposed_pdf": True,
            "imposed_pages_per_signature": 16,
            "binding_direction_label": "LTR",
            "max_end_padding_label": "Default",
        }

        text = window._build_results_text(payload)

        assert "Input type: PDF" in text
        assert "book - Interior.pdf" in text
        assert "book - Imposed.pdf" in text
        assert "book - Signature Plan.md" in text
    finally:
        window.close()
        window.deleteLater()
