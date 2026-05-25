from __future__ import annotations

from docx.oxml.ns import qn
from core.font_catalog import font_css_stack


UNICODE_PDF_FONT_STACK = font_css_stack("unicode-global")

DOCX_LATIN_FONT = "DejaVu Serif"
DOCX_EAST_ASIA_FONT = "Noto Serif CJK SC"


def apply_docx_unicode_font(run_or_style_font) -> None:
    """Apply a broad Unicode font policy to python-docx runs/styles."""
    try:
        run_or_style_font.name = DOCX_LATIN_FONT
    except Exception:
        pass


def apply_docx_run_unicode_fallback(run) -> None:
    """Set latin and eastAsia run font hints for mixed-language DOCX output."""
    try:
        run.font.name = DOCX_LATIN_FONT
        rpr = run._element.get_or_add_rPr()
        rfonts = rpr.rFonts
        if rfonts is None:
            from docx.oxml import OxmlElement

            rfonts = OxmlElement("w:rFonts")
            rpr.append(rfonts)

        rfonts.set(qn("w:ascii"), DOCX_LATIN_FONT)
        rfonts.set(qn("w:hAnsi"), DOCX_LATIN_FONT)
        rfonts.set(qn("w:cs"), DOCX_LATIN_FONT)
        rfonts.set(qn("w:eastAsia"), DOCX_EAST_ASIA_FONT)
    except Exception:
        return
