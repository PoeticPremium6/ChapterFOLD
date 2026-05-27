from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.product_hardening import (
    build_conversion_report,
    write_conversion_report,
    write_manual_qa_log_template,
    write_sample_gallery_manifest,
)


def run_command(command: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.returncode, proc.stdout, proc.stderr


def main() -> int:
    output_root = ROOT / "reports" / "v2_hardening_smoke"
    output_root.mkdir(parents=True, exist_ok=True)

    samples = [
        {
            "title": "Unicode multilingual smoke",
            "input": "tests/fixtures/unicode/multilingual.epub",
            "output_dir": "reports/v2_hardening_smoke/unicode",
            "args": [
                "--variant",
                "standard",
                "--page-number-start",
                "after-title-page",
                "--page-ornament",
                "poetic-vine",
                "--page-ornament-amount",
                "balanced",
                "--chapter-ornament",
                "rose-window",
            ],
        },
        {
            "title": "Pride ornament smoke",
            "input": "tests/fixtures/gutenberg/raw/Pride and Prejudice.epub",
            "output_dir": "reports/v2_hardening_smoke/pride",
            "args": [
                "--variant",
                "standard",
                "--contents-mode",
                "rebuild",
                "--page-number-start",
                "after-title-page",
                "--page-ornament",
                "bookbinder-rule",
                "--page-ornament-amount",
                "subtle",
                "--chapter-ornament",
                "poetic-vine",
            ],
        },
    ]

    gallery: list[dict] = []
    failures: list[str] = []

    for sample in samples:
        report_json = ROOT / sample["output_dir"] / "report.json"
        command = [
            sys.executable,
            "scripts/run_chapterfold_job.py",
            sample["input"],
            sample["output_dir"],
            *sample["args"],
            "--report-json",
            str(report_json),
        ]

        code, stdout, stderr = run_command(command)

        payload = {}
        if report_json.exists():
            payload = json.loads(report_json.read_text(encoding="utf-8"))

        conversion_report = build_conversion_report(
            payload=payload or {
                "success": False,
                "stage": "subprocess",
                "output_files": [],
                "warnings": [],
                "error": stderr or stdout,
            },
            input_path=sample["input"],
            output_dir=sample["output_dir"],
            input_type="epub",
            settings={"args": sample["args"]},
        )
        write_conversion_report(conversion_report, ROOT / sample["output_dir"])
        write_manual_qa_log_template(ROOT / sample["output_dir"])

        gallery.append(
            {
                "title": sample["title"],
                "input": sample["input"],
                "output_dir": sample["output_dir"],
                "conversion_report": str(Path(sample["output_dir"]) / "conversion_report.json"),
                "manual_qa_log": str(Path(sample["output_dir"]) / "manual_qa_log.md"),
                "success": conversion_report.success,
            }
        )

        if code != 0 or not conversion_report.success:
            failures.append(sample["title"])

    write_sample_gallery_manifest(output_root, gallery)

    print(json.dumps({"success": not failures, "failures": failures, "samples": gallery}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
