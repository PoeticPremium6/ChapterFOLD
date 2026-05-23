from __future__ import annotations

from docx import Document

from core.epub_service import LayoutSettings, _apply_docx_paragraph_format


def _indent_pt_for_mode(mode: str) -> float:
    doc = Document()
    paragraph = doc.add_paragraph("First body paragraph.")
    _apply_docx_paragraph_format(
        paragraph,
        LayoutSettings(paragraph_spacing_mode=mode),
        is_first_in_block=True,
    )
    indent = paragraph.paragraph_format.first_line_indent
    return 0.0 if indent is None else indent.pt


def test_docx_first_paragraph_indents_in_indented_compact():
    assert _indent_pt_for_mode("indented-compact") > 0


def test_docx_first_paragraph_indents_in_traditional():
    assert _indent_pt_for_mode("traditional") > 0


def test_docx_first_paragraph_does_not_indent_in_no_indent_modes():
    assert _indent_pt_for_mode("no-indents") == 0
    assert _indent_pt_for_mode("uniform") == 0
