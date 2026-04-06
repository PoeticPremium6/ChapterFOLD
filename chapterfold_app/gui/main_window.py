from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gui.worker import Worker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("ChapterFOLD")
        self.resize(900, 720)

        self.thread: QThread | None = None
        self.worker: Worker | None = None
        self.last_output_dir: str | None = None

        self.input_edit = QLineEdit()
        self.output_edit = QLineEdit()

        self.variant_combo = QComboBox()
        self.variant_combo.addItem("standard", "standard")
        self.variant_combo.addItem("aggressive-cleanup", "aggressive-cleanup")
        self.variant_combo.addItem("paragraph-dialogue-merge", "paragraph-dialogue-merge")

        self.export_docx_checkbox = QCheckBox("Also export DOCX")
        self.export_docx_checkbox.setChecked(True)

        self.export_markdown_checkbox = QCheckBox("Also export Markdown")
        self.export_markdown_checkbox.setChecked(False)

        self.spacing_mode_combo = QComboBox()
        self.spacing_mode_combo.addItem("Traditional", "traditional")
        self.spacing_mode_combo.addItem("Uniform", "uniform")
        self.spacing_mode_combo.addItem("No indents", "no-indents")
        self.spacing_mode_combo.addItem("Indented compact", "indented-compact")

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
        for value in (4, 8, 12, 16, 20, 24, 28, 32):
            self.signature_pages_combo.addItem(str(value), value)
        self.signature_pages_combo.setCurrentText("16")

        self.binding_direction_combo = QComboBox()
        self.binding_direction_combo.addItem("Left-to-right", "ltr")
        self.binding_direction_combo.addItem("Right-to-left", "rtl")

        self.max_end_padding_combo = QComboBox()
        self.max_end_padding_combo.addItem("Unlimited", None)
        self.max_end_padding_combo.addItem("0", 0)
        self.max_end_padding_combo.addItem("2", 2)
        self.max_end_padding_combo.addItem("4", 4)
        self.max_end_padding_combo.addItem("8", 8)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        self.browse_input_btn = QPushButton("Browse...")
        self.browse_output_btn = QPushButton("Browse...")
        self.process_btn = QPushButton("Process EPUB")
        self.open_output_btn = QPushButton("Open Output Folder")
        self.open_output_btn.setEnabled(False)

        self._build_ui()
        self._connect_signals()

        default_output = Path.cwd()
        self.output_edit.setText(str(default_output))
        self._sync_layout_visibility()

    def _build_two_spin_row(
        self,
        left_label: str,
        left_spin: QDoubleSpinBox,
        right_label: str,
        right_spin: QDoubleSpinBox,
    ) -> QWidget:
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

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        form = QGridLayout()
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(10)

        form.addWidget(QLabel("Input EPUB:"), 0, 0)
        form.addWidget(self.input_edit, 0, 1)
        form.addWidget(self.browse_input_btn, 0, 2)

        form.addWidget(QLabel("Output folder:"), 1, 0)
        form.addWidget(self.output_edit, 1, 1)
        form.addWidget(self.browse_output_btn, 1, 2)

        form.addWidget(QLabel("Cleanup variant:"), 2, 0)
        form.addWidget(self.variant_combo, 2, 1)

        form.addWidget(QLabel("Paragraph spacing:"), 3, 0)
        form.addWidget(self.spacing_mode_combo, 3, 1)

        form.addWidget(QLabel("Page size:"), 4, 0)
        form.addWidget(self.page_size_combo, 4, 1)

        self.custom_trim_widget = self._build_two_spin_row(
            "Width",
            self.trim_width_spin,
            "Height",
            self.trim_height_spin,
        )
        form.addWidget(self.custom_trim_widget, 5, 1)

        form.addWidget(QLabel("Margin preset:"), 6, 0)
        form.addWidget(self.margin_preset_combo, 6, 1)

        self.custom_margin_widget = QWidget()
        custom_margin_layout = QVBoxLayout(self.custom_margin_widget)
        custom_margin_layout.setContentsMargins(0, 0, 0, 0)
        custom_margin_layout.setSpacing(8)
        custom_margin_layout.addWidget(
            self._build_two_spin_row(
                "Top",
                self.margin_top_spin,
                "Bottom",
                self.margin_bottom_spin,
            )
        )
        custom_margin_layout.addWidget(
            self._build_two_spin_row(
                "Inside",
                self.margin_inside_spin,
                "Outside",
                self.margin_outside_spin,
            )
        )
        form.addWidget(self.custom_margin_widget, 7, 1)

        options_widget = QWidget()
        options_layout = QVBoxLayout(options_widget)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(6)
        options_layout.addWidget(self.export_docx_checkbox)
        options_layout.addWidget(self.export_markdown_checkbox)

        form.addWidget(QLabel("Editable outputs:"), 8, 0)
        form.addWidget(options_widget, 8, 1)

        form.addWidget(QLabel("Imposition output:"), 9, 0)
        form.addWidget(self.imposition_mode_combo, 9, 1)

        form.addWidget(QLabel("Pages per signature:"), 10, 0)
        form.addWidget(self.signature_pages_combo, 10, 1)

        form.addWidget(QLabel("Binding direction:"), 11, 0)
        form.addWidget(self.binding_direction_combo, 11, 1)

        form.addWidget(QLabel("Max blank end pages:"), 12, 0)
        form.addWidget(self.max_end_padding_combo, 12, 1)

        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addWidget(self.open_output_btn)
        buttons.addStretch()
        buttons.addWidget(self.process_btn)
        layout.addLayout(buttons)

        layout.addWidget(QLabel("Log"))
        layout.addWidget(self.log_box)

    def _connect_signals(self) -> None:
        self.browse_input_btn.clicked.connect(self._browse_input)
        self.browse_output_btn.clicked.connect(self._browse_output)
        self.process_btn.clicked.connect(self._start_processing)
        self.open_output_btn.clicked.connect(self._open_output_folder)

        self.page_size_combo.currentIndexChanged.connect(self._sync_layout_visibility)
        self.margin_preset_combo.currentIndexChanged.connect(self._sync_layout_visibility)

    def _sync_layout_visibility(self) -> None:
        custom_size = self.page_size_combo.currentData() == "custom"
        custom_margins = self.margin_preset_combo.currentData() == "custom"

        self.custom_trim_widget.setVisible(custom_size)
        self.custom_margin_widget.setVisible(custom_margins)

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

    def _set_busy(self, busy: bool) -> None:
        self.process_btn.setEnabled(not busy)
        self.browse_input_btn.setEnabled(not busy)
        self.browse_output_btn.setEnabled(not busy)
        self.variant_combo.setEnabled(not busy)
        self.export_docx_checkbox.setEnabled(not busy)
        self.export_markdown_checkbox.setEnabled(not busy)
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

    def _start_processing(self) -> None:
        input_path = self.input_edit.text().strip()
        output_dir = self.output_edit.text().strip()

        variant = self.variant_combo.currentData()
        export_docx = self.export_docx_checkbox.isChecked()
        export_markdown = self.export_markdown_checkbox.isChecked()
        paragraph_spacing_mode = self.spacing_mode_combo.currentData()
        margin_preset = self.margin_preset_combo.currentData()
        page_size_preset = self.page_size_combo.currentData()

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

        if not output_dir:
            QMessageBox.warning(self, "Missing output", "Please choose an output folder.")
            return

        self.log_box.clear()
        self.open_output_btn.setEnabled(False)
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

    def _on_success(self, payload: dict) -> None:
        pdf_path = payload.get("output_pdf", "")
        docx_path = payload.get("output_docx", "")
        markdown_path = payload.get("output_markdown", "")
        title = payload.get("title", "")
        author = payload.get("author", "")
        output_dir = payload.get("output_dir", "")

        self.last_output_dir = output_dir
        self.open_output_btn.setEnabled(bool(output_dir))

        self._append_log("")
        self._append_log(f"Title: {title}")
        self._append_log(f"Author: {author}")
        self._append_log(f"Page size: {payload.get('page_size_preset_label', '')}")
        self._append_log(
            f"Trim size: {payload.get('trim_width_cm', '')} x {payload.get('trim_height_cm', '')} cm"
        )
        self._append_log(f"Margin preset: {payload.get('margin_preset_label', '')}")
        self._append_log(
            "Margins: "
            f"top {payload.get('margin_top_cm', '')}, "
            f"bottom {payload.get('margin_bottom_cm', '')}, "
            f"inside {payload.get('margin_inside_cm', '')}, "
            f"outside {payload.get('margin_outside_cm', '')} cm"
        )
        self._append_log(f"PDF created: {pdf_path}")

        if docx_path:
            self._append_log(f"DOCX created: {docx_path}")
        if markdown_path:
            self._append_log(f"Markdown created: {markdown_path}")

        message = f"Completed successfully.\n\nPDF:\n{pdf_path}"
        if docx_path:
            message += f"\n\nDOCX:\n{docx_path}"
        if markdown_path:
            message += f"\n\nMarkdown:\n{markdown_path}"

        QMessageBox.information(self, "Success", message)

    def _on_error(self, error_text: str) -> None:
        self._append_log(error_text)
        QMessageBox.critical(self, "Error", error_text)

    def _open_output_folder(self) -> None:
        if not self.last_output_dir:
            return

        path = Path(self.last_output_dir)
        if not path.exists():
            QMessageBox.warning(self, "Missing folder", "The output folder no longer exists.")
            return

        os.startfile(str(path))
