#!/usr/bin/env python3
"""
Convert EPUB into a print-ready interior PDF.

Features:
- Title page
- Blank page after title
- Body starts on a right-hand page
- Bottom-centre page numbering
- Mirrored margins for bookbinding
- Reads title/author from EPUB metadata if not supplied
- Ignores unknown IDE/PyDev arguments
- Fails cleanly if WeasyPrint native libraries are missing

Example:
    python epub_to_pdf.py "C:\\Users\\jonat\\Documents\\Bees_Books\\Running_on_Air.epub"
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path
from typing import List, Tuple

from bs4 import BeautifulSoup
from ebooklib import epub, ITEM_DOCUMENT

try:
    from weasyprint import HTML
except Exception as e:
    HTML = None
    WEASYPRINT_IMPORT_ERROR = e
else:
    WEASYPRINT_IMPORT_ERROR = None


DEFAULT_FONT_STACK = '"Garamond", "EB Garamond", "Cormorant Garamond", serif'
DEFAULT_EPUB_PATH = r"C:\Users\jonat\Documents\Bees_Books\Running_on_Air.epub"


def cm(value: float) -> str:
    return f"{value:.3f}cm"


def get_input_path_interactively() -> str:
    print("No EPUB path was provided.")
    print(f"Press Enter to use the example path:\n{DEFAULT_EPUB_PATH}\n")
    entered = input("EPUB path: ").strip()
    return entered or DEFAULT_EPUB_PATH


def get_metadata(book: epub.EpubBook) -> Tuple[str, str]:
    title = "Unknown Title"
    author = "Unknown Author"

    title_meta = book.get_metadata("DC", "title")
    if title_meta and title_meta[0] and title_meta[0][0]:
        title = str(title_meta[0][0]).strip()

    creator_meta = book.get_metadata("DC", "creator")
    if creator_meta and creator_meta[0] and creator_meta[0][0]:
        author = str(creator_meta[0][0]).strip()

    return title, author


def read_epub_sections_and_metadata(epub_path: Path) -> Tuple[str, str, List[Tuple[str, str]]]:
    book = epub.read_epub(str(epub_path))
    title, author = get_metadata(book)
    sections: List[Tuple[str, str]] = []

    for item in book.get_items_of_type(ITEM_DOCUMENT):
        raw = item.get_content()
        soup = BeautifulSoup(raw, "lxml")

        for bad in soup(["script", "style"]):
            bad.decompose()

        body = soup.body or soup

        heading = ""
        for tag in body.find_all(["h1", "h2", "h3"]):
            txt = tag.get_text(" ", strip=True)
            if txt:
                heading = txt
                break

        body_html = "".join(str(x) for x in body.contents).strip()
        if body_html:
            sections.append((heading, body_html))

    return title, author, sections


def sanitize_section_html(fragment: str, drop_notes: bool = False) -> str:
    soup = BeautifulSoup(fragment, "lxml")

    selectors_to_drop = [
        ".landmark",
        ".actions",
        ".download",
        "nav",
    ]

    if drop_notes:
        selectors_to_drop.extend(
            [
                ".preface",
                ".notes",
                ".endnotes",
                "#notes",
                "#work_endnotes",
            ]
        )

    for selector in selectors_to_drop:
        for el in soup.select(selector):
            el.decompose()

    for p in soup.find_all("p"):
        text = p.get_text(" ", strip=False)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n", text)
        if text.strip():
            p.clear()
            p.append(text)
        else:
            p.decompose()

    return "".join(str(x) for x in (soup.body.contents if soup.body else soup.contents))


def build_html_document(
    *,
    title: str,
    author: str,
    sections: List[Tuple[str, str]],
    trim_width_cm: float,
    trim_height_cm: float,
    margin_top_cm: float,
    margin_bottom_cm: float,
    margin_inside_cm: float,
    margin_outside_cm: float,
    font_size_pt: float,
    line_height: float,
    font_family: str,
    drop_notes: bool,
) -> str:
    blocks = []

    blocks.append(
        f"""
        <section class="title-page">
          <div class="title-wrap">
            <h1>{html.escape(title)}</h1>
            <p class="author">{html.escape(author)}</p>
          </div>
        </section>
        """
    )

    blocks.append('<section class="blank-page" aria-hidden="true"></section>')

    first_real_section = True
    for heading, raw_html in sections:
        cleaned = sanitize_section_html(raw_html, drop_notes=drop_notes)
        if not cleaned.strip():
            continue

        heading_html = (
            f"<h1 class='chapter-title'>{html.escape(heading)}</h1>" if heading else ""
        )

        chapter_class = "chapter first-body-chapter" if first_real_section else "chapter"
        first_real_section = False

        blocks.append(
            f"""
            <section class="{chapter_class}">
              {heading_html}
              {cleaned}
            </section>
            """
        )

    css = f"""
    @page {{
      size: {cm(trim_width_cm)} {cm(trim_height_cm)};
      margin-top: {cm(margin_top_cm)};
      margin-bottom: {cm(margin_bottom_cm)};
      @bottom-center {{
        content: counter(page);
        font-size: 9pt;
      }}
    }}

    @page :right {{
      margin-left: {cm(margin_inside_cm)};
      margin-right: {cm(margin_outside_cm)};
    }}

    @page :left {{
      margin-left: {cm(margin_outside_cm)};
      margin-right: {cm(margin_inside_cm)};
    }}

    html {{
      font-size: {font_size_pt}pt;
    }}

    body {{
      margin: 0;
      padding: 0;
      color: #111;
      font-family: {font_family};
      line-height: {line_height};
      -weasy-bookmark-level: none;
    }}

    .title-page {{
      break-after: page;
      min-height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      text-align: center;
    }}

    .title-wrap h1 {{
      margin: 0 0 0.45em 0;
      font-size: {font_size_pt * 2.0:.2f}pt;
      line-height: 1.15;
    }}

    .title-wrap .author {{
      margin: 0;
      font-size: {font_size_pt * 1.15:.2f}pt;
    }}

    .blank-page {{
      break-after: page;
    }}

    .first-body-chapter {{
      break-before: right;
    }}

    .chapter {{
      break-before: page;
    }}

    .first-body-chapter.chapter {{
      break-before: right;
    }}

    .chapter-title {{
      text-align: center;
      margin: 0 0 1.8em 0;
      font-size: {font_size_pt * 1.45:.2f}pt;
      page-break-after: avoid;
    }}

    p {{
      margin: 0 0 0.65em 0;
      text-align: justify;
      text-indent: 0;
      orphans: 2;
      widows: 2;
    }}

    .chapter p + p {{
      text-indent: 1.2em;
    }}

    h1, h2, h3, h4 {{
      page-break-after: avoid;
    }}

    em {{
      font-style: italic;
    }}

    strong {{
      font-weight: bold;
    }}

    hr {{
      margin: 1.2em auto;
      width: 25%;
    }}
    """

    return f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>{html.escape(title)}</title>
      <style>{css}</style>
    </head>
    <body>
      {''.join(blocks)}
    </body>
    </html>
    """


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("epub_path", nargs="?", help="Input EPUB path")
    parser.add_argument("--title", default=None, help="Override book title")
    parser.add_argument("--author", default=None, help="Override author name")
    parser.add_argument("--out", default="interior.pdf", help="Output PDF path")

    parser.add_argument("--trim-width-cm", type=float, default=15.24)
    parser.add_argument("--trim-height-cm", type=float, default=22.86)

    parser.add_argument("--margin-top-cm", type=float, default=1.5)
    parser.add_argument("--margin-bottom-cm", type=float, default=1.5)
    parser.add_argument("--margin-inside-cm", type=float, default=1.8)
    parser.add_argument("--margin-outside-cm", type=float, default=1.0)

    parser.add_argument("--font-size-pt", type=float, default=11.5)
    parser.add_argument("--line-height", type=float, default=1.35)
    parser.add_argument("--font-family", default=DEFAULT_FONT_STACK)

    parser.add_argument("--drop-notes", action="store_true")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args, unknown = parser.parse_known_args(argv)

    epub_path_str = args.epub_path or get_input_path_interactively()
    epub_path = Path(epub_path_str)

    if not epub_path.exists():
        print(f"EPUB not found: {epub_path}", file=sys.stderr)
        return 2

    try:
        detected_title, detected_author, sections = read_epub_sections_and_metadata(epub_path)
    except Exception as e:
        print(f"Failed to read EPUB: {e}", file=sys.stderr)
        return 3

    if not sections:
        print("No readable content sections found in EPUB.", file=sys.stderr)
        return 4

    title = args.title or detected_title
    author = args.author or detected_author

    html_doc = build_html_document(
        title=title,
        author=author,
        sections=sections,
        trim_width_cm=args.trim_width_cm,
        trim_height_cm=args.trim_height_cm,
        margin_top_cm=args.margin_top_cm,
        margin_bottom_cm=args.margin_bottom_cm,
        margin_inside_cm=args.margin_inside_cm,
        margin_outside_cm=args.margin_outside_cm,
        font_size_pt=args.font_size_pt,
        line_height=args.line_height,
        font_family=args.font_family,
        drop_notes=args.drop_notes,
    )

    if HTML is None:
        print("WeasyPrint could not be imported because its native libraries are missing.", file=sys.stderr)
        print("Your Python code is fine, but the Windows rendering dependencies are not installed correctly.", file=sys.stderr)
        print("", file=sys.stderr)
        print("Next steps:", file=sys.stderr)
        print("1. Install WeasyPrint's Windows native dependencies.", file=sys.stderr)
        print("2. Make sure the required GTK/Pango libraries are on PATH.", file=sys.stderr)
        print("3. Then rerun this script.", file=sys.stderr)
        print("", file=sys.stderr)
        print(f"Original import error: {WEASYPRINT_IMPORT_ERROR}", file=sys.stderr)
        return 10

    try:
        HTML(string=html_doc).write_pdf(args.out)
    except Exception as e:
        print(f"Failed to write PDF: {e}", file=sys.stderr)
        return 5

    print(f"Detected title:  {detected_title}")
    print(f"Detected author: {detected_author}")
    print(f"Used title:      {title}")
    print(f"Used author:     {author}")
    print(f"Wrote:           {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
