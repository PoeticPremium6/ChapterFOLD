from __future__ import annotations

import json
import zipfile
from pathlib import Path

from core.engine_api import run_engine_job


def _make_minimal_epub(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/epub+zip")
        z.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
""",
        )
        z.writestr(
            "OEBPS/content.opf",
            """<?xml version="1.0" encoding="utf-8"?>
<package version="3.0" unique-identifier="bookid" xmlns="http://www.idpf.org/2007/opf">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">chapterfold-smoke</dc:identifier>
    <dc:title>ChapterFOLD EPUB Smoke</dc:title>
    <dc:language>en</dc:language>
    <dc:creator>ChapterFOLD Test</dc:creator>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="chapter1"/>
  </spine>
</package>
""",
        )
        z.writestr(
            "OEBPS/nav.xhtml",
            """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head><title>Contents</title></head>
  <body>
    <nav epub:type="toc" xmlns:epub="http://www.idpf.org/2007/ops">
      <ol><li><a href="chapter1.xhtml">Chapter 1</a></li></ol>
    </nav>
  </body>
</html>
""",
        )
        z.writestr(
            "OEBPS/chapter1.xhtml",
            """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head><title>Chapter 1</title></head>
  <body>
    <h1>Chapter 1</h1>
    <p>This is a minimal EPUB fixture for the ChapterFOLD engine API smoke test.</p>
    <p>It confirms EPUB conversion works through the worker-safe engine boundary.</p>
  </body>
</html>
""",
        )

    return path


def test_epub_engine_api_path_creates_outputs_and_reports(tmp_path: Path) -> None:
    input_epub = _make_minimal_epub(tmp_path / "chapterfold-smoke.epub")

    result = run_engine_job(
        input_path=input_epub,
        workspace_root=tmp_path / "jobs",
        job_id="epub-engine-api-smoke",
        settings={},
        validate_settings=False,
    )

    assert result.success is True, result.to_json()
    assert result.input_type == "epub"
    assert result.output_files, result.to_json()

    output_files = [Path(path) for path in result.output_files]
    assert any(path.suffix.lower() in {".pdf", ".md", ".docx"} for path in output_files)

    assert result.report_json
    assert Path(result.report_json).exists()

    assert result.manifest_json
    assert Path(result.manifest_json).exists()

    report = json.loads(Path(result.report_json).read_text(encoding="utf-8"))
    manifest = json.loads(Path(result.manifest_json).read_text(encoding="utf-8"))

    assert report["success"] is True
    assert report["input_type"] == "epub"
    assert report["output_files"]

    assert manifest["status"] == "complete"
    assert manifest["stage"] == "complete"
    assert manifest["input_type"] == "epub"
    assert manifest["output_files"]
