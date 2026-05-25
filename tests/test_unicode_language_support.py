from __future__ import annotations

from pathlib import Path

from core.epub_service import (
    CleanupSettings,
    LayoutSettings,
    build_css,
    extract_clean_text_from_html,
)
from core.font_policy import UNICODE_PDF_FONT_STACK
from core.markdown_book_renderer import markdown_to_html_body, render_markdown_book


def test_unicode_cleanup_preserves_latin_accents_and_non_latin_text():
    html = """
    <body>
      <p>Swedish: ö ä å. German: Fußgänger. Spanish: niño. French: café.</p>
      <p>Greek: Καλημέρα κόσμε.</p>
      <p>Chinese: 你好，世界。孟子曰：仁者愛人。</p>
    </body>
    """

    text = extract_clean_text_from_html(html, cleanup_settings=CleanupSettings())

    assert "ö ä å" in text
    assert "Fußgänger" in text
    assert "niño" in text
    assert "café" in text
    assert "Καλημέρα κόσμε" in text
    assert "你好，世界" in text
    assert "孟子曰" in text


def test_pdf_css_uses_unicode_font_fallbacks():
    css = build_css(LayoutSettings())

    assert "Noto Serif CJK SC" in css
    assert "Noto Sans CJK SC" in css
    assert "DejaVu Serif" in css


def test_markdown_html_preserves_unicode_text():
    markdown = "# Unicode Book\n\n## CHAPTER I\n\nö ä å café 你好，世界。"

    html = markdown_to_html_body(markdown)

    assert "ö ä å café" in html
    assert "你好，世界" in html


def test_markdown_render_roundtrip_unicode_no_pdf(tmp_path):
    src = tmp_path / "unicode.md"
    out = tmp_path / "out"
    src.write_text(
        "# Unicode Book\n\n_By Åsa Müller_\n\n## CHAPTER I\n\nö ä å café 你好，世界。",
        encoding="utf-8",
    )

    result = render_markdown_book(src, out, export_pdf=False, copy_markdown=True)

    assert result.success
    copied = Path(result.output_files[0]).read_text(encoding="utf-8")
    assert "Åsa Müller" in copied
    assert "你好，世界" in copied
    assert "ö ä å café" in copied


def test_font_policy_contains_cjk_fallbacks():
    assert "Noto Serif CJK SC" in UNICODE_PDF_FONT_STACK
    assert "WenQuanYi Micro Hei" in UNICODE_PDF_FONT_STACK
