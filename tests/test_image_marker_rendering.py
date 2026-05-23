from __future__ import annotations

from core.epub_service import (
    _clean_heading_candidate,
    _image_payload_encode,
    _image_marker_to_html,
    extract_clean_text_from_html,
    sanitize_section_html,
)


def _marker() -> str:
    payload = _image_payload_encode(
        src="data:image/png;base64,abc123",
        alt="She is tolerable",
        name="i_001.png",
    )
    return f"[[CHAPTERFOLD_IMAGE:{payload}]]"


def test_image_marker_renders_as_figure_not_visible_placeholder():
    marker = _marker()
    html = f"<body><p>{marker}</p></body>"

    rendered = sanitize_section_html(html)

    assert 'class="book-image"' in rendered
    assert "[[CHAPTERFOLD_IMAGE:" not in rendered


def test_image_marker_is_not_used_as_heading():
    assert _clean_heading_candidate(_marker()) == ""


def test_orphan_copyright_caption_is_removed():
    html = """
    <body>
      <p>[ Copyright 1894 by George Allen. ]</p>
      <p>This was invitation enough.</p>
    </body>
    """

    rendered = sanitize_section_html(html)
    text = extract_clean_text_from_html(html)

    assert "Copyright 1894" not in rendered
    assert "Copyright 1894" not in text
    assert "This was invitation enough." in rendered
