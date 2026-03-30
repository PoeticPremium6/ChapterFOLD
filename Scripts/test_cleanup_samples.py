#!/usr/bin/env python3
"""
Small manual test harness for ChapterFOLD cleanup behavior.

Usage:
    python Scripts/test_cleanup_samples.py

Optional:
    python Scripts/test_cleanup_samples.py path/to/samples.txt

Sample file format:
    === Sample Name ===
    <p>"Hello,"</p>
    <p>she said.</p>

    === Another Sample ===
    <p>"What?"</p>
    <p>"Nothing."</p>
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.epub_service import CleanupSettings, sanitize_section_html  # noqa: E402


DEFAULT_SAMPLES: list[tuple[str, str]] = [
    (
        "Split dialogue paragraph with tag continuation",
        """
        <html><body>
        <p>"Had a chat to Malfoy's solicitor?" Ron asks shrewdly. His time as an Auror
        has cultivated a surprising amount of cunning.</p>

        <p>"Well," Hermione says, "a law used to exist, stating that those who knew the
        whereabouts of felons — but didn't report them straight away — could be
        arrested for hindering prosecution. But the law has long since been abolished."</p>

        <p>"So," Harry says carefully, "Draco disappeared half an hour before his
        appointment with the solicitor, who would have told him that there would be
        no legal consequences for him if he turned Lucius over to the authorities."</p>

        <p>"Maybe he did turn Lucius in," Ron says suddenly.</p>

        <p>"What?"</p>

        <p>"Remember when we caught Lucius Malfoy? Everyone wanted to be the
        one to track down the last Death Eater, but in the end, it all came down to an
        anonymous tip."</p>
        </body></html>
        """,
    ),
    (
        "Two paras that should merge",
        """
        <html><body>
        <p>"I don't know,"</p>
        <p>she said quietly, staring at the floor.</p>
        </body></html>
        """,
    ),
    (
        "Lowercase continuation after quote",
        """
        <html><body>
        <p>"You can't be serious,"</p>
        <p>he muttered.</p>
        </body></html>
        """,
    ),
    (
        "Em dash continuation",
        """
        <html><body>
        <p>"Wait —"</p>
        <p>but the door had already slammed shut.</p>
        </body></html>
        """,
    ),
    (
        "New speaker should stay separate",
        """
        <html><body>
        <p>"Where are you going?" Harry asked.</p>
        <p>"Out," said Draco.</p>
        </body></html>
        """,
    ),
    (
        "Narrative paragraphs should stay separate",
        """
        <html><body>
        <p>The room was silent except for the ticking clock.</p>
        <p>Snow drifted softly against the windowpanes.</p>
        </body></html>
        """,
    ),
    (
        "Soft-wrapped line inside one paragraph",
        """
        <html><body>
        <p>"This was wrapped
        across lines in one paragraph," she said.</p>
        </body></html>
        """,
    ),
]


def make_variants() -> list[tuple[str, CleanupSettings]]:
    standard = CleanupSettings(
        join_soft_wrapped_lines=True,
        join_dialogue_continuations=True,
        merge_dialogue_paragraphs=False,
        collapse_extra_blank_lines=True,
        preserve_scene_breaks=True,
    )

    aggressive = CleanupSettings(
        join_soft_wrapped_lines=True,
        join_dialogue_continuations=True,
        merge_dialogue_paragraphs=False,
        collapse_extra_blank_lines=True,
        preserve_scene_breaks=True,
    )

    paragraph_dialogue_merge = replace(
        aggressive,
        merge_dialogue_paragraphs=True,
    )

    return [
        ("standard", standard),
        ("aggressive-cleanup", aggressive),
        ("paragraph-dialogue-merge", paragraph_dialogue_merge),
    ]


def parse_samples_file(path: Path) -> list[tuple[str, str]]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    samples: list[tuple[str, str]] = []
    current_name: str | None = None
    current_body: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("===") and stripped.endswith("==="):
            if current_name is not None:
                samples.append((current_name, "\n".join(current_body).strip()))
            current_name = stripped.strip("=").strip()
            current_body = []
        else:
            current_body.append(line)

    if current_name is not None:
        samples.append((current_name, "\n".join(current_body).strip()))

    if not samples:
        raise ValueError(
            f"No samples found in {path}. Expected blocks like:\n"
            f"=== Sample Name ==="
        )

    return samples


def compact_html(html: str) -> str:
    lines = [line.rstrip() for line in html.strip().splitlines()]
    cleaned = [line for line in lines if line.strip()]
    return "\n".join(cleaned)


def print_rule(char: str = "-", width: int = 88) -> None:
    print(char * width)


def run_samples(samples: Iterable[tuple[str, str]]) -> None:
    variants = make_variants()

    for index, (name, html) in enumerate(samples, start=1):
        print_rule("=")
        print(f"SAMPLE {index}: {name}")
        print_rule("=")
        print("INPUT:")
        print(compact_html(html))
        print()

        for variant_name, settings in variants:
            print_rule()
            print(f"VARIANT: {variant_name}")
            print_rule()
            try:
                output = sanitize_section_html(html, settings)
            except Exception as exc:
                print(f"[ERROR] {type(exc).__name__}: {exc}")
                print()
                continue

            print(compact_html(output))
            print()

        print()


def main() -> int:
    if len(sys.argv) > 2:
        print("Usage: python Scripts/test_cleanup_samples.py [samples.txt]")
        return 2

    if len(sys.argv) == 2:
        sample_path = Path(sys.argv[1]).resolve()
        if not sample_path.exists():
            print(f"Sample file not found: {sample_path}")
            return 1
        samples = parse_samples_file(sample_path)
    else:
        samples = DEFAULT_SAMPLES

    run_samples(samples)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
