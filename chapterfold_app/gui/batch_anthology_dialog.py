from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.batch_anthology_service import anthology_result_to_dict, write_anthology_markdown


class BatchAnthologyDialog(QDialog):
    buildCompleted = Signal(dict)

    def __init__(
        self,
        paths: list[str],
        *,
        default_output_dir: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle("Batch Anthology Builder")
        self.resize(720, 520)

        self.title_edit = QLineEdit("Collected Works")
        self.author_edit = QLineEdit("Various Authors")
        self.output_dir_edit = QLineEdit(default_output_dir)

        self.file_list = QListWidget()
        for path in paths:
            if Path(path).suffix.lower() == ".epub":
                self.file_list.addItem(path)

        self.browse_output_btn = QPushButton("Browse...")
        self.remove_btn = QPushButton("Remove")
        self.up_btn = QPushButton("Move Up")
        self.down_btn = QPushButton("Move Down")
        self.build_btn = QPushButton("Build Anthology")
        self.close_btn = QPushButton("Close")

        self.browse_output_btn.clicked.connect(self._browse_output_dir)
        self.remove_btn.clicked.connect(self._remove_selected)
        self.up_btn.clicked.connect(self._move_selected_up)
        self.down_btn.clicked.connect(self._move_selected_down)
        self.build_btn.clicked.connect(self._build_anthology)
        self.close_btn.clicked.connect(self.close)

        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        note = QLabel(
            "Batch mode combines multiple EPUBs into one editable anthology Markdown file. "
            "PDF batch input and final PDF/DOCX rendering can be added later."
        )
        note.setWordWrap(True)
        root.addWidget(note)

        form = QFormLayout()
        form.addRow("Anthology title", self.title_edit)
        form.addRow("Author/editor line", self.author_edit)

        output_row = QHBoxLayout()
        output_row.addWidget(self.output_dir_edit, 1)
        output_row.addWidget(self.browse_output_btn)
        form.addRow("Output folder", output_row)

        root.addLayout(form)

        root.addWidget(QLabel("Dropped EPUB files"))
        root.addWidget(self.file_list, 1)

        list_buttons = QHBoxLayout()
        list_buttons.addWidget(self.up_btn)
        list_buttons.addWidget(self.down_btn)
        list_buttons.addWidget(self.remove_btn)
        list_buttons.addStretch(1)
        root.addLayout(list_buttons)

        action_row = QHBoxLayout()
        action_row.addStretch(1)
        action_row.addWidget(self.build_btn)
        action_row.addWidget(self.close_btn)
        root.addLayout(action_row)

    def paths(self) -> list[str]:
        return [self.file_list.item(i).text() for i in range(self.file_list.count())]

    def _browse_output_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose output folder", self.output_dir_edit.text())
        if folder:
            self.output_dir_edit.setText(folder)

    def _remove_selected(self) -> None:
        row = self.file_list.currentRow()
        if row >= 0:
            self.file_list.takeItem(row)

    def _move_selected_up(self) -> None:
        row = self.file_list.currentRow()
        if row <= 0:
            return

        item = self.file_list.takeItem(row)
        self.file_list.insertItem(row - 1, item)
        self.file_list.setCurrentRow(row - 1)

    def _move_selected_down(self) -> None:
        row = self.file_list.currentRow()
        if row < 0 or row >= self.file_list.count() - 1:
            return

        item = self.file_list.takeItem(row)
        self.file_list.insertItem(row + 1, item)
        self.file_list.setCurrentRow(row + 1)

    def _build_anthology(self) -> None:
        paths = self.paths()
        if not paths:
            QMessageBox.warning(self, "No files", "Please add at least one EPUB file.")
            return

        output_dir = self.output_dir_edit.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "Missing output folder", "Please choose an output folder.")
            return

        title = self.title_edit.text().strip() or "Collected Works"
        author = self.author_edit.text().strip() or "Various Authors"

        try:
            result = write_anthology_markdown(
                paths,
                output_dir,
                anthology_title=title,
                anthology_author=author,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Batch build failed", str(exc))
            return

        payload = anthology_result_to_dict(result)
        payload["input_type"] = "batch-anthology"
        payload["stage"] = "complete"
        payload["output_files"] = [
            payload["markdown_path"],
            payload["manifest_json_path"],
        ]

        self.buildCompleted.emit(payload)

        QMessageBox.information(
            self,
            "Anthology built",
            f"Created anthology Markdown:\n{payload['markdown_path']}",
        )
