from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox, QComboBox,
    QDialog,
    QFileDialog, QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class MarkdownRenderDialog(QDialog):
    """Small GUI workflow for Issue #22: edit Markdown, then render it back.

    The dialog deliberately calls scripts/render_markdown_book.py instead of
    duplicating rendering code. This keeps the GUI path aligned with the tested
    CLI path added in Patch 015.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Render Edited Markdown")
        self.resize(760, 520)

        self.markdown_path = QLineEdit()
        self.markdown_path.setPlaceholderText("Select a ChapterFOLD Editable.md file...")

        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholderText("Select an output folder...")

        self.export_docx = QCheckBox, QComboBox("Also export DOCX")
        self.export_docx.setChecked(False)

        choose_md = QPushButton("Choose Markdown…")
        choose_md.clicked.connect(self.choose_markdown)

        open_md = QPushButton("Open for Editing")
        open_md.clicked.connect(self.open_markdown)

        choose_out = QPushButton("Choose Output Folder…")
        choose_out.clicked.connect(self.choose_output_dir)

        render_btn = QPushButton("Render PDF")
        render_btn.clicked.connect(self.render_markdown)
        render_btn.setDefault(True)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Render output will appear here…")

        md_row = QHBoxLayout()
        md_row.addWidget(self.markdown_path, 1)
        md_row.addWidget(choose_md)
        md_row.addWidget(open_md)

        out_row = QHBoxLayout()
        out_row.addWidget(self.output_dir, 1)
        out_row.addWidget(choose_out)

        form = QFormLayout()
        form.addRow("Edited Markdown", md_row)
        form.addRow("Output Folder", out_row)
        form.addRow("Options", self.export_docx)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(render_btn)
        buttons.addWidget(close_btn)

        help_text = QLabel(
            "Workflow: convert an EPUB normally, open the generated Editable.md, "
            "make edits, then render that edited Markdown back into a printable PDF."
        )
        help_text.setWordWrap(True)
        help_text.setAlignment(Qt.AlignLeft)

        layout = QVBoxLayout(self)
        layout.addWidget(help_text)
        layout.addLayout(form)
        layout.addWidget(self.log, 1)
        layout.addLayout(buttons)

    def choose_markdown(self) -> None:
        path, _ = QFileDialog, QComboBox.getOpenFileName(
            self,
            "Choose edited Markdown file",
            str(Path.home()),
            "Markdown files (*.md *.markdown);;All files (*)",
        )
        if path:
            self.markdown_path.setText(path)
            if not self.output_dir.text().strip():
                default_out = Path(path).with_suffix("").parent / f"{Path(path).stem}_rendered"
                self.output_dir.setText(str(default_out))

    def choose_output_dir(self) -> None:
        path = QFileDialog, QComboBox.getExistingDirectory(
            self,
            "Choose output folder",
            str(Path.home()),
        )
        if path:
            self.output_dir.setText(path)

    def open_markdown(self) -> None:
        path = Path(self.markdown_path.text().strip())
        if not path.exists():
            QMessageBox.warning(self, "Markdown not found", "Choose an existing Markdown file first.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def render_markdown(self) -> None:
        md = Path(self.markdown_path.text().strip())
        out = Path(self.output_dir.text().strip())

        if not md.exists():
            QMessageBox.warning(self, "Markdown not found", "Choose an existing Markdown file first.")
            return
        if md.suffix.lower() not in {".md", ".markdown"}:
            QMessageBox.warning(self, "Expected Markdown", "Please choose a .md or .markdown file.")
            return
        if not out:
            QMessageBox.warning(self, "Output folder required", "Choose an output folder.")
            return

        root = Path(__file__).resolve().parents[2]
        script = root / "scripts" / "render_markdown_book.py"
        if not script.exists():
            QMessageBox.critical(self, "Renderer missing", f"Could not find {script}")
            return

        cmd = [sys.executable, str(script), str(md), str(out)]
        if self.export_docx.isChecked():
            cmd.append("--docx")

        self.log.append("COMMAND:\n" + " ".join(cmd) + "\n")
        out.mkdir(parents=True, exist_ok=True)

        env = dict(os.environ)
        env["PYTHONPATH"] = str(root) + os.pathsep + env.get("PYTHONPATH", "")

        result = subprocess.run(cmd, text=True, capture_output=True, cwd=root, env=env)
        if result.stdout:
            self.log.append("STDOUT:\n" + result.stdout)
        if result.stderr:
            self.log.append("STDERR:\n" + result.stderr)

        if result.returncode == 0:
            QMessageBox.information(self, "Render complete", f"Rendered files to:\n{out}")
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(out)))
        else:
            QMessageBox.critical(
                self,
                "Render failed",
                "Markdown rendering failed. See the log in this window for details.",
            )


def launch_markdown_render_dialog(parent: QWidget | None = None) -> MarkdownRenderDialog:
    dialog = MarkdownRenderDialog(parent)
    dialog.show()
    return dialog
