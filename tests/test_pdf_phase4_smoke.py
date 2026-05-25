from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader

from core.pdf_binding_service import process_pdf_for_binding
from chapterfold_app.services.input_runner import detect_input_kind, run_input_processing
from core.schemas import ChapterfoldSettings
from scripts.run_chapterfold_input_job import main as input_cli_main


FIXTURE = Path("tests/fixtures/pdf/simple-binding.pdf")


def test_pdf_fixture_exists_and_has_pages():
    assert FIXTURE.exists()
    assert len(PdfReader(str(FIXTURE)).pages) == 7


def test_pdf_binding_fixture_outputs_interior_and_signature_files(tmp_path):
    result = process_pdf_for_binding(
        FIXTURE,
        tmp_path,
        create_imposed_pdf=True,
        pages_per_signature=4,
    )

    assert result.success
    assert result.page_count == 7
    assert result.interior_pdf.exists()
    assert result.imposed_pdf is not None and result.imposed_pdf.exists()
    assert result.signature_plan_json is not None and result.signature_plan_json.exists()
    assert result.signature_plan_markdown is not None and result.signature_plan_markdown.exists()


def test_input_runner_routes_pdf_fixture_to_pdf_pipeline(tmp_path):
    settings = ChapterfoldSettings(
        create_imposed_pdf=True,
        imposed_pages_per_signature=4,
    )

    payload = run_input_processing(FIXTURE, tmp_path, settings)

    assert payload["success"]
    assert payload["input_type"] == "pdf"
    assert payload["page_count"] == 7
    assert Path(payload["interior_pdf"]).exists()
    assert Path(payload["imposed_pdf"]).exists()
    assert Path(payload["signature_plan_json"]).exists()
    assert Path(payload["signature_plan_markdown"]).exists()


def test_dual_input_cli_pdf_fixture_smoke(tmp_path):
    report = tmp_path / "report.json"

    exit_code = input_cli_main(
        [
            str(FIXTURE),
            str(tmp_path),
            "--impose",
            "--signature-pages",
            "4",
            "--report-json",
            str(report),
        ]
    )

    assert exit_code == 0
    data = json.loads(report.read_text(encoding="utf-8"))

    assert data["success"]
    assert data["input_type"] == "pdf"
    assert data["page_count"] == 7
    assert Path(data["interior_pdf"]).exists()
    assert Path(data["imposed_pdf"]).exists()
    assert Path(data["signature_plan_json"]).exists()
    assert Path(data["signature_plan_markdown"]).exists()


def test_detect_input_kind_accepts_pdf_and_epub():
    assert detect_input_kind("book.pdf") == "pdf"
    assert detect_input_kind("book.epub") == "epub"
