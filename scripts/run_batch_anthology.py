#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.batch_anthology_service import anthology_result_to_dict, write_anthology_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a Markdown anthology from multiple EPUB files.")
    parser.add_argument("inputs", nargs="+", help="Input EPUB files")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--title", default="Collected Works", help="Anthology title")
    parser.add_argument("--author", default="Various Authors", help="Anthology/editor author line")
    parser.add_argument("--report-json", default=None, help="Optional JSON report path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    result = write_anthology_markdown(
        args.inputs,
        args.output_dir,
        anthology_title=args.title,
        anthology_author=args.author,
    )

    payload = anthology_result_to_dict(result)
    payload["input_type"] = "batch-anthology"
    payload["stage"] = "complete"

    if args.report_json:
        report_path = Path(args.report_json)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
