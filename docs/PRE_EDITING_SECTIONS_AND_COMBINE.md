# Pre-editing with sections and combined books

Patch 016 extends the pre-editing workflow introduced in Patch 015.

The intended workflow is:

```text
EPUB -> Editable.md -> sectionize/edit/combine -> render final PDF
```

## Add section markers

```bash
python scripts/sectionize_markdown_book.py \
  "Book - Editable.md" \
  "Book - Sectioned.md" \
  --manifest reports/book_sections.md
```

The output contains comments such as:

```markdown
<!-- chapterfold-section: Chapter One -->
## Chapter One
```

These comments make it easier to delete, search, move, or combine sections.

## Combine two edited books

```bash
python scripts/combine_markdown_books.py \
  book_a_sectioned.md \
  book_b_sectioned.md \
  --title "Combined Volume" \
  --author "Various Authors" \
  --output combined_volume.md \
  --manifest combined_manifest.md
```

Then render the combined Markdown using Patch 015:

```bash
python scripts/render_markdown_book.py combined_volume.md reports/combined_volume
```

## Why this matters

Users can remove author notes, combine short books, or make manual edits without going through Word/Google Docs -> EPUB again.

This is safer because Markdown is easier to inspect and less likely to contain messy Word/Docs HTML.
