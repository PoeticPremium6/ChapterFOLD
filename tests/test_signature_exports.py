from __future__ import annotations

import json

from core.signature_exports import (
    calculate_signature_groups,
    split_markdown_into_signature_batches,
    write_signature_plan_json,
    write_signature_plan_markdown,
)


def test_calculate_signature_groups_adds_final_blanks():
    groups = calculate_signature_groups(total_pages=34, pages_per_signature=16)

    assert len(groups) == 3
    assert groups[0].start_page == 1
    assert groups[0].end_page == 16
    assert groups[-1].start_page == 33
    assert groups[-1].end_page == 48
    assert groups[-1].blank_pages == 14


def test_signature_plan_exports(tmp_path):
    groups = calculate_signature_groups(total_pages=20, pages_per_signature=16)

    json_path = write_signature_plan_json(
        output_path=tmp_path / "plan.json",
        total_pages=20,
        pages_per_signature=16,
        groups=groups,
    )
    md_path = write_signature_plan_markdown(
        output_path=tmp_path / "plan.md",
        title="Test Book",
        total_pages=20,
        pages_per_signature=16,
        groups=groups,
    )

    data = json.loads(json_path.read_text(encoding="utf-8"))
    md = md_path.read_text(encoding="utf-8")

    assert data["total_signatures"] == 2
    assert data["blank_pages_added"] == 12
    assert "Signature 1: pages 1-16" in md
    assert "Signature 2: pages 17-32" in md


def test_signature_markdown_batches_are_created():
    groups = calculate_signature_groups(total_pages=20, pages_per_signature=16)
    markdown = "# Book\n\nPara 1.\n\nPara 2.\n\nPara 3."

    batched = split_markdown_into_signature_batches(markdown, groups)

    assert "# Signature Batches" in batched
    assert "## Signature 1: pages 1-16" in batched
    assert "## Signature 2: pages 17-32" in batched
