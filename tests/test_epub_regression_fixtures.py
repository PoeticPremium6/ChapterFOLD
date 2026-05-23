from __future__ import annotations

import sys
from pathlib import Path

from bs4 import BeautifulSoup
from ebooklib import ITEM_DOCUMENT, epub

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.text_cleanup import CleanupSettings, clean_text_block
from scripts.build_sample_epubs import build_sample_epubs


def _document_text(epub_path: Path) -> str:
    book = epub.read_epub(str(epub_path))
    chunks: list[str] = []
    for item in book.get_items_of_type(ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "html.parser")
        chunks.append(soup.get_text("\n"))
    return "\n".join(chunks)


def test_sample_epub_builder_writes_valid_epubs(tmp_path):
    fixture_dir = tmp_path / "epubs"
    paths = build_sample_epubs(fixture_dir)

    assert {p.name for p in paths} == {
        "scene-breaks.epub",
        "dialogue-softwrap.epub",
        "unicode-punctuation.epub",
    }
    assert (fixture_dir / "manifest.json").exists()

    for path in paths:
        book = epub.read_epub(str(path))
        assert book.get_metadata("DC", "title")
        assert list(book.get_items_of_type(ITEM_DOCUMENT))


def test_scene_break_fixture_preserves_scene_marker_after_cleanup(tmp_path):
    paths = build_sample_epubs(tmp_path)
    scene_epub = next(path for path in paths if path.name == "scene-breaks.epub")

    raw_text = _document_text(scene_epub)
    cleaned = clean_text_block(raw_text, CleanupSettings(preserve_scene_breaks=True))

    assert "The rain softened" in cleaned
    assert "* * *" in cleaned
    assert "By morning" in cleaned


def test_dialogue_softwrap_fixture_joins_dialogue_continuation(tmp_path):
    paths = build_sample_epubs(tmp_path)
    dialogue_epub = next(path for path in paths if path.name == "dialogue-softwrap.epub")

    raw_text = _document_text(dialogue_epub)
    cleaned = clean_text_block(
        raw_text,
        CleanupSettings(join_soft_wrapped_lines=True, join_dialogue_continuations=True),
    )

    assert '"I can fold this," she said.' in cleaned
    assert "split across two visual lines" in cleaned


def test_unicode_punctuation_fixture_survives_extraction(tmp_path):
    paths = build_sample_epubs(tmp_path)
    unicode_epub = next(path for path in paths if path.name == "unicode-punctuation.epub")

    raw_text = _document_text(unicode_epub)
    cleaned = clean_text_block(raw_text)

    assert "Wait—don’t trim" in cleaned
    assert "Café" in cleaned
    assert "naïve" in cleaned
