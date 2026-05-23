from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMainWindow

from chapterfold_app.gui.markdown_tools import install_markdown_render_action


def test_install_markdown_render_action_adds_tools_menu_action():
    app = QApplication.instance() or QApplication([])
    window = QMainWindow()

    assert install_markdown_render_action(window) is True
    assert install_markdown_render_action(window) is True

    action_texts = []
    for top_action in window.menuBar().actions():
        menu = top_action.menu()
        if menu:
            action_texts.extend(action.text().replace("&", "") for action in menu.actions())

    assert action_texts.count("Render Edited Markdown...") == 1
