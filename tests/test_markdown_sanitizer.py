from __future__ import annotations

from core.markdown_sanitizer import sanitize_chapterfold_markdown_for_render


def test_sanitize_removes_chapterfold_structural_markup():
    raw = """<section class="chapterfold-title-page">
Fairy Tales
By Various Authors
</section>

<div class="chapterfold-page-break"></div>

<!-- ANTHOLOGYSOURCEINDEX: 1 -->
# Alice
"""

    cleaned = sanitize_chapterfold_markdown_for_render(raw)

    assert '<section class="chapterfold-title-page">' not in cleaned
    assert "</section>" not in cleaned
    assert "<!-- ANTHOLOGYSOURCEINDEX" not in cleaned
    assert "Fairy Tales" in cleaned
    assert "By Various Authors" in cleaned
    assert "# Alice" in cleaned


def test_sanitize_converts_page_break_marker():
    raw = "A\n\n<div class=\"chapterfold-page-break\"></div>\n\nB"

    cleaned = sanitize_chapterfold_markdown_for_render(raw)

    assert "chapterfold-page-break" not in cleaned
    assert 'page-break-after: always' in cleaned
