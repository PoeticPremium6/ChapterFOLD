from __future__ import annotations

import json
import subprocess
import sys
import traceback
from pathlib import Path
from zipfile import BadZipFile

from PySide6.QtCore import QObject, Signal, Slot
from ebooklib.epub import EpubException

try:
    from chapterfold_app.services.chapterfold_runner import run_processing
except ModuleNotFoundError:
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
        export_markdown: bool,
        paragraph_spacing_mode: str,
        margin_preset: str,
        page_size_preset: str,
        custom_trim_width_cm: float | None,
        custom_trim_height_cm: float | None,
        custom_margin_top_cm: float | None,
        custom_margin_bottom_cm: float | None,
        custom_margin_inside_cm: float | None,
        custom_margin_outside_cm: float | None,
        output_font_key: str = "classic-serif",
        contents_mode: str = "rebuild",
        page_number_start_mode: str = "after-title-page",
        front_matter_page_number_style: str = "hidden",
        imposition_mode: str = "none",
        imposed_pages_per_signature: int = 16,
        binding_direction: str = "ltr",
        max_end_padding: int | None = None,
    ) -> None:
        super().__init__()

        # Kept as input_epub for compatibility with the existing MainWindow call.
        self.input_epub = input_epub
        self.input_path = input_epub
        self.output_dir = output_dir
        self.variant = variant
        self.export_docx = export_docx
        self.export_markdown = export_markdown
        self.paragraph_spacing_mode = paragraph_spacing_mode
        self.margin_preset = margin_preset
        self.page_size_preset = page_size_preset
        self.custom_trim_width_cm = custom_trim_width_cm
        self.custom_trim_height_cm = custom_trim_height_cm
        self.custom_margin_top_cm = custom_margin_top_cm
        self.custom_margin_bottom_cm = custom_margin_bottom_cm
        self.custom_margin_inside_cm = custom_margin_inside_cm
        self.custom_margin_outside_cm = custom_margin_outside_cm
        self.output_font_key = output_font_key
        self.contents_mode = contents_mode
        self.page_number_start_mode = page_number_start_mode
        self.front_matter_page_number_style = front_matter_page_number_style
        self.imposition_mode = imposition_mode
        self.imposed_pages_per_signature = imposed_pages_per_signature
        self.binding_direction = binding_direction
        self.max_end_padding = max_end_padding

    def _run_pdf_subprocess(self, input_pdf: Path, output_dir: Path) -> dict:
        output_dir.mkdir(parents=True, exist_ok=True)
        report_json = output_dir / ".chapterfold_pdf_gui_report.json"

        cmd = [
            sys.executable,
            "-m",
            "scripts.run_chapterfold_input_job",
            str(input_pdf),
            str(output_dir),
            "--report-json",
            str(report_json),
        ]

        if self.imposition_mode != "none":
            cmd.append("--impose")

        cmd.extend(["--signature-pages", str(self.imposed_pages_per_signature)])
        cmd.extend(["--binding-direction", str(self.binding_direction)])

        if self.max_end_padding is not None:
            cmd.extend(["--max-end-padding", str(self.max_end_padding)])

        self.log.emit("PDF mode: starting binding/imposition subprocess...")
        self.log.emit("PDF mode: this may take a while for large or complex PDFs.")

        proc = subprocess.run(
            cmd,
            cwd=str(Path(__file__).resolve().parents[2]),
            text=True,
            capture_output=True,
        )

        if proc.stdout.strip():
            for line in proc.stdout.strip().splitlines():
                self.log.emit(line)

        if proc.returncode != 0:
            detail = proc.stderr.strip() or proc.stdout.strip() or "Unknown PDF subprocess error."
            raise RuntimeError(f"PDF binding subprocess failed:\n{detail}")

        if not report_json.exists():
            raise RuntimeError(f"PDF subprocess completed but did not write report:\n{report_json}")

        payload = json.loads(report_json.read_text(encoding="utf-8"))

        # Normalize keys for the existing GUI result/open-button code.
        payload.setdefault("input_type", "pdf")
        payload["output_pdf"] = payload.get("interior_pdf") or payload.get("output_pdf", "")
        payload["imposed_output_pdf"] = payload.get("imposed_pdf") or payload.get("imposed_output_pdf", "")
        payload["create_imposed_pdf"] = bool(payload.get("imposed_output_pdf"))
        payload["export_docx"] = False
        payload["export_markdown"] = False
        payload["preview_sample_count"] = 0
        payload["preview_samples"] = []
        payload["imposed_pages_per_signature"] = self.imposed_pages_per_signature
        payload["binding_direction_label"] = self.binding_direction.upper()
        payload["max_end_padding_label"] = "Default" if self.max_end_padding is None else str(self.max_end_padding)

        self.log.emit("PDF mode: binding/imposition completed.")
        return payload

    @Slot()
    def run(self) -> None:
        try:
            input_path = Path(self.input_path)
            output_dir = Path(self.output_dir)

            if input_path.suffix.lower() == ".pdf":
                payload = self._run_pdf_subprocess(input_path, output_dir)
                self.success.emit(payload)
                return

            payload = run_processing(
                input_epub=input_path,
                output_dir=output_dir,
                variant=self.variant,
                export_docx=self.export_docx,
                export_markdown=self.export_markdown,
                paragraph_spacing_mode=self.paragraph_spacing_mode,
                margin_preset=self.margin_preset,
                page_size_preset=self.page_size_preset,
                custom_trim_width_cm=self.custom_trim_width_cm,
                custom_trim_height_cm=self.custom_trim_height_cm,
                custom_margin_top_cm=self.custom_margin_top_cm,
                custom_margin_bottom_cm=self.custom_margin_bottom_cm,
                custom_margin_inside_cm=self.custom_margin_inside_cm,
                custom_margin_outside_cm=self.custom_margin_outside_cm,
                output_font_key=self.output_font_key,
                contents_mode=self.contents_mode,
                page_number_start_mode=self.page_number_start_mode,
                front_matter_page_number_style=self.front_matter_page_number_style,
                imposition_mode=self.imposition_mode,
                imposed_pages_per_signature=self.imposed_pages_per_signature,
                binding_direction=self.binding_direction,
                max_end_padding=self.max_end_padding,
                log_callback=self.log.emit,
            )
            payload.setdefault("input_type", "epub")
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
