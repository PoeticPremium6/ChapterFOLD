from __future__ import annotations

from core.gutenberg_selector import decide_gutenberg_body_items, apply_gutenberg_selection_to_report


def _item(index, text_chars, *, spine=None, start=False, end=False, toc=False, boilerplate=False, links=0, paras=1, chapters=None):
    return {
        "index": index,
        "href": f"item{index}.html",
        "spine_position": spine if spine is not None else index + 1,
        "text_chars": text_chars,
        "has_gutenberg_start": start,
        "has_gutenberg_end": end,
        "has_toc_hint": toc,
        "has_boilerplate_hint": boilerplate,
        "link_count": links,
        "paragraph_count": paras,
        "chapter_heading_candidates": chapters or [],
        "first_text": "",
        "last_text": "",
    }


def test_selector_drops_gutenberg_frontmatter_and_license():
    report = {
        "total_text_chars": 103_000,
        "html_items": [
            _item(0, 2500, spine=1, start=True, toc=True, boilerplate=True, links=40, paras=5),
            _item(1, 50_000, spine=2, chapters=["CHAPTER I"]),
            _item(2, 50_000, spine=3, chapters=["CHAPTER II"]),
            _item(3, 500, spine=4, end=True),
        ],
    }

    selection = decide_gutenberg_body_items(report)

    assert selection.selected_item_count == 2
    assert selection.selected_text_chars == 100_000
    assert selection.selected_retention_ratio > 0.9
    reasons = [decision.reason for decision in selection.decisions]
    assert "front_gutenberg_notice_or_contents" in reasons
    assert "gutenberg_end_license" in reasons


def test_selector_keeps_short_preface_after_frontmatter():
    report = {
        "total_text_chars": 33_000,
        "html_items": [
            _item(0, 1000, spine=1, start=True, toc=True, boilerplate=True, links=20),
            _item(1, 800, spine=2),
            _item(2, 30_000, spine=3, chapters=["CHAPTER I."]),
            _item(3, 1200, spine=4, end=True),
        ],
    }

    selection = decide_gutenberg_body_items(report)
    selected_indexes = [decision.index for decision in selection.decisions if decision.selected]

    assert selected_indexes == [1, 2]


def test_selector_does_not_drop_large_body_item_with_toc_word():
    report = {
        "total_text_chars": 20_000,
        "html_items": [
            _item(0, 18_000, spine=1, toc=True, links=1, paras=60, chapters=["CHAPTER X."]),
            _item(1, 1000, spine=2, end=True),
        ],
    }

    selection = decide_gutenberg_body_items(report)
    selected_indexes = [decision.index for decision in selection.decisions if decision.selected]

    assert selected_indexes == [0]


def test_apply_selection_updates_legacy_estimate_fields():
    report = {
        "total_text_chars": 100_000,
        "estimated_body_text_chars_between_gutenberg_markers": 345,
        "estimated_body_retention_ratio": 0.003,
        "risk_flags": ["estimated_body_text_very_short", "estimated_body_less_than_25_percent_of_total"],
        "html_items": [
            _item(0, 1000, spine=1, start=True, toc=True, boilerplate=True, links=30),
            _item(1, 80_000, spine=2, chapters=["CHAPTER I"]),
            _item(2, 19_000, spine=3, end=True),
        ],
    }

    updated = apply_gutenberg_selection_to_report(report)

    assert updated["estimated_body_text_chars_between_gutenberg_markers"] == 80_000
    assert updated["spine_selected_body_text_chars"] == 80_000
    assert "estimated_body_text_very_short" not in updated["risk_flags"]
