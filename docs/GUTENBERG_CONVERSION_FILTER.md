# Gutenberg conversion filtering

Patch 010 wires the Gutenberg spine selector into the actual EPUB loading path.

## Why

Patch 009 showed that Gutenberg EPUBs have healthy body text, but the body needs
to be selected by EPUB spine structure rather than by global START/END text
slices.

## Behaviour

When ChapterFOLD detects Project Gutenberg markers/boilerplate, it now:

1. builds selector-compatible records for each EPUB document item;
2. drops obvious front Gutenberg notice/contents items;
3. drops final Gutenberg license items;
4. keeps substantial body spine items;
5. falls back to keeping all items if selected retention is dangerously low;
6. attaches a retention report to the loaded EPUB content.

This should reduce failures where Gutenberg books produce only a title page,
notices, or a tiny fragment of the real book.

## What to test next

Run the four local Gutenberg books through the GUI or CLI using standard cleanup
and `indented-compact`:

```bash
python scripts/check_project.py
python chapterfold_app/app.py
```

For CLI/API testing, use a small output folder outside Git-tracked fixtures:

```bash
mkdir -p tmp_outputs/gutenberg
python scripts/run_chapterfold_job.py "tests/fixtures/gutenberg/raw/Little Women.epub" tmp_outputs/gutenberg --dry-run
```

The raw Gutenberg EPUBs and generated reports should remain ignored and should
not be committed.
