from __future__ import annotations

from core.gutenberg_inline_trim import (
    trim_gutenberg_boilerplate_from_sections,
    trim_gutenberg_inline_boilerplate_text,
)


def test_trim_text_before_start_marker():
    text = "Usage notice\n\n*** START OF THE PROJECT GUTENBERG EBOOK TEST ***\nReal beginning\nMore text"
    trimmed, actions = trim_gutenberg_inline_boilerplate_text(text)
    assert trimmed.startswith("Real beginning")
    assert "Usage notice" not in trimmed
    assert "trimmed_before_start_marker" in actions


def test_trim_text_after_end_marker():
    text = "Real ending\n*** END OF THE PROJECT GUTENBERG EBOOK TEST ***\nLicense text"
    trimmed, actions = trim_gutenberg_inline_boilerplate_text(text)
    assert trimmed == "Real ending"
    assert "License text" not in trimmed
    assert "trimmed_after_end_marker" in actions


def test_trim_tuple_sections_and_clear_boilerplate_heading():
    sections = [
        (
            "The Project Gutenberg eBook of The Real Cyberpunk Fakebook",
            "This eBook is for use...\n*** START OF THE PROJECT GUTENBERG EBOOK THE REAL CYBERPUNK FAKEBOOK ***\nThe Real Cyberpunk Fakebook, by St. Jude",
        )
    ]
    trimmed = trim_gutenberg_boilerplate_from_sections(sections)
    assert trimmed[0][0] == ""
    assert trimmed[0][1].startswith("The Real Cyberpunk Fakebook")
    assert "This eBook is for use" not in trimmed[0][1]


def test_non_gutenberg_text_is_unchanged():
    sections = [("Chapter 1", "A normal fanfic chapter with no boilerplate.")]
    assert trim_gutenberg_boilerplate_from_sections(sections) == sections
