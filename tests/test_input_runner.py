from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from core.schemas import ChapterfoldSettings
from chapterfold_app.services.input_runner import detect_input_kind, run_input_processing
from scripts.run_chapterfold_input_job import main as input_cli_main


def make_test_pdf(path: Path, pages: int = 5) -> None:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=300, height=400)
    with path.open("wb") as f:
        writer.write(f)


def test_detect_input_kind():
    assert detect_input_kind("book.epub") == "epub"
    assert detect_input_kind("book.pdf") == "pdf"


def test_detect_input_kind_rejects_unknown():
    try:
        detect_input_kind("book.txt")
    except ValueError as exc:
        assert ".epub or .pdf" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_run_input_processing_pdf_binding_only(tmp_path):
    pdf = tmp_path / "book.pdf"
    out = tmp_path / "out"
    make_test_pdf(pdf, pages=3)

    payload = run_input_processing(pdf, out, ChapterfoldSettings())

    assert payload["success"]
    assert payload["input_type"] == "pdf"
    assert payload["page_count"] == 3
    assert Path(payload["interior_pdf"]).exists()
    assert len(PdfReader(payload["interior_pdf"]).pages) == 3


def test_run_input_processing_pdf_with_imposition(tmp_path):
    pdf = tmp_path / "book.pdf"
    out = tmp_path / "out"
    make_test_pdf(pdf, pages=5)

    settings = ChapterfoldSettings(create_imposed_pdf=True, imposed_pages_per_signature=4)
    payload = run_input_processing(pdf, out, settings)

    assert payload["success"]
    assert Path(payload["imposed_pdf"]).exists()
    assert Path(payload["signature_plan_json"]).exists()
    assert Path(payload["signature_plan_markdown"]).exists()


def test_dual_input_cli_pdf_route(tmp_path):
    pdf = tmp_path / "book.pdf"
    out = tmp_path / "out"
    report = tmp_path / "report.json"
    make_test_pdf(pdf, pages=2)

    exit_code = input_cli_main([
        str(pdf),
        str(out),
        "--impose",
        "--signature-pages",
        "4",
        "--report-json",
        str(report),
    ])

    assert exit_code == 0
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["input_type"] == "pdf"
    assert data["page_count"] == 2
    assert Path(data["interior_pdf"]).exists()
    assert Path(data["imposed_pdf"]).exists()
