
#!/usr/bin/env python3
"""Run a ChapterFOLD EPUB conversion from the command line."""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.job import run_chapterfold_job
from core.schemas import ChapterfoldJobInput, ChapterfoldSettings


def _setting_names() -> set[str]:
    return set(ChapterfoldSettings.__dataclass_fields__)


def _settings_from_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Settings JSON must contain an object/dictionary.")
    unknown = sorted(set(data) - _setting_names())
    if unknown:
        raise ValueError(f"Unknown setting(s) in JSON: {', '.join(unknown)}")
    return data


def build_settings(args: argparse.Namespace) -> ChapterfoldSettings:
    data = _settings_from_json(args.settings_json)

    overrides: dict[str, Any] = {
        "variant": args.variant,
        "export_docx": True if args.export_docx else None,
        "export_markdown": True if args.export_markdown else None,
        "paragraph_spacing_mode": args.paragraph_spacing_mode,
        "margin_preset": args.margin_preset,
        "page_size_preset": args.page_size_preset,
        "create_imposed_pdf": True if args.impose else None,
        "imposed_pages_per_signature": args.signature_pages,
        "signature_size": args.signature_pages,
        "binding_direction": args.binding_direction,
        "max_end_padding": args.max_end_padding,
        "custom_trim_width_cm": args.custom_trim_width_cm,
        "custom_trim_height_cm": args.custom_trim_height_cm,
        "custom_margin_top_cm": args.custom_margin_top_cm,
        "custom_margin_bottom_cm": args.custom_margin_bottom_cm,
        "custom_margin_inside_cm": args.custom_margin_inside_cm,
        "custom_margin_outside_cm": args.custom_margin_outside_cm,
    }

    for key, value in overrides.items():
        if value is not None:
            data[key] = value

    settings = ChapterfoldSettings.from_dict(data)
    settings.validate()
    return settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a ChapterFOLD EPUB conversion from the command line.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("input_epub", type=Path, help="Path to the source .epub file")
    parser.add_argument("output_dir", type=Path, help="Directory for generated files")
    parser.add_argument("--settings-json", type=Path, default=None, help="Optional JSON settings file")
    parser.add_argument("--variant", choices=["standard", "aggressive-cleanup", "paragraph-dialogue-merge"], default=None)
    parser.add_argument("--export-docx", action="store_true", help="Also export a DOCX file")
    parser.add_argument("--export-markdown", action="store_true", help="Also export a Markdown file")
    parser.add_argument("--paragraph-spacing-mode", choices=["traditional", "uniform", "no-indents", "indented-compact"], default=None)
    parser.add_argument("--page-size-preset", choices=["default-trade", "a4", "a5", "a6", "letter", "half-letter", "trade-5x8", "trade-6x9", "custom"], default=None)
    parser.add_argument("--custom-trim-width-cm", type=float, default=None)
    parser.add_argument("--custom-trim-height-cm", type=float, default=None)
    parser.add_argument("--margin-preset", choices=["standard", "compact", "wide", "large-print", "custom"], default=None)
    parser.add_argument("--custom-margin-top-cm", type=float, default=None)
    parser.add_argument("--custom-margin-bottom-cm", type=float, default=None)
    parser.add_argument("--custom-margin-inside-cm", type=float, default=None)
    parser.add_argument("--custom-margin-outside-cm", type=float, default=None)
    parser.add_argument("--impose", action="store_true", help="Create an imposed/signature PDF")
    parser.add_argument("--signature-pages", type=int, default=None, help="Pages per signature; must be a multiple of 4")
    parser.add_argument("--binding-direction", choices=["ltr", "rtl"], default=None)
    parser.add_argument("--max-end-padding", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs/settings and print planned job without converting")
    parser.add_argument("--report-json", type=Path, default=None, help="Write a JSON report for the completed job")
    parser.add_argument("--traceback", action="store_true", help="Print full traceback if conversion fails")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        settings = build_settings(args)
        job = ChapterfoldJobInput(input_epub=args.input_epub, output_dir=args.output_dir, settings=settings)

        if args.dry_run:
            print(json.dumps(job.to_dict(), indent=2))
            return 0

        result = run_chapterfold_job(job)
        result_data = result.to_dict()
        print(json.dumps(result_data, indent=2))

        if args.report_json:
            args.report_json.parent.mkdir(parents=True, exist_ok=True)
            args.report_json.write_text(json.dumps(result_data, indent=2), encoding="utf-8")

        return 0 if result.success else 1
    except Exception as exc:
        if args.traceback:
            traceback.print_exc()
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
