#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from typing import Any

from core.schemas import ChapterfoldSettings
from chapterfold_app.services.input_runner import run_input_processing


def _settings_from_json(path: str | Path | None) -> dict[str, Any]:
    if not path:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run ChapterFOLD on EPUB or PDF input.")
    parser.add_argument("input_file", help="Input .epub or .pdf")
    parser.add_argument("output_dir", help="Output directory")
    parser.add_argument("--settings-json", default=None)

    parser.add_argument("--variant", choices=["standard", "aggressive-cleanup", "paragraph-dialogue-merge"], default=None)
    parser.add_argument("--export-docx", action="store_true")
    parser.add_argument("--export-markdown", action="store_true")
    parser.add_argument("--paragraph-spacing-mode", choices=["traditional", "uniform", "no-indents", "indented-compact"], default=None)
    parser.add_argument("--contents-mode", choices=["keep", "remove", "rebuild", "rebuild-paged"], default=None)

    parser.add_argument("--page-number-start", dest="page_number_start_mode", choices=["after-title-page", "main-text", "first-page", "none"], default=None)
    parser.add_argument("--front-matter-numbers", dest="front_matter_page_number_style", choices=["hidden", "roman-lower", "roman-upper", "arabic"], default=None)
    parser.add_argument("--page-ornament-amount", dest="page_ornament_amount", choices=["subtle", "balanced", "ornate"], default=None, help="How many ornaments appear around visible page numbers")
    parser.add_argument("--page-ornament", dest="page_ornament", choices=['none', 'classic-rule', 'botanical-leaf', 'floral-corner', 'gothic-flourish', 'storybook', 'vine', 'laurel', 'victorian-dots', 'celestial', 'rose', 'ivy', 'acanthus', 'minimal-divider', 'poetic-vine', 'moon-garden', 'rose-window', 'ivy-thorn', 'asterism', 'bookbinder-rule'], default=None, help="Decorative ornament around visible PDF page numbers")

    parser.add_argument("--chapter-ornament", dest="chapter_ornament", choices=['none', 'classic-rule', 'botanical-divider', 'poetic-vine', 'moon-garden', 'rose-window', 'bookbinder-rule'], default=None, help="Decorative ornament below chapter headings")
    parser.add_argument("--page-size-preset", choices=["default-trade", "a4", "a5", "a6", "letter", "half-letter", "trade-5x8", "trade-6x9", "custom"], default=None)
    parser.add_argument("--custom-trim-width-cm", type=float, default=None)
    parser.add_argument("--custom-trim-height-cm", type=float, default=None)

    parser.add_argument("--margin-preset", choices=["standard", "compact", "wide", "large-print", "custom"], default=None)
    parser.add_argument("--custom-margin-top-cm", type=float, default=None)
    parser.add_argument("--custom-margin-bottom-cm", type=float, default=None)
    parser.add_argument("--custom-margin-inside-cm", type=float, default=None)
    parser.add_argument("--custom-margin-outside-cm", type=float, default=None)

    parser.add_argument("--impose", action="store_true")
    parser.add_argument("--signature-pages", type=int, default=None)
    parser.add_argument("--binding-direction", choices=["ltr", "rtl"], default=None)
    parser.add_argument("--max-end-padding", type=int, default=None)

    parser.add_argument("--report-json", default=None)
    return parser


def build_settings(args: argparse.Namespace) -> ChapterfoldSettings:
    data = _settings_from_json(args.settings_json)

    overrides = {
        "variant": args.variant,
        "export_docx": True if args.export_docx else None,
        "export_markdown": True if args.export_markdown else None,
        "paragraph_spacing_mode": args.paragraph_spacing_mode,
        "contents_mode": args.contents_mode,
        "page_number_start_mode": args.page_number_start_mode,
        "front_matter_page_number_style": args.front_matter_page_number_style,
        "page_ornament": args.page_ornament,
        "page_ornament_amount": args.page_ornament_amount,
        "chapter_ornament": args.chapter_ornament,
        "page_size_preset": args.page_size_preset,
        "custom_trim_width_cm": args.custom_trim_width_cm,
        "custom_trim_height_cm": args.custom_trim_height_cm,
        "margin_preset": args.margin_preset,
        "custom_margin_top_cm": args.custom_margin_top_cm,
        "custom_margin_bottom_cm": args.custom_margin_bottom_cm,
        "custom_margin_inside_cm": args.custom_margin_inside_cm,
        "custom_margin_outside_cm": args.custom_margin_outside_cm,
        "create_imposed_pdf": True if args.impose else None,
        "imposed_pages_per_signature": args.signature_pages,
        "signature_size": args.signature_pages,
        "binding_direction": args.binding_direction,
        "max_end_padding": args.max_end_padding,
    }

    for key, value in overrides.items():
        if value is not None:
            data[key] = value

    return ChapterfoldSettings.from_dict(data)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    settings = build_settings(args)
    payload = run_input_processing(args.input_file, args.output_dir, settings)

    if args.report_json:
        report_path = Path(args.report_json)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
