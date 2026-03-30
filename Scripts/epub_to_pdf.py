#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.epub_service import (
    DEFAULT_FONT_STACK,
    CleanupSettings,
    LayoutSettings,
    process_epub_to_pdf,
)

DEFAULT_EPUB_PATH = r"C:\Users\jonat\Documents\Bees_Books\Running_on_Air.epub"


def get_input_path_interactively() -> str:
    print("No EPUB path was provided.")
    print(f"Press Enter to use the example path:\n{DEFAULT_EPUB_PATH}\n")
    entered = input("EPUB path: ").strip()
    return entered or DEFAULT_EPUB_PATH


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("epub_path", nargs="?", help="Input EPUB path")
    parser.add_argument("--title", default=None, help="Override book title")
    parser.add_argument("--author", default=None, help="Override author name")
    parser.add_argument("--out", default=None, help="Output PDF path")

    parser.add_argument("--export-docx", action="store_true", help="Also create an editable DOCX")
    parser.add_argument("--docx-out", default=None, help="Custom DOCX output path")

    parser.add_argument("--trim-width-cm", type=float, default=15.24)
    parser.add_argument("--trim-height-cm", type=float, default=22.86)
    parser.add_argument("--margin-top-cm", type=float, default=1.5)
    parser.add_argument("--margin-bottom-cm", type=float, default=1.5)
    parser.add_argument("--margin-inside-cm", type=float, default=1.8)
    parser.add_argument("--margin-outside-cm", type=float, default=1.0)
    parser.add_argument("--font-size-pt", type=float, default=11.5)
    parser.add_argument("--line-height", type=float, default=1.35)
    parser.add_argument("--font-family", default=DEFAULT_FONT_STACK)
    parser.add_argument("--drop-notes", action="store_true")

    parser.add_argument("--no-join-soft-wraps", action="store_true")
    parser.add_argument("--no-join-dialogue", action="store_true")

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args, _unknown = parser.parse_known_args(argv)

    epub_path = args.epub_path or get_input_path_interactively()

    layout_settings = LayoutSettings(
        trim_width_cm=args.trim_width_cm,
        trim_height_cm=args.trim_height_cm,
        margin_top_cm=args.margin_top_cm,
        margin_bottom_cm=args.margin_bottom_cm,
        margin_inside_cm=args.margin_inside_cm,
        margin_outside_cm=args.margin_outside_cm,
        font_size_pt=args.font_size_pt,
        line_height=args.line_height,
        font_family=args.font_family,
        drop_notes=args.drop_notes,
    )

    cleanup_settings = CleanupSettings(
        join_soft_wrapped_lines=not args.no_join_soft_wraps,
        join_dialogue_continuations=not args.no_join_dialogue,
        collapse_extra_blank_lines=True,
        preserve_scene_breaks=True,
    )

    try:
        result = process_epub_to_pdf(
            epub_path=epub_path,
            output_pdf_path=args.out,
            output_docx_path=args.docx_out,
            export_docx=args.export_docx,
            title=args.title,
            author=args.author,
            settings=layout_settings,
            cleanup_settings=cleanup_settings,
        )
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 2
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 4
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 10
    except Exception as e:
        print(f"Failed to create PDF: {e}", file=sys.stderr)
        return 5

    print()
    print("EPUB to PDF completed successfully.")
    print(f"Input EPUB:       {result.input_epub}")
    print(f"Detected title:   {result.detected_title}")
    print(f"Detected author:  {result.detected_author}")
    print(f"Used title:       {result.used_title}")
    print(f"Used author:      {result.used_author}")
    print(f"Book slug:        {result.book_slug}")
    print(f"Output folder:    {result.output_dir}")
    print(f"Output PDF:       {result.output_pdf}")
    if result.output_docx:
        print(f"Output DOCX:      {result.output_docx}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
