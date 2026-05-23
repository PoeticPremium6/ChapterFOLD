from __future__ import annotations

from core.epub_service import (
    _caption_matches_image_alt,
    _clean_heading_candidate,
    _collapse_image_adjacent_captions,
    _image_payload_encode,
    extract_clean_items_from_html,
    extract_clean_text_from_html,
    sanitize_section_html,
)


def _marker(alt: str = "She is tolerable") -> str:
    payload = _image_payload_encode(
        src="data:image/png;base64,abc123",
        alt=alt,
        name="i_001.png",
    )
    return f"[[CHAPTERFOLD_IMAGE:{payload}]]"


def test_image_marker_renders_as_figure_and_never_leaks():
    marker = _marker()
    html = f"<body><p>{marker}</p></body>"

    rendered = sanitize_section_html(html)

    assert 'class="book-image"' in rendered
    assert "[[CHAPTERFOLD_IMAGE:" not in rendered


def test_image_marker_is_not_used_as_heading():
    assert _clean_heading_candidate(_marker()) == ""


def test_copyright_caption_is_removed_from_html_and_text():
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


def test_duplicate_caption_after_image_is_collapsed():
    marker = _marker("She is tolerable")
    items = [
        ("image", marker),
        ("p", "“She is tolerable”"),
        ("p", "[ Copyright 1894 by George Allen. ]"),
        ("p", "Which do you mean?"),
    ]

    collapsed = _collapse_image_adjacent_captions(items)

    assert collapsed == [
        ("image", marker),
        ("p", "Which do you mean?"),
    ]


def test_caption_matching_normalizes_quotes_and_punctuation():
    marker = _marker("She is tolerable")
    assert _caption_matches_image_alt("“She is tolerable”", marker)


def test_extract_items_keeps_image_but_not_duplicate_caption_cluster():
    marker = _marker("He came down to see the place")
    html = f"""
    <body>
      <p>{marker}</p>
      <p>“He came down to see the place”</p>
      <p>[ Copyright 1894 by George Allen. ]</p>
      <p>This was invitation enough.</p>
    </body>
    """

    items = extract_clean_items_from_html(html)

    assert items[0][0] == "image"
    assert all("Copyright 1894" not in value for _, value in items)
    assert all("[[CHAPTERFOLD_IMAGE:" not in value for kind, value in items if kind != "image")
    assert ("p", "This was invitation enough.") in items
