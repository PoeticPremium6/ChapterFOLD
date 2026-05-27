from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from core.font_catalog import FONT_CHOICES, get_font_choice

from PySide6.QtCore import QThread, Qt, Signal
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
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QApplication,
)

from PySide6.QtGui import QFont, QAction
from core.diagnostics import build_diagnostic_report
from core.page_ornaments import chapter_ornament_choices, ordered_page_ornament_choices, page_ornament_amount_choices, page_ornament_choices

try:
    from chapterfold_app.gui.batch_anthology_dialog import BatchAnthologyDialog
except ModuleNotFoundError:
    from gui.batch_anthology_dialog import BatchAnthologyDialog

try:
    from chapterfold_app.gui.worker import Worker
except ModuleNotFoundError:
    from gui.worker import Worker
from chapterfold_app.gui.markdown_tools import install_markdown_render_action


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

QScrollArea {
    border: none;
    background: transparent;
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
    border-radius: 4px;
}

QSplitter::handle:hover {
    background: #d7c5ee;
}

QSplitter::handle:horizontal {
    width: 12px;
}

QSplitter::handle:vertical {
    height: 10px;
}
"""


class DropPathLineEdit(QLineEdit):
    """Line edit that accepts EPUB/PDF paths by drag and drop."""

    ACCEPTED_SUFFIXES = {".epub", ".pdf"}
    multipleFilesDropped = Signal(list)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.setPlaceholderText("Choose or drag an EPUB/PDF file here")

    @classmethod
    def accepted_paths_from_urls(cls, urls) -> list[str]:
        paths: list[str] = []
        for url in urls:
            if not url.isLocalFile():
                continue
            path = Path(url.toLocalFile())
            if path.suffix.lower() in cls.ACCEPTED_SUFFIXES:
                paths.append(str(path))
        return paths

    @classmethod
    def accepted_path_from_urls(cls, urls) -> str:
        paths = cls.accepted_paths_from_urls(urls)
        return paths[0] if paths else ""

    def dragEnterEvent(self, event) -> None:  # noqa: N802 - Qt method name
        if self.accepted_paths_from_urls(event.mimeData().urls()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:  # noqa: N802 - Qt method name
        if self.accepted_paths_from_urls(event.mimeData().urls()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:  # noqa: N802 - Qt method name
        paths = self.accepted_paths_from_urls(event.mimeData().urls())
        if not paths:
            event.ignore()
            return

        if len(paths) == 1:
            self.setText(paths[0])
        else:
            self.multipleFilesDropped.emit(paths)

        event.acceptProposedAction()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._install_diagnostics_menu_action()
        self.setWindowTitle("ChapterFOLD")
        self.resize(1320, 980)
        self.setMinimumSize(1100, 780)
        self.setStyleSheet(APP_STYLESHEET)

        self.thread: QThread | None = None
        self.worker: Worker | None = None

        self.input_edit = DropPathLineEdit()
        self.input_edit.multipleFilesDropped.connect(self._handle_multiple_files_dropped)
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

        self.contents_mode_combo = QComboBox()
        self.contents_mode_combo.addItem("Rebuild clean contents", "rebuild")
        self.contents_mode_combo.addItem("Rebuild clean contents with PDF page numbers", "rebuild-paged")
        self.contents_mode_combo.addItem("Remove source contents", "remove")
        self.contents_mode_combo.addItem("Keep source contents", "keep")
        self.contents_mode_combo.setToolTip("Choose how ChapterFOLD handles the book's table of contents.")

        self.page_number_start_combo = QComboBox()
        self.page_number_start_combo.addItem("After title page (hide title page number)", "after-title-page")
        self.page_number_start_combo.addItem("At main text / first body chapter", "main-text")
        self.page_number_start_combo.addItem("From first page", "first-page")
        self.page_number_start_combo.addItem("No page numbers", "none")
        self.page_number_start_combo.setToolTip("Choose where visible PDF page numbers begin.")

        self.front_matter_numbers_combo = QComboBox()
        self.front_matter_numbers_combo.addItem("Hidden", "hidden")
        self.front_matter_numbers_combo.addItem("Roman lowercase (i, ii, iii)", "roman-lower")
        self.front_matter_numbers_combo.addItem("Roman uppercase (I, II, III)", "roman-upper")
        self.front_matter_numbers_combo.addItem("Arabic (1, 2, 3)", "arabic")
        self.front_matter_numbers_combo.setToolTip("Optional front matter numbering; most useful when page numbers start at main text.")

        self.page_ornament_amount_combo = QComboBox()
        for key, label, description in page_ornament_amount_choices():
            self.page_ornament_amount_combo.addItem(label, key)
            self.page_ornament_amount_combo.setItemData(
                self.page_ornament_amount_combo.count() - 1,
                description,
                Qt.ToolTipRole,
            )
        self.page_ornament_amount_combo.setToolTip(
            "Choose how many ornaments appear around visible PDF page numbers."
        )

        self.chapter_ornament_combo = QComboBox()
        for key, label, description in chapter_ornament_choices():
            self.chapter_ornament_combo.addItem(label, key)
            self.chapter_ornament_combo.setItemData(
                self.chapter_ornament_combo.count() - 1,
                description,
                Qt.ToolTipRole,
            )
        self.chapter_ornament_combo.setToolTip(
            "Optional decorative flourish below chapter headings."
        )

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
        self.page_ornament_combo = QComboBox()
        self._populate_page_ornament_combo()

        self.font_combo = QComboBox()
        for choice in FONT_CHOICES:
            self.font_combo.addItem(choice.dropdown_label, choice.key)
            index = self.font_combo.count() - 1
            self.font_combo.setItemData(index, choice.description, Qt.ToolTipRole)
            # Show each option in an approximate matching family when available.
            primary_family = choice.css_stack.split(",")[0].strip().strip('"')
            self.font_combo.setItemData(index, QFont(primary_family, 11), Qt.FontRole)
        self.font_combo.setToolTip("Choose the output font. Each option includes a suggested use case.")

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
            "Convert EPUBs into clean print interiors, or prepare existing PDFs for binding/imposition."
        )
        self.subtitle_label.setObjectName("subtitleLabel")

        self.preview_heading_label = QLabel("Text preview sample: none")
        self.preview_index_label = QLabel("0 / 0")
        self.status_label = QLabel("Ready to process an EPUB or PDF")
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

        self.open_signature_plan_btn = QPushButton("Open Signature Plan")
        self.open_signature_plan_btn.setEnabled(False)

        self.open_signature_batches_btn = QPushButton("Open Signature Batches")
        self.open_signature_batches_btn.setEnabled(False)


        self.prev_preview_btn = QPushButton("Previous")
        self.next_preview_btn = QPushButton("Next")
        self.prev_preview_btn.setEnabled(False)
        self.next_preview_btn.setEnabled(False)

        self.last_output_dir: str | None = None
        self.last_output_pdf: str | None = None
        self.last_output_docx: str | None = None
        self.last_output_markdown: str | None = None
        self.last_imposed_pdf: str | None = None
        self.last_signature_plan: str | None = None
        self.last_signature_batches: str | None = None
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

    def _wrap_in_scroll_area(self, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(widget)
        return scroll

    def _populate_page_ornament_combo(self) -> None:
        self.page_ornament_combo.clear()
        for key, label, description in ordered_page_ornament_choices():
            self.page_ornament_combo.addItem(label, key)
            self.page_ornament_combo.setItemData(
                self.page_ornament_combo.count() - 1,
                description,
                Qt.ToolTipRole,
            )
        self.page_ornament_combo.setToolTip(
            "Optional decorative ornament around visible PDF page numbers."
        )

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

        self.top_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.top_splitter.setChildrenCollapsible(False)
        self.top_splitter.setHandleWidth(12)
        self.top_splitter.addWidget(self._build_book_group())
        self.top_splitter.addWidget(self._wrap_in_scroll_area(self._build_cleanup_group()))
        self.top_splitter.setStretchFactor(0, 2)
        self.top_splitter.setStretchFactor(1, 3)
        self.top_splitter.setSizes([480, 760])
        root.addWidget(self.top_splitter, 0)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        action_row.addWidget(self.open_output_btn)
        action_row.addWidget(self.open_pdf_btn)
        action_row.addWidget(self.open_docx_btn)
        action_row.addWidget(self.open_markdown_btn)
        action_row.addWidget(self.open_imposed_btn)
        action_row.addWidget(self.open_signature_plan_btn)
        action_row.addWidget(self.open_signature_batches_btn)
        action_row.addStretch()
        action_row.addWidget(self.process_btn)
        root.addLayout(action_row)

        lower_splitter = QSplitter(Qt.Orientation.Vertical)
        lower_splitter.setChildrenCollapsible(False)
        lower_splitter.setHandleWidth(10)
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
        group.setMinimumWidth(360)
        group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QGridLayout(group)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(12)

        layout.addWidget(
            self._hint_label("Choose or drag the source EPUB/PDF and where the outputs should be saved."),
            0,
            0,
            1,
            3,
        )

        layout.addWidget(QLabel("Input EPUB/PDF"), 1, 0)
        layout.addWidget(self.input_edit, 1, 1)
        layout.addWidget(self.browse_input_btn, 1, 2)

        layout.addWidget(QLabel("Output folder"), 2, 0)
        layout.addWidget(self.output_edit, 2, 1)
        layout.addWidget(self.browse_output_btn, 2, 2)

        layout.setColumnStretch(1, 1)
        return group

    def _build_cleanup_group(self) -> QGroupBox:
        group = QGroupBox("Cleanup, layout, binding, and outputs")
        group.setMinimumWidth(560)
        group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QGridLayout(group)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(12)
        layout.setColumnMinimumWidth(0, 170)
        layout.setColumnStretch(1, 1)

        layout.addWidget(
            self._hint_label(
                "Choose cleanup strength, typography, optional signature imposition, and editable export formats. "
                "For PDF input, ChapterFOLD uses a binding/imposition-only workflow."
            ),
            0,
            0,
            1,
            2,
        )

        row = 1

        layout.addWidget(QLabel("Cleanup mode"), row, 0)
        layout.addWidget(self.variant_combo, row, 1)
        row += 1

        layout.addWidget(QLabel("Paragraph spacing"), row, 0)
        layout.addWidget(self.spacing_mode_combo, row, 1)
        row += 1

        layout.addWidget(QLabel("Contents mode"), row, 0)
        layout.addWidget(self.contents_mode_combo, row, 1)
        row += 1

        layout.addWidget(QLabel("Page numbers"), row, 0)
        layout.addWidget(self.page_number_start_combo, row, 1)
        row += 1

        layout.addWidget(QLabel("Front matter numbers"), row, 0)
        layout.addWidget(self.front_matter_numbers_combo, row, 1)
        row += 1

        layout.addWidget(QLabel("Page ornament"), row, 0)
        layout.addWidget(self.page_ornament_combo, row, 1)
        row += 1

        layout.addWidget(QLabel("Ornament amount"), row, 0)
        layout.addWidget(self.page_ornament_amount_combo, row, 1)
        row += 1

        layout.addWidget(QLabel("Chapter ornament"), row, 0)
        layout.addWidget(self.chapter_ornament_combo, row, 1)
        row += 1

        layout.addWidget(QLabel("Output font"), row, 0)
        layout.addWidget(self.font_combo, row, 1)
        row += 1

        layout.addWidget(QLabel("Page size"), row, 0)
        layout.addWidget(self.page_size_combo, row, 1)
        row += 1

        self.custom_trim_widget = self._build_two_spin_row(
            "Width",
            self.trim_width_spin,
            "Height",
            self.trim_height_spin,
        )
        layout.addWidget(self.custom_trim_widget, row, 1)
        row += 1

        layout.addWidget(QLabel("Margins"), row, 0)
        layout.addWidget(self.margin_preset_combo, row, 1)
        row += 1

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
        layout.addWidget(self.custom_margin_widget, row, 1)
        row += 1

        layout.addWidget(QLabel("Imposition output"), row, 0)
        layout.addWidget(self.imposition_mode_combo, row, 1)
        row += 1

        layout.addWidget(QLabel("Pages per signature"), row, 0)
        layout.addWidget(self.signature_pages_combo, row, 1)
        row += 1

        layout.addWidget(QLabel("Binding direction"), row, 0)
        layout.addWidget(self.binding_direction_combo, row, 1)
        row += 1

        layout.addWidget(QLabel("Max blank end pages"), row, 0)
        layout.addWidget(self.max_end_padding_combo, row, 1)
        row += 1

        layout.addWidget(QLabel("Editable outputs"), row, 0)

        outputs_container = QWidget()
        outputs_layout = QVBoxLayout(outputs_container)
        outputs_layout.setContentsMargins(0, 0, 0, 0)
        outputs_layout.setSpacing(8)
        outputs_layout.addWidget(self.export_docx_btn)
        outputs_layout.addWidget(self.export_markdown_btn)

        layout.addWidget(outputs_container, row, 1)

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
        preview_splitter.setChildrenCollapsible(False)
        preview_splitter.setHandleWidth(10)

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
        self.open_signature_plan_btn.clicked.connect(self._open_signature_plan)
        self.open_signature_batches_btn.clicked.connect(self._open_signature_batches)
        self.prev_preview_btn.clicked.connect(self._show_previous_preview)
        self.next_preview_btn.clicked.connect(self._show_next_preview)
        self.export_docx_btn.toggled.connect(self._refresh_output_toggle_styles)
        self.export_markdown_btn.toggled.connect(self._refresh_output_toggle_styles)
        self.page_size_combo.currentIndexChanged.connect(self._sync_layout_visibility)
        self.margin_preset_combo.currentIndexChanged.connect(self._sync_layout_visibility)
        self.input_edit.textChanged.connect(self._sync_input_mode)

    def _handle_multiple_files_dropped(self, paths: list[str]) -> None:
        epub_paths = [path for path in paths if Path(path).suffix.lower() == ".epub"]
        ignored = [path for path in paths if Path(path).suffix.lower() != ".epub"]

        if not epub_paths:
            QMessageBox.warning(
                self,
                "No EPUB files",
                "Batch anthology mode currently supports multiple EPUB files only.",
            )
            return

        self.status_label.setText(
            f"Batch anthology mode: {len(epub_paths)} EPUB files detected."
        )

        if ignored:
            self.log_box.appendPlainText(
                f"Batch anthology ignored {len(ignored)} non-EPUB file(s)."
            )

        dialog = BatchAnthologyDialog(
            epub_paths,
            default_output_dir=self.output_edit.text().strip(),
            parent=self,
        )
        dialog.buildCompleted.connect(self._on_batch_anthology_success)
        self.batch_anthology_dialog = dialog
        dialog.show()

    def _input_suffix(self) -> str:
        return Path(self.input_edit.text().strip()).suffix.lower()

    def _is_pdf_input(self) -> bool:
        return self._input_suffix() == ".pdf"

    def _is_epub_input(self) -> bool:
        return self._input_suffix() == ".epub"

    def _sync_input_mode(self) -> None:
        is_pdf = self._is_pdf_input()
        is_known = self._is_epub_input() or is_pdf

        self.process_btn.setText("Process PDF" if is_pdf else "Process EPUB")

        # PDF mode is binding/imposition-only. EPUB-only cleanup/export controls
        # remain visible but disabled so users understand the scope.
        epub_controls_enabled = not is_pdf

        for widget in [
            self.variant_combo,
            self.export_docx_btn,
            self.export_markdown_btn,
            self.spacing_mode_combo,
            self.contents_mode_combo,
            self.page_number_start_combo,
            self.front_matter_numbers_combo,
            self.page_ornament_combo,
            self.page_ornament_amount_combo,
            self.font_combo,
        ]:
            widget.setEnabled(epub_controls_enabled)

        if is_pdf:
            self.export_docx_btn.setChecked(False)
            self.export_markdown_btn.setChecked(False)

            # PDF mode is mainly useful for binding, so default to imposed output
            # unless the user explicitly changes it afterward.
            if self.imposition_mode_combo.currentData() == "none":
                index = self.imposition_mode_combo.findData("also")
                if index >= 0:
                    self.imposition_mode_combo.setCurrentIndex(index)

            self.status_label.setText(
                "PDF mode: binding/imposition only. Cleanup, DOCX, Markdown, fonts, and page-number controls are disabled."
            )
        elif is_known:
            self.status_label.setText("EPUB mode: cleanup, typography, DOCX/Markdown, PDF, and imposition are available.")

        self._refresh_output_toggle_styles()
        self._sync_layout_visibility()


    def _browse_input(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select EPUB or PDF",
            "",
            "Book files (*.epub *.pdf);;EPUB files (*.epub);;PDF files (*.pdf);;All files (*.*)",
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
        enabled = not busy
        is_pdf = self._is_pdf_input()

        self.process_btn.setEnabled(enabled)
        self.browse_input_btn.setEnabled(enabled)
        self.browse_output_btn.setEnabled(enabled)

        # EPUB-only controls.
        self.variant_combo.setEnabled(enabled and not is_pdf)
        self.export_docx_btn.setEnabled(enabled and not is_pdf)
        self.export_markdown_btn.setEnabled(enabled and not is_pdf)
        self.spacing_mode_combo.setEnabled(enabled and not is_pdf)
        self.contents_mode_combo.setEnabled(enabled and not is_pdf)
        self.page_number_start_combo.setEnabled(enabled and not is_pdf)
        self.front_matter_numbers_combo.setEnabled(enabled and not is_pdf)
        self.font_combo.setEnabled(enabled and not is_pdf)

        # Layout/binding controls remain available for both modes.
        self.page_size_combo.setEnabled(enabled)
        self.margin_preset_combo.setEnabled(enabled)
        self.trim_width_spin.setEnabled(enabled)
        self.trim_height_spin.setEnabled(enabled)
        self.margin_top_spin.setEnabled(enabled)
        self.margin_bottom_spin.setEnabled(enabled)
        self.margin_inside_spin.setEnabled(enabled)
        self.margin_outside_spin.setEnabled(enabled)
        self.imposition_mode_combo.setEnabled(enabled)
        self.signature_pages_combo.setEnabled(enabled)
        self.binding_direction_combo.setEnabled(enabled)
        self.max_end_padding_combo.setEnabled(enabled)

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
        self.last_signature_plan = None
        self.last_signature_batches = None
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
        contents_mode = self.contents_mode_combo.currentData() or "rebuild"
        page_number_start_mode = self.page_number_start_combo.currentData() or "after-title-page"
        front_matter_page_number_style = self.front_matter_numbers_combo.currentData() or "hidden"
        page_ornament = self.page_ornament_combo.currentData() or "none"
        page_ornament_amount = self.page_ornament_amount_combo.currentData() or "subtle"
        chapter_ornament = self.chapter_ornament_combo.currentData() or "none"
        page_size_preset = self.page_size_combo.currentData()
        output_font_key = self.font_combo.currentData() or "classic-serif"
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
            QMessageBox.warning(self, "Missing input", "Please choose an EPUB or PDF file.")
            return

        if not Path(input_path).exists():
            QMessageBox.warning(self, "Invalid input", "The selected input file does not exist.")
            return

        input_suffix = Path(input_path).suffix.lower()
        if input_suffix not in {".epub", ".pdf"}:
            QMessageBox.warning(self, "Invalid input", "Please choose a file with the .epub or .pdf extension.")
            return

        if input_suffix == ".pdf":
            export_docx = False
            export_markdown = False

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
            output_font_key=output_font_key,
            contents_mode=contents_mode,
            page_number_start_mode=page_number_start_mode,
            front_matter_page_number_style=front_matter_page_number_style,
            page_ornament=page_ornament,
            page_ornament_amount=page_ornament_amount,
            chapter_ornament=chapter_ornament,
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
        if payload.get("input_type") == "batch-anthology":
            lines = [
                "Input type: Batch anthology",
                f"Title: {payload.get('title', '')}",
                f"Author/editor: {payload.get('author', '')}",
                f"Markdown: {payload.get('markdown_path', '')}",
                f"Manifest: {payload.get('manifest_json_path', '')}",
                "",
                "Inputs:",
            ]

            for item in payload.get("inputs", []):
                lines.append(
                    f"- {item.get('title', '')} by {item.get('author', '')} "
                    f"({item.get('section_count', 0)} sections)"
                )

            if payload.get("warnings"):
                lines.extend(["", "Warnings:"])
                for warning in payload.get("warnings", []):
                    lines.append(f"- {warning}")

            return "\n".join(lines)

        if payload.get("input_type") == "pdf":
            lines = [
                "Input type: PDF",
                "Workflow: binding/imposition only",
                f"Input PDF: {payload.get('input_pdf', '')}",
                f"Interior PDF: {payload.get('interior_pdf') or payload.get('output_pdf', '')}",
                f"Page count: {payload.get('page_count', 'N/A')}",
            ]

            if payload.get("create_imposed_pdf"):
                lines.extend([
                    "",
                    "Imposed signature PDF:",
                    f"Imposed PDF: {payload.get('imposed_output_pdf') or payload.get('imposed_pdf', '')}",
                    f"Pages per signature: {payload.get('imposed_pages_per_signature', 'N/A')}",
                    f"Binding direction: {payload.get('binding_direction_label', '')}",
                    f"Max blank end pages: {payload.get('max_end_padding_label', '')}",
                    f"Signature plan: {payload.get('signature_plan_markdown', '')}",
                ])

            lines.extend([
                "",
                "Note: PDF mode does not run EPUB cleanup, typography reflow, DOCX export, Markdown export, or OCR.",
            ])
            return "\n".join(lines)

        lines = [
            f"Title: {payload.get('title', '')}",
            f"Author: {payload.get('author', '')}",
            f"Cleanup mode: {payload.get('variant_label', payload.get('variant', ''))}",
            f"Paragraph spacing mode: {payload.get('paragraph_spacing_mode_label', '')}",
            f"Output font: {payload.get('output_font_label', '')}",
            f"Contents mode: {payload.get('contents_mode', '')}",
            f"Page number start: {payload.get('page_number_start_mode', '')}",
            f"Front matter numbers: {payload.get('front_matter_page_number_style', '')}",
            f"Page ornament: {payload.get('page_ornament', '')}",
            f"Page ornament amount: {payload.get('page_ornament_amount', '')}",
            f"Chapter ornament: {payload.get('chapter_ornament', '')}",
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
                f"Signature plan: {payload.get('signature_plan_markdown', '')}",
                f"Signature batches: {payload.get('signature_batches_markdown') or payload.get('signature_batches_docx') or ''}",
            ])

        lines.extend([
            "",
            f"Text cleanup preview changes found: {payload.get('preview_sample_count', 0)}",
        ])

        return "\n".join(lines)

    def _on_batch_anthology_success(self, payload: dict) -> None:
        self.last_output_dir = payload.get("output_dir", "")
        self.last_output_markdown = payload.get("markdown_path", "")
        self.last_output_pdf = ""
        self.last_output_docx = ""
        self.last_imposed_pdf = ""
        self.last_signature_plan = ""

        self.results_box.setPlainText(self._build_results_text(payload))
        self.open_output_btn.setEnabled(bool(self.last_output_dir))
        self.open_markdown_btn.setEnabled(bool(self.last_output_markdown))
        self.open_pdf_btn.setEnabled(False)
        self.open_docx_btn.setEnabled(False)
        self.open_imposed_btn.setEnabled(False)
        self.open_signature_plan_btn.setEnabled(False)
        self.status_label.setText("Batch anthology build complete.")

    def _on_success(self, payload: dict) -> None:
        self.last_output_dir = payload.get("output_dir", "")
        self.last_output_pdf = payload.get("output_pdf", "") or payload.get("interior_pdf", "")
        self.last_output_docx = payload.get("output_docx", "")
        self.last_output_markdown = payload.get("output_markdown", "")
        self.last_imposed_pdf = payload.get("imposed_output_pdf", "") or payload.get("imposed_pdf", "")
        self.last_signature_plan = payload.get("signature_plan_markdown") or payload.get("signature_plan_json") or ""
        self.last_signature_batches = payload.get("signature_batches_markdown") or payload.get("signature_batches_docx") or ""

        self.open_output_btn.setEnabled(bool(self.last_output_dir))
        self.open_pdf_btn.setEnabled(bool(self.last_output_pdf))
        self.open_docx_btn.setEnabled(bool(self.last_output_docx))
        self.open_markdown_btn.setEnabled(bool(self.last_output_markdown))
        self.open_imposed_btn.setEnabled(bool(self.last_imposed_pdf))
        self.open_signature_plan_btn.setEnabled(bool(self.last_signature_plan))
        self.open_signature_batches_btn.setEnabled(bool(self.last_signature_batches))

        self.results_box.setPlainText(self._build_results_text(payload))

        self.preview_samples = payload.get("preview_samples", []) or []
        self.current_preview_index = 0
        if payload.get("input_type") == "pdf":
            self.preview_heading_label.setText("Text preview sample: PDF mode")
            self.preview_index_label.setText("0 / 0")
            self.before_preview.setPlainText("PDF mode uses the existing PDF pages as the source.")
            self.after_preview.setPlainText("No EPUB cleanup or text preview is generated for PDF binding mode.")
            self.prev_preview_btn.setEnabled(False)
            self.next_preview_btn.setEnabled(False)
        else:
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

    def _open_path(self, path_value: str | None, label: str = "file") -> None:
        if not path_value:
            QMessageBox.warning(self, "Nothing to open", f"No {label} is available yet.")
            return

        path = Path(path_value).expanduser().resolve()
        if not path.exists():
            QMessageBox.warning(self, "File not found", f"The {label} does not exist:\n{path}")
            return

        try:
            if sys.platform.startswith("linux"):
                subprocess.Popen(
                    ["xdg-open", str(path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return

            if sys.platform == "darwin":
                subprocess.Popen(
                    ["open", str(path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return

            if os.name == "nt":
                os.startfile(str(path))  # type: ignore[attr-defined]
                return

        except Exception as exc:
            QMessageBox.critical(self, "Open failed", f"Could not open {label}:\n{path}\n\n{exc}")
            return

        QMessageBox.warning(self, "Open failed", f"Could not open {label}:\n{path}")

    def _open_output_folder(self) -> None:
        self._open_path(self.last_output_dir, "output folder")
    def _open_pdf(self) -> None:
        self._open_path(self.last_output_pdf, "PDF")
    def _open_docx(self) -> None:
        self._open_path(self.last_output_docx, "DOCX")
    def _open_markdown(self) -> None:
        self._open_path(self.last_output_markdown, "Markdown")
    def _open_signature_plan(self) -> None:
        self._open_path(self.last_signature_plan, "signature plan")
    def _open_signature_batches(self) -> None:
        self._open_path(self.last_signature_batches, "signature batches")
    def _open_imposed_pdf(self) -> None:
        self._open_path(self.last_imposed_pdf, "imposed PDF")
    def _chapterfold_collect_current_settings_for_diagnostics(self):
        """Best-effort settings capture for support reports.

        This intentionally avoids document contents. It tries common attribute names
        without assuming a specific UI implementation.
        """
        settings = {}
        for name in (
            "settings",
            "current_settings",
            "processing_settings",
            "last_settings",
        ):
            if hasattr(self, name):
                value = getattr(self, name)
                try:
                    settings[name] = dict(value) if isinstance(value, dict) else repr(value)
                except Exception:
                    settings[name] = "unavailable"
        return settings

    def _copy_diagnostic_report(self):
        """Copy a privacy-conscious diagnostic report to the clipboard."""
        report = build_diagnostic_report(
            app_version=getattr(self, "APP_VERSION", "unknown"),
            stage="manual GUI report",
            settings=self._chapterfold_collect_current_settings_for_diagnostics(),
        )
        QApplication.clipboard().setText(report)
        QMessageBox.information(self, "ChapterFOLD", "Diagnostic report copied to clipboard.")

    def _install_diagnostics_menu_action(self):
        """Add Help > Copy diagnostic report if a menu bar is available."""
        try:
            menu_bar = self.menuBar()
            help_menu = None
            for action in menu_bar.actions():
                if action.text().replace("&", "").lower() == "help":
                    help_menu = action.menu()
                    break
            if help_menu is None:
                help_menu = menu_bar.addMenu("Help")
            diagnostic_action = QAction("Copy diagnostic report", self)
            diagnostic_action.triggered.connect(self._copy_diagnostic_report)
            help_menu.addAction(diagnostic_action)
        except Exception:
            # Diagnostics must never prevent the app from starting.
            pass

