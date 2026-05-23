# Manual GUI integration for diagnostics

Patch 002 created `core/diagnostics.py`, but could not safely patch the GUI automatically.

Add something like this inside your main window class:

```python
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMessageBox
from core.diagnostics import build_diagnostic_report


def _copy_diagnostic_report(self):
    report = build_diagnostic_report(app_version="unknown", stage="manual GUI report")
    QApplication.clipboard().setText(report)
    QMessageBox.information(self, "ChapterFOLD", "Diagnostic report copied to clipboard.")
```

Then add a Help menu action:

```python
help_menu = self.menuBar().addMenu("Help")
diagnostic_action = QAction("Copy diagnostic report", self)
diagnostic_action.triggered.connect(self._copy_diagnostic_report)
help_menu.addAction(diagnostic_action)
```

This gives users a quick way to copy system/package/settings information when reporting bugs.
