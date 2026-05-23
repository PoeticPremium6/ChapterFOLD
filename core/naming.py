from __future__ import annotations

import re
from pathlib import Path, PureWindowsPath
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



def _path_name_and_parent_name(path: Path) -> tuple[str, str]:
    """Return filename and parent name for POSIX or Windows-style paths.

    Tests may pass Windows paths while running on Linux. pathlib.Path treats
    backslashes as literal characters on POSIX, so use PureWindowsPath when a
    string contains backslashes.
    """

    raw = str(path)
    if "\\" in raw:
        win_path = PureWindowsPath(raw)
        return win_path.name, win_path.parent.name
    return path.name, path.parent.name

def infer_book_slug_from_interior_pdf(path):
    """Infer the book slug from an interior PDF path.

    Handles both native paths and Windows-style strings while running on Linux.
    Examples:
    - C:\books\name_output\name__interior.pdf -> name
    - C:\books\name_output\interior.pdf -> name
    """
    filename = _any_name(path)
    stem = filename[:-4] if filename.lower().endswith(".pdf") else filename

    if stem.endswith("__interior"):
        return stem[: -len("__interior")]

    if stem.lower() == "interior":
        parent = _any_parent_name(path)
        if parent.endswith("_output"):
            return parent[: -len("_output")]
        return parent or stem

    if stem.endswith("_interior"):
        return stem[: -len("_interior")]

    # Fallback: keep previous behaviour broadly slug-like without eating path separators.
    return stem.replace(" ", "-").lower()

def _split_any_path(path_obj) -> list[str]:
    raw = str(path_obj).replace("\\", "/")
    return [part for part in raw.split("/") if part]


def _any_name(path_obj) -> str:
    parts = _split_any_path(path_obj)
    return parts[-1] if parts else ""


def _any_parent_name(path_obj) -> str:
    parts = _split_any_path(path_obj)
    return parts[-2] if len(parts) >= 2 else ""
