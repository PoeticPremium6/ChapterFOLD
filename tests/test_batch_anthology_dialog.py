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


def test_batch_anthology_dialog_lists_epub_paths(tmp_path):
    _app()
    from chapterfold_app.gui.batch_anthology_dialog import BatchAnthologyDialog

    one = tmp_path / "one.epub"
    two = tmp_path / "two.epub"
    pdf = tmp_path / "ignored.pdf"
    one.touch()
    two.touch()
    pdf.touch()

    dialog = BatchAnthologyDialog([str(one), str(two), str(pdf)], default_output_dir=str(tmp_path))
    try:
        assert dialog.file_list.count() == 2
        assert dialog.paths() == [str(one), str(two)]
        assert dialog.output_dir_edit.text() == str(tmp_path)
    finally:
        dialog.close()
        dialog.deleteLater()


def test_batch_anthology_dialog_reorder_and_remove(tmp_path):
    _app()
    from chapterfold_app.gui.batch_anthology_dialog import BatchAnthologyDialog

    one = tmp_path / "one.epub"
    two = tmp_path / "two.epub"
    three = tmp_path / "three.epub"
    one.touch()
    two.touch()
    three.touch()

    dialog = BatchAnthologyDialog([str(one), str(two), str(three)], default_output_dir=str(tmp_path))
    try:
        dialog.file_list.setCurrentRow(1)
        dialog._move_selected_up()
        assert dialog.paths() == [str(two), str(one), str(three)]

        dialog._move_selected_down()
        assert dialog.paths() == [str(one), str(two), str(three)]

        dialog.file_list.setCurrentRow(1)
        dialog._remove_selected()
        assert dialog.paths() == [str(one), str(three)]
    finally:
        dialog.close()
        dialog.deleteLater()


def test_main_window_batch_result_text():
    _app()
    from chapterfold_app.gui.main_window import MainWindow

    window = MainWindow()
    try:
        text = window._build_results_text(
            {
                "input_type": "batch-anthology",
                "title": "My Anthology",
                "author": "Editor",
                "markdown_path": "/tmp/My Anthology - Anthology.md",
                "manifest_json_path": "/tmp/My Anthology - Anthology Manifest.json",
                "inputs": [
                    {"title": "Story One", "author": "A", "section_count": 2},
                    {"title": "Story Two", "author": "B", "section_count": 1},
                ],
                "warnings": [],
            }
        )

        assert "Input type: Batch anthology" in text
        assert "Story One by A" in text
        assert "Story Two by B" in text
    finally:
        window.close()
        window.deleteLater()
