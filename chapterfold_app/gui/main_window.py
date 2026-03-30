from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
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
        self.resize(800, 560)

        self.thread: QThread | None = None
        self.worker: Worker | None = None

        self.input_edit = QLineEdit()
        self.output_edit = QLineEdit()

        self.variant_combo = QComboBox()
        self.variant_combo.addItems([
            "standard",
            "aggressive-cleanup",
            "paragraph-dialogue-merge",
        ])

        self.export_docx_checkbox = QCheckBox("Also export DOCX")
        self.export_docx_checkbox.setChecked(True)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        self.browse_input_btn = QPushButton("Browse...")
        self.browse_output_btn = QPushButton("Browse...")
        self.process_btn = QPushButton("Process EPUB")
        self.open_output_btn = QPushButton("Open Output Folder")
        self.open_output_btn.setEnabled(False)

        self.last_output_dir: str | None = None

        self._build_ui()
        self._connect_signals()

        default_output = Path.cwd()
        self.output_edit.setText(str(default_output))

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        form = QGridLayout()
        form.addWidget(QLabel("Input EPUB:"), 0, 0)
        form.addWidget(self.input_edit, 0, 1)
        form.addWidget(self.browse_input_btn, 0, 2)

        form.addWidget(QLabel("Output folder:"), 1, 0)
        form.addWidget(self.output_edit, 1, 1)
        form.addWidget(self.browse_output_btn, 1, 2)

        form.addWidget(QLabel("Cleanup variant:"), 2, 0)
        form.addWidget(self.variant_combo, 2, 1)

        form.addWidget(QLabel("Options:"), 3, 0)
        form.addWidget(self.export_docx_checkbox, 3, 1)

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

    def _start_processing(self) -> None:
        input_path = self.input_edit.text().strip()
        output_dir = self.output_edit.text().strip()
        variant = self.variant_combo.currentText()
        export_docx = self.export_docx_checkbox.isChecked()

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
        title = payload.get("title", "")
        author = payload.get("author", "")
        output_dir = payload.get("output_dir", "")

        self.last_output_dir = output_dir
        self.open_output_btn.setEnabled(bool(output_dir))

        self._append_log("")
        self._append_log(f"Title: {title}")
        self._append_log(f"Author: {author}")
        self._append_log(f"PDF created: {pdf_path}")
        if docx_path:
            self._append_log(f"DOCX created: {docx_path}")

        message = f"Completed successfully.\n\nPDF:\n{pdf_path}"
        if docx_path:
            message += f"\n\nDOCX:\n{docx_path}"

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

        import os
        os.startfile(str(path))
