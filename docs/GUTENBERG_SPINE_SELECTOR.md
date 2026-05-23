# Gutenberg spine selector

Patch 009 adds a safer way to reason about Project Gutenberg EPUBs.

## Problem found

The previous inspection logic estimated body text by looking between global
Project Gutenberg START/END markers. In several Gutenberg EPUBs this produced a
false body estimate of only a few hundred characters, even when the EPUB clearly
contained hundreds of thousands of characters across spine items.

This happens because Gutenberg EPUBs commonly use this structure:

```text
front notice / contents / START marker
chapter spine item 1
chapter spine item 2
...
final license / END marker
```

## Patch 009 behaviour

The new selector:

- orders HTML files by EPUB spine position;
- drops empty/wrap items;
- drops front Gutenberg notice/contents items;
- drops final Gutenberg license items;
- drops short link-heavy contents pages;
- keeps substantial spine items;
- keeps chapter-heading spine items;
- keeps short prefaces/dedications after frontmatter.

The inspector now reports:

```text
spine_selected_body_text_chars
spine_selected_body_retention_ratio
spine_selected_body_item_count
gutenberg_body_selection.decisions
```

## Re-run reports

```bash
python scripts/inspect_gutenberg_batch.py tests/fixtures/gutenberg/raw reports/gutenberg
```

Then check:

```bash
cat reports/gutenberg/summary.md
```

This patch does **not** change the main ChapterFOLD conversion path yet. It
only improves diagnosis and creates a reusable selector.
