from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from core.epub_service import (
    CleanupSettings,
    build_clean_text_sections,
    load_epub_content,
)


def build_multilingual_epub(path: Path) -> None:
    mimetype = "application/epub+zip"

    container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

    content_opf = """<?xml version="1.0" encoding="UTF-8"?>
<package version="2.0" unique-identifier="bookid" xmlns="http://www.idpf.org/2007/opf">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">chapterfold-multilingual-test</dc:identifier>
    <dc:title>Ångström, Café, and 你好</dc:title>
    <dc:creator>Mårten Öberg</dc:creator>
    <dc:language>zh</dc:language>
  </metadata>
  <manifest>
    <item id="chapter1" href="chapter_001.xhtml" media-type="application/xhtml+xml"/>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="chapter1"/>
  </spine>
</package>
"""

    toc_ncx = """<?xml version="1.0" encoding="UTF-8"?>
<ncx version="2005-1" xmlns="http://www.daisy.org/z3986/2005/ncx/">
  <head>
    <meta name="dtb:uid" content="chapterfold-multilingual-test"/>
  </head>
  <docTitle><text>Ångström, Café, and 你好</text></docTitle>
  <navMap>
    <navPoint id="chapter1" playOrder="1">
      <navLabel><text>Multilingual Chapter</text></navLabel>
      <content src="chapter_001.xhtml"/>
    </navPoint>
  </navMap>
</ncx>
"""

    chapter = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh">
<head><title>Multilingual Chapter</title></head>
<body>
<h1>Förord</h1>
<p>Swedish letters: ö ä å. German: Fußgänger. Spanish: niño. French: café.</p>
<h1>第一章</h1>
<p>Chinese text: 你好，世界。孟子曰：仁者愛人。</p>
<p>Greek text: Καλημέρα κόσμε.</p>
<p>Mixed line: Åsa läser ChapterFOLD，而中文也应该保留。</p>
</body>
</html>
"""

    with ZipFile(path, "w") as zf:
        zf.writestr("mimetype", mimetype, compress_type=0)
        zf.writestr("META-INF/container.xml", container_xml, compress_type=ZIP_DEFLATED)
        zf.writestr("OEBPS/content.opf", content_opf, compress_type=ZIP_DEFLATED)
        zf.writestr("OEBPS/toc.ncx", toc_ncx, compress_type=ZIP_DEFLATED)
        zf.writestr("OEBPS/chapter_001.xhtml", chapter, compress_type=ZIP_DEFLATED)


def test_multilingual_epub_load_and_cleanup_preserves_unicode(tmp_path):
    epub_path = tmp_path / "multilingual.epub"
    build_multilingual_epub(epub_path)

    content = load_epub_content(epub_path)
    raw = "\n".join(section for _, section in content.sections)

    assert "ö ä å" in raw
    assert "Fußgänger" in raw
    assert "niño" in raw
    assert "café" in raw
    assert "你好，世界" in raw
    assert "孟子曰" in raw
    assert "Καλημέρα κόσμε" in raw

    cleaned_sections = build_clean_text_sections(
        content.sections,
        drop_notes=False,
        cleanup_settings=CleanupSettings(),
    )
    cleaned = "\n".join(section for _, section in cleaned_sections)

    assert "ö ä å" in cleaned
    assert "Fußgänger" in cleaned
    assert "niño" in cleaned
    assert "café" in cleaned
    assert "你好，世界" in cleaned
    assert "孟子曰" in cleaned
    assert "Καλημέρα κόσμε" in cleaned
    assert "中文也应该保留" in cleaned
