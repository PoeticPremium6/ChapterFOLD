# TOC Render Integration

Issue #20 adds a Markdown-level table-of-contents policy to the pre-edit workflow.

The first implementation is deliberately simple and reliable:

```bash
python scripts/render_markdown_book.py Edited.md outputs --toc-mode rebuild
```

Supported modes:

- `keep` — leave the edited/source contents as-is.
- `remove` — remove an obvious `Contents` / `Table of Contents` block.
- `rebuild` — remove the old contents block and insert a clean generated contents list from Markdown headings.

This does not yet add page numbers. Page-synced TOC generation should be handled later with a two-pass PDF render.

Recommended client workflow:

1. Convert EPUB normally and open `Editable.md`.
2. Edit/delete/reorder text as needed.
3. Render the edited Markdown with `--toc-mode rebuild`.
4. Inspect the generated PDF.

Future enhancement:

- two-pass PDF page-number TOC,
- GUI dropdown for TOC mode,
- conversion report entries for detected TOC headings and inserted entries.
