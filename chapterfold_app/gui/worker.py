from __future__ import annotations

import traceback
from pathlib import Path
from zipfile import BadZipFile

from PySide6.QtCore import QObject, Signal, Slot
from ebooklib.epub import EpubException

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
        create_imposed_pdf: bool,
        imposed_pages_per_signature: int,
        binding_direction: str,
    ) -> None:
        super().__init__()
        self.input_epub = input_epub
        self.output_dir = output_dir
        self.variant = variant
        self.export_docx = export_docx
        self.paragraph_spacing_mode = paragraph_spacing_mode
        self.margin_preset = margin_preset
        self.create_imposed_pdf = create_imposed_pdf
        self.imposed_pages_per_signature = imposed_pages_per_signature
        self.binding_direction = binding_direction

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
                create_imposed_pdf=self.create_imposed_pdf,
                imposed_pages_per_signature=self.imposed_pages_per_signature,
                binding_direction=self.binding_direction,
                log_callback=self.log.emit,
            )
            self.success.emit(payload)

        except (BadZipFile, EpubException):
            self.error.emit(
                "The selected file is not a valid EPUB archive.\n\n"
                "Please make sure you selected a real .epub file and that it is not corrupted."
            )

        except FileNotFoundError as exc:
            self.error.emit(str(exc))

        except Exception:
            self.error.emit(traceback.format_exc())

        finally:
            self.finished.emit()
