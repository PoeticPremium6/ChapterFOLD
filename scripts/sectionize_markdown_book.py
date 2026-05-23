#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.markdown_sections import add_section_markers, render_section_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Add ChapterFOLD section markers to an Editable.md file.")
    parser.add_argument("input_markdown", help="Input Markdown file, usually ChapterFOLD Editable.md")
    parser.add_argument("output_markdown", help="Output Markdown file with section markers")
    parser.add_argument("--manifest", help="Optional Markdown manifest listing detected sections")
    args = parser.parse_args()

    input_path = Path(args.input_markdown)
    output_path = Path(args.output_markdown)
    text = input_path.read_text(encoding="utf-8")
    marked = add_section_markers(text)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(marked, encoding="utf-8")
    print(f"Wrote {output_path}")

    if args.manifest:
        manifest_path = Path(args.manifest)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(render_section_manifest(marked), encoding="utf-8")
        print(f"Wrote {manifest_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
