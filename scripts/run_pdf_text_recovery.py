#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.pdf_text_extraction import result_to_dict, write_pdf_text_exports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Experimental PDF text recovery for text-based PDFs."
    )
    parser.add_argument("input_pdf", help="Input PDF")
    parser.add_argument("output_dir", help="Output directory")
    parser.add_argument("--export-markdown", action="store_true", help="Write extracted editable Markdown")
    parser.add_argument("--export-docx", action="store_true", help="Write simple extracted DOCX")
    parser.add_argument("--report-json", default=None, help="Optional JSON report path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    export_markdown = bool(args.export_markdown)
    export_docx = bool(args.export_docx)

    # Default to report/analyze + Markdown if no explicit export selected.
    if not export_markdown and not export_docx:
        export_markdown = True

    result = write_pdf_text_exports(
        args.input_pdf,
        args.output_dir,
        export_markdown=export_markdown,
        export_docx=export_docx,
    )

    payload = result_to_dict(result)
    payload["input_type"] = "pdf-text-recovery"
    payload["stage"] = "complete"

    if args.report_json:
        report_path = Path(args.report_json)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
