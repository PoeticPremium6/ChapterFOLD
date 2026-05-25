from __future__ import annotations

from pathlib import Path

from chapterfold_app.gui.markdown_tools import _latest_markdown_from_main_window


class DummyWindow:
    pass


def test_latest_markdown_from_payload_output_files(tmp_path):
    md = tmp_path / "Book - Editable.md"
    md.write_text("# Book", encoding="utf-8")

    window = DummyWindow()
    window._last_payload = {"output_files": [str(tmp_path / "Book.pdf"), str(md)]}

    assert _latest_markdown_from_main_window(window) == md


def test_latest_markdown_from_direct_attr(tmp_path):
    md = tmp_path / "Book.md"
    md.write_text("# Book", encoding="utf-8")

    window = DummyWindow()
    window.output_markdown = str(md)

    assert _latest_markdown_from_main_window(window) == md
