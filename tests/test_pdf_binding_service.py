from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader, PdfWriter

from core.pdf_binding_service import (
    count_pdf_pages,
    process_pdf_for_binding,
    safe_pdf_stem,
)


def make_test_pdf(path: Path, pages: int = 5) -> None:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=300, height=400)
    with path.open("wb") as f:
        writer.write(f)


def test_safe_pdf_stem():
    assert safe_pdf_stem(Path('Bad:Name?.pdf')) == "Bad-Name-"


def test_count_pdf_pages(tmp_path):
    pdf = tmp_path / "sample.pdf"
    make_test_pdf(pdf, pages=3)

    assert count_pdf_pages(pdf) == 3


def test_process_pdf_for_binding_copies_interior_pdf(tmp_path):
    pdf = tmp_path / "sample.pdf"
    out = tmp_path / "out"
    make_test_pdf(pdf, pages=3)

    result = process_pdf_for_binding(pdf, out)

    assert result.success
    assert result.page_count == 3
    assert result.interior_pdf.exists()
    assert result.output_files == [result.interior_pdf]
    assert len(PdfReader(str(result.interior_pdf)).pages) == 3


def test_process_pdf_for_binding_with_imposition_outputs_signature_plan(tmp_path):
    pdf = tmp_path / "sample.pdf"
    out = tmp_path / "out"
    make_test_pdf(pdf, pages=5)

    result = process_pdf_for_binding(
        pdf,
        out,
        create_imposed_pdf=True,
        pages_per_signature=4,
    )

    assert result.success
    assert result.imposed_pdf is not None
    assert result.imposed_pdf.exists()
    assert result.signature_plan_json is not None
    assert result.signature_plan_json.exists()
    assert result.signature_plan_markdown is not None
    assert result.signature_plan_markdown.exists()
    assert any(path.name.endswith("Imposed.pdf") for path in result.output_files)
    assert any(path.name.endswith("Signature Plan.json") for path in result.output_files)
    assert any(path.name.endswith("Signature Plan.md") for path in result.output_files)
