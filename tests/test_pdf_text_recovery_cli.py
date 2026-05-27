from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfWriter

from scripts.run_pdf_text_recovery import main as recovery_main


def make_blank_pdf(path: Path, pages: int = 2) -> None:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=300, height=400)
    with path.open("wb") as f:
        writer.write(f)


def test_pdf_text_recovery_cli_exports_markdown_by_default(tmp_path):
    pdf = tmp_path / "blank.pdf"
    out = tmp_path / "out"
    report = tmp_path / "report.json"
    make_blank_pdf(pdf)

    exit_code = recovery_main([str(pdf), str(out), "--report-json", str(report)])

    assert exit_code == 0
    data = json.loads(report.read_text(encoding="utf-8"))

    assert data["input_type"] == "pdf-text-recovery"
    assert data["success"]
    assert data["markdown_path"]
    assert Path(data["markdown_path"]).exists()
    assert data["quality_report"]["ocr_needed"] == "yes"


def test_pdf_text_recovery_cli_exports_docx_when_requested(tmp_path):
    pdf = tmp_path / "blank.pdf"
    out = tmp_path / "out"
    report = tmp_path / "report.json"
    make_blank_pdf(pdf)

    exit_code = recovery_main(
        [
            str(pdf),
            str(out),
            "--export-markdown",
            "--export-docx",
            "--report-json",
            str(report),
        ]
    )

    assert exit_code == 0
    data = json.loads(report.read_text(encoding="utf-8"))

    assert Path(data["markdown_path"]).exists()
    assert Path(data["docx_path"]).exists()
