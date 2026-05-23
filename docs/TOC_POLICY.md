# ChapterFOLD table-of-contents policy

Issue #20 introduces a safe first step for table-of-contents handling.

ChapterFOLD can now apply a Markdown-level TOC policy:

- `keep`: keep the source TOC as-is.
- `remove`: remove a clear `Contents` / `Table of Contents` block.
- `rebuild`: remove the source TOC and insert a clean generated `## Contents` list from detected headings.

Example:

```bash
python scripts/rebuild_toc_markdown.py \
  "Book - Editable.md" \
  "Book - Rebuilt TOC.md" \
  --mode rebuild \
  --report-json reports/book_toc_report.json
```

Then render the edited Markdown:

```bash
python scripts/render_markdown_book.py "Book - Rebuilt TOC.md" reports/rendered
```

## Why page numbers are not included yet

Page numbers only exist after PDF rendering. A page-synced TOC needs a later two-pass render:

1. render the book once,
2. detect heading page positions,
3. generate a page-numbered TOC,
4. render the final PDF.

This patch deliberately starts with reliable source-TOC policy and clean Markdown TOC rebuilding.
