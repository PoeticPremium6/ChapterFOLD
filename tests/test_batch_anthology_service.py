from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from core.batch_anthology_service import (
    anthology_result_to_dict,
    build_anthology_markdown,
    write_anthology_markdown,
)


def build_tiny_epub(path: Path, *, title: str, author: str, body: str) -> None:
    with ZipFile(path, "w", ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
""",
        )
        zf.writestr(
            "OEBPS/content.opf",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>{title}</dc:title>
    <dc:creator>{author}</dc:creator>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="chap1" href="chap1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="chap1"/>
  </spine>
</package>
""",
        )
        zf.writestr(
            "OEBPS/chap1.xhtml",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>{title}</title></head>
<body>
<h1>{title}</h1>
<p>{body}</p>
</body>
</html>
""",
        )


def test_build_anthology_markdown_combines_multiple_epubs(tmp_path):
    one = tmp_path / "one.epub"
    two = tmp_path / "two.epub"

    build_tiny_epub(one, title="Story One", author="Author A", body="First story body.")
    build_tiny_epub(two, title="Story Two", author="Author B", body="Second story body.")

    markdown, records, warnings = build_anthology_markdown(
        [one, two],
        anthology_title="My Anthology",
        anthology_author="Editor Name",
    )

    assert warnings == []
    assert len(records) == 2
    assert "# My Anthology" in markdown
    assert "_By Editor Name_" in markdown
    assert '<section class="chapterfold-title-page">' in markdown
    assert '<div class="chapterfold-page-break"></div>' in markdown
    assert "<!-- ANTHOLOGY_SOURCE_INDEX: 1 -->" in markdown
    assert "<!-- ANTHOLOGY_SOURCE_INDEX: 2 -->" in markdown
    assert "- Story One" in markdown
    assert "- Story Two" in markdown
    assert "# Story One" in markdown
    assert "# Story Two" in markdown
    assert "First story body." in markdown
    assert "Second story body." in markdown


def test_write_anthology_markdown_outputs_manifest(tmp_path):
    one = tmp_path / "one.epub"
    two = tmp_path / "two.epub"
    out = tmp_path / "out"

    build_tiny_epub(one, title="Poem One", author="Poet A", body="Roses are readable.")
    build_tiny_epub(two, title="Poem Two", author="Poet B", body="Violets are printable.")

    result = write_anthology_markdown(
        [one, two],
        out,
        anthology_title="Poem Bundle",
        anthology_author="Various",
    )

    assert result.success
    assert result.markdown_path.exists()
    assert result.manifest_json_path.exists()

    data = json.loads(result.manifest_json_path.read_text(encoding="utf-8"))
    assert data["input_count"] == 2
    assert data["title"] == "Poem Bundle"
    assert data["inputs"][0]["title"] == "Poem One"

    as_dict = anthology_result_to_dict(result)
    assert as_dict["success"]
    assert len(as_dict["inputs"]) == 2


def test_build_anthology_rejects_non_epub(tmp_path):
    txt = tmp_path / "notes.txt"
    txt.write_text("hello", encoding="utf-8")

    try:
        build_anthology_markdown([txt])
    except ValueError as exc:
        assert "EPUB inputs only" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
