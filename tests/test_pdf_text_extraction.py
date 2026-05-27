from __future__ import annotations

from pathlib import Path

from pypdf import PdfWriter

from core.pdf_text_extraction import (
    extract_pdf_text_pages,
    pdf_text_to_markdown,
    result_to_dict,
    write_pdf_text_markdown,
)


def make_blank_pdf(path: Path, pages: int = 2) -> None:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=300, height=400)
    with path.open("wb") as f:
        writer.write(f)


def test_extract_pdf_text_pages_from_blank_pdf(tmp_path):
    pdf = tmp_path / "blank.pdf"
    make_blank_pdf(pdf, pages=2)

    result = extract_pdf_text_pages(pdf)

    assert result.success
    assert result.page_count == 2
    assert len(result.pages) == 2
    assert result.total_chars == 0
    assert any("No extractable text" in warning for warning in result.warnings)


def test_pdf_text_to_markdown_has_page_sections(tmp_path):
    pdf = tmp_path / "blank.pdf"
    make_blank_pdf(pdf, pages=2)

    result = extract_pdf_text_pages(pdf)
    markdown = pdf_text_to_markdown(result)

    assert "# Editable draft extracted from: blank" in markdown
    assert "### Page 1" in markdown
    assert "### Page 2" in markdown
    assert "Experimental PDF text recovery" in markdown


def test_write_pdf_text_markdown(tmp_path):
    pdf = tmp_path / "blank.pdf"
    out = tmp_path / "out"
    make_blank_pdf(pdf, pages=1)

    result = write_pdf_text_markdown(pdf, out)

    assert result.markdown_path is not None
    assert result.markdown_path.exists()
    assert "## Page 1" in result.markdown_path.read_text(encoding="utf-8")


def test_result_to_dict(tmp_path):
    pdf = tmp_path / "blank.pdf"
    make_blank_pdf(pdf, pages=1)

    result = extract_pdf_text_pages(pdf)
    data = result_to_dict(result)

    assert data["success"]
    assert data["page_count"] == 1
    assert data["pages"][0]["page_number"] == 1
