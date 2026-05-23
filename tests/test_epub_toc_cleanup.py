from __future__ import annotations

from core.epub_toc_cleanup import strip_original_toc_blocks
from core.epub_service import extract_clean_text_from_html


def test_strip_gutenberg_toc_link_block_keeps_preface_prose():
    html = """
    <body>
      <div class="blk">
        <p class="toc">
          <a href="#PREFACE">PREFACE.</a><br/>
          <a href="#ILLUSTRATIONS">List of Illustrations.</a><br/>
          <a href="#CHAPTER_I">I.</a><br/>
          <a href="#CHAPTER_II">II.</a><br/>
          <a href="#CHAPTER_III">III.</a><br/>
          <a href="#CHAPTER_IV">IV.</a><br/>
          <a href="#CHAPTER_V">V.</a><br/>
          <a href="#CHAPTER_VI">VI.</a><br/>
          <a href="#CHAPTER_VII">VII.</a><br/>
          <a href="#CHAPTER_VIII">VIII.</a><br/>
        </p>
      </div>
      <h2>PREFACE.</h2>
      <p>This edition of Pride and Prejudice is illustrated.</p>
      <h2>CHAPTER I.</h2>
      <p>It is a truth universally acknowledged.</p>
    </body>
    """

    cleaned = strip_original_toc_blocks(html)

    assert 'href="#CHAPTER_I"' not in cleaned
    assert "This edition of Pride and Prejudice is illustrated." in cleaned
    assert "It is a truth universally acknowledged." in cleaned


def test_extraction_does_not_emit_cramped_original_toc_lines():
    html = """
    <body>
      <p class="toc">
        <a href="#PREFACE">PREFACE.</a><br/>
        <a href="#I">I.</a><br/>
        <a href="#II">II.</a><br/>
        <a href="#III">III.</a><br/>
        <a href="#IV">IV.</a><br/>
        <a href="#V">V.</a><br/>
        <a href="#VI">VI.</a><br/>
        <a href="#VII">VII.</a><br/>
        <a href="#VIII">VIII.</a><br/>
      </p>
      <p>Real preface text remains.</p>
    </body>
    """

    text = extract_clean_text_from_html(html)

    assert "Real preface text remains." in text
    assert "VIII" not in text
