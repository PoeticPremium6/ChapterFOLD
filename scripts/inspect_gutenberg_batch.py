#!/usr/bin/env python3
"""Inspect all EPUB files in a directory and write Gutenberg reports."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.inspect_epub_structure import markdown_from_report, write_report


def _slug(path: Path) -> str:
    slug = path.stem.strip().lower().replace(" ", "_").replace("-", "_")
    return "".join(ch for ch in slug if ch.isalnum() or ch == "_") or "epub"


def _summary_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Gutenberg inspection batch summary",
        "",
        "| File | HTML items | Total chars | Selected body chars | Ratio | Risk flags |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('filename', '')} | {row.get('html_item_count', 0)} | "
            f"{row.get('total_text_chars', 0)} | {row.get('selected_body_text_chars', 0)} | "
            f"{row.get('selected_body_retention_ratio', 0)} | {', '.join(row.get('risk_flags', [])) or 'none'} |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect all EPUB files in a directory for Gutenberg body-selection behavior.")
    parser.add_argument("input_dir")
    parser.add_argument("output_dir")
    args = parser.parse_args(argv)

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for epub_path in sorted(input_dir.glob("*.epub")):
        slug = _slug(epub_path)
        output_json = output_dir / f"{slug}.json"
        output_md = output_dir / f"{slug}.md"
        report = write_report(epub_path, output_json, output_md)
        rows.append(
            {
                "filename": report.get("filename"),
                "metadata_title": report.get("metadata_title"),
                "html_item_count": report.get("html_item_count"),
                "total_text_chars": report.get("total_text_chars"),
                "selected_body_text_chars": report.get("selected_body_text_chars"),
                "selected_body_retention_ratio": report.get("selected_body_retention_ratio"),
                "risk_flags": report.get("risk_flags", []),
                "json_report": str(output_json),
                "markdown_report": str(output_md),
            }
        )

    (output_dir / "summary.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / "summary.md").write_text(_summary_markdown(rows), encoding="utf-8")
    print(f"Wrote {output_dir / 'summary.json'}")
    print(f"Wrote {output_dir / 'summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
