# Gutenberg local fixtures

Put real Project Gutenberg EPUB files in:

```text
tests/fixtures/gutenberg/raw/
```

These files are intentionally ignored by Git because they are full books and can be large.

Generate inspection reports with:

```bash
python scripts/inspect_gutenberg_batch.py tests/fixtures/gutenberg/raw reports/gutenberg
```
