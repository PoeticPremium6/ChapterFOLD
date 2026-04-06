from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QThread, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gui.worker import Worker


APP_STYLESHEET = """
QMainWindow {
    background: #f6f2fb;
}

QWidget {
    font-size: 11pt;
    color: #231b2f;
    font-family: "Segoe UI", "Inter", sans-serif;
}

QGroupBox {
    background: #ffffff;
    border: 1px solid #dfd4ee;
    border-radius: 14px;
    margin-top: 12px;
    font-weight: 700;
    padding-top: 12px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #5a2a82;
}

QLabel#titleLabel {
    font-size: 24pt;
    font-weight: 800;
    color: #4b1f6f;
}

QLabel#subtitleLabel {
    font-size: 10pt;
    color: #7a6a8c;
}

QLabel#statusLabel {
    background: #efe7f8;
    border: 1px solid #dcccf0;
    border-radius: 10px;
    padding: 10px 12px;
    color: #4b2f63;
    font-weight: 600;
}

QLabel#sectionHintLabel {
    color: #7a6a8c;
    font-size: 10pt;
}

QLineEdit,
QComboBox,
QTextEdit,
QDoubleSpinBox {
    background: #ffffff;
    border: 1px solid #d8cbe8;
    border-radius: 10px;
    padding: 8px 10px;
    selection-background-color: #d9b8ff;
}

QLineEdit:focus,
QComboBox:focus,
QTextEdit:focus,
QDoubleSpinBox:focus {
    border: 1px solid #8b4fd8;
}

QComboBox,
QDoubleSpinBox {
    min-height: 24px;
}

QComboBox::drop-down {
    border: none;
    width: 28px;
}

QPushButton {
    background: #ffffff;
    border: 1px solid #d8cbe8;
    border-radius: 10px;
    padding: 9px 14px;
    min-height: 20px;
    font-weight: 600;
}

QPushButton:hover {
    background: #f7f1fc;
}

QPushButton:pressed {
    background: #efe5f9;
}

QPushButton:disabled {
    color: #ab9cbb;
    background: #faf8fc;
}

QPushButton#primaryButton {
    background: #7b2cbf;
    color: white;
    border: 1px solid #7b2cbf;
    font-weight: 700;
}

QPushButton#primaryButton:hover {
    background: #6f24ad;
}

QPushButton#primaryButton:pressed {
    background: #611f98;
}

QCheckBox {
    spacing: 8px;
    padding: 2px 0;
    color: #231b2f;
    font-weight: 600;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
}

QCheckBox::indicator:unchecked {
    border: 1px solid #bfaed6;
    border-radius: 4px;
    background: #ffffff;
}

QCheckBox::indicator:checked {
    border: 1px solid #8b4fd8;
    border-radius: 4px;
    background: #ead7fb;
}

QTextEdit#resultsBox {
    background: #fcfafe;
}

QTextEdit#beforePreview,
QTextEdit#afterPreview,
QTextEdit#logBox {
    background: #ffffff;
}

QSplitter::handle {
    background: #e8ddf4;
}

QSplitter::handle:horizontal {
    width: 8px;
}

QSplitter::handle:vertical {
    height: 8px;
}
"""


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ChapterFOLD")
        self.resize(1260, 980)
        self.setMinimumSize(1080, 780)
        self.setStyleSheet(APP_STYLESHEET)

        self.thread: QThread | None = None
        self.worker: Worker | None = None

        self.input_edit = QLineEdit()
        self.output_edit = QLineEdit()

        self.variant_combo = QComboBox()
        self.variant_combo.addItem("Standard Cleanup", "standard")
        self.variant_combo.addItem("Dialogue Merge", "paragraph-dialogue-merge")
        self.variant_combo.addItem("Aggressive Cleanup", "aggressive-cleanup")

        self.export_docx_btn = QCheckBox("DOCX (.docx)")
        self.export_docx_btn.setChecked(True)
        self.export_docx_btn.setToolTip("Export an editable DOCX for Word / LibreOffice.")

        self.export_markdown_btn = QCheckBox("Markdown (.md)")
        self.export_markdown_btn.setChecked(True)
        self.export_markdown_btn.setToolTip("Export editable Markdown for Google Docs or other editors.")

        self.spacing_mode_combo = QComboBox()
        self.spacing_mode_combo.addItem("Traditional (paragraph spacing + indents)", "traditional")
        self.spacing_mode_combo.addItem("No indents (keep paragraph spacing)", "no-indents")
        self.spacing_mode_combo.addItem("Indented compact (minimal paragraph gap + indents)", "indented-compact")
        self.spacing_mode_combo.addItem("Uniform (no paragraph gap, no indents)", "uniform")

        self.page_size_combo = QComboBox()
        self.page_size_combo.addItem("Default trade (6 x 9 in)", "default-trade")
        self.page_size_combo.addItem("A4", "a4")
        self.page_size_combo.addItem("A5", "a5")
        self.page_size_combo.addItem("A6", "a6")
        self.page_size_combo.addItem("US Letter", "letter")
        self.page_size_combo.addItem("Half Letter", "half-letter")
        self.page_size_combo.addItem("Trade 5 x 8 in", "trade-5x8")
        self.page_size_combo.addItem("Trade 6 x 9 in", "trade-6x9")
        self.page_size_combo.addItem("Custom size", "custom")

        self.margin_preset_combo = QComboBox()
        self.margin_preset_combo.addItem("Standard", "standard")
        self.margin_preset_combo.addItem("Compact", "compact")
        self.margin_preset_combo.addItem("Wide", "wide")
        self.margin_preset_combo.addItem("Large print friendly", "large-print")
        self.margin_preset_combo.addItem("Custom margins", "custom")

        self.trim_width_spin = QDoubleSpinBox()
        self.trim_width_spin.setDecimals(2)
        self.trim_width_spin.setRange(5.0, 50.0)
        self.trim_width_spin.setSingleStep(0.1)
        self.trim_width_spin.setSuffix(" cm")
        self.trim_width_spin.setValue(15.24)

        self.trim_height_spin = QDoubleSpinBox()
        self.trim_height_spin.setDecimals(2)
        self.trim_height_spin.setRange(5.0, 50.0)
        self.trim_height_spin.setSingleStep(0.1)
        self.trim_height_spin.setSuffix(" cm")
        self.trim_height_spin.setValue(22.86)

        self.margin_top_spin = QDoubleSpinBox()
        self.margin_top_spin.setDecimals(2)
        self.margin_top_spin.setRange(0.3, 10.0)
        self.margin_top_spin.setSingleStep(0.1)
        self.margin_top_spin.setSuffix(" cm")
        self.margin_top_spin.setValue(1.5)

        self.margin_bottom_spin = QDoubleSpinBox()
        self.margin_bottom_spin.setDecimals(2)
        self.margin_bottom_spin.setRange(0.3, 10.0)
        self.margin_bottom_spin.setSingleStep(0.1)
        self.margin_bottom_spin.setSuffix(" cm")
        self.margin_bottom_spin.setValue(1.5)

        self.margin_inside_spin = QDoubleSpinBox()
        self.margin_inside_spin.setDecimals(2)
        self.margin_inside_spin.setRange(0.3, 10.0)
        self.margin_inside_spin.setSingleStep(0.1)
        self.margin_inside_spin.setSuffix(" cm")
        self.margin_inside_spin.setValue(1.8)

        self.margin_outside_spin = QDoubleSpinBox()
        self.margin_outside_spin.setDecimals(2)
        self.margin_outside_spin.setRange(0.3, 10.0)
        self.margin_outside_spin.setSingleStep(0.1)
        self.margin_outside_spin.setSuffix(" cm")
        self.margin_outside_spin.setValue(1.0)

        self.imposition_mode_combo = QComboBox()
        self.imposition_mode_combo.addItem("Do not create imposed PDF", "none")
        self.imposition_mode_combo.addItem("Also create imposed PDF", "also")

        self.signature_pages_combo = QComboBox()
        for pages in (4, 8, 16, 20, 24, 32):
            self.signature_pages_combo.addItem(str(pages), pages)
        self.signature_pages_combo.setCurrentText("16")

        self.binding_direction_combo = QComboBox()
        self.binding_direction_combo.addItem("Left-to-right", "ltr")
        self.binding_direction_combo.addItem("Right-to-left", "rtl")

        self.max_end_padding_combo = QComboBox()
        self.max_end_padding_combo.addItem("Unlimited", None)
        self.max_end_padding_combo.addItem("0", 0)
        self.max_end_padding_combo.addItem("4", 4)
        self.max_end_padding_combo.addItem("8", 8)
        self.max_end_padding_combo.addItem("12", 12)

        self.log_box = QTextEdit()
        self.log_box.setObjectName("logBox")
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(180)

        self.results_box = QTextEdit()
        self.results_box.setObjectName("resultsBox")
        self.results_box.setReadOnly(True)
        self.results_box.setMinimumHeight(180)

        self.before_preview = QTextEdit()
        self.before_preview.setObjectName("beforePreview")
        self.before_preview.setReadOnly(True)

        self.after_preview = QTextEdit()
        self.after_preview.setObjectName("afterPreview")
        self.after_preview.setReadOnly(True)

        self.title_label = QLabel("ChapterFOLD")
        self.title_label.setObjectName("titleLabel")

        self.subtitle_label = QLabel(
            "Convert EPUBs into cleaner print-ready interiors and optional imposed signature PDFs."
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

        self.open_markdown_btn = QPushButton("Open Markdown")
        self.open_markdown_btn.setEnabled(False)

        self.open_imposed_btn = QPushButton("Open Imposed PDF")
        self.open_imposed_btn.setEnabled(False)

        self.prev_preview_btn = QPushButton("Previous")
        self.next_preview_btn = QPushButton("Next")
        self.prev_preview_btn.setEnabled(False)
        self.next_preview_btn.setEnabled(False)

        self.last_output_dir: str | None = None
        self.last_output_pdf: str | None = None
        self.last_output_docx: str | None = None
        self.last_output_markdown: str | None = None
        self.last_imposed_pdf: str | None = None
        self.preview_samples: list[dict[str, str]] = []
        self.current_preview_index = 0

        self._build_ui()
        self._connect_signals()

        default_output = Path.cwd()
        self.output_edit.setText(str(default_output))
        self._sync_layout_visibility()

    def _hint_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("sectionHintLabel")
        label.setWordWrap(True)
        return label

    def _refresh_output_toggle_styles(self) -> None:
        return

    def _build_two_spin_row(self, left_label: str, left_spin, right_label: str, right_spin) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(QLabel(left_label))
        layout.addWidget(left_spin, 1)
        layout.addSpacing(8)
        layout.addWidget(QLabel(right_label))
        layout.addWidget(right_spin, 1)
        return container

    def _sync_layout_visibility(self) -> None:
        custom_size = self.page_size_combo.currentData() == "custom"
        custom_margins = self.margin_preset_combo.currentData() == "custom"

        if hasattr(self, "custom_trim_widget"):
            self.custom_trim_widget.setVisible(custom_size)
        if hasattr(self, "custom_margin_widget"):
            self.custom_margin_widget.setVisible(custom_margins)

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

        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.addWidget(self._build_book_group())
        top_splitter.addWidget(self._build_cleanup_group())
        top_splitter.setStretchFactor(0, 3)
        top_splitter.setStretchFactor(1, 3)
        top_splitter.setSizes([640, 560])
        root.addWidget(top_splitter, 0)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        action_row.addWidget(self.open_output_btn)
        action_row.addWidget(self.open_pdf_btn)
        action_row.addWidget(self.open_docx_btn)
        action_row.addWidget(self.open_markdown_btn)
        action_row.addWidget(self.open_imposed_btn)
        action_row.addStretch()
        action_row.addWidget(self.process_btn)
        root.addLayout(action_row)

        lower_splitter = QSplitter(Qt.Orientation.Vertical)
        lower_splitter.addWidget(self._build_results_group())
        lower_splitter.addWidget(self._build_preview_group())
        lower_splitter.addWidget(self._build_log_group())
        lower_splitter.setStretchFactor(0, 2)
        lower_splitter.setStretchFactor(1, 4)
        lower_splitter.setStretchFactor(2, 3)
        lower_splitter.setSizes([240, 360, 240])
        root.addWidget(lower_splitter, 1)

    def _build_book_group(self) -> QGroupBox:
        group = QGroupBox("Book")
        group.setMinimumWidth(460)
        group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QGridLayout(group)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(12)

        layout.addWidget(
            self._hint_label("Choose the source EPUB and where the outputs should be saved."),
            0,
            0,
            1,
            3,
        )

        layout.addWidget(QLabel("Input EPUB"), 1, 0)
        layout.addWidget(self.input_edit, 1, 1)
        layout.addWidget(self.browse_input_btn, 1, 2)

        layout.addWidget(QLabel("Output folder"), 2, 0)
        layout.addWidget(self.output_edit, 2, 1)
        layout.addWidget(self.browse_output_btn, 2, 2)

        layout.setColumnStretch(1, 1)
        return group

    def _build_cleanup_group(self) -> QGroupBox:
        group = QGroupBox("Cleanup, layout, binding, and outputs")
        group.setMinimumWidth(500)
        group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QGridLayout(group)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(12)

        layout.addWidget(
            self._hint_label("Choose cleanup strength, typography, optional signature imposition, and editable export formats."),
            0,
            0,
            1,
            2,
        )

        layout.addWidget(QLabel("Cleanup mode"), 1, 0)
        layout.addWidget(self.variant_combo, 1, 1)

        layout.addWidget(QLabel("Paragraph spacing"), 2, 0)
        layout.addWidget(self.spacing_mode_combo, 2, 1)

        layout.addWidget(QLabel("Page size"), 3, 0)
        layout.addWidget(self.page_size_combo, 3, 1)

        self.custom_trim_widget = self._build_two_spin_row(
            "Width",
            self.trim_width_spin,
            "Height",
            self.trim_height_spin,
        )
        layout.addWidget(self.custom_trim_widget, 4, 1)

        layout.addWidget(QLabel("Margins"), 5, 0)
        layout.addWidget(self.margin_preset_combo, 5, 1)

        self.custom_margin_widget = QWidget()
        custom_margin_layout = QVBoxLayout(self.custom_margin_widget)
        custom_margin_layout.setContentsMargins(0, 0, 0, 0)
        custom_margin_layout.setSpacing(8)
        custom_margin_layout.addWidget(
            self._build_two_spin_row("Top", self.margin_top_spin, "Bottom", self.margin_bottom_spin)
        )
        custom_margin_layout.addWidget(
            self._build_two_spin_row("Inside", self.margin_inside_spin, "Outside", self.margin_outside_spin)
        )
        layout.addWidget(self.custom_margin_widget, 6, 1)

        layout.addWidget(QLabel("Editable outputs"), 7, 0)
        layout.addWidget(self.export_docx_btn, 7, 1)

        layout.addWidget(QLabel(""), 8, 0)
        layout.addWidget(self.export_markdown_btn, 8, 1)

        layout.addWidget(QLabel("Imposition output"), 9, 0)
        layout.addWidget(self.imposition_mode_combo, 9, 1)

        layout.addWidget(QLabel("Pages per signature"), 10, 0)
        layout.addWidget(self.signature_pages_combo, 10, 1)

        layout.addWidget(QLabel("Binding direction"), 11, 0)
        layout.addWidget(self.binding_direction_combo, 11, 1)

        layout.addWidget(QLabel("Max blank end pages"), 12, 0)
        layout.addWidget(self.max_end_padding_combo, 12, 1)

        layout.setColumnStretch(1, 1)
        return group

    def _build_results_group(self) -> QGroupBox:
        group = QGroupBox("Results")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        layout.addWidget(self._hint_label("Summary of generated files, layout impact, and imposition details."))
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

        preview_splitter = QSplitter(Qt.Orientation.Horizontal)

        before_container = QWidget()
        before_layout = QVBoxLayout(before_container)
        before_layout.setContentsMargins(0, 0, 0, 0)
        before_layout.addWidget(QLabel("Before"))
        before_layout.addWidget(self.before_preview)

        after_container = QWidget()
        after_layout = QVBoxLayout(after_container)
        after_layout.setContentsMargins(0, 0, 0, 0)
        after_layout.addWidget(QLabel("After"))
        after_layout.addWidget(self.after_preview)

        preview_splitter.addWidget(before_container)
        preview_splitter.addWidget(after_container)
        preview_splitter.setStretchFactor(0, 1)
        preview_splitter.setStretchFactor(1, 1)
        preview_splitter.setSizes([500, 500])

        layout.addWidget(preview_splitter)
        return group

    def _build_log_group(self) -> QGroupBox:
        group = QGroupBox("Processing log")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        layout.addWidget(self._hint_label("Detailed processing messages and errors appear here."))
        layout.addWidget(self.log_box)
        return group

    def _connect_signals(self) -> None:
        self.browse_input_btn.clicked.connect(self._browse_input)
        self.browse_output_btn.clicked.connect(self._browse_output)
        self.process_btn.clicked.connect(self._start_processing)
        self.open_output_btn.clicked.connect(self._open_output_folder)
        self.open_pdf_btn.clicked.connect(self._open_pdf)
        self.open_docx_btn.clicked.connect(self._open_docx)
        self.open_markdown_btn.clicked.connect(self._open_markdown)
        self.open_imposed_btn.clicked.connect(self._open_imposed_pdf)
        self.prev_preview_btn.clicked.connect(self._show_previous_preview)
        self.next_preview_btn.clicked.connect(self._show_next_preview)
        self.export_docx_btn.toggled.connect(self._refresh_output_toggle_styles)
        self.export_markdown_btn.toggled.connect(self._refresh_output_toggle_styles)
        self.page_size_combo.currentIndexChanged.connect(self._sync_layout_visibility)
        self.margin_preset_combo.currentIndexChanged.connect(self._sync_layout_visibility)

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
        self.export_docx_btn.setEnabled(not busy)
        self.export_markdown_btn.setEnabled(not busy)
        self.spacing_mode_combo.setEnabled(not busy)
        self.page_size_combo.setEnabled(not busy)
        self.margin_preset_combo.setEnabled(not busy)
        self.trim_width_spin.setEnabled(not busy)
        self.trim_height_spin.setEnabled(not busy)
        self.margin_top_spin.setEnabled(not busy)
        self.margin_bottom_spin.setEnabled(not busy)
        self.margin_inside_spin.setEnabled(not busy)
        self.margin_outside_spin.setEnabled(not busy)
        self.imposition_mode_combo.setEnabled(not busy)
        self.signature_pages_combo.setEnabled(not busy)
        self.binding_direction_combo.setEnabled(not busy)
        self.max_end_padding_combo.setEnabled(not busy)

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
        self.last_output_markdown = None
        self.last_imposed_pdf = None
        self.open_output_btn.setEnabled(False)
        self.open_pdf_btn.setEnabled(False)
        self.open_docx_btn.setEnabled(False)
        self.open_markdown_btn.setEnabled(False)
        self.open_imposed_btn.setEnabled(False)

    def _start_processing(self) -> None:
        input_path = self.input_edit.text().strip()
        output_dir = self.output_edit.text().strip()
        variant = self.variant_combo.currentData()
        export_docx = self.export_docx_btn.isChecked()
        export_markdown = self.export_markdown_btn.isChecked()
        paragraph_spacing_mode = self.spacing_mode_combo.currentData()
        page_size_preset = self.page_size_combo.currentData()
        margin_preset = self.margin_preset_combo.currentData()

        custom_trim_width_cm = self.trim_width_spin.value() if page_size_preset == "custom" else None
        custom_trim_height_cm = self.trim_height_spin.value() if page_size_preset == "custom" else None

        custom_margin_top_cm = self.margin_top_spin.value() if margin_preset == "custom" else None
        custom_margin_bottom_cm = self.margin_bottom_spin.value() if margin_preset == "custom" else None
        custom_margin_inside_cm = self.margin_inside_spin.value() if margin_preset == "custom" else None
        custom_margin_outside_cm = self.margin_outside_spin.value() if margin_preset == "custom" else None

        imposition_mode = self.imposition_mode_combo.currentData()
        imposed_pages_per_signature = int(self.signature_pages_combo.currentData())
        binding_direction = self.binding_direction_combo.currentData()
        max_end_padding = self.max_end_padding_combo.currentData()

        if not input_path:
            QMessageBox.warning(self, "Missing input", "Please choose an EPUB file.")
            return

        if not Path(input_path).exists():
            QMessageBox.warning(self, "Invalid input", "The selected EPUB file does not exist.")
            return

        if Path(input_path).suffix.lower() != ".epub":
            QMessageBox.warning(self, "Invalid input", "Please choose a file with the .epub extension.")
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
            export_markdown=export_markdown,
            paragraph_spacing_mode=paragraph_spacing_mode,
            margin_preset=margin_preset,
            page_size_preset=page_size_preset,
            custom_trim_width_cm=custom_trim_width_cm,
            custom_trim_height_cm=custom_trim_height_cm,
            custom_margin_top_cm=custom_margin_top_cm,
            custom_margin_bottom_cm=custom_margin_bottom_cm,
            custom_margin_inside_cm=custom_margin_inside_cm,
            custom_margin_outside_cm=custom_margin_outside_cm,
            imposition_mode=imposition_mode,
            imposed_pages_per_signature=imposed_pages_per_signature,
            binding_direction=binding_direction,
            max_end_padding=max_end_padding,
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
            f"Page size: {payload.get('page_size_preset_label', '')}",
            f"Trim size: {payload.get('trim_width_cm', '')} x {payload.get('trim_height_cm', '')} cm",
            f"Margins: {payload.get('margin_preset_label', '')}",
            (
                "Margin values: "
                f"top {payload.get('margin_top_cm', '')} / "
                f"bottom {payload.get('margin_bottom_cm', '')} / "
                f"inside {payload.get('margin_inside_cm', '')} / "
                f"outside {payload.get('margin_outside_cm', '')} cm"
            ),
            f"Imposition output: {payload.get('imposition_mode_label', '')}",
            "",
            f"Input EPUB: {payload.get('input_epub', '')}",
            f"Output PDF: {payload.get('output_pdf', '')}",
            f"DOCX export: {'Yes (Word / LibreOffice)' if payload.get('export_docx') else 'No'}",
            f"Markdown export: {'Yes (Google Docs)' if payload.get('export_markdown') else 'No'}",
        ]

        output_docx = payload.get("output_docx", "")
        output_markdown = payload.get("output_markdown", "")

        if output_docx:
            lines.append(f"Output DOCX: {output_docx}")
        if output_markdown:
            lines.append(f"Output Markdown: {output_markdown}")

        lines.extend([
            "",
            f"Input EPUB size: {self._format_size(payload.get('input_size_mb'))}",
            f"Selected PDF size: {self._format_size(payload.get('pdf_size_mb'))}",
        ])

        if payload.get("docx_size_mb") is not None:
            lines.append(f"Output DOCX size: {self._format_size(payload.get('docx_size_mb'))}")
        if payload.get("markdown_size_mb") is not None:
            lines.append(f"Output Markdown size: {self._format_size(payload.get('markdown_size_mb'))}")

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

        if payload.get("create_imposed_pdf"):
            lines.extend([
                "",
                "Imposed signature PDF:",
                f"Imposed PDF: {payload.get('imposed_output_pdf', '')}",
                f"Pages per signature: {payload.get('imposed_pages_per_signature', 'N/A')}",
                f"Binding direction: {payload.get('binding_direction_label', '')}",
                f"Max blank end pages: {payload.get('max_end_padding_label', '')}",
                f"Blank pages added: {payload.get('imposed_blank_pages_added', 'N/A')}",
                f"Total signatures: {payload.get('imposed_total_signatures', 'N/A')}",
                f"Output sheet sides: {payload.get('imposed_output_sheet_sides', 'N/A')}",
                f"Physical sheets total: {payload.get('imposed_physical_sheets_total', 'N/A')}",
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
        self.last_output_markdown = payload.get("output_markdown", "")
        self.last_imposed_pdf = payload.get("imposed_output_pdf", "")

        self.open_output_btn.setEnabled(bool(self.last_output_dir))
        self.open_pdf_btn.setEnabled(bool(self.last_output_pdf))
        self.open_docx_btn.setEnabled(bool(self.last_output_docx))
        self.open_markdown_btn.setEnabled(bool(self.last_output_markdown))
        self.open_imposed_btn.setEnabled(bool(self.last_imposed_pdf))

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
                "This can still be normal if the visible difference is mainly layout, spacing, margins, or signature imposition."
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

    def _open_markdown(self) -> None:
        if not self.last_output_markdown:
            return

        path = Path(self.last_output_markdown)
        if not path.exists():
            QMessageBox.warning(self, "Missing file", "The Markdown file no longer exists.")
            return

        os.startfile(str(path))

    def _open_imposed_pdf(self) -> None:
        if not self.last_imposed_pdf:
            return

        path = Path(self.last_imposed_pdf)
        if not path.exists():
            QMessageBox.warning(self, "Missing file", "The imposed PDF file no longer exists.")
            return

        os.startfile(str(path))
