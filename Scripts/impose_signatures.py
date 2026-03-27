#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.impose_service import (
    DEFAULT_SHEETS_PER_SIGNATURE,
    build_signature_settings,
    impose_pdf,
)

DEFAULT_INPUT_PDF = r"C:\Users\jonat\Documents\Bees_Books\Running_on_Air_output\interior.pdf"


def get_paths_interactively() -> tuple[str, str | None]:
    print("No PDF paths were provided.")
    print(f"Press Enter to use the example input path:\n{DEFAULT_INPUT_PDF}\n")
    input_path = input("Input PDF path: ").strip() or DEFAULT_INPUT_PDF
    output_path = input(
        "Output PDF path (press Enter to auto-place it in the same output folder): "
    ).strip()
    return input_path, (output_path or None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_pdf", nargs="?", help="Interior PDF to impose")
    parser.add_argument("output_pdf", nargs="?", help="Output imposed PDF")

    parser.add_argument(
        "--sheets-per-signature",
        type=int,
        default=None,
        help=f"Number of folded sheets in each signature ({DEFAULT_SHEETS_PER_SIGNATURE} sheets = {DEFAULT_SHEETS_PER_SIGNATURE * 4} pages by default)",
    )
    parser.add_argument(
        "--pages-per-signature",
        type=int,
        default=None,
        help="Number of book pages in each signature (must be a multiple of 4)",
    )
    parser.add_argument(
        "--max-end-padding",
        type=int,
        default=None,
        help="Fail if more than this many blank pages would be added at the end",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args, _unknown = parser.parse_known_args(argv)

    if args.input_pdf:
        input_pdf = args.input_pdf
        output_pdf = args.output_pdf
    else:
        input_pdf, output_pdf = get_paths_interactively()

    try:
        settings = build_signature_settings(
            sheets_per_signature=args.sheets_per_signature,
            pages_per_signature=args.pages_per_signature,
            max_end_padding=args.max_end_padding,
        )
    except ValueError as e:
        print(f"Signature size error: {e}", file=sys.stderr)
        return 3

    try:
        result = impose_pdf(
            input_pdf=input_pdf,
            output_pdf=output_pdf,
            settings=settings,
        )
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"Imposition failed: {e}", file=sys.stderr)
        return 4
    except Exception as e:
        print(f"Imposition failed: {e}", file=sys.stderr)
        return 5

    print()
    print("Signature imposition completed successfully.")
    print(f"Input PDF:            {result.input_pdf}")
    print(f"Output folder:        {result.output_dir}")
    print(f"Output PDF:           {result.output_pdf}")
    print(f"Input pages:          {result.input_pages}")
    print(f"Sheets/signature:     {result.sheets_per_signature}")
    print(f"Pages/signature:      {result.pages_per_signature}")
    print(f"End blanks added:     {result.end_blanks_added}")
    print(f"Output sheet sides:   {result.output_sheet_sides}")
    print(f"Physical sheets/sig:  {result.sheets_per_signature}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
