from pathlib import Path

from core.naming import (
    build_book_slug,
    infer_book_slug_from_interior_pdf,
    imposed_pdf_name,
    interior_pdf_name,
)


def test_build_book_slug_with_author_and_title():
    slug = build_book_slug(title="Running on Air", author="eleventy7")
    assert slug == "eleventy7__running-on-air"


def test_build_book_slug_falls_back_to_stem():
    slug = build_book_slug(fallback_stem="My Weird Book_v2")
    assert slug == "my-weird-book-v2"


def test_interior_pdf_name():
    assert interior_pdf_name("eleventy7__running-on-air") == "eleventy7__running-on-air__interior.pdf"


def test_imposed_pdf_name():
    assert (
        imposed_pdf_name("eleventy7__running-on-air", 4, 16)
        == "eleventy7__running-on-air__imposed__4sheets__16pages.pdf"
    )


def test_infer_book_slug_from_named_interior_pdf():
    path = Path(r"C:\books\eleventy7__running-on-air_output\eleventy7__running-on-air__interior.pdf")
    assert infer_book_slug_from_interior_pdf(path) == "eleventy7__running-on-air"


def test_infer_book_slug_from_generic_interior_pdf():
    path = Path(r"C:\books\running-on-air_output\interior.pdf")
    assert infer_book_slug_from_interior_pdf(path) == "running-on-air"
