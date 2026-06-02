#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.engine_api import run_engine_job


def _load_settings(path: str | None) -> dict:
    if not path:
        return {}

    settings_path = Path(path)
    if not settings_path.exists():
        raise FileNotFoundError(f"Settings JSON does not exist: {settings_path}")

    data = json.loads(settings_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Settings JSON must contain an object/dictionary.")

    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a ChapterFOLD engine job using the web-worker-safe API."
    )
    parser.add_argument("input_path", help="Input EPUB/PDF path.")
    parser.add_argument(
        "output_dir",
        nargs="?",
        help="Output directory. Optional when --workspace-root is used.",
    )
    parser.add_argument(
        "--settings-json",
        help="Path to JSON settings file.",
    )
    parser.add_argument(
        "--workspace-root",
        help="Optional root directory for isolated job workspaces.",
    )
    parser.add_argument(
        "--job-id",
        help="Optional external job ID, useful for future Supabase/Render jobs.",
    )
    parser.add_argument(
        "--report-json",
        help="Optional path to write the engine result JSON.",
    )
    parser.add_argument(
        "--validate-settings",
        action="store_true",
        help="Validate settings against the web-safe settings catalog.",
    )
    parser.add_argument(
        "--no-reports",
        action="store_true",
        help="Do not write conversion/manual QA reports.",
    )

    args = parser.parse_args(argv)

    try:
        settings = _load_settings(args.settings_json)

        result = run_engine_job(
            input_path=args.input_path,
            output_dir=args.output_dir,
            workspace_root=args.workspace_root,
            job_id=args.job_id,
            settings=settings,
            report_json=args.report_json,
            write_reports=not args.no_reports,
            validate_settings=args.validate_settings,
        )

        result_json = result.to_json()
        print(result_json)

        if args.report_json:
            report_path = Path(args.report_json)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(result_json, encoding="utf-8")

        return 0 if result.success else 1

    except Exception as exc:
        payload = {
            "success": False,
            "stage": "failed",
            "error": str(exc),
            "input_path": args.input_path,
            "output_dir": args.output_dir or "",
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
