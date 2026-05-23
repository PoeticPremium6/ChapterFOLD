# Gutenberg Batch Assessment

This tool runs ChapterFOLD over a folder of local Gutenberg EPUBs and summarises output quality across the set.

It is designed for before/after checks while improving Gutenberg handling.

## Run current conversion batch

```bash
python scripts/assess_gutenberg_batch.py \
  tests/fixtures/gutenberg/raw \
  reports/gutenberg_batch_after
```

The script writes per-book outputs and:

```text
reports/gutenberg_batch_after/summary.md
reports/gutenberg_batch_after/summary.csv
reports/gutenberg_batch_after/summary.json
```

## Before/after workflow

A true "before" comparison needs an old commit or saved outputs.

Option A: before changing code, run:

```bash
python scripts/assess_gutenberg_batch.py tests/fixtures/gutenberg/raw reports/gutenberg_batch_before
```

Then after changes:

```bash
python scripts/assess_gutenberg_batch.py \
  tests/fixtures/gutenberg/raw \
  reports/gutenberg_batch_after \
  --baseline reports/gutenberg_batch_before
```

Option B: if code has already changed, check out the previous commit/branch, run the baseline, then return to your working branch and run the after assessment.

## What to inspect

Focus on:

- `markdown_chars`
- `pdf_pages`
- `selected_text_chars`
- `warnings`
- `markdown_first_body_line`

For failures like the old Moby Dick case, the warnings should flag suspiciously tiny Markdown or PDF output.
