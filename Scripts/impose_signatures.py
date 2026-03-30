#!/usr/bin/env python3
"""
Core service for imposing a book interior PDF into 2-up printer spreads
for folded signatures.

Concept:
- 1 sheet of paper = 4 book pages total
  (2 on the front, 2 on the back)
- 4 sheets per signature = 16 book pages per signature
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from pypdf import PdfReader, PdfWriter, Transformation
from pypdf._page import PageObject


DEFAULT_SHEETS_PER_SIGNATURE = 4


@dataclass
class SignatureSettings:
    sheets_per_signature: int = DEFAULT_SHEETS_PER_SIGNATURE
    pages_per_signature: int = 16
    max_end_padding: Optional[int] = None


@dataclass
class ImposeResult:
    input_pdf: Path
    output_dir: Path
    output_pdf: Path
    input_pages: int
    sheets_per_signature: int
    pages_per_signature: int
    end_blanks_added: int
    output_sheet_sides: int


def safe_name(name: str) -> str:
    name = re.sub(r"\s+", "_", name.strip())
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    return name or "book"


def make_blank_like(page: PageObject) -> PageObject:
    return PageObject.create_blank_page(
        width=float(page.mediabox.width),
        height=float(page.mediabox.height),
    )


def next_multiple(n: int, m: int) -> int:
    return ((n + m - 1) // m) * m


def pages_from_sheets(sheets_per_signature: int) -> int:
    if sheets_per_signature <= 0:
        raise ValueError("Sheets per signature must be greater than 0")
    return sheets_per_signature * 4


def resolve_signature_size(
    sheets_per_signature: Optional[int],
    pages_per_signature: Optional[int],
) -> Tuple[int, int]:
    if sheets_per_signature is not None and pages_per_signature is not None:
        expected_pages = pages_from_sheets(sheets_per_signature)
        if pages_per_signature != expected_pages:
            raise ValueError(
                f"Conflicting options: {sheets_per_signature} sheets/signature "
                f"implies {expected_pages} pages/signature, not {pages_per_signature}"
            )
        return sheets_per_signature, pages_per_signature

    if sheets_per_signature is not None:
        return sheets_per_signature, pages_from_sheets(sheets_per_signature)

    if pages_per_signature is not None:
        if pages_per_signature <= 0 or pages_per_signature % 4 != 0:
            raise ValueError("Pages per signature must be a positive multiple of 4")
        return pages_per_signature // 4, pages_per_signature

    return DEFAULT_SHEETS_PER_SIGNATURE, pages_from_sheets(DEFAULT_SHEETS_PER_SIGNATURE)


def build_signature_settings(
    *,
    sheets_per_signature: Optional[int] = None,
    pages_per_signature: Optional[int] = None,
    max_end_padding: Optional[int] = None,
) -> SignatureSettings:
    resolved_sheets, resolved_pages = resolve_signature_size(
        sheets_per_signature=sheets_per_signature,
        pages_per_signature=pages_per_signature,
    )
    return SignatureSettings(
        sheets_per_signature=resolved_sheets,
        pages_per_signature=resolved_pages,
        max_end_padding=max_end_padding,
    )


def signature_sheet_pairs(
    pages_per_signature: int,
) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """
    Example for 16 pages:
      sheet 1 front: (16, 1), back: (2, 15)
      sheet 2 front: (14, 3), back: (4, 13)
      sheet 3 front: (12, 5), back: (6, 11)
      sheet 4 front: (10, 7), back: (8, 9)
    """
    if pages_per_signature % 4 != 0:
        raise ValueError("Pages per signature must be a multiple of 4")

    sheets = []
    low = 1
    high = pages_per_signature

    while low < high:
        front = (high, low)
        back = (low + 1, high - 1)
        sheets.append((front, back))
        low += 2
        high -= 2

    return sheets


def create_sheet_page(left_page: PageObject, right_page: PageObject) -> PageObject:
    w = float(left_page.mediabox.width)
    h = float(left_page.mediabox.height)

    sheet = PageObject.create_blank_page(width=w * 2, height=h)
    sheet.merge_transformed_page(left_page, Transformation().translate(tx=0, ty=0))
    sheet.merge_transformed_page(right_page, Transformation().translate(tx=w, ty=0))
    return sheet


def get_page_or_blank(
    reader: PdfReader,
    one_based_index: int,
    padded_total: int,
    original_total: int,
    template_page: PageObject,
) -> PageObject:
    if 1 <= one_based_index <= original_total:
        return reader.pages[one_based_index - 1]
    if 1 <= one_based_index <= padded_total:
        return make_blank_like(template_page)
    raise ValueError("Page index out of range")


def default_output_pdf_path(
    input_pdf: Path,
    sheets_per_signature: int,
    pages_per_signature: int,
) -> Path:
    return input_pdf.parent / f"imposed_{sheets_per_signature}sheets_{pages_per_signature}pages.pdf"


def impose_pdf(
    *,
    input_pdf: str | Path,
    output_pdf: str | Path | None = None,
    settings: SignatureSettings | None = None,
) -> ImposeResult:
    input_pdf = Path(input_pdf)
    if not input_pdf.exists():
        raise FileNotFoundError(f"Input PDF not found: {input_pdf}")

    settings = settings or build_signature_settings()

    reader = PdfReader(str(input_pdf))
    writer = PdfWriter()

    total_pages = len(reader.pages)
    if total_pages == 0:
        raise ValueError("Input PDF has no pages")

    if settings.pages_per_signature % 4 != 0:
        raise ValueError("Pages per signature must be a multiple of 4")

    padded_total = next_multiple(total_pages, settings.pages_per_signature)
    end_padding = padded_total - total_pages

    if settings.max_end_padding is not None and end_padding > settings.max_end_padding:
        raise ValueError(
            f"Would need {end_padding} blank end pages, which exceeds "
            f"max_end_padding={settings.max_end_padding}"
        )

    template_page = reader.pages[0]
    per_signature_sheets = signature_sheet_pairs(settings.pages_per_signature)

    for sig_start in range(1, padded_total + 1, settings.pages_per_signature):
        for (front_left_local, front_right_local), (back_left_local, back_right_local) in per_signature_sheets:
            front_left_abs = sig_start + front_left_local - 1
            front_right_abs = sig_start + front_right_local - 1
            back_left_abs = sig_start + back_left_local - 1
            back_right_abs = sig_start + back_right_local - 1

            front_left_page = get_page_or_blank(
                reader, front_left_abs, padded_total, total_pages, template_page
            )
            front_right_page = get_page_or_blank(
                reader, front_right_abs, padded_total, total_pages, template_page
            )
            back_left_page = get_page_or_blank(
                reader, back_left_abs, padded_total, total_pages, template_page
            )
            back_right_page = get_page_or_blank(
                reader, back_right_abs, padded_total, total_pages, template_page
            )

            writer.add_page(create_sheet_page(front_left_page, front_right_page))
            writer.add_page(create_sheet_page(back_left_page, back_right_page))

    output_pdf = Path(output_pdf) if output_pdf else default_output_pdf_path(
        input_pdf,
        settings.sheets_per_signature,
        settings.pages_per_signature,
    )
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    with open(output_pdf, "wb") as f:
        writer.write(f)

    return ImposeResult(
        input_pdf=input_pdf,
        output_dir=output_pdf.parent,
        output_pdf=output_pdf,
        input_pages=total_pages,
        sheets_per_signature=settings.sheets_per_signature,
        pages_per_signature=settings.pages_per_signature,
        end_blanks_added=end_padding,
        output_sheet_sides=len(writer.pages),
    )

print()
print("Signature imposition completed successfully.")
print(f"Input PDF:            {result.input_pdf}")
print(f"Book slug:            {result.book_slug}")
print(f"Output folder:        {result.output_dir}")
print(f"Output PDF:           {result.output_pdf}")
print(f"Input pages:          {result.input_pages}")
print(f"Sheets/signature:     {result.sheets_per_signature}")
print(f"Pages/signature:      {result.pages_per_signature}")
print(f"End blanks added:     {result.end_blanks_added}")
print(f"Output sheet sides:   {result.output_sheet_sides}")
print(f"Physical sheets/sig:  {result.sheets_per_signature}")
print()
