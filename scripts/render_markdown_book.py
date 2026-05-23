#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.markdown_book_renderer import render_markdown_book


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render edited ChapterFOLD Markdown into printable outputs."
    )
    parser.add_argument("input_markdown", help="Path to edited Markdown file.")
    parser.add_argument("output_dir", help="Directory for rendered outputs.")
    parser.add_argument("--title", help="Override book title.")
    parser.add_argument("--author", help="Override author.")
    parser.add_argument("--no-pdf", action="store_true", help="Do not export PDF.")
    parser.add_argument("--docx", action="store_true", help="Also export DOCX.")
    parser.add_argument(
        "--no-copy-markdown",
        action="store_true",
        help="Do not copy edited Markdown into output folder.",
    )
    parser.add_argument(
        "--toc-mode",
        choices=["keep", "remove", "rebuild"],
        default="keep",
        help="Table of contents handling: keep source TOC, remove it, or rebuild a clean one.",
    )
    parser.add_argument("--report-json", help="Optional path to write render report JSON.")

    args = parser.parse_args()

    result = render_markdown_book(
        args.input_markdown,
        args.output_dir,
        title=args.title,
        author=args.author,
        export_pdf=not args.no_pdf,
        export_docx=args.docx,
        copy_markdown=not args.no_copy_markdown,
        toc_mode=args.toc_mode,
    )

    payload = {
        "success": result.success,
        "output_files": result.output_files,
        "warnings": result.warnings,
        "error": result.error,
        "title": result.title,
        "author": result.author,
        "word_count": getattr(result, "word_count", None),
        "toc_mode": args.toc_mode,
    }

    print(json.dumps(payload, indent=2, ensure_ascii=False))

    if args.report_json:
        report_path = Path(args.report_json)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
