from pathlib import Path
import subprocess
import sys

from core.markdown_book_renderer import (
    build_print_html,
    markdown_to_html_body,
    parse_markdown_metadata,
    render_markdown_book,
)


def test_parse_chapterfold_markdown_metadata():
    md = "# Test Book\n\n_By Jane Example_\n\n## Chapter 1\n\nHello."
    metadata = parse_markdown_metadata(md)
    assert metadata.title == "Test Book"
    assert metadata.author == "Jane Example"


def test_markdown_to_html_body_preserves_basic_structure():
    md = "# Title\n\n_By Author_\n\n## Chapter 1\n\nHello *world*.\n\n***\n\nNext."
    html = markdown_to_html_body(md)
    assert "<h1>Title</h1>" in html
    assert "<h2>Chapter 1</h2>" in html
    assert "<em>world</em>" in html
    assert "<hr>" in html


def test_build_print_html_contains_title_page():
    html = build_print_html("# My Book\n\n_By Me_\n\nText.")
    assert "<section class=\"title-page\">" in html
    assert "My Book" in html
    assert "Me" in html


def test_render_markdown_book_no_pdf(tmp_path):
    src = tmp_path / "edited.md"
    src.write_text("# Edited Book\n\n_By Tester_\n\n## Chapter 1\n\nEdited text.", encoding="utf-8")
    out = tmp_path / "out"

    result = render_markdown_book(src, out, export_pdf=False)
    assert result.success is True
    assert result.title == "Edited Book"
    assert result.author == "Tester"
    assert result.output_files
    assert Path(result.output_files[0]).exists()


def test_render_markdown_cli_help_runs():
    result = subprocess.run(
        [sys.executable, "scripts/render_markdown_book.py", "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Render edited ChapterFOLD Markdown" in result.stdout
