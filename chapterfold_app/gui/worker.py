from __future__ import annotations

import traceback
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from services.chapterfold_runner import run_processing


class Worker(QObject):
    finished = Signal()
    error = Signal(str)
    log = Signal(str)
    success = Signal(dict)

    def __init__(
        self,
        *,
        input_epub: str,
        output_dir: str,
        variant: str,
        export_docx: bool,
        paragraph_spacing_mode: str,
        margin_preset: str,
    ) -> None:
        super().__init__()
        self.input_epub = input_epub
        self.output_dir = output_dir
        self.variant = variant
        self.export_docx = export_docx
        self.paragraph_spacing_mode = paragraph_spacing_mode
        self.margin_preset = margin_preset

    @Slot()
    def run(self) -> None:
        try:
            payload = run_processing(
                input_epub=Path(self.input_epub),
                output_dir=Path(self.output_dir),
                variant=self.variant,
                export_docx=self.export_docx,
                paragraph_spacing_mode=self.paragraph_spacing_mode,
                margin_preset=self.margin_preset,
                log_callback=self.log.emit,
            )
            self.success.emit(payload)
        except Exception:
            self.error.emit(traceback.format_exc())
        finally:
            self.finished.emit()
