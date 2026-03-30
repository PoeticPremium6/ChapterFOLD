#!/usr/bin/env python3
from __future__ import annotations

import html
import re
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from ebooklib import ITEM_DOCUMENT, epub
from docx import Document

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

try:
    from weasyprint import HTML
except Exception as e:
    HTML = None
    WEASYPRINT_IMPORT_ERROR = e
else:
    WEASYPRINT_IMPORT_ERROR = None


DEFAULT_FONT_STACK = '"Garamond", "EB Garamond", "Cormorant Garamond", serif'


@dataclass
class LayoutSettings:
    trim_width_cm: float = 15.24
    trim_height_cm: float = 22.86
    margin_top_cm: float = 1.5
    margin_bottom_cm: float = 1.5
    margin_inside_cm: float = 1.8
    margin_outside_cm: float = 1.0
    font_size_pt: float = 11.5
    line_height: float = 1.35
    font_family: str = DEFAULT_FONT_STACK
    drop_notes: bool = False


@dataclass
class CleanupSettings:
    join_soft_wrapped_lines: bool = True
    join_dialogue_continuations: bool = True
    collapse_extra_blank_lines: bool = True
    preserve_scene_breaks: bool = True


@dataclass
class EpubContent:
    detected_title: str
    detected_author: str
    sections: List[Tuple[str, str]]


@dataclass
class EpubToPdfResult:
    input_epub: Path
    output_dir: Path
    output_pdf: Path
    output_docx: Path | None
    book_slug: str
    detected_title: str
    detected_author: str
    used_title: str
    used_author: str


SCENE_BREAK_RE = re.compile(
    r"^\s*(\*\s*){3,}$|^\s*#{3,}\s*$|^\s*-\s*-\s*-\s*$|^\s*~\s*~\s*~\s*$"
)


def cm(value: float) -> str:
    return f"{value:.3f}cm"


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    value = re.sub(r"[\s_-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-") or "book"


def build_book_slug(
    *,
    title: str | None = None,
    author: str | None = None,
    fallback_stem: str | None = None,
) -> str:
    parts = []
    if author:
        parts.append(slugify(author))
    if title:
        parts.append(slugify(title))

    if parts:
        return "__".join(parts)

    if fallback_stem:
        return slugify(fallback_stem)

    return "book"


def output_dir_for_book(base_dir: Path, book_slug: str) -> Path:
    return base_dir / f"{book_slug}_output"


def interior_pdf_name(book_slug: str) -> str:
    return f"{book_slug}__interior.pdf"


def editable_docx_name(book_slug: str) -> str:
    return f"{book_slug}__editable.docx"


def normalize_line_endings(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def normalize_spaces(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text


def is_scene_break(line: str) -> bool:
    return bool(SCENE_BREAK_RE.match(line.strip()))


def join_dialogue_line_pair(current: str, nxt: str) -> str | None:
    current = current.rstrip()
    nxt = nxt.lstrip()

    if not current or not nxt:
        return None

    if re.search(r'[,"\u201d\u2019—-]$', current) and re.match(r"^[a-z(]", nxt):
        return f"{current} {nxt}"

    if re.search(r'["\u201d\u2019]$', current) and re.match(
        r"^(he|she|they|i|we|it|you|his|her|their|the)\b",
        nxt,
        flags=re.IGNORECASE,
    ):
        return f"{current} {nxt}"

    return None


def clean_block_lines(lines: list[str], settings: CleanupSettings) -> list[str]:
    if not lines:
        return []

    result: list[str] = []
    i = 0

    while i < len(lines):
        current = lines[i].strip()

        if settings.join_dialogue_continuations and i + 1 < len(lines):
            joined = join_dialogue_line_pair(current, lines[i + 1])
            if joined is not None:
                result.append(joined)
                i += 2
                continue

        result.append(current)
        i += 1

    if settings.join_soft_wrapped_lines:
        merged = " ".join(x for x in result if x.strip())
        merged = re.sub(r" {2,}", " ", merged).strip()
        return [merged] if merged else []

    return result


def clean_text_block(text: str, settings: CleanupSettings | None = None) -> str:
    settings = settings or CleanupSettings()

    text = normalize_line_endings(text)
    text = normalize_spaces(text)

    lines = text.split("\n")
    output_blocks: list[str] = []
    current_block: list[str] = []

    def flush_current_block() -> None:
        nonlocal current_block
        if not current_block:
            return
        cleaned_lines = clean_block_lines(current_block, settings)
        if cleaned_lines:
            output_blocks.append("\n".join(cleaned_lines))
        current_block = []

    blank_run = 0

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            blank_run += 1
            flush_current_block()
            if not settings.collapse_extra_blank_lines or blank_run == 1:
                output_blocks.append("")
            continue

        blank_run = 0

        if settings.preserve_scene_breaks and is_scene_break(line):
            flush_current_block()
            output_blocks.append(line)
            continue

        current_block.append(line)

    flush_current_block()

    cleaned = "\n".join(output_blocks)

    if settings.collapse_extra_blank_lines:
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()


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


def load_epub_content(epub_path: Path) -> EpubContent:
    book = epub.read_epub(str(epub_path))
    title, author = get_metadata(book)
    sections: List[Tuple[str, str]] = []

    for item in book.get_items_of_type(ITEM_DOCUMENT):
        raw = item.get_content()
        soup = BeautifulSoup(raw, "xml")

        for bad in soup(["script", "style"]):
            bad.decompose()

        body = soup.find("body") or soup

        heading = ""
        for tag in body.find_all(["h1", "h2", "h3"]):
            txt = tag.get_text(" ", strip=True)
            if txt:
                heading = txt
                break

        body_html = "".join(str(x) for x in body.contents).strip()
        if body_html:
            sections.append((heading, body_html))

    return EpubContent(
        detected_title=title,
        detected_author=author,
        sections=sections,
    )


def sanitize_section_html(
    fragment: str,
    *,
    drop_notes: bool = False,
    cleanup_settings: CleanupSettings | None = None,
) -> str:
    soup = BeautifulSoup(fragment, "xml")

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

    cleanup_settings = cleanup_settings or CleanupSettings()

    for p in soup.find_all("p"):
        text = p.get_text("\n", strip=False)
        cleaned = clean_text_block(text, cleanup_settings)

        if cleaned.strip():
            p.clear()
            p.append(cleaned)
        else:
            p.decompose()

    body = soup.find("body")
    if body:
        return "".join(str(x) for x in body.contents)
    return "".join(str(x) for x in soup.contents)


def extract_clean_text_from_html(
    fragment: str,
    *,
    drop_notes: bool = False,
    cleanup_settings: CleanupSettings | None = None,
) -> str:
    soup = BeautifulSoup(fragment, "xml")

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

    cleanup_settings = cleanup_settings or CleanupSettings()
    paragraphs: list[str] = []

    for p in soup.find_all("p"):
        text = p.get_text("\n", strip=False)
        cleaned = clean_text_block(text, cleanup_settings)
        if cleaned.strip():
            paragraphs.append(cleaned.strip())

    return "\n\n".join(paragraphs).strip()


def build_clean_text_sections(
    sections: List[Tuple[str, str]],
    *,
    drop_notes: bool,
    cleanup_settings: CleanupSettings | None = None,
) -> List[Tuple[str, str]]:
    cleaned_sections: List[Tuple[str, str]] = []

    for heading, raw_html in sections:
        cleaned_text = extract_clean_text_from_html(
            raw_html,
            drop_notes=drop_notes,
            cleanup_settings=cleanup_settings,
        )
        if cleaned_text.strip():
            cleaned_sections.append((heading, cleaned_text))

    return cleaned_sections


def build_section_blocks(
    sections: List[Tuple[str, str]],
    *,
    drop_notes: bool,
    cleanup_settings: CleanupSettings | None = None,
) -> List[str]:
    blocks: List[str] = []
    first_real_section = True

    for heading, raw_html in sections:
        cleaned = sanitize_section_html(
            raw_html,
            drop_notes=drop_notes,
            cleanup_settings=cleanup_settings,
        )
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

    return blocks


def build_css(settings: LayoutSettings) -> str:
    return f"""
    @page {{
      size: {cm(settings.trim_width_cm)} {cm(settings.trim_height_cm)};
      margin-top: {cm(settings.margin_top_cm)};
      margin-bottom: {cm(settings.margin_bottom_cm)};
      @bottom-center {{
        content: counter(page);
        font-size: 9pt;
      }}
    }}

    @page :right {{
      margin-left: {cm(settings.margin_inside_cm)};
      margin-right: {cm(settings.margin_outside_cm)};
    }}

    @page :left {{
      margin-left: {cm(settings.margin_outside_cm)};
      margin-right: {cm(settings.margin_inside_cm)};
    }}

    html {{
      font-size: {settings.font_size_pt}pt;
    }}

    body {{
      margin: 0;
      padding: 0;
      color: #111;
      font-family: {settings.font_family};
      line-height: {settings.line_height};
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
      font-size: {settings.font_size_pt * 2.0:.2f}pt;
      line-height: 1.15;
    }}

    .title-wrap .author {{
      margin: 0;
      font-size: {settings.font_size_pt * 1.15:.2f}pt;
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
      font-size: {settings.font_size_pt * 1.45:.2f}pt;
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


def build_html_document(
    *,
    title: str,
    author: str,
    sections: List[Tuple[str, str]],
    settings: LayoutSettings,
    cleanup_settings: CleanupSettings | None = None,
) -> str:
    blocks = [
        f"""
        <section class="title-page">
          <div class="title-wrap">
            <h1>{html.escape(title)}</h1>
            <p class="author">{html.escape(author)}</p>
          </div>
        </section>
        """,
        '<section class="blank-page" aria-hidden="true"></section>',
        *build_section_blocks(
            sections,
            drop_notes=settings.drop_notes,
            cleanup_settings=cleanup_settings,
        ),
    ]

    css = build_css(settings)

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


def default_output_pdf_path(
    epub_path: Path,
    *,
    used_title: str,
    used_author: str,
) -> Path:
    book_slug = build_book_slug(
        title=used_title,
        author=used_author,
        fallback_stem=epub_path.stem,
    )
    output_dir = output_dir_for_book(epub_path.parent, book_slug)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / interior_pdf_name(book_slug)


def default_output_docx_path(output_dir: Path, book_slug: str) -> Path:
    return output_dir / editable_docx_name(book_slug)


def ensure_weasyprint_available() -> None:
    if HTML is None:
        raise RuntimeError(
            "WeasyPrint could not be imported because its native libraries are missing.\n"
            "Install WeasyPrint's system dependencies and try again.\n\n"
            f"Original import error: {WEASYPRINT_IMPORT_ERROR}"
        )


def render_pdf(html_doc: str, output_pdf_path: Path) -> None:
    ensure_weasyprint_available()
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html_doc).write_pdf(str(output_pdf_path))


def export_clean_docx(
    *,
    title: str,
    author: str,
    sections: List[Tuple[str, str]],
    output_path: str | Path,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = Document()
    doc.add_heading(title, level=0)
    if author.strip():
        doc.add_paragraph(author)

    first_section = True
    for heading, text in sections:
        if not first_section:
            doc.add_page_break()
        first_section = False

        if heading.strip():
            doc.add_heading(heading, level=1)

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        for para in paragraphs:
            doc.add_paragraph(para)

    doc.save(str(output_path))
    return output_path


def process_epub_to_pdf(
    *,
    epub_path: str | Path,
    output_pdf_path: str | Path | None = None,
    output_docx_path: str | Path | None = None,
    export_docx: bool = False,
    title: str | None = None,
    author: str | None = None,
    settings: LayoutSettings | None = None,
    cleanup_settings: CleanupSettings | None = None,
) -> EpubToPdfResult:
    epub_path = Path(epub_path)
    if not epub_path.exists():
        raise FileNotFoundError(f"EPUB not found: {epub_path}")

    settings = settings or LayoutSettings()
    cleanup_settings = cleanup_settings or CleanupSettings()

    epub_content = load_epub_content(epub_path)
    if not epub_content.sections:
        raise ValueError("No readable content sections found in EPUB.")

    used_title = title or epub_content.detected_title
    used_author = author or epub_content.detected_author

    html_doc = build_html_document(
        title=used_title,
        author=used_author,
        sections=epub_content.sections,
        settings=settings,
        cleanup_settings=cleanup_settings,
    )

    book_slug = build_book_slug(
        title=used_title,
        author=used_author,
        fallback_stem=epub_path.stem,
    )

    output_pdf = (
        Path(output_pdf_path)
        if output_pdf_path
        else default_output_pdf_path(
            epub_path,
            used_title=used_title,
            used_author=used_author,
        )
    )

    render_pdf(html_doc, output_pdf)

    output_docx: Path | None = None
    if export_docx:
        clean_text_sections = build_clean_text_sections(
            epub_content.sections,
            drop_notes=settings.drop_notes,
            cleanup_settings=cleanup_settings,
        )
        output_docx = (
            Path(output_docx_path)
            if output_docx_path
            else default_output_docx_path(output_pdf.parent, book_slug)
        )
        export_clean_docx(
            title=used_title,
            author=used_author,
            sections=clean_text_sections,
            output_path=output_docx,
        )

    return EpubToPdfResult(
        input_epub=epub_path,
        output_dir=output_pdf.parent,
        output_pdf=output_pdf,
        output_docx=output_docx,
        book_slug=book_slug,
        detected_title=epub_content.detected_title,
        detected_author=epub_content.detected_author,
        used_title=used_title,
        used_author=used_author,
    )
