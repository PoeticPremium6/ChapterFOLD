#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.markdown_sections import combine_markdown_books, read_markdown_files, render_section_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Combine multiple ChapterFOLD Editable.md files into one Markdown book.")
    parser.add_argument("input_markdown", nargs="+", help="Input Markdown files to combine, in order")
    parser.add_argument("-o", "--output", required=True, help="Combined Markdown output path")
    parser.add_argument("--title", default="Combined ChapterFOLD Book", help="Combined book title")
    parser.add_argument("--author", default="Various Authors", help="Combined book author line")
    parser.add_argument("--no-source-titles", action="store_true", help="Do not insert each source book title as a section")
    parser.add_argument("--manifest", help="Optional Markdown manifest listing combined sections")
    args = parser.parse_args()

    input_paths = [Path(p) for p in args.input_markdown]
    docs = read_markdown_files(input_paths)
    combined = combine_markdown_books(
        docs,
        title=args.title,
        author=args.author,
        include_source_titles=not args.no_source_titles,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(combined, encoding="utf-8")
    print(f"Wrote {output_path}")

    if args.manifest:
        manifest_path = Path(args.manifest)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(render_section_manifest(combined), encoding="utf-8")
        print(f"Wrote {manifest_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
