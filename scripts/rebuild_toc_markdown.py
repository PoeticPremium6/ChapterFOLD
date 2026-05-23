#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.toc_policy import apply_toc_policy


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply ChapterFOLD table-of-contents policy to an editable Markdown book.")
    parser.add_argument("input_markdown", type=Path)
    parser.add_argument("output_markdown", type=Path)
    parser.add_argument("--mode", choices=["remove", "keep", "rebuild"], default="rebuild")
    parser.add_argument("--report-json", type=Path, help="Optional TOC policy report JSON path.")
    args = parser.parse_args(argv)

    markdown = args.input_markdown.read_text(encoding="utf-8")
    result = apply_toc_policy(markdown, args.mode)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.write_text(result.markdown, encoding="utf-8")

    report = {
        "input_markdown": str(args.input_markdown),
        "output_markdown": str(args.output_markdown),
        "mode": result.mode,
        "removed_existing_toc": result.removed_existing_toc,
        "entry_count": len(result.entries),
        "entries": [{"level": e.level, "title": e.title} for e in result.entries],
        "warning": result.warning,
    }
    if args.report_json:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        args.report_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
