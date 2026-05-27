from __future__ import annotations

import json
from pathlib import Path

from core.batch_anthology_service import (
    externalize_anthology_image_markers,
    write_anthology_markdown,
)
from core.epub_service import _image_payload_encode
from tests.test_batch_anthology_service import build_tiny_epub


def _marker(name: str = "tiny.png") -> str:
    payload = _image_payload_encode(
        src="data:image/png;base64,YWJjMTIz",
        alt="Tiny illustration",
        name=name,
    )
    return f"[[CHAPTERFOLD_IMAGE:{payload}]]"


def test_externalize_anthology_image_markers_writes_asset_and_link(tmp_path):
    marker = _marker()
    markdown = f"# Test\n\n{marker}\n"

    rewritten, files = externalize_anthology_image_markers(
        markdown,
        tmp_path,
        anthology_slug="test-book",
    )

    assert "CHAPTERFOLD_IMAGE" not in rewritten
    assert "![Tiny illustration](" in rewritten
    assert len(files) == 1
    assert Path(files[0]).exists()


def test_write_anthology_markdown_externalizes_embedded_markers(tmp_path):
    one = tmp_path / "illustrated.epub"
    out = tmp_path / "out"
    marker = _marker("story-image.png")

    build_tiny_epub(
        one,
        title="Illustrated Story",
        author="Artist Author",
        body=f"{marker} This story has an illustration.",
    )

    result = write_anthology_markdown(
        [one],
        out,
        anthology_title="External Image Test",
        anthology_author="Various",
    )

    markdown = result.markdown_path.read_text(encoding="utf-8")
    data = json.loads(result.manifest_json_path.read_text(encoding="utf-8"))

    assert "CHAPTERFOLD_IMAGE" not in markdown
    assert "![Tiny illustration](" in markdown
    assert result.externalized_image_files
    assert data["externalized_image_count"] == 1
    assert Path(data["externalized_image_files"][0]).exists()
