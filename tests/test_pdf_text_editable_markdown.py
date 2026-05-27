from __future__ import annotations

from pathlib import Path

from core.pdf_text_extraction import (
    PdfExtractedPage,
    PdfTextExtractionResult,
    build_pdf_text_quality_report,
    page_text_to_editable_markdown,
    pdf_text_to_markdown,
)


def _result_with_page(text: str) -> PdfTextExtractionResult:
    page = PdfExtractedPage(1, text, len(text))
    result = PdfTextExtractionResult(
        success=True,
        input_pdf=Path("sample.pdf"),
        page_count=1,
        pages=[page],
        total_chars=len(text),
    )
    result.quality_report = build_pdf_text_quality_report(result)
    return result


def test_page_text_to_editable_markdown_joins_wrapped_lines():
    page = PdfExtractedPage(
        1,
        "This is a wrapped\nline that should become one paragraph.\n\nThis is another paragraph.",
        0,
    )

    output = page_text_to_editable_markdown(page)

    assert "This is a wrapped line that should become one paragraph." in output
    assert "This is another paragraph." in output


def test_page_text_to_editable_markdown_dehyphenates_simple_wrap():
    page = PdfExtractedPage(1, "distribu-\nted systems are hard.", 0)

    output = page_text_to_editable_markdown(page)

    assert "distributed systems are hard." in output


def test_page_text_to_editable_markdown_marks_safe_headings():
    page = PdfExtractedPage(1, "CHAPTER ONE\n\nSome text follows.", 0)

    output = page_text_to_editable_markdown(page)

    assert "## CHAPTER ONE" in output


def test_pdf_text_to_markdown_has_editable_draft_banner_and_page_breaks():
    result = _result_with_page("Chapter One\n\nThis is text.")

    markdown = pdf_text_to_markdown(result)

    assert "# Editable draft extracted from: sample" in markdown
    assert "Experimental PDF text recovery" in markdown
    assert "<!-- PDF_PAGE_BREAK: 1 -->" in markdown
    assert "### Page 1" in markdown
    assert "## Extracted Draft" in markdown
