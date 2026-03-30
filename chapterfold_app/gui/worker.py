from __future__ import annotations

import traceback
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from services.chapterfold_runner import run_processing


class Worker(QObject):
    finished = Signal()
    error = Signal(str)
    log = Signal(str)
    success = Signal(str)

    def __init__(self, input_epub: str, output_dir: str, variant: str) -> None:
        super().__init__()
        self.input_epub = input_epub
        self.output_dir = output_dir
        self.variant = variant

    @Slot()
    def run(self) -> None:
        try:
            self.log.emit(f"Input: {self.input_epub}")
            self.log.emit(f"Output: {self.output_dir}")
            self.log.emit(f"Variant: {self.variant}")
            output_path = run_processing(
                input_epub=Path(self.input_epub),
                output_dir=Path(self.output_dir),
                variant=self.variant,
                log_callback=self.log.emit,
            )
            self.success.emit(str(output_path))
        except Exception:
            self.error.emit(traceback.format_exc())
        finally:
            self.finished.emit()
