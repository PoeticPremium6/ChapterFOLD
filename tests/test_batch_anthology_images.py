from __future__ import annotations

import json
from pathlib import Path

from core.batch_anthology_service import build_anthology_markdown, write_anthology_markdown
from core.epub_service import _image_payload_encode
from tests.test_batch_anthology_service import build_tiny_epub


def _marker() -> str:
    payload = _image_payload_encode(
        src="data:image/png;base64,abc123",
        alt="Tiny illustration",
    )
    return f"[[CHAPTERFOLD_IMAGE:{payload}]]"


def test_batch_anthology_preserves_image_markers_in_markdown(tmp_path):
    one = tmp_path / "illustrated.epub"
    marker = _marker()

    build_tiny_epub(
        one,
        title="Illustrated Story",
        author="Artist Author",
        body=f"{marker} This story has an illustration.",
    )

    markdown, records, warnings = build_anthology_markdown(
        [one],
        anthology_title="Image Test",
        anthology_author="Various",
    )

    assert warnings == []
    assert marker in markdown
    assert "CHAPTERFOLD_IMAGE" in markdown
    assert records[0].image_marker_count >= 1


def test_batch_anthology_manifest_records_image_fields(tmp_path):
    one = tmp_path / "illustrated.epub"
    out = tmp_path / "out"
    marker = _marker()

    build_tiny_epub(
        one,
        title="Illustrated Story",
        author="Artist Author",
        body=f"{marker} This story has an illustration.",
    )

    result = write_anthology_markdown(
        [one],
        out,
        anthology_title="Image Manifest Test",
        anthology_author="Various",
    )

    data = json.loads(result.manifest_json_path.read_text(encoding="utf-8"))
    first = data["inputs"][0]

    assert "image_marker_count" in first
    assert "image_asset_count" in first
    assert "image_asset_files" in first
    assert first["image_marker_count"] >= 1


def test_batch_anthology_counts_raw_markers_when_preserved(tmp_path):
    one = tmp_path / "illustrated.epub"
    marker = _marker()

    build_tiny_epub(
        one,
        title="Marker Count Story",
        author="Artist Author",
        body=f"{marker}",
    )

    markdown, records, warnings = build_anthology_markdown(
        [one],
        anthology_title="Marker Count Test",
        anthology_author="Various",
    )

    assert warnings == []
    assert marker in markdown
    assert records[0].image_marker_count == 1
