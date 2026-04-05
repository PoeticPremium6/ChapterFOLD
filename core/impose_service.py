#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pypdf import PdfReader, PdfWriter, Transformation
from pypdf._page import PageObject


DEFAULT_SHEETS_PER_SIGNATURE = 4


@dataclass(frozen=True)
class SignatureSettings:
    sheets_per_signature: int
    pages_per_signature: int
    max_end_padding: int | None = None
    binding_direction: str = "ltr"


@dataclass(frozen=True)
class ImpositionResult:
    input_pdf: Path
    output_pdf: Path
    input_pages: int
    blank_pages_added: int
    output_sheet_sides: int
    physical_sheets_total: int
    total_signatures: int
    settings: SignatureSettings


def next_multiple(n: int, m: int) -> int:
    if m <= 0:
        raise ValueError("Multiple must be greater than 0")
    return ((n + m - 1) // m) * m


def pages_from_sheets(sheets_per_signature: int) -> int:
    if sheets_per_signature <= 0:
        raise ValueError("Sheets per signature must be greater than 0")
    return sheets_per_signature * 4


def resolve_signature_size(
    sheets_per_signature: Optional[int],
    pages_per_signature: Optional[int],
) -> tuple[int, int]:
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
    sheets_per_signature: int | None = None,
    pages_per_signature: int | None = None,
    max_end_padding: int | None = None,
    binding_direction: str = "ltr",
) -> SignatureSettings:
    sheets, pages = resolve_signature_size(sheets_per_signature, pages_per_signature)

    direction = (binding_direction or "ltr").strip().lower()
    if direction not in {"ltr", "rtl"}:
        raise ValueError("Binding direction must be 'ltr' or 'rtl'")

    if max_end_padding is not None and max_end_padding < 0:
        raise ValueError("Max end padding cannot be negative")

    return SignatureSettings(
        sheets_per_signature=sheets,
        pages_per_signature=pages,
        max_end_padding=max_end_padding,
        binding_direction=direction,
    )


def signature_sheet_pairs(
    pages_per_signature: int,
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    if pages_per_signature % 4 != 0:
        raise ValueError("Pages per signature must be a multiple of 4")

    sheets: list[tuple[tuple[int, int], tuple[int, int]]] = []
    low = 1
    high = pages_per_signature

    while low < high:
        front = (high, low)
        back = (low + 1, high - 1)
        sheets.append((front, back))
        low += 2
        high -= 2

    return sheets


def make_blank_like(page: PageObject) -> PageObject:
    return PageObject.create_blank_page(
        width=float(page.mediabox.width),
        height=float(page.mediabox.height),
    )


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


def create_sheet_side(
    first_page: PageObject,
    second_page: PageObject,
    *,
    binding_direction: str,
) -> PageObject:
    """
    Create one landscape sheet side from two portrait pages.

    For left-to-right binding, page order is left then right.
    For right-to-left binding, the side is mirrored.
    """
    w = float(first_page.mediabox.width)
    h = float(first_page.mediabox.height)

    sheet = PageObject.create_blank_page(width=w * 2, height=h)

    if binding_direction == "rtl":
        left_page = second_page
        right_page = first_page
    else:
        left_page = first_page
        right_page = second_page

    sheet.merge_transformed_page(left_page, Transformation().translate(tx=0, ty=0))
    sheet.merge_transformed_page(right_page, Transformation().translate(tx=w, ty=0))
    return sheet


def default_imposed_output_path(
    input_pdf: Path,
    *,
    pages_per_signature: int,
    binding_direction: str,
) -> Path:
    direction_label = "RTL" if binding_direction == "rtl" else "LTR"
    return input_pdf.with_name(
        f"{input_pdf.stem} - Imposed {pages_per_signature}pp {direction_label}.pdf"
    )


def impose_pdf(
    *,
    input_pdf: str | Path,
    output_pdf: str | Path | None = None,
    settings: SignatureSettings,
) -> ImpositionResult:
    input_pdf = Path(input_pdf)
    if not input_pdf.exists():
        raise FileNotFoundError(f"Input PDF not found: {input_pdf}")

    reader = PdfReader(str(input_pdf))
    writer = PdfWriter()

    total_pages = len(reader.pages)
    if total_pages == 0:
        raise ValueError("Input PDF has no pages")

    padded_total = next_multiple(total_pages, settings.pages_per_signature)
    blank_pages_added = padded_total - total_pages

    if (
        settings.max_end_padding is not None
        and blank_pages_added > settings.max_end_padding
    ):
        raise ValueError(
            f"Would need {blank_pages_added} blank end pages, which exceeds the "
            f"maximum allowed padding of {settings.max_end_padding}"
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
                reader,
                front_left_abs,
                padded_total,
                total_pages,
                template_page,
            )
            front_right_page = get_page_or_blank(
                reader,
                front_right_abs,
                padded_total,
                total_pages,
                template_page,
            )
            back_left_page = get_page_or_blank(
                reader,
                back_left_abs,
                padded_total,
                total_pages,
                template_page,
            )
            back_right_page = get_page_or_blank(
                reader,
                back_right_abs,
                padded_total,
                total_pages,
                template_page,
            )

            writer.add_page(
                create_sheet_side(
                    front_left_page,
                    front_right_page,
                    binding_direction=settings.binding_direction,
                )
            )
            writer.add_page(
                create_sheet_side(
                    back_left_page,
                    back_right_page,
                    binding_direction=settings.binding_direction,
                )
            )

    output_pdf_path = (
        Path(output_pdf)
        if output_pdf is not None
        else default_imposed_output_path(
            input_pdf,
            pages_per_signature=settings.pages_per_signature,
            binding_direction=settings.binding_direction,
        )
    )
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_pdf_path, "wb") as handle:
        writer.write(handle)

    output_sheet_sides = len(writer.pages)
    physical_sheets_total = output_sheet_sides // 2
    total_signatures = padded_total // settings.pages_per_signature

    return ImpositionResult(
        input_pdf=input_pdf,
        output_pdf=output_pdf_path,
        input_pages=total_pages,
        blank_pages_added=blank_pages_added,
        output_sheet_sides=output_sheet_sides,
        physical_sheets_total=physical_sheets_total,
        total_signatures=total_signatures,
        settings=settings,
    )
