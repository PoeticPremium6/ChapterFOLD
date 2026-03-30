#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.epub_service import (  # noqa: E402
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
    parser = argparse.ArgumentParser(
        description="Generate multiple ChapterFOLD output variants with different cleanup heuristics."
    )
    parser.add_argument("epub_path", nargs="?", help="Input EPUB path")
    parser.add_argument("--title", default=None, help="Override book title")
    parser.add_argument("--author", default=None, help="Override author name")

    parser.add_argument("--trim-width-cm", type=float, default=15.24)
    parser.add_argument("--trim-height-cm", type=float, default=22.86)
    parser.add_argument("--margin-top-cm", type=float, default=1.5)
    parser.add_argument("--margin-bottom-cm", type=float, default=1.5)
    parser.add_argument("--margin-inside-cm", type=float, default=1.8)
    parser.add_argument("--margin-outside-cm", type=float, default=1.0)
    parser.add_argument("--font-size-pt", type=float, default=11.5)
    parser.add_argument("--line-height", type=float, default=1.35)
    parser.add_argument(
        "--font-family",
        default='"Garamond", "EB Garamond", "Cormorant Garamond", serif',
    )
    parser.add_argument("--drop-notes", action="store_true")
    parser.add_argument(
        "--variants",
        nargs="*",
        default=None,
        help=(
            "Optional subset of variants to generate. "
            "Choices: standard edit-friendly aggressive-cleanup no-dialogue-join paragraph-dialogue-merge"
        ),
    )
    return parser


def build_layout_settings(args: argparse.Namespace) -> LayoutSettings:
    return LayoutSettings(
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


def make_variant_path(base_output_dir: Path, variant_name: str, suffix: str) -> Path:
    variant_dir = base_output_dir / "variants"
    variant_dir.mkdir(parents=True, exist_ok=True)
    return variant_dir / f"{variant_name}{suffix}"


def build_variants() -> list[dict]:
    return [
        {
            "name": "standard",
            "description": "Default line cleanup with dialogue-line joining.",
            "cleanup": CleanupSettings(
                join_soft_wrapped_lines=True,
                join_dialogue_continuations=True,
                merge_dialogue_paragraphs=False,
                collapse_extra_blank_lines=True,
                preserve_scene_breaks=True,
            ),
            "export_docx": True,
        },
        {
            "name": "edit-friendly",
            "description": "Keeps more original paragraph and line structure for manual edits.",
            "cleanup": CleanupSettings(
                join_soft_wrapped_lines=False,
                join_dialogue_continuations=False,
                merge_dialogue_paragraphs=False,
                collapse_extra_blank_lines=True,
                preserve_scene_breaks=True,
            ),
            "export_docx": True,
        },
        {
            "name": "aggressive-cleanup",
            "description": "Line cleanup plus paragraph-level dialogue merge.",
            "cleanup": CleanupSettings(
                join_soft_wrapped_lines=True,
                join_dialogue_continuations=True,
                merge_dialogue_paragraphs=True,
                collapse_extra_blank_lines=True,
                preserve_scene_breaks=True,
            ),
            "export_docx": True,
        },
        {
            "name": "no-dialogue-join",
            "description": "Soft-wrap joining only; dialogue continuations stay separate.",
            "cleanup": CleanupSettings(
                join_soft_wrapped_lines=True,
                join_dialogue_continuations=False,
                merge_dialogue_paragraphs=False,
                collapse_extra_blank_lines=True,
                preserve_scene_breaks=True,
            ),
            "export_docx": True,
        },
        {
            "name": "paragraph-dialogue-merge",
            "description": "Only paragraph-level dialogue merge, useful for chatty fic EPUBs.",
            "cleanup": CleanupSettings(
                join_soft_wrapped_lines=False,
                join_dialogue_continuations=False,
                merge_dialogue_paragraphs=True,
                collapse_extra_blank_lines=True,
                preserve_scene_breaks=True,
            ),
            "export_docx": True,
        },
    ]


def main(argv=None) -> int:
    parser = build_parser()
    args, _unknown = parser.parse_known_args(argv)

    epub_path = args.epub_path or get_input_path_interactively()
    layout_settings = build_layout_settings(args)
    all_variants = build_variants()

    if args.variants:
        wanted = {name.strip() for name in args.variants}
        variants = [variant for variant in all_variants if variant["name"] in wanted]
        missing = sorted(wanted - {variant["name"] for variant in variants})
        if missing:
            print(
                "Unknown variant name(s): " + ", ".join(missing),
                file=sys.stderr,
            )
            return 2
    else:
        variants = all_variants

    first_result = None
    results = []

    for variant in variants:
        try:
            if first_result is None:
                preview_result = process_epub_to_pdf(
                    epub_path=epub_path,
                    title=args.title,
                    author=args.author,
                    settings=layout_settings,
                    cleanup_settings=variant["cleanup"],
                    export_docx=False,
                )
                first_result = preview_result

            base_output_dir = first_result.output_dir
            pdf_out = make_variant_path(
                base_output_dir,
                variant["name"],
                "__interior.pdf",
            )
            docx_out = make_variant_path(
                base_output_dir,
                variant["name"],
                "__editable.docx",
            )

            result = process_epub_to_pdf(
                epub_path=epub_path,
                output_pdf_path=pdf_out,
                output_docx_path=docx_out,
                export_docx=variant["export_docx"],
                title=args.title,
                author=args.author,
                settings=layout_settings,
                cleanup_settings=variant["cleanup"],
            )
            results.append((variant, result))
        except Exception as e:
            print(f"Variant '{variant['name']}' failed: {e}", file=sys.stderr)

    if not results:
        print("No variants were generated successfully.", file=sys.stderr)
        return 1

    print()
    print("Variant generation completed.")
    print(f"Input EPUB: {results[0][1].input_epub}")
    print(f"Output folder: {results[0][1].output_dir / 'variants'}")
    print()

    for variant, result in results:
        print(f"[{variant['name']}]")
        print(variant["description"])
        print(f"PDF: {result.output_pdf}")
        if result.output_docx:
            print(f"DOCX: {result.output_docx}")
        print(
            "Cleanup: "
            f"join_soft_wrapped_lines={variant['cleanup'].join_soft_wrapped_lines}, "
            f"join_dialogue_continuations={variant['cleanup'].join_dialogue_continuations}, "
            f"merge_dialogue_paragraphs={variant['cleanup'].merge_dialogue_paragraphs}"
        )
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
