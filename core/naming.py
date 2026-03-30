from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    value = re.sub(r"[\s_-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-") or "book"


def build_book_slug(
    *,
    title: Optional[str] = None,
    author: Optional[str] = None,
    fallback_stem: Optional[str] = None,
) -> str:
    parts = []
    if author:
        parts.append(slugify(author))
    if title:
        parts.append(slugify(title))

    if parts:
        return "__".join(parts)

    if fallback_stem:
        return slugify(fallback_stem)

    return "book"


def output_dir_for_book(base_dir: Path, book_slug: str) -> Path:
    return base_dir / f"{book_slug}_output"


def interior_pdf_name(book_slug: str) -> str:
    return f"{book_slug}__interior.pdf"


def imposed_pdf_name(book_slug: str, sheets_per_signature: int, pages_per_signature: int) -> str:
    return (
        f"{book_slug}__imposed__"
        f"{sheets_per_signature}sheets__"
        f"{pages_per_signature}pages.pdf"
    )


def infer_book_slug_from_interior_pdf(input_pdf: Path) -> str:
    stem = input_pdf.stem

    if stem.endswith("__interior"):
        return stem[: -len("__interior")]

    if stem == "interior":
        parent_stem = input_pdf.parent.name
        if parent_stem.endswith("_output"):
            return parent_stem[: -len("_output")] or "book"
        return parent_stem or "book"

    return slugify(stem)
