#!/usr/bin/env python3
"""Build synthetic EPUB fixtures for ChapterFOLD regression tests.

These fixtures are intentionally tiny and generated from inline text so the repo
can test EPUB handling without storing copyrighted books.
"""
from __future__ import annotations

import argparse
import json
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from textwrap import dedent
from uuid import uuid4


@dataclass(frozen=True)
class SampleEpub:
    slug: str
    title: str
    author: str
    description: str
    chapter_html: str


def _xhtml_body(inner_html: str, title: str) -> str:
    return dedent(f"""\
    <?xml version="1.0" encoding="utf-8"?>
    <!DOCTYPE html>
    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
      <head>
        <title>{title}</title>
      </head>
      <body>
        <h1>{title}</h1>
        {inner_html}
      </body>
    </html>
    """).strip()


SAMPLES: tuple[SampleEpub, ...] = (
    SampleEpub(
        slug="scene-breaks",
        title="Scene Break Regression Sample",
        author="ChapterFOLD Test Suite",
        description="Checks that common scene-break markers survive extraction and cleanup.",
        chapter_html=_xhtml_body(
            """
            <p>The rain softened against the workshop window.</p>
            <p>* * *</p>
            <p>By morning, the glue had cured.</p>
            """,
            "Scene Break Regression Sample",
        ),
    ),
    SampleEpub(
        slug="dialogue-softwrap",
        title="Dialogue Softwrap Regression Sample",
        author="ChapterFOLD Test Suite",
        description="Checks dialogue continuation lines and soft wrapped text.",
        chapter_html=_xhtml_body(
            """
            <p>&quot;I can fold this,&quot;<br/>she said.</p>
            <p>The next paragraph was split<br/>across two visual lines.</p>
            """,
            "Dialogue Softwrap Regression Sample",
        ),
    ),
    SampleEpub(
        slug="unicode-punctuation",
        title="Unicode Punctuation Regression Sample",
        author="ChapterFOLD Test Suite",
        description="Checks curly quotes, em dashes, ellipses, and non-ASCII text survive parsing.",
        chapter_html=_xhtml_body(
            """
            <p>“Wait—don’t trim that margin yet…”</p>
            <p>Café binding notes: naïve spacing should not break extraction.</p>
            """,
            "Unicode Punctuation Regression Sample",
        ),
    ),
)


def write_epub(sample: SampleEpub, output_dir: Path) -> Path:
    """Write one minimal EPUB 3-ish archive and return its path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    epub_path = output_dir / f"{sample.slug}.epub"
    book_id = f"urn:uuid:{uuid4()}"

    container_xml = dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
      <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
      </rootfiles>
    </container>
    """).strip()

    content_opf = dedent(f"""\
    <?xml version="1.0" encoding="UTF-8"?>
    <package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="3.0">
      <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:identifier id="bookid">{book_id}</dc:identifier>
        <dc:title>{sample.title}</dc:title>
        <dc:creator>{sample.author}</dc:creator>
        <dc:language>en</dc:language>
        <meta property="dcterms:modified">2026-01-01T00:00:00Z</meta>
      </metadata>
      <manifest>
        <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
        <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
      </manifest>
      <spine>
        <itemref idref="chapter1"/>
      </spine>
    </package>
    """).strip()

    nav_xhtml = dedent(f"""\
    <?xml version="1.0" encoding="utf-8"?>
    <!DOCTYPE html>
    <html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
      <head><title>{sample.title} Navigation</title></head>
      <body>
        <nav epub:type="toc" id="toc">
          <h1>Contents</h1>
          <ol><li><a href="chapter1.xhtml">Chapter 1</a></li></ol>
        </nav>
      </body>
    </html>
    """).strip()

    with zipfile.ZipFile(epub_path, "w") as zf:
        # EPUB requires mimetype to be the first file and stored uncompressed.
        zf.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", container_xml, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/content.opf", content_opf, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/nav.xhtml", nav_xhtml, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/chapter1.xhtml", sample.chapter_html, compress_type=zipfile.ZIP_DEFLATED)

    return epub_path


def build_sample_epubs(output_dir: Path) -> list[Path]:
    paths = [write_epub(sample, output_dir) for sample in SAMPLES]
    manifest = {
        "generated_by": "scripts/build_sample_epubs.py",
        "samples": [asdict(sample) | {"filename": f"{sample.slug}.epub"} for sample in SAMPLES],
    }
    for sample in manifest["samples"]:
        sample.pop("chapter_html", None)
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Build synthetic EPUB regression fixtures.")
    parser.add_argument(
        "output_dir",
        nargs="?",
        default="tests/fixtures/epubs/generated",
        type=Path,
        help="Directory where generated sample EPUBs should be written.",
    )
    args = parser.parse_args()
    paths = build_sample_epubs(args.output_dir)
    print("Built EPUB fixtures:")
    for path in paths:
        print(f"  {path}")
    return 0




# Patch 009b fixture compatibility aliases
def _write_compatibility_aliases() -> None:
    """Create underscore-named aliases expected by older tests.

    Patch 004 originally generated hyphenated fixture names. Some tests and
    docs refer to underscore names, so keep both names available. These files
    live under tests/fixtures/epubs/generated/ and are ignored by git.
    """
    aliases = {
        "scene-breaks.epub": "scene_breaks.epub",
        "dialogue-softwrap.epub": "dialogue_softwrap.epub",
        "unicode-punctuation.epub": "unicode_punctuation.epub",
    }
    generated_dir = Path("tests/fixtures/epubs/generated")
    for src_name, alias_name in aliases.items():
        src = generated_dir / src_name
        alias = generated_dir / alias_name
        if src.exists():
            alias.write_bytes(src.read_bytes())


if __name__ == "__main__":
    raise SystemExit(main())
    _write_compatibility_aliases()
