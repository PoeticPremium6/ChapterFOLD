# Issue 22: Pre-editing workflow

ChapterFOLD now supports the first safe version of a pre-edit workflow:

```text
EPUB -> Editable.md -> user edits Markdown -> PDF/DOCX
```

This is intended to replace fragile workflows like:

```text
Word / Google Docs -> EPUB -> ChapterFOLD cleanup
```

Word/Docs EPUB exports often contain messy HTML, heavy inline spans, unstable headings,
and odd anchors. Markdown is easier for users to inspect, delete sections from, merge,
and regenerate.

## Basic workflow

1. Run an EPUB through ChapterFOLD as usual.
2. Open the generated `Editable.md`.
3. Delete author notes, unwanted sections, or combine text from another `Editable.md`.
4. Render the edited Markdown:

```bash
python scripts/render_markdown_book.py edited_book.md outputs/edited_book
```

Optional DOCX:

```bash
python scripts/render_markdown_book.py edited_book.md outputs/edited_book --docx
```

Optional metadata overrides:

```bash
python scripts/render_markdown_book.py edited_book.md outputs/edited_book \
  --title "Combined Volume" \
  --author "Various"
```

## What this patch does not do yet

This patch does not add a GUI button. It adds the rendering foundation first.

Recommended next patch:

```text
Patch 016: GUI option / Tools > Render edited Markdown
```

Then:

```text
Patch 017: combine multiple Markdown books
```
