from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
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
    """Render an edited ChapterFOLD Markdown file back into book outputs."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        initial_markdown_path: str | Path | None = None,
        initial_output_dir: str | Path | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("ChapterFOLD Markdown Studio")
        self.resize(860, 620)

        self.last_output_files: list[Path] = []
        self.last_output_dir: Path | None = None

        self.markdown_path = QLineEdit()
        self.markdown_path.setPlaceholderText("Select a ChapterFOLD Editable.md file...")

        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholderText("Select an output folder...")

        self.title_override = QLineEdit()
        self.title_override.setPlaceholderText("Optional; otherwise inferred from Markdown")

        self.author_override = QLineEdit()
        self.author_override.setPlaceholderText("Optional; otherwise inferred from Markdown")

        self.toc_mode = QComboBox()
        self.toc_mode.addItem("Keep existing TOC", "keep")
        self.toc_mode.addItem("Remove existing TOC", "remove")
        self.toc_mode.addItem("Rebuild TOC", "rebuild")
        self.toc_mode.setCurrentIndex(0)

        self.export_pdf = QCheckBox("Export PDF")
        self.export_pdf.setChecked(True)

        self.export_docx = QCheckBox("Export DOCX")
        self.export_docx.setChecked(False)

        self.copy_markdown = QCheckBox("Copy edited Markdown to output folder")
        self.copy_markdown.setChecked(True)

        self.choose_md_btn = QPushButton("Choose Markdown…")
        self.choose_md_btn.clicked.connect(self.choose_markdown)

        self.open_md_btn = QPushButton("Open for Editing")
        self.open_md_btn.clicked.connect(self.open_markdown)

        self.choose_out_btn = QPushButton("Choose Output Folder…")
        self.choose_out_btn.clicked.connect(self.choose_output_dir)

        self.render_btn = QPushButton("Render Markdown")
        self.render_btn.clicked.connect(self.render_markdown)
        self.render_btn.setDefault(True)

        self.open_output_btn = QPushButton("Open Output Folder")
        self.open_output_btn.clicked.connect(self.open_output_folder)
        self.open_output_btn.setEnabled(False)

        self.open_pdf_btn = QPushButton("Open PDF")
        self.open_pdf_btn.clicked.connect(self.open_latest_pdf)
        self.open_pdf_btn.setEnabled(False)

        self.open_docx_btn = QPushButton("Open DOCX")
        self.open_docx_btn.clicked.connect(self.open_latest_docx)
        self.open_docx_btn.setEnabled(False)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Markdown render log appears here…")

        self._build_layout()

        if initial_markdown_path:
            self.set_markdown_path(initial_markdown_path)
        if initial_output_dir:
            self.output_dir.setText(str(initial_output_dir))

    def _build_layout(self) -> None:
        help_text = QLabel(
            "Iterative workflow: convert EPUB → edit the generated Editable.md → "
            "render the edited Markdown back into PDF/DOCX without reprocessing the EPUB."
        )
        help_text.setWordWrap(True)
        help_text.setAlignment(Qt.AlignLeft)

        md_row = QHBoxLayout()
        md_row.addWidget(self.markdown_path, 1)
        md_row.addWidget(self.choose_md_btn)
        md_row.addWidget(self.open_md_btn)

        out_row = QHBoxLayout()
        out_row.addWidget(self.output_dir, 1)
        out_row.addWidget(self.choose_out_btn)

        form = QFormLayout()
        form.addRow("Edited Markdown", md_row)
        form.addRow("Output Folder", out_row)
        form.addRow("Title Override", self.title_override)
        form.addRow("Author Override", self.author_override)
        form.addRow("TOC Mode", self.toc_mode)

        options_box = QGroupBox("Outputs")
        options_layout = QGridLayout(options_box)
        options_layout.addWidget(self.export_pdf, 0, 0)
        options_layout.addWidget(self.export_docx, 0, 1)
        options_layout.addWidget(self.copy_markdown, 1, 0, 1, 2)

        action_row = QHBoxLayout()
        action_row.addWidget(self.open_output_btn)
        action_row.addWidget(self.open_pdf_btn)
        action_row.addWidget(self.open_docx_btn)
        action_row.addStretch(1)
        action_row.addWidget(self.render_btn)
        action_row.addWidget(self.close_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(help_text)
        layout.addLayout(form)
        layout.addWidget(options_box)
        layout.addWidget(self.log, 1)
        layout.addLayout(action_row)

    def set_markdown_path(self, path: str | Path) -> None:
        path = Path(path)
        self.markdown_path.setText(str(path))
        if not self.output_dir.text().strip():
            self.output_dir.setText(str(path.parent / f"{path.stem}_rendered"))

    def choose_markdown(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose edited Markdown file",
            str(Path.home()),
            "Markdown files (*.md *.markdown *.txt);;All files (*)",
        )
        if path:
            self.set_markdown_path(path)

    def choose_output_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(
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

    def open_output_folder(self) -> None:
        path = self.last_output_dir or Path(self.output_dir.text().strip())
        if not path.exists():
            QMessageBox.warning(self, "Output folder missing", "Render the Markdown first or choose an existing output folder.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _open_latest_by_suffix(self, suffixes: set[str], label: str) -> None:
        for path in self.last_output_files:
            if path.suffix.lower() in suffixes and path.exists():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
                return
        QMessageBox.warning(self, f"{label} missing", f"No rendered {label} file was found yet.")

    def open_latest_pdf(self) -> None:
        self._open_latest_by_suffix({".pdf"}, "PDF")

    def open_latest_docx(self) -> None:
        self._open_latest_by_suffix({".docx"}, "DOCX")

    def _validate(self) -> tuple[Path, Path] | None:
        md = Path(self.markdown_path.text().strip())
        out = Path(self.output_dir.text().strip())

        if not md.exists():
            QMessageBox.warning(self, "Markdown not found", "Choose an existing Markdown file first.")
            return None

        if md.suffix.lower() not in {".md", ".markdown", ".txt"}:
            QMessageBox.warning(self, "Expected Markdown", "Please choose a .md, .markdown, or .txt file.")
            return None

        if not str(out).strip():
            QMessageBox.warning(self, "Output folder required", "Choose an output folder.")
            return None

        if not self.export_pdf.isChecked() and not self.export_docx.isChecked() and not self.copy_markdown.isChecked():
            QMessageBox.warning(self, "No outputs selected", "Select at least one output type.")
            return None

        return md, out

    def render_markdown(self) -> None:
        validated = self._validate()
        if validated is None:
            return

        md, out = validated
        root = Path(__file__).resolve().parents[2]
        script = root / "scripts" / "render_markdown_book.py"

        if not script.exists():
            QMessageBox.critical(self, "Renderer missing", f"Could not find {script}")
            return

        cmd = [sys.executable, str(script), str(md), str(out)]

        title = self.title_override.text().strip()
        author = self.author_override.text().strip()
        if title:
            cmd.extend(["--title", title])
        if author:
            cmd.extend(["--author", author])

        if not self.export_pdf.isChecked():
            cmd.append("--no-pdf")
        if self.export_docx.isChecked():
            cmd.append("--docx")
        if not self.copy_markdown.isChecked():
            cmd.append("--no-copy-markdown")

        cmd.extend(["--toc-mode", str(self.toc_mode.currentData() or "keep")])

        report_json = out / "markdown_render_report.json"
        cmd.extend(["--report-json", str(report_json)])

        out.mkdir(parents=True, exist_ok=True)

        self.log.clear()
        self.log.append("COMMAND:\n" + " ".join(cmd) + "\n")

        env = dict(os.environ)
        env["PYTHONPATH"] = str(root) + os.pathsep + env.get("PYTHONPATH", "")

        self.render_btn.setEnabled(False)
        try:
            result = subprocess.run(cmd, text=True, capture_output=True, cwd=root, env=env)
        finally:
            self.render_btn.setEnabled(True)

        if result.stdout:
            self.log.append("STDOUT:\n" + result.stdout)
        if result.stderr:
            self.log.append("STDERR:\n" + result.stderr)

        self.last_output_files = []
        self.last_output_dir = out

        if report_json.exists():
            try:
                data = json.loads(report_json.read_text(encoding="utf-8"))
                self.last_output_files = [Path(p) for p in data.get("output_files", [])]
            except Exception as exc:
                self.log.append(f"\nCould not parse report JSON: {exc}")

        if not self.last_output_files and out.exists():
            self.last_output_files = sorted(out.glob("*"))

        self.open_output_btn.setEnabled(out.exists())
        self.open_pdf_btn.setEnabled(any(p.suffix.lower() == ".pdf" and p.exists() for p in self.last_output_files))
        self.open_docx_btn.setEnabled(any(p.suffix.lower() == ".docx" and p.exists() for p in self.last_output_files))

        if result.returncode == 0:
            QMessageBox.information(self, "Render complete", f"Rendered files to:\n{out}")
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
