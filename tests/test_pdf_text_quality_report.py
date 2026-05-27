from __future__ import annotations

from pathlib import Path

from pypdf import PdfWriter

from core.pdf_text_extraction import (
    PdfExtractedPage,
    PdfTextExtractionResult,
    build_pdf_text_quality_report,
    extract_pdf_text_pages,
    pdf_text_to_markdown,
    result_to_dict,
)


def make_blank_pdf(path: Path, pages: int = 3) -> None:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=300, height=400)
    with path.open("wb") as f:
        writer.write(f)


def test_quality_report_marks_blank_pdf_as_ocr_needed(tmp_path):
    pdf = tmp_path / "blank.pdf"
    make_blank_pdf(pdf, pages=3)

    result = extract_pdf_text_pages(pdf)

    assert result.quality_report is not None
    assert result.quality_report.ocr_needed == "yes"
    assert result.quality_report.confidence == "poor"
    assert result.quality_report.empty_pages == [1, 2, 3]
    assert result.quality_report.likely_scanned_pages == [1, 2, 3]


def test_quality_report_good_for_text_like_pages():
    result = PdfTextExtractionResult(
        success=True,
        input_pdf=Path("text.pdf"),
        page_count=2,
        pages=[
            PdfExtractedPage(1, "Chapter One\n" + "Readable text. " * 80, 0),
            PdfExtractedPage(2, "Chapter Two\n" + "More readable text. " * 80, 0),
        ],
    )

    for page in result.pages:
        page.char_count = len(page.text)
    result.total_chars = sum(page.char_count for page in result.pages)

    report = build_pdf_text_quality_report(result)

    assert report.ocr_needed == "no"
    assert report.confidence == "good"
    assert report.empty_pages == []


def test_quality_report_detects_repeated_lines():
    result = PdfTextExtractionResult(
        success=True,
        input_pdf=Path("headers.pdf"),
        page_count=3,
        pages=[
            PdfExtractedPage(1, "Shared Header\nBody one " * 20, 0),
            PdfExtractedPage(2, "Shared Header\nBody two " * 20, 0),
            PdfExtractedPage(3, "Shared Header\nBody three " * 20, 0),
        ],
    )
    for page in result.pages:
        page.char_count = len(page.text)
    result.total_chars = sum(page.char_count for page in result.pages)

    report = build_pdf_text_quality_report(result)

    assert "Shared Header" in report.repeated_line_candidates


def test_markdown_includes_quality_report(tmp_path):
    pdf = tmp_path / "blank.pdf"
    make_blank_pdf(pdf, pages=1)

    result = extract_pdf_text_pages(pdf)
    markdown = pdf_text_to_markdown(result)

    assert "## Extraction Quality Report" in markdown
    assert "OCR needed: yes" in markdown
    assert "Extraction confidence: poor" in markdown


def test_result_to_dict_includes_quality_report(tmp_path):
    pdf = tmp_path / "blank.pdf"
    make_blank_pdf(pdf, pages=1)

    result = extract_pdf_text_pages(pdf)
    data = result_to_dict(result)

    assert data["quality_report"]["ocr_needed"] == "yes"
    assert data["quality_report"]["confidence"] == "poor"
