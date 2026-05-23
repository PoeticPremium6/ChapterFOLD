from __future__ import annotations

from core.gutenberg_content_filter import apply_gutenberg_filter_to_records, build_epub_html_record


def _record(index, href, text, *, spine=None):
    return build_epub_html_record(
        index=index,
        href=href,
        spine_position=spine if spine is not None else index + 1,
        heading="",
        body_html=f"<body><p>{text}</p></body>",
    )


def test_non_gutenberg_records_are_kept():
    records = [
        _record(0, "chapter1.xhtml", "A normal non-Gutenberg chapter. " * 100),
        _record(1, "chapter2.xhtml", "Another normal non-Gutenberg chapter. " * 100),
    ]

    selected, report = apply_gutenberg_filter_to_records(records)

    assert selected == records
    assert report["gutenberg_detected"] is False
    assert report["selection_applied"] is False


def test_gutenberg_frontmatter_and_license_are_dropped():
    records = [
        _record(
            0,
            "front.xhtml",
            "The Project Gutenberg eBook of Example. START OF THE PROJECT GUTENBERG EBOOK EXAMPLE. Contents " + "link " * 50,
            spine=1,
        ),
        _record(1, "chapter1.xhtml", "CHAPTER I. " + "Real body text. " * 5000, spine=2),
        _record(2, "chapter2.xhtml", "CHAPTER II. " + "More real body text. " * 5000, spine=3),
        _record(3, "license.xhtml", "END OF THE PROJECT GUTENBERG EBOOK EXAMPLE. Project Gutenberg License.", spine=4),
    ]

    selected, report = apply_gutenberg_filter_to_records(records)
    selected_hrefs = [record["href"] for record in selected]

    assert selected_hrefs == ["chapter1.xhtml", "chapter2.xhtml"]
    assert report["gutenberg_detected"] is True
    assert report["selection_applied"] is True
    assert report["dropped_html_items"] == 2
    assert report["selected_retention_ratio"] > 0.8


def test_gutenberg_selection_falls_back_when_retention_is_dangerously_low():
    records = [
        _record(0, "front.xhtml", "START OF THE PROJECT GUTENBERG EBOOK EXAMPLE Project Gutenberg", spine=1),
        _record(1, "tiny.xhtml", "small", spine=2),
        _record(2, "license.xhtml", "END OF THE PROJECT GUTENBERG EBOOK EXAMPLE", spine=3),
    ]

    selected, report = apply_gutenberg_filter_to_records(records, min_retention_ratio=0.95)

    assert selected == records
    assert report["gutenberg_detected"] is True
    assert report["selection_applied"] is False
    assert report["warnings"]
