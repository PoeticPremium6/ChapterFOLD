from __future__ import annotations

from PySide6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QPushButton, QWidget

from chapterfold_app.gui.markdown_tools import install_markdown_render_button, install_markdown_render_ui


def test_install_markdown_render_button_next_to_open_markdown():
    app = QApplication.instance() or QApplication([])
    window = QMainWindow()
    central = QWidget()
    layout = QHBoxLayout(central)
    layout.addWidget(QPushButton("Open Markdown"))
    window.setCentralWidget(central)

    assert install_markdown_render_button(window) is True
    assert install_markdown_render_button(window) is True

    labels = [button.text().replace("&", "") for button in window.findChildren(QPushButton)]
    assert "Render Edited Markdown" in labels


def test_install_markdown_render_ui_returns_true_on_plain_window():
    app = QApplication.instance() or QApplication([])
    window = QMainWindow()
    assert install_markdown_render_ui(window) is True
