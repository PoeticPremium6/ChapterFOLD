#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication

from chapterfold_app.gui.markdown_render_dialog import MarkdownRenderDialog


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    dialog = MarkdownRenderDialog()
    dialog.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
