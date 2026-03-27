#!/usr/bin/env python3
"""
Impose a book interior PDF into 2-up printer spreads for signatures.

Features:
- Defaults to 16-page signatures
- Adds blank pages only at the end
- Can limit how many blank end pages are allowed
- Ignores unknown IDE/PyDev arguments
- Prompts for input/output if needed
- By default writes output into the same *_output folder as the interior PDF

Typical workflow:
    1. Run epub_to_pdf.py
    2. This creates something like:
       C:\\Users\\jonat\\Documents\\Bees_Books\\Running_on_Air_output\\interior.pdf
    3. Run this script on that PDF
    4. It creates:
       C:\\Users\\jonat\\Documents\\Bees_Books\\Running_on_Air_output\\imposed_16sig.pdf
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from pypdf import PdfReader, PdfWriter, Transformation
from pypdf._page import PageObject


DEFAULT_INPUT_PDF = r"C:\Users\jonat\Documents\Bees_Books\Running_on_Air_output\interior.pdf"


def safe_name(name: str) -> str:
    name = re.sub(r"\s+", "_", name.strip())
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    return name or "book"


def get_paths_interactively() -> Tuple[str, Optional[str]]:
    print("No PDF paths were provided.")
    print(f"Press Enter to use the example input path:\n{DEFAULT_INPUT_PDF}\n")
    input_path = input("Input PDF path: ").strip() or DEFAULT_INPUT_PDF
    output_path = input(
        "Output PDF path (press Enter to auto-place it in the same output folder): "
    ).strip()
    return input_path, (output_path or None)


def make_blank_like(page: PageObject) -> PageObject:
    return PageObject.create_blank_page(
        width=float(page.mediabox.width),
        height=float(page.mediabox.height),
    )


def next_multiple(n: int, m: int) -> int:
    return ((n + m - 1) // m) * m


def signature_sheet_pairs(sig_size: int) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """
    Return sheet pairings for one signature.

    For a 16-page signature:
      sheet 1 front: (16, 1), back: (2, 15)
      sheet 2 front: (14, 3), back: (4, 13)
      ...
    """
    if sig_size % 4 != 0:
        raise ValueError("Signature size must be a multiple of 4")

    sheets = []
    low = 1
    high = sig_size

    while low < high:
        front = (high, low)
        back = (low + 1, high - 1)
        sheets.append((front, back))
        low += 2
        high -= 2

    return sheets


def create_sheet_page(left_page: PageObject, right_page: PageObject) -> PageObject:
    """
    Place two portrait pages side-by-side on one landscape sheet side.
    """
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


def default_output_pdf_path(input_pdf: Path, signature_size: int) -> Path:
    """
    Write imposed output into the same folder as the interior PDF by default.
    """
    return input_pdf.parent / f"imposed_{signature_size}sig.pdf"


def impose(
    input_pdf: Path,
    output_pdf: Path,
    signature_size: int = 16,
    max_end_padding: Optional[int] = None,
) -> Tuple[int, int, int]:
    reader = PdfReader(str(input_pdf))
    writer = PdfWriter()

    total_pages = len(reader.pages)
    if total_pages == 0:
        raise ValueError("Input PDF has no pages")

    if signature_size % 4 != 0:
        raise ValueError("Signature size must be a multiple of 4")

    padded_total = next_multiple(total_pages, signature_size)
    end_padding = padded_total - total_pages

    if max_end_padding is not None and end_padding > max_end_padding:
        raise ValueError(
            f"Would need {end_padding} blank end pages, which exceeds "
            f"--max-end-padding {max_end_padding}"
        )

    template_page = reader.pages[0]
    per_signature_sheets = signature_sheet_pairs(signature_size)

    for sig_start in range(1, padded_total + 1, signature_size):
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

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    with open(output_pdf, "wb") as f:
        writer.write(f)

    return total_pages, end_padding, len(writer.pages)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_pdf", nargs="?", help="Interior PDF to impose")
    parser.add_argument("output_pdf", nargs="?", help="Output imposed PDF")
    parser.add_argument("--signature", type=int, default=16, help="Pages per signature")
    parser.add_argument(
        "--max-end-padding",
        type=int,
        default=None,
        help="Fail if more than this many blank pages would be added at the end",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args, unknown = parser.parse_known_args(argv)

    if args.input_pdf:
        input_pdf_str = args.input_pdf
        output_pdf_str = args.output_pdf
    else:
        input_pdf_str, output_pdf_str = get_paths_interactively()

    input_pdf = Path(input_pdf_str)

    if not input_pdf.exists():
        print(f"Input PDF not found: {input_pdf}", file=sys.stderr)
        return 2

    output_pdf = Path(output_pdf_str) if output_pdf_str else default_output_pdf_path(
        input_pdf, args.signature
    )

    try:
        total_pages, end_padding, output_sheet_sides = impose(
            input_pdf=input_pdf,
            output_pdf=output_pdf,
            signature_size=args.signature,
            max_end_padding=args.max_end_padding,
        )
    except Exception as e:
        print(f"Imposition failed: {e}", file=sys.stderr)
        return 3

    print()
    print("Signature imposition completed successfully.")
    print(f"Input PDF:         {input_pdf}")
    print(f"Output folder:     {output_pdf.parent}")
    print(f"Output PDF:        {output_pdf}")
    print(f"Input pages:       {total_pages}")
    print(f"Signature size:    {args.signature}")
    print(f"End blanks added:  {end_padding}")
    print(f"Sheet sides total: {output_sheet_sides}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
