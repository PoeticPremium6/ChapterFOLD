from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QThread, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gui.worker import Worker


APP_STYLESHEET = """
QMainWindow {
    background: #f5f6f8;
}

QWidget {
    font-size: 11pt;
    color: #222222;
}

QGroupBox {
    background: #ffffff;
    border: 1px solid #d9dde3;
    border-radius: 10px;
    margin-top: 12px;
    font-weight: 600;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #2d3748;
}

QLabel#titleLabel {
    font-size: 22pt;
    font-weight: 700;
    color: #1f2937;
}

QLabel#subtitleLabel {
    font-size: 10pt;
    color: #667085;
}

QLabel#statusLabel {
    background: #eef2f7;
    border: 1px solid #d9dde3;
    border-radius: 8px;
    padding: 8px 10px;
    color: #334155;
    font-weight: 500;
}

QLineEdit,
QComboBox,
QTextEdit {
    background: #ffffff;
    border: 1px solid #cfd6df;
    border-radius: 8px;
    padding: 8px 10px;
    selection-background-color: #cfe3ff;
}

QLineEdit:focus,
QComboBox:focus,
QTextEdit:focus {
    border: 1px solid #6b9cff;
}

QComboBox {
    min-height: 22px;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QPushButton {
    background: #ffffff;
    border: 1px solid #cfd6df;
    border-radius: 8px;
    padding: 8px 14px;
    min-height: 18px;
}

QPushButton:hover {
    background: #f3f6fb;
}

QPushButton:pressed {
    background: #e9eef7;
}

QPushButton:disabled {
    color: #97a3b6;
    background: #f7f8fa;
}

QPushButton#primaryButton {
    background: #1f6feb;
    color: white;
    border: 1px solid #1f6feb;
    font-weight: 600;
}

QPushButton#primaryButton:hover {
    background: #1a62d0;
}

QPushButton#primaryButton:pressed {
    background: #1656b8;
}

QTextEdit#resultsBox {
    background: #fbfcfe;
}

QTextEdit#beforePreview,
QTextEdit#afterPreview {
    background: #ffffff;
}

QFrame#divider {
    background: #d9dde3;
    max-height: 1px;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
}

QLabel.sectionHint {
    color: #667085;
    font-size: 10pt;
}
"""


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ChapterFOLD")
        self.resize(1160, 860)
        self.setStyleSheet(APP_STYLESHEET)

        self.thread: QThread | None = None
        self.worker: Worker | None = None

        self.input_edit = QLineEdit()
        self.output_edit = QLineEdit()

        self.variant_combo = QComboBox()
        self.variant_combo.addItem("Standard Cleanup", "standard")
        self.variant_combo.addItem("Dialogue Merge", "paragraph-dialogue-merge")
        self.variant_combo.addItem("Aggressive Cleanup", "aggressive-cleanup")

        self.export_docx_checkbox = QCheckBox("Also export DOCX")
        self.export_docx_checkbox.setChecked(True)

        self.spacing_mode_combo = QComboBox()
        self.spacing_mode_combo.addItem("Traditional (paragraph spacing + indents)", "traditional")
        self.spacing_mode_combo.addItem("No indents (keep paragraph spacing)", "no-indents")
        self.spacing_mode_combo.addItem("Indented compact (minimal paragraph gap + indents)", "indented-compact")
        self.spacing_mode_combo.addItem("Uniform (no paragraph gap, no indents)", "uniform")

        self.margin_preset_combo = QComboBox()
        self.margin_preset_combo.addItem("Standard", "standard")
        self.margin_preset_combo.addItem("Compact", "compact")
        self.margin_preset_combo.addItem("Wide", "wide")
        self.margin_preset_combo.addItem("Large print friendly", "large-print")

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(150)

        self.results_box = QTextEdit()
        self.results_box.setObjectName("resultsBox")
        self.results_box.setReadOnly(True)
        self.results_box.setMaximumHeight(280)

        self.before_preview = QTextEdit()
        self.before_preview.setObjectName("beforePreview")
        self.before_preview.setReadOnly(True)

        self.after_preview = QTextEdit()
        self.after_preview.setObjectName("afterPreview")
        self.after_preview.setReadOnly(True)

        self.title_label = QLabel("ChapterFOLD")
        self.title_label.setObjectName("titleLabel")

        self.subtitle_label = QLabel(
            "Convert EPUBs into cleaner print-ready PDF and DOCX interiors."
        )
        self.subtitle_label.setObjectName("subtitleLabel")

        self.preview_heading_label = QLabel("Text preview sample: none")
        self.preview_index_label = QLabel("0 / 0")

        self.status_label = QLabel("Ready to process an EPUB")
        self.status_label.setObjectName("statusLabel")

        self.browse_input_btn = QPushButton("Browse...")
        self.browse_output_btn = QPushButton("Browse...")
        self.process_btn = QPushButton("Process EPUB")
        self.process_btn.setObjectName("primaryButton")

        self.open_output_btn = QPushButton("Open Output Folder")
        self.open_output_btn.setEnabled(False)

        self.open_pdf_btn = QPushButton("Open PDF")
        self.open_pdf_btn.setEnabled(False)

        self.open_docx_btn = QPushButton("Open DOCX")
        self.open_docx_btn.setEnabled(False)

        self.prev_preview_btn = QPushButton("Previous")
        self.next_preview_btn = QPushButton("Next")
        self.prev_preview_btn.setEnabled(False)
        self.next_preview_btn.setEnabled(False)

        self.last_output_dir: str | None = None
        self.last_output_pdf: str | None = None
        self.last_output_docx: str | None = None
        self.preview_samples: list[dict[str, str]] = []
        self.current_preview_index = 0

        self._build_ui()
        self._connect_signals()

        default_output = Path.cwd()
        self.output_edit.setText(str(default_output))

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.subtitle_label)
        root.addLayout(header_layout)

        root.addWidget(self.status_label)

        top_row = QHBoxLayout()
        top_row.setSpacing(14)

        top_row.addWidget(self._build_book_group(), 3)
        top_row.addWidget(self._build_cleanup_group(), 2)

        root.addLayout(top_row)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        action_row.addWidget(self.open_output_btn)
        action_row.addWidget(self.open_pdf_btn)
        action_row.addWidget(self.open_docx_btn)
        action_row.addStretch()
        action_row.addWidget(self.process_btn)
        root.addLayout(action_row)

        root.addWidget(self._build_results_group())
        root.addWidget(self._build_preview_group(), 1)
        root.addWidget(self._build_log_group())

    def _build_book_group(self) -> QGroupBox:
        group = QGroupBox("Book")
        layout = QGridLayout(group)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(10)

        input_hint = QLabel("Choose the source EPUB and where outputs should be saved.")
        input_hint.setProperty("class", "sectionHint")
        input_hint.setWordWrap(True)

        layout.addWidget(input_hint, 0, 0, 1, 3)

        layout.addWidget(QLabel("Input EPUB"), 1, 0)
        layout.addWidget(self.input_edit, 1, 1)
        layout.addWidget(self.browse_input_btn, 1, 2)

        layout.addWidget(QLabel("Output folder"), 2, 0)
        layout.addWidget(self.output_edit, 2, 1)
        layout.addWidget(self.browse_output_btn, 2, 2)

        layout.setColumnStretch(1, 1)
        return group

    def _build_cleanup_group(self) -> QGroupBox:
        group = QGroupBox("Cleanup and layout")
        layout = QGridLayout(group)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(10)

        hint = QLabel("Choose cleanup intensity, paragraph style, and margin preset.")
        hint.setProperty("class", "sectionHint")
        hint.setWordWrap(True)

        layout.addWidget(hint, 0, 0, 1, 2)

        layout.addWidget(QLabel("Cleanup mode"), 1, 0)
        layout.addWidget(self.variant_combo, 1, 1)

        layout.addWidget(QLabel("Paragraph spacing"), 2, 0)
        layout.addWidget(self.spacing_mode_combo, 2, 1)

        layout.addWidget(QLabel("Margins"), 3, 0)
        layout.addWidget(self.margin_preset_combo, 3, 1)

        layout.addWidget(QLabel("Options"), 4, 0)
        options_layout = QVBoxLayout()
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(6)
        options_layout.addWidget(self.export_docx_checkbox)
        layout.addLayout(options_layout, 4, 1)

        layout.setColumnStretch(1, 1)
        return group

    def _build_results_group(self) -> QGroupBox:
        group = QGroupBox("Results")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        hint = QLabel("Summary of the generated files, layout impact, and comparison stats.")
        hint.setProperty("class", "sectionHint")
        hint.setWordWrap(True)

        layout.addWidget(hint)
        layout.addWidget(self.results_box)
        return group

    def _build_preview_group(self) -> QGroupBox:
        group = QGroupBox("Text cleanup preview")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        top = QHBoxLayout()
        top.addWidget(self.preview_heading_label)
        top.addStretch()
        top.addWidget(self.prev_preview_btn)
        top.addWidget(self.next_preview_btn)
        top.addWidget(self.preview_index_label)

        layout.addLayout(top)

        preview_row = QHBoxLayout()
        preview_row.setSpacing(12)

        before_col = QVBoxLayout()
        before_label = QLabel("Before")
        before_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        before_col.addWidget(before_label)
        before_col.addWidget(self.before_preview)

        after_col = QVBoxLayout()
        after_label = QLabel("After")
        after_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        after_col.addWidget(after_label)
        after_col.addWidget(self.after_preview)

        preview_row.addLayout(before_col, 1)
        preview_row.addLayout(after_col, 1)

        layout.addLayout(preview_row)
        return group

    def _build_log_group(self) -> QGroupBox:
        group = QGroupBox("Processing log")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        hint = QLabel("Detailed processing messages and diagnostics.")
        hint.setProperty("class", "sectionHint")
        hint.setWordWrap(True)

        layout.addWidget(hint)
        layout.addWidget(self.log_box)
        return group

    def _connect_signals(self) -> None:
        self.browse_input_btn.clicked.connect(self._browse_input)
        self.browse_output_btn.clicked.connect(self._browse_output)
        self.process_btn.clicked.connect(self._start_processing)
        self.open_output_btn.clicked.connect(self._open_output_folder)
        self.open_pdf_btn.clicked.connect(self._open_pdf)
        self.open_docx_btn.clicked.connect(self._open_docx)
        self.prev_preview_btn.clicked.connect(self._show_previous_preview)
        self.next_preview_btn.clicked.connect(self._show_next_preview)

    def _browse_input(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select EPUB",
            "",
            "EPUB files (*.epub);;All files (*.*)",
        )
        if path:
            self.input_edit.setText(path)

    def _browse_output(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self,
            "Select output folder",
            self.output_edit.text().strip() or "",
        )
        if path:
            self.output_edit.setText(path)

    def _append_log(self, message: str) -> None:
        self.log_box.append(message)
        if message.strip():
            self.status_label.setText(message)

    def _set_busy(self, busy: bool) -> None:
        self.process_btn.setEnabled(not busy)
        self.browse_input_btn.setEnabled(not busy)
        self.browse_output_btn.setEnabled(not busy)
        self.variant_combo.setEnabled(not busy)
        self.export_docx_checkbox.setEnabled(not busy)
        self.spacing_mode_combo.setEnabled(not busy)
        self.margin_preset_combo.setEnabled(not busy)

    def _reset_results_ui(self) -> None:
        self.results_box.clear()
        self.before_preview.clear()
        self.after_preview.clear()
        self.preview_heading_label.setText("Text preview sample: none")
        self.preview_index_label.setText("0 / 0")
        self.preview_samples = []
        self.current_preview_index = 0
        self.prev_preview_btn.setEnabled(False)
        self.next_preview_btn.setEnabled(False)
        self.last_output_dir = None
        self.last_output_pdf = None
        self.last_output_docx = None
        self.open_output_btn.setEnabled(False)
        self.open_pdf_btn.setEnabled(False)
        self.open_docx_btn.setEnabled(False)

    def _start_processing(self) -> None:
        input_path = self.input_edit.text().strip()
        output_dir = self.output_edit.text().strip()
        variant = self.variant_combo.currentData()
        export_docx = self.export_docx_checkbox.isChecked()
        paragraph_spacing_mode = self.spacing_mode_combo.currentData()
        margin_preset = self.margin_preset_combo.currentData()

        if not input_path:
            QMessageBox.warning(self, "Missing input", "Please choose an EPUB file.")
            return

        if not Path(input_path).exists():
            QMessageBox.warning(self, "Invalid input", "The selected EPUB file does not exist.")
            return

        if not output_dir:
            QMessageBox.warning(self, "Missing output", "Please choose an output folder.")
            return

        self.log_box.clear()
        self._reset_results_ui()

        self._append_log("Launching job...")
        self._set_busy(True)

        self.thread = QThread()
        self.worker = Worker(
            input_epub=input_path,
            output_dir=output_dir,
            variant=variant,
            export_docx=export_docx,
            paragraph_spacing_mode=paragraph_spacing_mode,
            margin_preset=margin_preset,
        )
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.log.connect(self._append_log)
        self.worker.error.connect(self._on_error)
        self.worker.success.connect(self._on_success)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(lambda: self._set_busy(False))

        self.thread.start()

    def _format_size(self, value: float | None) -> str:
        if value is None:
            return "N/A"
        return f"{value:.2f} MB"

    def _format_signed_int(self, value: int | None) -> str:
        if value is None:
            return "N/A"
        return f"{value:+d}"

    def _format_signed_float(self, value: float | None) -> str:
        if value is None:
            return "N/A"
        return f"{value:+.2f} MB"

    def _build_results_text(self, payload: dict) -> str:
        lines = [
            f"Title: {payload.get('title', '')}",
            f"Author: {payload.get('author', '')}",
            f"Cleanup mode: {payload.get('variant_label', payload.get('variant', ''))}",
            f"Paragraph spacing mode: {payload.get('paragraph_spacing_mode_label', '')}",
            f"Margins: {payload.get('margin_preset_label', '')}",
            "",
            f"Input EPUB: {payload.get('input_epub', '')}",
            f"Output PDF: {payload.get('output_pdf', '')}",
        ]

        output_docx = payload.get("output_docx", "")
        if output_docx:
            lines.append(f"Output DOCX: {output_docx}")

        lines.extend([
            "",
            f"Input EPUB size: {self._format_size(payload.get('input_size_mb'))}",
            f"Selected PDF size: {self._format_size(payload.get('pdf_size_mb'))}",
        ])

        if payload.get("docx_size_mb") is not None:
            lines.append(f"Output DOCX size: {self._format_size(payload.get('docx_size_mb'))}")

        lines.append(f"Selected PDF pages: {payload.get('output_pdf_pages', 'N/A')}")

        if payload.get("variant") != "standard":
            lines.extend([
                "",
                "Baseline comparison (Standard Cleanup):",
                f"Baseline PDF: {payload.get('baseline_pdf', '')}",
                f"Baseline PDF size: {self._format_size(payload.get('baseline_pdf_size_mb'))}",
                f"Baseline PDF pages: {payload.get('baseline_pdf_pages', 'N/A')}",
                f"Page delta vs baseline: {self._format_signed_int(payload.get('page_delta_vs_baseline'))}",
                f"PDF size delta vs baseline: {self._format_signed_float(payload.get('size_delta_mb_vs_baseline'))}",
            ])

        lines.extend([
            "",
            f"Text cleanup preview changes found: {payload.get('preview_sample_count', 0)}",
        ])

        return "\n".join(lines)

    def _on_success(self, payload: dict) -> None:
        self.last_output_dir = payload.get("output_dir", "")
        self.last_output_pdf = payload.get("output_pdf", "")
        self.last_output_docx = payload.get("output_docx", "")

        self.open_output_btn.setEnabled(bool(self.last_output_dir))
        self.open_pdf_btn.setEnabled(bool(self.last_output_pdf))
        self.open_docx_btn.setEnabled(bool(self.last_output_docx))

        self.results_box.setPlainText(self._build_results_text(payload))

        self.preview_samples = payload.get("preview_samples", []) or []
        self.current_preview_index = 0
        self._render_current_preview()

        self.status_label.setText("Completed successfully.")
        QMessageBox.information(self, "Success", "Completed successfully.")

    def _on_error(self, error_text: str) -> None:
        self._append_log(error_text)
        self.status_label.setText("Error")
        QMessageBox.critical(self, "Error", error_text)

    def _render_current_preview(self) -> None:
        total = len(self.preview_samples)

        if total == 0:
            self.preview_heading_label.setText("Text preview sample: none")
            self.preview_index_label.setText("0 / 0")
            self.before_preview.setPlainText("No text cleanup preview samples were found.")
            self.after_preview.setPlainText(
                "This can still be normal if the visible difference is mainly layout, spacing, margins, or pagination."
            )
            self.prev_preview_btn.setEnabled(False)
            self.next_preview_btn.setEnabled(False)
            return

        sample = self.preview_samples[self.current_preview_index]
        heading = sample.get("heading", "(Untitled section)")
        before = sample.get("before", "")
        after = sample.get("after", "")

        self.preview_heading_label.setText(f"Text preview sample: {heading}")
        self.preview_index_label.setText(f"{self.current_preview_index + 1} / {total}")
        self.before_preview.setPlainText(before)
        self.after_preview.setPlainText(after)

        self.prev_preview_btn.setEnabled(self.current_preview_index > 0)
        self.next_preview_btn.setEnabled(self.current_preview_index < total - 1)

    def _show_previous_preview(self) -> None:
        if self.current_preview_index > 0:
            self.current_preview_index -= 1
            self._render_current_preview()

    def _show_next_preview(self) -> None:
        if self.current_preview_index < len(self.preview_samples) - 1:
            self.current_preview_index += 1
            self._render_current_preview()

    def _open_output_folder(self) -> None:
        if not self.last_output_dir:
            return

        path = Path(self.last_output_dir)
        if not path.exists():
            QMessageBox.warning(self, "Missing folder", "The output folder no longer exists.")
            return

        os.startfile(str(path))

    def _open_pdf(self) -> None:
        if not self.last_output_pdf:
            return

        path = Path(self.last_output_pdf)
        if not path.exists():
            QMessageBox.warning(self, "Missing file", "The PDF file no longer exists.")
            return

        os.startfile(str(path))

    def _open_docx(self) -> None:
        if not self.last_output_docx:
            return

        path = Path(self.last_output_docx)
        if not path.exists():
            QMessageBox.warning(self, "Missing file", "The DOCX file no longer exists.")
            return

        os.startfile(str(path))
