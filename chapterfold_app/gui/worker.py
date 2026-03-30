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
    ) -> None:
        super().__init__()
        self.input_epub = input_epub
        self.output_dir = output_dir
        self.variant = variant
        self.export_docx = export_docx

    @Slot()
    def run(self) -> None:
        try:
            result = run_processing(
                input_epub=Path(self.input_epub),
                output_dir=Path(self.output_dir),
                variant=self.variant,
                export_docx=self.export_docx,
                log_callback=self.log.emit,
            )
            self.success.emit(
                {
                    "output_pdf": str(result.output_pdf),
                    "output_docx": str(result.output_docx) if result.output_docx else "",
                    "title": result.used_title,
                    "author": result.used_author,
                    "output_dir": str(result.output_dir),
                }
            )
        except Exception:
            self.error.emit(traceback.format_exc())
        finally:
            self.finished.emit()
