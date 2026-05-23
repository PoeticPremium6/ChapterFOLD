#!/usr/bin/env python3
"""Run ChapterFOLD over a folder of Gutenberg EPUBs and summarise output quality.

This is intended for before/after regression checks. It can run conversions via
scripts/run_chapterfold_job.py, then collect conversion reports, Markdown length,
PDF page counts, and Gutenberg retention metrics into JSON/CSV/Markdown summary
files.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - optional in report mode
    PdfReader = None  # type: ignore


def _json_safe(value):
    """Convert Path/dataclass/list/dict values into JSON-serialisable objects."""
    from dataclasses import asdict, is_dataclass
    from pathlib import Path as _Path

    if isinstance(value, _Path):
        return str(value)
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    return value


@dataclass
class BookAssessment:
    filename: str
    status: str
    output_dir: str
    command_returncode: int | None = None
    title: str = ""
    author: str = ""
    gutenberg_detected: bool | None = None
    selected_html_items: int | None = None
    dropped_html_items: int | None = None
    total_text_chars: int | None = None
    selected_text_chars: int | None = None
    selected_retention_ratio: float | None = None
    markdown_chars: int | None = None
    markdown_nonblank_lines: int | None = None
    markdown_first_body_line: str = ""
    pdf_pages: int | None = None
    pdf_size_bytes: int | None = None
    report_path: str = ""
    markdown_path: str = ""
    pdf_path: str = ""
    warnings: str = ""
    error: str = ""
    baseline_markdown_chars: int | None = None
    baseline_pdf_pages: int | None = None
    delta_markdown_chars: int | None = None
    delta_pdf_pages: int | None = None


def slugify(name: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in name)
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "book"


def find_first(path: Path, patterns: list[str]) -> Path | None:
    for pattern in patterns:
        matches = sorted(path.rglob(pattern))
        if matches:
            return matches[0]
    return None


def read_json(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def markdown_stats(path: Path | None) -> tuple[int | None, int | None, str]:
    if not path or not path.exists():
        return None, None, ""
    text = path.read_text(encoding="utf-8", errors="replace")
    nonblank = [line.strip() for line in text.splitlines() if line.strip()]
    first_body = ""
    for line in nonblank:
        if line.startswith("#") or line.startswith("_"):
            continue
        first_body = line[:160]
        break
    return len(text), len(nonblank), first_body


def pdf_stats(path: Path | None) -> tuple[int | None, int | None]:
    if not path or not path.exists():
        return None, None
    size = path.stat().st_size
    if PdfReader is None:
        return None, size
    try:
        reader = PdfReader(str(path))
        return len(reader.pages), size
    except Exception:
        return None, size


def run_conversion(epub_path: Path, out_dir: Path, args: argparse.Namespace) -> tuple[int, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    report_json = out_dir / "batch_job_report.json"
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_chapterfold_job.py"),
        str(epub_path),
        str(out_dir),
        "--variant",
        args.variant,
        "--paragraph-spacing-mode",
        args.paragraph_spacing_mode,
        "--report-json",
        str(report_json),
    ]
    if args.export_markdown:
        cmd.append("--export-markdown")
    if args.export_docx:
        cmd.append("--export-docx")
    if args.impose:
        cmd.append("--impose")
        if args.signature_pages:
            cmd.extend(["--signature-pages", str(args.signature_pages)])

    completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
    log_path = out_dir / "batch_command.log"
    log_path.write_text(
        "COMMAND:\n" + " ".join(cmd) + "\n\nSTDOUT:\n" + completed.stdout + "\n\nSTDERR:\n" + completed.stderr,
        encoding="utf-8",
    )
    return completed.returncode, str(log_path)


def assess_output(epub_path: Path, out_dir: Path, returncode: int | None, baseline: dict[str, Any] | None = None) -> BookAssessment:
    report_path = find_first(out_dir, ["*Conversion Report*.json", "batch_job_report.json", "*.json"])
    markdown_path = find_first(out_dir, ["*Editable*.md", "*.md"])
    pdf_path = find_first(out_dir, ["*Interior*.pdf", "*.pdf"])

    report = read_json(report_path)
    gutenberg = report.get("gutenberg_report", {}) if isinstance(report.get("gutenberg_report", {}), dict) else {}

    md_chars, md_lines, first_body = markdown_stats(markdown_path)
    pdf_pages, pdf_size = pdf_stats(pdf_path)

    warnings = []
    warnings.extend(str(w) for w in gutenberg.get("warnings", []) or [])
    if md_chars is not None and gutenberg.get("selected_text_chars"):
        selected = int(gutenberg.get("selected_text_chars") or 0)
        if selected and md_chars < selected * 0.20:
            warnings.append("markdown_chars_less_than_20_percent_of_selected_text")
    if pdf_pages is not None and pdf_pages < 10 and (md_chars or 0) > 100_000:
        warnings.append("pdf_page_count_suspiciously_low")
    if md_chars is not None and md_chars < 5_000:
        warnings.append("markdown_output_very_short")

    assessment = BookAssessment(
        filename=epub_path.name,
        status="ok" if not warnings and (returncode in (None, 0)) else "warning" if returncode in (None, 0) else "failed",
        output_dir=str(out_dir),
        command_returncode=returncode,
        title=str(report.get("title") or ""),
        author=str(report.get("author") or ""),
        gutenberg_detected=gutenberg.get("gutenberg_detected"),
        selected_html_items=gutenberg.get("selected_html_items"),
        dropped_html_items=gutenberg.get("dropped_html_items"),
        total_text_chars=gutenberg.get("total_text_chars"),
        selected_text_chars=gutenberg.get("selected_text_chars"),
        selected_retention_ratio=gutenberg.get("selected_retention_ratio"),
        markdown_chars=md_chars,
        markdown_nonblank_lines=md_lines,
        markdown_first_body_line=first_body,
        pdf_pages=pdf_pages,
        pdf_size_bytes=pdf_size,
        report_path=str(report_path or ""),
        markdown_path=str(markdown_path or ""),
        pdf_path=str(pdf_path or ""),
        warnings="; ".join(warnings),
    )

    if baseline:
        b_md = baseline.get("markdown_chars")
        b_pages = baseline.get("pdf_pages")
        assessment.baseline_markdown_chars = b_md
        assessment.baseline_pdf_pages = b_pages
        if isinstance(b_md, int) and isinstance(md_chars, int):
            assessment.delta_markdown_chars = md_chars - b_md
        if isinstance(b_pages, int) and isinstance(pdf_pages, int):
            assessment.delta_pdf_pages = pdf_pages - b_pages

    return assessment


def load_baseline(path: Path | None) -> dict[str, dict[str, Any]]:
    if not path:
        return {}
    summary = path / "summary.json" if path.is_dir() else path
    if not summary.exists():
        return {}
    data = json.loads(summary.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "books" in data:
        rows = data["books"]
    else:
        rows = data
    return {row.get("filename", ""): row for row in rows if isinstance(row, dict)}


def write_summaries(rows: list[BookAssessment], output_root: Path, args: argparse.Namespace) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    dicts = [asdict(row) for row in rows]

    (output_root / "summary.json").write_text(
        json.dumps({"settings": _json_safe(vars(args)), "books": _json_safe(dicts)}, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    csv_path = output_root / "summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(dicts[0].keys()) if dicts else list(BookAssessment.__dataclass_fields__.keys()))
        writer.writeheader()
        writer.writerows(dicts)

    lines = [
        "# Gutenberg batch assessment",
        "",
        f"Input directory: `{args.input_dir}`",
        f"Output directory: `{args.output_dir}`",
        "",
        "| File | Status | Selected chars | MD chars | PDF pages | Δ MD chars | Δ pages | Warnings | First body line |",
        "|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.filename} | {row.status} | {row.selected_text_chars or ''} | {row.markdown_chars or ''} | "
            f"{row.pdf_pages or ''} | {row.delta_markdown_chars if row.delta_markdown_chars is not None else ''} | "
            f"{row.delta_pdf_pages if row.delta_pdf_pages is not None else ''} | {row.warnings or 'none'} | {row.markdown_first_body_line.replace('|', '/')} |"
        )
    (output_root / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {output_root / 'summary.md'}")
    print(f"Wrote {output_root / 'summary.csv'}")
    print(f"Wrote {output_root / 'summary.json'}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch convert and assess Gutenberg EPUB outputs.")
    parser.add_argument("input_dir", type=Path, help="Directory containing raw EPUB files.")
    parser.add_argument("output_dir", type=Path, help="Directory where per-book outputs and summaries are written.")
    parser.add_argument("--baseline", type=Path, help="Previous assessment directory or summary.json to compare against.")
    parser.add_argument("--no-convert", action="store_true", help="Do not run conversion; only summarise existing output directories.")
    parser.add_argument("--variant", default="standard", choices=["standard", "aggressive-cleanup", "paragraph-dialogue-merge"])
    parser.add_argument("--paragraph-spacing-mode", default="indented-compact", choices=["traditional", "uniform", "no-indents", "indented-compact"])
    parser.add_argument("--export-markdown", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--export-docx", action="store_true")
    parser.add_argument("--impose", action="store_true")
    parser.add_argument("--signature-pages", type=int)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    input_dir: Path = args.input_dir
    output_root: Path = args.output_dir
    epub_files = sorted(input_dir.glob("*.epub"))
    if not epub_files:
        print(f"No EPUB files found in {input_dir}", file=sys.stderr)
        return 2

    baseline = load_baseline(args.baseline)
    rows: list[BookAssessment] = []
    for epub_path in epub_files:
        slug = slugify(epub_path.stem)
        out_dir = output_root / slug
        print(f"\n=== {epub_path.name} ===")
        returncode: int | None = None
        if not args.no_convert:
            returncode, log_path = run_conversion(epub_path, out_dir, args)
            print(f"returncode={returncode}; log={log_path}")
        row = assess_output(epub_path, out_dir, returncode, baseline.get(epub_path.name))
        rows.append(row)
        print(f"status={row.status}; md_chars={row.markdown_chars}; pdf_pages={row.pdf_pages}; warnings={row.warnings or 'none'}")

    write_summaries(rows, output_root, args)
    return 1 if any(row.status == "failed" for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
