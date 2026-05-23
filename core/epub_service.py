#!/usr/bin/env python3
from __future__ import annotations

import base64
import html
from core.special_layout import preserve_special_short_line_blocks
import json
import re
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from ebooklib import ITEM_DOCUMENT, epub
from docx import Document

from docx.enum.section import WD_SECTION_START
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from core.gutenberg_inline_trim import trim_gutenberg_boilerplate_from_sections
from core.epub_toc_cleanup import strip_original_toc_blocks

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
    paragraph_spacing_mode: str = "traditional"


@dataclass
class CleanupSettings:
    join_soft_wrapped_lines: bool = True
    join_dialogue_continuations: bool = True
    merge_dialogue_paragraphs: bool = False
    aggressive_mode: bool = False
    collapse_extra_blank_lines: bool = True
    preserve_scene_breaks: bool = True


@dataclass
class EpubContent:
    detected_title: str
    detected_author: str
    sections: List[Tuple[str, str]]
    cover_image_data_uri: str = ""
    cover_image_name: str = ""


@dataclass
class EpubToPdfResult:
    input_epub: Path
    output_dir: Path
    output_pdf: Path
    output_docx: Path | None
    output_markdown: Path | None
    book_slug: str
    detected_title: str
    detected_author: str
    used_title: str
    used_author: str


SCENE_BREAK_RE = re.compile(
    r"^\s*(\*\s*){3,}$|^\s*#{3,}\s*$|^\s*-\s*-\s*-\s*$|^\s*~\s*~\s*~\s*$"
)

DIALOGUE_TAG_START_RE = re.compile(
    r"^(?:"
    r"he|she|they|i|we|it|you|his|her|their|the|"
    r"said|asked|whispered|murmured|replied|answered|shouted|yelled|"
    r"cried|called|snapped|hissed|muttered|breathed|added|continued|"
    r"harry|ron|hermione|draco|ginny|luna|neville|snape|remus|sirius|"
    r"malfoy|potter|granger|he'd|she'd|they'd|he'll|she'll|they'll"
    r")\b",
    flags=re.IGNORECASE,
)

LOWER_CONTINUATION_RE = re.compile(r"^[a-z(\[\u2014\-']")
TERMINAL_END_RE = re.compile(r"""[.!?]["\u201d\u2019']?$""")
OPENING_QUOTE_RE = re.compile(r"""^["\u201c\u2018]""")

CHAPTER_HEADING_TEXT_RE = re.compile(
    r"^\s*(?:CHAPTER\s+(?:\d+|[IVXLCDM]+)\.?\s+.+|Epilogue)\s*$",
    flags=re.IGNORECASE,
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


def markdown_name(book_slug: str) -> str:
    return f"{book_slug}__google-docs.md"


def normalize_line_endings(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def normalize_spaces(text: str) -> str:
    text = text.replace("\xa0", " ")
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

    if re.search(r"""[,\u2014\-]|["\u201d\u2019]$""", current) and LOWER_CONTINUATION_RE.match(nxt):
        return f"{current} {nxt}"

    if re.search(r"""["\u201d\u2019]$""", current) and DIALOGUE_TAG_START_RE.match(nxt):
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


def _extract_cover_image_data_uri(book: epub.EpubBook) -> tuple[str, str]:
    """Return a data URI for the best available EPUB cover image.

    This is intentionally conservative for v1: it prefers items marked as
    cover-image, then image files with "cover" in the name, then the first
    image resource.
    """
    image_items = []
    for item in book.get_items():
        media_type = str(getattr(item, "media_type", "") or "")
        name = str(item.get_name() or "")
        lower_name = name.lower()
        if media_type.startswith("image/") or lower_name.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
            image_items.append(item)

    if not image_items:
        return "", ""

    def score(item) -> tuple[int, str]:
        name = str(item.get_name() or "")
        lower_name = name.lower()
        props = set(getattr(item, "properties", []) or [])
        if "cover-image" in props:
            return (0, name)
        if "cover" in lower_name:
            return (1, name)
        return (2, name)

    best = sorted(image_items, key=score)[0]
    media_type = str(getattr(best, "media_type", "") or "")
    name = str(best.get_name() or "cover-image")
    if not media_type.startswith("image/"):
        suffix = Path(name).suffix.lower()
        media_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }.get(suffix, "image/jpeg")

    data = best.get_content()
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{media_type};base64,{encoded}", name




IMAGE_MARKER_RE = re.compile(r"^\[\[CHAPTERFOLD_IMAGE:(?P<payload>[A-Za-z0-9_\-=]+)\]\]$")


def _image_payload_encode(*, src: str, alt: str = "", name: str = "") -> str:
    payload = {"src": src or "", "alt": alt or "", "name": name or ""}
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def _image_payload_decode(marker: str) -> dict[str, str] | None:
    match = IMAGE_MARKER_RE.match(marker.strip())
    if not match:
        return None
    try:
        raw = base64.urlsafe_b64decode(match.group("payload").encode("ascii"))
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    return {
        "src": str(data.get("src") or ""),
        "alt": str(data.get("alt") or ""),
        "name": str(data.get("name") or ""),
    }


def _is_image_marker(value: str) -> bool:
    return _image_payload_decode(value) is not None


def _image_marker_to_html(value: str) -> str:
    data = _image_payload_decode(value)
    if not data or not data.get("src"):
        return ""

    src = html.escape(data["src"], quote=True)
    alt = html.escape(data.get("alt") or "", quote=True)
    caption = html.escape(data.get("alt") or "")
    caption_html = f"<figcaption>{caption}</figcaption>" if caption else ""

    return (
        '<figure class="book-image">'
        f'<img src="{src}" alt="{alt}" />'
        f'{caption_html}'
        '</figure>'
    )


def _build_image_data_uri_lookup(book: epub.EpubBook) -> dict[str, str]:
    lookup: dict[str, str] = {}

    for item in book.get_items():
        media_type = str(getattr(item, "media_type", "") or "")
        name = str(item.get_name() or "")
        lower_name = name.lower()

        if not (
            media_type.startswith("image/")
            or lower_name.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"))
        ):
            continue

        if not media_type.startswith("image/"):
            suffix = Path(name).suffix.lower()
            media_type = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
                ".svg": "image/svg+xml",
            }.get(suffix, "image/jpeg")

        data_uri = "data:{};base64,{}".format(
            media_type,
            base64.b64encode(item.get_content()).decode("ascii"),
        )

        for key in {
            name,
            name.replace("\\", "/"),
            Path(name).name,
            Path(name).as_posix(),
        }:
            if key:
                lookup[key] = data_uri

    return lookup


def _resolve_epub_image_src(src: str, *, item_name: str, lookup: dict[str, str]) -> str:
    src = (src or "").strip()
    if not src:
        return ""

    src_no_anchor = src.split("#", 1)[0]
    candidates = [
        src,
        src_no_anchor,
        Path(src_no_anchor).name,
        str((Path(item_name).parent / src_no_anchor).as_posix()).lstrip("./"),
    ]

    for candidate in candidates:
        candidate = candidate.replace("\\", "/")
        if candidate in lookup:
            return lookup[candidate]

    return ""


def _replace_epub_images_with_markers(body, *, item_name: str, image_lookup: dict[str, str]) -> None:
    """Replace EPUB img nodes with paragraph markers that survive text cleanup."""
    for img in list(body.find_all("img")):
        src = _resolve_epub_image_src(
            str(img.get("src") or ""),
            item_name=item_name,
            lookup=image_lookup,
        )
        if not src:
            img.decompose()
            continue

        alt = str(img.get("alt") or "").strip()
        name = str(img.get("src") or "").strip()
        marker = "[[CHAPTERFOLD_IMAGE:{}]]".format(
            _image_payload_encode(src=src, alt=alt, name=name)
        )

        marker_soup = BeautifulSoup("", "html.parser")
        new_p = marker_soup.new_tag("p")
        new_p.string = marker
        img.replace_with(new_p)




COPYRIGHT_CAPTION_RE = re.compile(
    r"""^\[?\s*copyright\s+\d{4}\s+by\s+.+?\]?\s*\.?$""",
    re.IGNORECASE,
)


def _is_orphan_copyright_caption(value: str) -> bool:
    return bool(COPYRIGHT_CAPTION_RE.match((value or "").strip()))


def _clean_heading_candidate(value: str) -> str:
    """Avoid using internal image markers/copyright notices as section headings."""
    value = clean_text_block(value or "").strip()
    if not value:
        return ""
    if _is_image_marker(value):
        return ""
    if "[[CHAPTERFOLD_IMAGE:" in value:
        return ""
    if _is_orphan_copyright_caption(value):
        return ""
    return value




COPYRIGHT_CAPTION_RE = re.compile(
    r"""^\[?\s*copyright\s+\d{4}\s+by\s+.+?\]?\s*\.?$""",
    re.IGNORECASE,
)

IMAGE_MARKER_ANYWHERE_RE = re.compile(
    r"\[\[CHAPTERFOLD_IMAGE:[A-Za-z0-9_\-=]+\]\]"
)


def _strip_internal_image_markers(value: str) -> str:
    return IMAGE_MARKER_ANYWHERE_RE.sub("", value or "")


def _normalize_caption_text(value: str) -> str:
    value = html.unescape(value or "")
    value = _strip_internal_image_markers(value)
    value = re.sub(r"\[\s*copyright\s+\d{4}\s+by\s+.+?\]", "", value, flags=re.I)
    value = value.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    value = re.sub(r"[^A-Za-z0-9]+", " ", value).strip().casefold()
    return value


def _is_orphan_copyright_caption(value: str) -> bool:
    return bool(COPYRIGHT_CAPTION_RE.match((value or "").strip()))


def _image_marker_alt(value: str) -> str:
    data = _image_payload_decode(value)
    if not data:
        return ""
    return str(data.get("alt") or "").strip()


def _caption_matches_image_alt(caption: str, image_marker: str) -> bool:
    caption_norm = _normalize_caption_text(caption)
    alt_norm = _normalize_caption_text(_image_marker_alt(image_marker))
    if not caption_norm or not alt_norm:
        return False
    return caption_norm == alt_norm or caption_norm in alt_norm or alt_norm in caption_norm


def _is_probable_standalone_caption(value: str, image_marker: str = "") -> bool:
    value = clean_text_block(value or "").strip()
    if not value:
        return False

    if _is_orphan_copyright_caption(value):
        return True

    if image_marker and _caption_matches_image_alt(value, image_marker):
        return True

    if image_marker:
        cleaned = re.sub(r"\[\s*copyright\s+\d{4}\s+by\s+.+?\]", "", value, flags=re.I).strip()
        if len(cleaned) <= 90 and (
            cleaned.startswith(("“", '"', "'"))
            or cleaned.endswith(("”", '"', "'"))
        ):
            return True

    return False


def _clean_heading_candidate(value: str) -> str:
    value = clean_text_block(value or "").strip()
    if not value:
        return ""

    value = _strip_internal_image_markers(value).strip()
    if not value:
        return ""

    if _is_orphan_copyright_caption(value):
        return ""

    if len(value) <= 90 and value.startswith(("“", '"', "'")):
        return ""

    return value


def _collapse_image_adjacent_captions(items: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Remove duplicated caption/copyright paragraphs immediately after images."""
    collapsed: list[tuple[str, str]] = []
    i = 0

    while i < len(items):
        kind, value = items[i]

        if kind != "image":
            collapsed.append((kind, value))
            i += 1
            continue

        collapsed.append((kind, value))
        i += 1

        while i < len(items):
            next_kind, next_value = items[i]
            if next_kind not in {"p", "heading"}:
                break
            if _is_probable_standalone_caption(next_value, value):
                i += 1
                continue
            break

    return collapsed


def _spine_positions_by_href(book: epub.EpubBook) -> dict[str, int]:
    positions: dict[str, int] = {}
    for pos, entry in enumerate(getattr(book, "spine", []) or [], start=1):
        idref = entry[0] if isinstance(entry, (tuple, list)) and entry else entry
        try:
            item = book.get_item_with_id(idref)
        except Exception:
            item = None
        href = getattr(item, "file_name", None) if item is not None else None
        if href:
            positions[str(href)] = pos
    return positions


def load_epub_content(epub_path: Path) -> EpubContent:
    book = epub.read_epub(str(epub_path))
    title, author = get_metadata(book)
    cover_image_data_uri, cover_image_name = _extract_cover_image_data_uri(book)
    image_data_uri_lookup = _build_image_data_uri_lookup(book)

    from core.gutenberg_content_filter import (
        apply_gutenberg_filter_to_records,
        build_epub_html_record,
    )

    spine_positions = _spine_positions_by_href(book)
    records: list[dict] = []

    for index, item in enumerate(book.get_items_of_type(ITEM_DOCUMENT)):
        raw = item.get_content()
        soup = BeautifulSoup(raw, "xml")
        for bad in soup(["script", "style"]):
            bad.decompose()

        body = soup.find("body") or soup
        href = str(getattr(item, "file_name", "") or item.get_name() or f"item-{index}")

        _replace_epub_images_with_markers(
            body,
            item_name=href,
            image_lookup=image_data_uri_lookup,
        )

        heading = ""
        for tag in body.find_all(["h1", "h2", "h3"]):
            txt = _clean_heading_candidate(tag.get_text(" ", strip=True))
            if txt:
                heading = txt
                break

        body_html = "".join(str(x) for x in body.contents).strip()
        if not body_html:
            continue

        record = build_epub_html_record(
            index=index,
            href=href,
            spine_position=spine_positions.get(href, index + 1),
            heading=heading,
            body_html=body_html,
        )
        records.append(record)

    selected_records, gutenberg_report = apply_gutenberg_filter_to_records(records)
    sections: List[Tuple[str, str]] = [
        (str(record.get("heading", "")), str(record.get("body_html", "")))
        for record in selected_records
        if str(record.get("body_html", "")).strip()
    ]

    sections = trim_gutenberg_boilerplate_from_sections(sections)
    content = EpubContent(
        detected_title=title,
        detected_author=author,
        sections=sections,
        cover_image_data_uri=cover_image_data_uri,
        cover_image_name=cover_image_name,
    )
    # Attached dynamically to avoid a broad dataclass/API rewrite.
    content.gutenberg_report = gutenberg_report
    return content

def _selectors_to_drop(drop_notes: bool) -> list[str]:
    selectors = [".landmark", ".actions", ".download", "nav"]
    if drop_notes:
        selectors.extend([
            ".preface",
            ".notes",
            ".endnotes",
            "#notes",
            "#work_endnotes",
        ])
    return selectors


def _drop_unwanted_nodes(soup: BeautifulSoup, *, drop_notes: bool) -> None:
    for selector in _selectors_to_drop(drop_notes):
        for el in soup.select(selector):
            el.decompose()


def _raw_paragraph_items_from_fragment(fragment: str, *, drop_notes: bool = False) -> list[tuple[str, str]]:
    fragment = strip_original_toc_blocks(fragment)
    soup = BeautifulSoup(fragment, "html.parser")
    _drop_unwanted_nodes(soup, drop_notes=drop_notes)
    body = soup.find("body") or soup

    items: list[tuple[str, str]] = []
    block_tags = {"p", "blockquote", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6"}
    scene_tags = {"hr"}

    for node in body.descendants:
        if not getattr(node, "name", None):
            continue

        if node.name in scene_tags:
            items.append(("scene", "***"))
            continue

        if node.name not in block_tags:
            continue

        if node.find(block_tags):
            continue

        text = node.get_text("\n", strip=False)
        cleaned = clean_text_block(text)
        if cleaned.strip():
            for chunk in [part.strip() for part in cleaned.split("\n\n") if part.strip()]:
                if _is_image_marker(chunk):
                    items.append(("image", chunk))
                elif is_scene_break(chunk):
                    items.append(("scene", "***"))
                elif node.name in {"h1", "h2", "h3", "h4", "h5", "h6"} or CHAPTER_HEADING_TEXT_RE.match(chunk):
                    items.append(("heading", chunk))
                else:
                    items.append(("p", chunk))

    deduped: list[tuple[str, str]] = []
    previous = None
    for item in items:
        if item == previous and item[0] == "scene":
            continue
        deduped.append(item)
        previous = item
    return deduped


def should_merge_dialogue_paragraphs(
    current: str,
    nxt: str,
    settings: CleanupSettings,
) -> bool:
    current = current.strip()
    nxt = nxt.strip()
    if not current or not nxt:
        return False

    if is_scene_break(current) or is_scene_break(nxt):
        return False

    if re.search(r"""["\u201d\u2019]$""", current) and DIALOGUE_TAG_START_RE.match(nxt):
        return True

    if re.search(r"""[,;:\u2014\-]$|["\u201d\u2019]$""", current) and (
        LOWER_CONTINUATION_RE.match(nxt) or DIALOGUE_TAG_START_RE.match(nxt)
    ):
        return True

    if not settings.aggressive_mode:
        return False

    if len(current) <= 110 and not TERMINAL_END_RE.search(current):
        if LOWER_CONTINUATION_RE.match(nxt) or DIALOGUE_TAG_START_RE.match(nxt):
            return True

    if len(current) <= 90 and OPENING_QUOTE_RE.match(current):
        if not TERMINAL_END_RE.search(current):
            return True

    if len(nxt) <= 120 and (
        LOWER_CONTINUATION_RE.match(nxt) or DIALOGUE_TAG_START_RE.match(nxt)
    ):
        if not TERMINAL_END_RE.search(current):
            return True

    return False


def merge_adjacent_paragraph_items(
    items: list[tuple[str, str]],
    settings: CleanupSettings,
) -> list[tuple[str, str]]:
    if not settings.merge_dialogue_paragraphs:
        return items

    merged: list[tuple[str, str]] = []
    for kind, text in items:
        if (
            merged
            and kind == "p"
            and merged[-1][0] == "p"
            and should_merge_dialogue_paragraphs(merged[-1][1], text, settings)
        ):
            merged[-1] = ("p", f"{merged[-1][1].rstrip()} {text.lstrip()}")
        else:
            merged.append((kind, text))
    return merged


def extract_clean_items_from_html(
    fragment: str,
    *,
    drop_notes: bool = False,
    cleanup_settings: CleanupSettings | None = None,
) -> list[tuple[str, str]]:
    cleanup_settings = cleanup_settings or CleanupSettings()
    raw_items = _raw_paragraph_items_from_fragment(fragment, drop_notes=drop_notes)

    normalized: list[tuple[str, str]] = []
    for kind, text in raw_items:
        if kind == "scene":
            if cleanup_settings.preserve_scene_breaks:
                normalized.append(("scene", "***"))
            continue

        cleaned = clean_text_block(text, cleanup_settings)
        if not cleaned.strip():
            continue

        cleaned_value = cleaned.strip()

        if _is_orphan_copyright_caption(cleaned_value):
            continue

        if kind == "image" or _is_image_marker(cleaned_value):
            normalized.append(("image", cleaned_value))
        elif kind == "heading" or CHAPTER_HEADING_TEXT_RE.match(cleaned_value):
            heading_value = _clean_heading_candidate(cleaned_value)
            if heading_value:
                normalized.append(("heading", heading_value))
        else:
            cleaned_value = _strip_internal_image_markers(cleaned_value).strip()
            if cleaned_value and not _is_orphan_copyright_caption(cleaned_value):
                normalized.append(("p", cleaned_value))

    normalized = _collapse_image_adjacent_captions(normalized)
    return merge_adjacent_paragraph_items(normalized, cleanup_settings)


def sanitize_section_html(
    fragment: str,
    *,
    drop_notes: bool = False,
    cleanup_settings: CleanupSettings | None = None,
) -> str:
    items = extract_clean_items_from_html(
        fragment,
        drop_notes=drop_notes,
        cleanup_settings=cleanup_settings,
    )

    html_parts: list[str] = []
    for kind, text in items:
        value = text.strip()

        if not value or _is_orphan_copyright_caption(value):
            continue

        if kind == "scene":
            html_parts.append('<hr class="scene-break" />')
        elif kind == "image":
            image_html = _image_marker_to_html(value)
            if image_html:
                html_parts.append(image_html)
        else:
            image_html = _image_marker_to_html(value)
            if image_html:
                html_parts.append(image_html)
            else:
                value = _strip_internal_image_markers(value).strip()
                if value and not _is_orphan_copyright_caption(value):
                    html_parts.append(f"<p>{html.escape(value)}</p>")

    return "\n".join(html_parts)


def extract_clean_text_from_html(
    fragment: str,
    *,
    drop_notes: bool = False,
    cleanup_settings: CleanupSettings | None = None,
) -> str:
    items = extract_clean_items_from_html(
        fragment,
        drop_notes=drop_notes,
        cleanup_settings=cleanup_settings,
    )

    parts: list[str] = []
    for kind, text in items:
        value = text.strip()
        if not value or _is_orphan_copyright_caption(value):
            continue

        if kind == "scene":
            parts.append("***")
        elif kind == "image":
            # Rich Markdown image export can be added later; never leak markers.
            continue
        else:
            value = _strip_internal_image_markers(value).strip()
            if value and not _is_orphan_copyright_caption(value):
                parts.append(value)

    return "\n\n".join(parts).strip()





def strip_internal_image_markers_for_counting(value: str) -> str:
    """Remove ChapterFOLD image markers before text-retention estimates."""
    return re.sub(r"\[\[CHAPTERFOLD_IMAGE:[A-Za-z0-9_\-=]+\]\]", "", value or "")


def estimate_sections_text_chars(sections: List[Tuple[str, str]]) -> int:
    """Estimate readable text characters in raw section HTML fragments."""

    total = 0
    for _, raw_html in sections:
        raw_html = strip_internal_image_markers_for_counting(raw_html or "")
        soup = BeautifulSoup(raw_html, "html.parser")
        for bad in soup(["script", "style"]):
            bad.decompose()
        total += len(soup.get_text("\n", strip=True))
    return total


def estimate_cleaned_text_chars(sections: List[Tuple[str, str]]) -> int:
    """Count characters in cleaned text sections."""

    return sum(len(strip_internal_image_markers_for_counting(text or "")) for _, text in sections)


def build_cleanup_retention_report(
    *,
    sections: List[Tuple[str, str]],
    cleaned_sections: List[Tuple[str, str]],
    gutenberg_report: dict | None = None,
) -> dict:
    """Build a stage-level cleanup retention report.

    For Gutenberg EPUBs, prefer the selector's selected_text_chars as the
    denominator because it describes the body content intentionally kept after
    notice/license filtering.
    """

    raw_chars = estimate_sections_text_chars(sections)
    cleaned_chars = estimate_cleaned_text_chars(cleaned_sections)

    selector_chars = 0
    gutenberg_detected = False
    if isinstance(gutenberg_report, dict):
        gutenberg_detected = bool(gutenberg_report.get("gutenberg_detected"))
        try:
            selector_chars = int(gutenberg_report.get("selected_text_chars") or 0)
        except (TypeError, ValueError):
            selector_chars = 0

    denominator = selector_chars or raw_chars

    # Image-preserving EPUBs can inflate selector_selected_text_chars because
    # internal image markers may contain base64 data URIs. If selector chars are
    # wildly larger than text extracted from the same selected sections, use the
    # text-only raw count for retention decisions.
    selector_image_inflated = bool(selector_chars and raw_chars and selector_chars > raw_chars * 5)
    if selector_image_inflated:
        denominator = raw_chars

    ratio = (cleaned_chars / denominator) if denominator else 0.0

    risk_flags: list[str] = []
    warnings: list[str] = []
    failed = False

    if denominator >= 50_000 and cleaned_chars < 10_000:
        risk_flags.append("cleaned_text_very_short")
    if denominator >= 50_000 and ratio < 0.20:
        risk_flags.append("cleanup_retention_below_20_percent")
    if gutenberg_detected and denominator >= 50_000 and ratio < 0.20:
        failed = True
        warnings.append(
            "Gutenberg cleanup removed most selected body text; conservative fallback was attempted."
        )

    return {
        "raw_section_text_chars": raw_chars,
        "selector_selected_text_chars": selector_chars,
        "selector_image_inflated": selector_image_inflated,
        "retention_denominator_chars": denominator,
        "cleaned_text_chars": cleaned_chars,
        "cleanup_retention_ratio": round(ratio, 4),
        "gutenberg_detected": gutenberg_detected,
        "risk_flags": risk_flags,
        "warnings": warnings,
        "failed": failed,
    }


def build_clean_text_sections_with_retention_guard(
    sections: List[Tuple[str, str]],
    *,
    drop_notes: bool,
    cleanup_settings: CleanupSettings | None = None,
    gutenberg_report: dict | None = None,
) -> tuple[List[Tuple[str, str]], dict]:
    """Clean sections and guard against catastrophic text loss.

    If a Gutenberg book loses most of its selected body during cleanup, retry
    with a conservative cleanup configuration. If the conservative pass still
    loses most text, raise an error instead of silently producing a tiny book.
    """

    cleanup_settings = cleanup_settings or CleanupSettings()
    cleaned = build_clean_text_sections(
        sections,
        drop_notes=drop_notes,
        cleanup_settings=cleanup_settings,
    )
    report = build_cleanup_retention_report(
        sections=sections,
        cleaned_sections=cleaned,
        gutenberg_report=gutenberg_report,
    )

    if report.get("failed"):
        conservative = CleanupSettings(
            join_soft_wrapped_lines=False,
            join_dialogue_continuations=False,
            merge_dialogue_paragraphs=False,
            aggressive_mode=False,
            collapse_extra_blank_lines=True,
            preserve_scene_breaks=True,
        )
        fallback = build_clean_text_sections(
            sections,
            drop_notes=drop_notes,
            cleanup_settings=conservative,
        )
        fallback_report = build_cleanup_retention_report(
            sections=sections,
            cleaned_sections=fallback,
            gutenberg_report=gutenberg_report,
        )
        fallback_report["fallback_attempted"] = True
        fallback_report["fallback_reason"] = "initial_cleanup_retention_too_low"

        if not fallback_report.get("failed"):
            fallback_report.setdefault("warnings", []).append(
                "Used conservative Gutenberg cleanup fallback because standard cleanup retained too little text."
            )
            return fallback, fallback_report

        raise ValueError(
            "Cleanup retained too little Gutenberg body text "
            f"({fallback_report.get('cleaned_text_chars')} chars from "
            f"{fallback_report.get('selector_selected_text_chars') or fallback_report.get('raw_section_text_chars')} chars). "
            "Aborting instead of producing an incomplete book."
        )

    report["fallback_attempted"] = False
    return cleaned, report

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


def strip_duplicate_opening_heading_paragraph(cleaned_html: str, heading: str) -> str:
    heading = heading.strip()
    if not heading:
        return cleaned_html

    lines = [line for line in cleaned_html.splitlines() if line.strip()]
    if not lines:
        return cleaned_html

    match = re.fullmatch(r"<p>(.*?)</p>", lines[0].strip())
    if not match:
        return cleaned_html

    first_para = html.unescape(match.group(1)).strip()

    def normalize(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip().casefold()

    if normalize(first_para) == normalize(heading):
        return "\n".join(lines[1:]).strip()

    return cleaned_html


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
        cleaned = strip_duplicate_opening_heading_paragraph(cleaned, heading)

        if not cleaned.strip():
            continue

        heading_html = (
            f'<h1 class="chapter-title">{html.escape(heading)}</h1>' if heading else ""
        )
        chapter_class = "chapter first-body-chapter" if first_real_section else "chapter"
        first_real_section = False

        blocks.append(
            f'<section class="{chapter_class}">{heading_html}{cleaned}</section>'
        )

    return blocks


def build_css(settings: LayoutSettings) -> str:
    mode = (settings.paragraph_spacing_mode or "traditional").strip().lower()

    if mode == "uniform":
        paragraph_css = """
p {
  margin: 0;
  text-align: justify;
  text-indent: 0;
  orphans: 2;
  widows: 2;
}

.chapter p + p {
  text-indent: 0;
  margin-top: 0;
}
"""
    elif mode == "no-indents":
        paragraph_css = """
p {
  margin: 0 0 0.65em 0;
  text-align: justify;
  text-indent: 0;
  orphans: 2;
  widows: 2;
}

.chapter p + p {
  text-indent: 0;
}
"""
    elif mode == "indented-compact":
        paragraph_css = """
p {
  margin: 0;
  text-align: justify;
  text-indent: 0;
  orphans: 2;
  widows: 2;
}

.chapter p {
  text-indent: 1.2em;
}

.chapter p.scene-break {
  text-indent: 0;
}

.chapter p + p {
  text-indent: 1.2em;
  margin-top: 0;
}
"""
    else:
        paragraph_css = """
p {
  margin: 0 0 0.65em 0;
  text-align: justify;
  text-indent: 0;
  orphans: 2;
  widows: 2;
}

.chapter p {
  text-indent: 1.2em;
}

.chapter p.scene-break {
  text-indent: 0;
}

.chapter p + p {
  text-indent: 1.2em;
}
"""

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

.cover-page {{
  break-after: page;
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}}

.cover-page img {{
  max-width: 90%;
  max-height: 90vh;
  object-fit: contain;
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

{paragraph_css}

h1, h2, h3, h4 {{
  page-break-after: avoid;
}}

em {{
  font-style: italic;
}}

strong {{
  font-weight: bold;
}}

hr, .scene-break {{
  margin: 1.2em auto;
  width: 25%;
  border: 0;
  border-top: 1px solid #666;
}}


.generated-contents {{
  break-after: page;
  page-break-after: always;
  margin: 0 auto 2em auto;
}}

.generated-contents h2 {{
  text-align: center;
  font-size: 1.35em;
  margin: 0 0 1.2em 0;
  text-indent: 0;
}}

.generated-contents ol {{
  list-style: none;
  margin: 0;
  padding: 0;
}}

.generated-contents li {{
  margin: 0.35em 0;
  padding: 0;
  text-indent: 0;
}}

.generated-contents a {{
  color: inherit;
  text-decoration: none;
}}

.generated-contents a::after {{
  content: leader(".") target-counter(attr(href), page);
}}

.toc-anchor {{
  display: block;
  height: 0;
  overflow: hidden;
}}


.book-image {{
  break-inside: avoid;
  page-break-inside: avoid;
  text-align: center;
  margin: 1.4em auto;
  text-indent: 0;
}}

.book-image img {{
  display: block;
  max-width: 88%;
  max-height: 72vh;
  object-fit: contain;
  margin: 0 auto;
}}

.book-image figcaption {{
  font-size: 0.85em;
  line-height: 1.2;
  text-align: center;
  margin-top: 0.4em;
  text-indent: 0;
}}



"""


def build_html_document(
    *,
    title: str,
    author: str,
    sections: List[Tuple[str, str]],
    settings: LayoutSettings,
    cleanup_settings: CleanupSettings | None = None,
    cover_image_data_uri: str = "",
) -> str:
    cover_block = ""
    if cover_image_data_uri:
        cover_block = f"""
<section class="cover-page">
  <img src="{cover_image_data_uri}" alt="{html.escape(title)} cover" />
</section>
"""

    blocks = [
        cover_block,
        f"""
<section class="title-page">
  <div class="title-wrap">
    <h1>{html.escape(title)}</h1>
    <p class="author">{html.escape(author)}</p>
  </div>
</section>
<div class="blank-page"></div>
""",
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
  <meta charset="utf-8" />
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


def default_output_markdown_path(output_dir: Path, book_slug: str) -> Path:
    return output_dir / markdown_name(book_slug)


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

def _add_page_number_field(paragraph) -> None:
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")

    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"

    fld_separate = OxmlElement("w:fldChar")
    fld_separate.set(qn("w:fldCharType"), "separate")

    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")

    run = paragraph.add_run()
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_separate)
    run._r.append(fld_end)


def _configure_docx_section(section, settings: LayoutSettings) -> None:
    section.page_width = Cm(settings.trim_width_cm)
    section.page_height = Cm(settings.trim_height_cm)

    section.top_margin = Cm(settings.margin_top_cm)
    section.bottom_margin = Cm(settings.margin_bottom_cm)
    section.left_margin = Cm(settings.margin_inside_cm)
    section.right_margin = Cm(settings.margin_outside_cm)

    section.footer_distance = Cm(0.8)

    footer = section.footer
    footer.is_linked_to_previous = False

    # Clear all existing footer paragraphs/runs so page number is only added once
    for paragraph in footer.paragraphs:
        p = paragraph._element
        p.getparent().remove(p)

    footer_p = footer.add_paragraph()
    footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_page_number_field(footer_p)


def _apply_docx_paragraph_format(paragraph, settings: LayoutSettings, *, is_first_in_block: bool) -> None:
    """Apply body paragraph formatting for DOCX export.

    Issue #18:
    In indented modes, normal body paragraphs should indent consistently,
    including the first paragraph after a chapter/story heading.
    """
    fmt = paragraph.paragraph_format
    mode = (settings.paragraph_spacing_mode or "traditional").strip().lower()

    if mode == "uniform":
        fmt.space_before = Pt(0)
        fmt.space_after = Pt(0)
        fmt.first_line_indent = Pt(0)
    elif mode == "no-indents":
        fmt.space_before = Pt(0)
        fmt.space_after = Pt(settings.font_size_pt * 0.65)
        fmt.first_line_indent = Pt(0)
    elif mode == "indented-compact":
        fmt.space_before = Pt(0)
        fmt.space_after = Pt(0)
        fmt.first_line_indent = Pt(settings.font_size_pt * 1.2)
    else:
        fmt.space_before = Pt(0)
        fmt.space_after = Pt(settings.font_size_pt * 0.65)
        fmt.first_line_indent = Pt(settings.font_size_pt * 1.2)

    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def export_clean_docx(
    *,
    title: str,
    author: str,
    sections: List[Tuple[str, str]],
    output_path: str | Path | None,
    settings: LayoutSettings,
) -> Path | None:
    if output_path is None:
        return None

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = Document()

    # Base document section
    section = doc.sections[0]
    _configure_docx_section(section, settings)

    # Normal style
    normal_style = doc.styles["Normal"]
    normal_style.font.size = Pt(settings.font_size_pt)

    # Title page
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_para.add_run(title)
    title_run.bold = True
    title_run.font.size = Pt(settings.font_size_pt * 2.0)

    if author.strip():
        author_para = doc.add_paragraph()
        author_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        author_run = author_para.add_run(author)
        author_run.font.size = Pt(settings.font_size_pt * 1.15)

    first_section = True

    for heading, text in sections:
        if first_section:
            doc.add_page_break()
            first_section = False
        else:
            new_section = doc.add_section(WD_SECTION_START.NEW_PAGE)
            _configure_docx_section(new_section, settings)

        if heading.strip():
            heading_para = doc.add_paragraph()
            heading_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            heading_run = heading_para.add_run(heading.strip())
            heading_run.bold = True
            heading_run.font.size = Pt(settings.font_size_pt * 1.45)
            heading_para.paragraph_format.space_after = Pt(settings.font_size_pt * 1.8)

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        first_body_paragraph = True

        for para in paragraphs:
            p = doc.add_paragraph()

            if is_scene_break(para) or para == "***":
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run("***")
                run.bold = False
                p.paragraph_format.space_before = Pt(settings.font_size_pt * 1.2)
                p.paragraph_format.space_after = Pt(settings.font_size_pt * 1.2)
                p.paragraph_format.first_line_indent = Pt(0)
                first_body_paragraph = True
                continue

            run = p.add_run(para)
            run.font.size = Pt(settings.font_size_pt)
            _apply_docx_paragraph_format(
                p,
                settings,
                is_first_in_block=first_body_paragraph,
            )
            first_body_paragraph = False

    doc.save(str(output_path))
    return output_path


def _escape_markdown_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("*", "\\*").replace("_", "\\_")


def export_clean_markdown(
    *,
    title: str,
    author: str,
    sections: List[Tuple[str, str]],
    output_path: str | Path,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    parts: list[str] = [f"# {_escape_markdown_text(title)}"]

    if author.strip():
        parts.append("")
        parts.append(f"_By {_escape_markdown_text(author)}_")

    for heading, text in sections:
        parts.append("")
        if heading.strip():
            parts.append(f"## {_escape_markdown_text(heading.strip())}")
            parts.append("")

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        for para in paragraphs:
            if is_scene_break(para) or para == "***":
                parts.append("***")
            else:
                parts.append(_escape_markdown_text(para))
            parts.append("")

    markdown_text = "\n".join(parts).rstrip() + "\n"
    output_path.write_text(markdown_text, encoding="utf-8")
    return output_path



def export_epub_image_assets(epub_path: str | Path, output_dir: str | Path, *, book_slug: str = "book") -> list[str]:
    """Export EPUB image resources beside generated outputs.

    This is intentionally non-invasive: it does not yet alter body flow,
    but it preserves all image resources for later Markdown/DOCX/PDF use.
    """
    epub_path = Path(epub_path)
    output_dir = Path(output_dir)
    assets_dir = output_dir / f"{book_slug}-assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    book = epub.read_epub(str(epub_path))
    exported: list[str] = []
    manifest: list[dict[str, str | int]] = []

    used_names: set[str] = set()

    for item in book.get_items():
        media_type = str(getattr(item, "media_type", "") or "")
        name = str(item.get_name() or "")
        lower_name = name.lower()

        if not (
            media_type.startswith("image/")
            or lower_name.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"))
        ):
            continue

        base = Path(name).name or "image"
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("_") or "image"

        if safe in used_names:
            stem = Path(safe).stem
            suffix = Path(safe).suffix
            n = 2
            while f"{stem}_{n}{suffix}" in used_names:
                n += 1
            safe = f"{stem}_{n}{suffix}"

        used_names.add(safe)
        out_path = assets_dir / safe
        data = item.get_content()
        out_path.write_bytes(data)

        exported.append(str(out_path))
        manifest.append(
            {
                "source_name": name,
                "output_file": str(out_path),
                "media_type": media_type,
                "size_bytes": len(data),
            }
        )

    if manifest:
        manifest_path = assets_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        exported.append(str(manifest_path))

    return exported


def process_epub_to_pdf(
    *,
    epub_path: str | Path,
    output_pdf_path: str | Path | None = None,
    output_docx_path: str | Path | None = None,
    output_markdown_path: str | Path | None = None,
    export_docx: bool = False,
    export_markdown: bool = False,
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
        cover_image_data_uri=getattr(epub_content, "cover_image_data_uri", ""),
    )

    book_slug = build_book_slug(
        title=used_title,
        author=used_author,
        fallback_stem=epub_path.stem,
    )

    image_asset_files: list[str] = []
    try:
        output_asset_dir = Path(output_pdf_path).parent if output_pdf_path is not None else epub_path.parent
        image_asset_files = export_epub_image_assets(epub_path, output_asset_dir, book_slug=book_slug)
    except Exception:
        image_asset_files = []

    output_pdf = (
        Path(output_pdf_path)
        if output_pdf_path is not None
        else default_output_pdf_path(
            epub_path,
            used_title=used_title,
            used_author=used_author,
        )
    )

    render_pdf(html_doc, output_pdf)

    clean_text_sections, cleanup_retention_report = build_clean_text_sections_with_retention_guard(
        epub_content.sections,
        drop_notes=settings.drop_notes,
        cleanup_settings=cleanup_settings,
        gutenberg_report=getattr(epub_content, "gutenberg_report", None),
    )

    output_docx: Path | None = None
    if export_docx:
        output_docx = (
            Path(output_docx_path)
            if output_docx_path is not None
            else default_output_docx_path(output_pdf.parent, book_slug)
        )
        export_clean_docx(
            title=used_title,
            author=used_author,
            sections=clean_text_sections or [],
            output_path=output_docx,
            settings=settings,
        )

    output_markdown: Path | None = None
    if export_markdown:
        output_markdown = (
            Path(output_markdown_path)
            if output_markdown_path is not None
            else default_output_markdown_path(output_pdf.parent, book_slug)
        )
        export_clean_markdown(
            title=used_title,
            author=used_author,
            sections=clean_text_sections or [],
            output_path=output_markdown,
        )

    result = EpubToPdfResult(
        input_epub=epub_path,
        output_dir=output_pdf.parent,
        output_pdf=output_pdf,
        output_docx=output_docx,
        output_markdown=output_markdown,
        book_slug=book_slug,
        detected_title=epub_content.detected_title,
        detected_author=epub_content.detected_author,
        used_title=used_title,
        used_author=used_author,
    )
    # Attached dynamically to avoid a broad public dataclass/API change.
    result.gutenberg_report = getattr(epub_content, "gutenberg_report", None)
    result.cleanup_retention_report = cleanup_retention_report
    return result


# --- ChapterFOLD layout-heavy cleanup integration START ---
# Applied after the normal text cleanup pipeline. This keeps the integration
# low-risk: normal extraction still runs first, then we remove accidental
# control artifacts and compact repeated ASCII divider noise.
try:
    from core.layout_heavy import clean_layout_heavy_text

    _chapterfold_original_build_clean_text_sections_layout_heavy = build_clean_text_sections

    def build_clean_text_sections(*args, **kwargs):  # type: ignore[no-redef]
        sections = _chapterfold_original_build_clean_text_sections_layout_heavy(*args, **kwargs)
        cleaned_sections = []
        for heading, text in sections:
            cleaned_sections.append((heading, clean_layout_heavy_text(text)))
        return cleaned_sections
except Exception:
    # Do not break imports if this module is loaded in a partial/dev context.
    pass
# --- ChapterFOLD layout-heavy cleanup integration END ---

